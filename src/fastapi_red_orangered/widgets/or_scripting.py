"""
Headless scripting widgets — provides a Jupyter-like Python cell
inside the OrangeRed visual canvas.

The user writes arbitrary Python code that executes against the
input data on the backend, with full access to Orange, NumPy, and Pandas.
"""

from __future__ import annotations

import io
import contextlib
import traceback
import logging
from typing import Any, Optional

import numpy as np
import pandas as pd

from Orange.data import Table, Domain, ContinuousVariable, DiscreteVariable, StringVariable

from ..headless_widget import HeadlessWidget
from ..schemas import SignalDesc

_log = logging.getLogger(__name__)


# ======================================================================
# Python Script — Jupyter-like Cell
# ======================================================================

class HLPythonScript(HeadlessWidget):
    """
    Execute arbitrary Python code against the input data.

    This widget acts like a single Jupyter notebook cell.  The user's
    script receives pre-bound variables and is expected to assign its
    results to conventional output names.

    Inputs
    ------
    - ``Data``       : primary ``Orange.data.Table`` (bound as ``in_data``)
    - ``Extra Data`` : secondary ``Orange.data.Table`` (bound as ``in_extra``)
    - ``Object``     : any Python object from upstream (bound as ``in_object``)

    Outputs
    -------
    - ``Data``   : whatever the script assigns to ``out_data``
    - ``Object`` : whatever the script assigns to ``out_object``

    State Variables
    ---------------
    The namespace dict is **preserved between executions** (like cells
    in a Jupyter notebook).  Any variable created in one execution
    is available in the next, enabling incremental workflows.
    """

    def get_input_signals(self) -> list[SignalDesc]:
        return [
            SignalDesc(name="Data", type="Orange.data.Table", flags={}),
            SignalDesc(name="Extra Data", type="Orange.data.Table", flags={}),
            SignalDesc(name="Object", type="object", flags={}),
        ]

    def get_output_signals(self) -> list[SignalDesc]:
        return [
            SignalDesc(name="Data", type="Orange.data.Table", flags={"default": True}),
            SignalDesc(name="Object", type="object", flags={}),
        ]

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self.data: Optional[Table] = None
        self.extra_data: Optional[Table] = None
        self.in_object: Any = None
        self._settings: dict[str, Any] = {
            "script": (
                "# Your Python code here\n"
                "# Available variables:\n"
                "#   in_data   — primary input table (Orange.data.Table or None)\n"
                "#   in_extra  — secondary input table (or None)\n"
                "#   in_object — any upstream Python object (or None)\n"
                "#\n"
                "# Assign results to:\n"
                "#   out_data   — Table to send downstream\n"
                "#   out_object — any Python object to send downstream\n"
                "#\n"
                "# Pre-imported: np (numpy), pd (pandas), Table, Domain\n"
                "# State: variables persist between executions\n"
                "\n"
                "out_data = in_data\n"
            ),
        }
        # Persistent namespace — survives across executions like Jupyter state
        self._namespace: dict[str, Any] = {}
        # Last captured console output
        self._console_output: str = ""

    def receive(self, input_name: str, value: Any) -> None:
        if input_name == "Data":
            self.data = value
        elif input_name == "Extra Data":
            self.extra_data = value
        elif input_name == "Object":
            self.in_object = value

    def handle_new_signals(self) -> None:
        script = self._settings.get("script", "")

        if not script.strip():
            self.send("Data", self.data)
            self.send("Object", None)
            self._console_output = ""
            return

        # Update the persistent namespace with current inputs and
        # convenience imports.  Previous state variables are preserved.
        self._namespace.update({
            # Inputs
            "in_data": self.data,
            "in_extra": self.extra_data,
            "in_object": self.in_object,
            # Clear previous outputs so stale values don't leak
            "out_data": None,
            "out_object": None,
            # Convenience imports
            "np": np,
            "pd": pd,
            "Table": Table,
            "Domain": Domain,
            "ContinuousVariable": ContinuousVariable,
            "DiscreteVariable": DiscreteVariable,
            "StringVariable": StringVariable,
        })

        # Capture stdout (print statements)
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()

        try:
            with contextlib.redirect_stdout(stdout_buf), \
                 contextlib.redirect_stderr(stderr_buf):
                exec(script, self._namespace)

            self._console_output = stdout_buf.getvalue()
            stderr_output = stderr_buf.getvalue()
            if stderr_output:
                self._console_output += "\n--- stderr ---\n" + stderr_output

        except Exception:
            tb = traceback.format_exc()
            self._console_output = f"--- Error ---\n{tb}"
            _log.warning("PythonScript node %s exec error:\n%s", self.node_id, tb)
            self.send("Data", None)
            self.send("Object", None)
            return

        # Read outputs from namespace
        out_data = self._namespace.get("out_data", None)
        out_object = self._namespace.get("out_object", None)

        self.send("Data", out_data)
        self.send("Object", out_object)
