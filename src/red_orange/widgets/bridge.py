"""
Bridge widgets to connect RedOrange with native Node-RED msg.payload flows.
"""

from typing import Any
import pandas as pd

from ..headless_widget import HeadlessWidget
from ..schemas import SignalDesc
from ..conversion import dataframe_to_table, table_to_dataframe

class NodeRedIn(HeadlessWidget):
    """
    Acts as a data source in RedOrange.
    Accepts JSON payloads injected via the API and outputs them as Orange Tables.
    """
    
    def get_input_signals(self) -> list[SignalDesc]:
        return []

    def get_output_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Data", type="Orange.data.Table")]

    def receive(self, input_name: str, value: Any) -> None:
        pass

    def handle_new_signals(self) -> None:
        pass  # Data is pushed via inject_payload

    def inject_payload(self, payload: list[dict[str, Any]]) -> None:
        """
        Called directly by the /inject API endpoint.
        Converts a list of dictionaries into an Orange Table and emits it.
        """
        if not payload:
            return
            
        df = pd.DataFrame(payload)
        table = dataframe_to_table(df)
        self.send("Data", table)


class NodeRedOut(HeadlessWidget):
    """
    Acts as a data sink in RedOrange.
    Receives Orange Tables and caches them to be fetched as JSON via the API.
    """
    
    def __init__(self, node_id: str, orchestrator) -> None:
        super().__init__(node_id, orchestrator)
        self._cached_data: list[dict[str, Any]] | None = None

    def get_input_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Data", type="Orange.data.Table")]

    def get_output_signals(self) -> list[SignalDesc]:
        return []

    def receive(self, input_name: str, value: Any) -> None:
        if input_name == "Data":
            self._table = value

    def handle_new_signals(self) -> None:
        table = getattr(self, "_table", None)
        if table is None:
            self._cached_data = None
            return

        # Convert Orange Table back to DataFrame, then to records
        df, _ = table_to_dataframe(table)
        self._cached_data = df.to_dict(orient="records")

    def export_payload(self) -> list[dict[str, Any]] | None:
        """
        Called directly by the /export API endpoint.
        Returns the cached JSON data.
        """
        return self._cached_data
