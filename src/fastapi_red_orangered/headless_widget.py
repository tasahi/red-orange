"""
Headless widget base class.

Provides the ``HeadlessWidget`` abstract base and the ``_OutputProxy`` that
replaces ``self.Outputs.X.send()`` with a callback into the DAG
orchestrator — no Qt required.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from .schemas import SignalDesc

if TYPE_CHECKING:
    from .orchestrator import Orchestrator

log = logging.getLogger(__name__)


class _OutputProxy:
    """
    Stand-in for ``self.Outputs.<signal>``.

    Calling ``proxy.send(value)`` dispatches the value through the
    orchestrator so that it reaches every linked downstream widget.
    """

    def __init__(
        self,
        name: str,
        sig_type: str,
        orchestrator: Orchestrator,
        node_id: str,
    ):
        self.name = name
        self.type = sig_type
        self._orchestrator = orchestrator
        self._node_id = node_id

    def send(self, value: Any) -> None:
        self._orchestrator.dispatch_output(self._node_id, self.name, value)


class HeadlessWidget(ABC):
    """
    Abstract base for headless Orange widget wrappers (Strategy B).

    Subclasses must implement:
      * ``get_input_signals``  — declare accepted inputs
      * ``get_output_signals`` — declare produced outputs
      * ``receive``            — handle an incoming signal
      * ``handle_new_signals`` — run the widget's core computation

    Subclasses should also populate ``self.default_settings`` in their
    ``__init__`` and may override ``update_settings`` for validation.
    """

    def __init__(self, node_id: str, orchestrator: Orchestrator):
        self.node_id = node_id
        self._orchestrator = orchestrator
        self._settings: dict[str, Any] = {}
        self._outputs: dict[str, _OutputProxy] = {}
        self._setup_outputs()

    # ------------------------------------------------------------------
    # Signal metadata (each subclass defines its own)
    # ------------------------------------------------------------------

    @abstractmethod
    def get_input_signals(self) -> list[SignalDesc]:
        ...

    @abstractmethod
    def get_output_signals(self) -> list[SignalDesc]:
        ...

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _setup_outputs(self) -> None:
        for sig in self.get_output_signals():
            self._outputs[sig.name] = _OutputProxy(
                sig.name, sig.type, self._orchestrator, self.node_id,
            )

    # ------------------------------------------------------------------
    # Public interface used by the orchestrator
    # ------------------------------------------------------------------

    def send(self, output_name: str, value: Any) -> None:
        """Emit a value on the named output signal."""
        proxy = self._outputs.get(output_name)
        if proxy is None:
            raise KeyError(
                f"Widget {type(self).__name__} has no output '{output_name}'"
            )
        proxy.send(value)

    @abstractmethod
    def receive(self, input_name: str, value: Any) -> None:
        """Accept a value on the named input signal."""
        ...

    @abstractmethod
    def handle_new_signals(self) -> None:
        """
        Called by the orchestrator after all pending inputs have been
        delivered.  This is where the widget runs its core computation
        and emits outputs via ``self.send()``.
        """
        ...

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    @property
    def settings(self) -> dict[str, Any]:
        return dict(self._settings)

    def update_settings(self, values: dict[str, Any]) -> None:
        """Merge *values* into the widget's current settings."""
        self._settings.update(values)

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------

    def get_output_type(self, output_name: str) -> str:
        for sig in self.get_output_signals():
            if sig.name == output_name:
                return sig.type
        raise KeyError(f"No output '{output_name}' on {type(self).__name__}")

    def get_input_type(self, input_name: str) -> str:
        for sig in self.get_input_signals():
            if sig.name == input_name:
                return sig.type
        raise KeyError(f"No input '{input_name}' on {type(self).__name__}")
