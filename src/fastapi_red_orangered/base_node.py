""" Base Node adapter connecting HeadlessWidgets with FastAPI-Red's FlowEngine.
"""

from __future__ import annotations

import asyncio
import copy
import logging
from typing import Any, Dict, List, Optional, Type

from fastapi_red.runtime.node import Node
from fastapi_red_orangered.headless_widget import HeadlessWidget
from fastapi_red_orangered.schemas import SignalDesc

logger = logging.getLogger("fastapi_red_orangered.base_node")

# Global node cache allowing preview API to fetch last known outputs
# node_id -> {"widget": HeadlessWidget, "outputs": dict[str, Any], "status": str, "error": str}
preview_cache: Dict[str, Dict[str, Any]] = {}


class _NodeOutputSink:
    """ Stand-in for HeadlessWidget's orchestrator dispatching outputs.
    """

    def __init__(self, node_wrapper: "OrangeBaseNode"):
        self.node_wrapper = node_wrapper

    def dispatch_output(self, node_id: str, output_name: str, value: Any) -> None:
        self.node_wrapper.record_output(output_name, value)


class OrangeBaseNode(Node):
    """ Wraps any OrangeRed HeadlessWidget into an asyncio Node-RED Node.
    """

    widget_cls: Type[HeadlessWidget]
    input_names: List[str] = []
    output_names: List[str] = []

    def __init__(self, config: Dict[str, Any], flow: Optional[Any] = None):
        super().__init__(config, flow)
        self.sink = _NodeOutputSink(self)
        self.widget = self.widget_cls(self.id, self.sink)  # type: ignore[arg-type]
        self.pending_outputs: Dict[str, Any] = {}
        self.last_status = "idle"
        self.last_error: Optional[str] = None

        # Apply settings from node config
        mapped_settings = self.map_config_to_settings(config)
        self.widget.update_settings(mapped_settings)

        # Register in global preview cache
        preview_cache[self.id] = {
            "widget": self.widget,
            "outputs": {},
            "status": "idle",
            "error": None,
        }

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """ Override in subclasses to extract specific widget settings.
        Default handles common camelCase -> snake_case parameters.
        """
        settings: Dict[str, Any] = {}
        if "filePath" in config:
            settings["file_path"] = config["filePath"]
        return settings

    def record_output(self, output_name: str, value: Any) -> None:
        self.pending_outputs[output_name] = value
        if self.id in preview_cache:
            preview_cache[self.id]["outputs"][output_name] = value

    async def on_input(self, msg: Dict[str, Any]) -> None:
        """ Handles message arrival from upstream wires.
        """
        await self.status(fill="blue", shape="dot", text="computing...")
        self.last_status = "running"
        if self.id in preview_cache:
            preview_cache[self.id]["status"] = "running"
            preview_cache[self.id]["error"] = None

        try:
            # 1. Deliver input signal into widget
            self.deliver_input(msg)

            # 2. Run widget's core computation in threadpool if CPU-bound
            self.pending_outputs.clear()
            await asyncio.to_thread(self.widget.handle_new_signals)

            # 3. Dispatch outputs to downstream ports
            # Node-RED supports multi-port outputs: [[msg_port_0], [msg_port_1], ...]
            port_messages: List[Optional[Dict[str, Any]]] = []
            for out_name in self.output_names:
                if out_name in self.pending_outputs:
                    val = self.pending_outputs[out_name]
                    port_messages.append({
                        "payload": val,
                        "_orange_signal": out_name,
                        "topic": msg.get("topic", "")
                    })
                else:
                    port_messages.append(None)

            if any(port_messages):
                await self.send(port_messages)

            # 4. Status update
            await self.status(fill="green", shape="dot", text="ready")
            self.last_status = "completed"
            if self.id in preview_cache:
                preview_cache[self.id]["status"] = "completed"

        except Exception as exc:
            logger.error(f"Error executing Orange node {self.id} ({self.type}): {exc}", exc_info=True)
            self.last_status = "error"
            self.last_error = str(exc)
            if self.id in preview_cache:
                preview_cache[self.id]["status"] = "error"
                preview_cache[self.id]["error"] = str(exc)
            await self.status(fill="red", shape="dot", text=str(exc)[:20])
            await self.error(str(exc), msg)

    def deliver_input(self, msg: Dict[str, Any]) -> None:
        """ Maps incoming message signal to widget input.
        """
        val = msg.get("payload")
        signal_name = msg.get("_orange_signal")

        if signal_name and signal_name in self.input_names:
            self.widget.receive(signal_name, val)
        elif self.input_names:
            # Default to first input port if unspecified
            self.widget.receive(self.input_names[0], val)

    async def close(self) -> None:
        await super().close()
        # Clean up preview cache if desired or retain for inspection
