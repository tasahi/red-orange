"""
Pydantic models for the OrangeRed API.

Defines DomainSchema/ColumnSpec (the sidecar that preserves Orange Domain
metadata when data crosses the pandas ↔ Orange boundary) and all
request/response models used by the REST API.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Domain metadata sidecar
# ---------------------------------------------------------------------------

class VarType(str, Enum):
    CONTINUOUS = "continuous"
    DISCRETE = "discrete"
    TIME = "time"
    STRING = "string"


class ColumnSpec(BaseModel):
    """Description of a single variable in the Orange domain."""

    name: str
    var_type: VarType
    values: Optional[list[str]] = None          # ordered categories (discrete)
    number_of_decimals: Optional[int] = None    # display precision (continuous)


class DomainSchema(BaseModel):
    """
    Metadata sidecar that preserves Orange Domain information across the
    pandas ↔ Orange Table boundary.

    When a user sends data as a DataFrame (JSON rows), the DomainSchema
    tells us which columns are features, which is the target, and which
    are metas — information that a flat DataFrame does not carry.
    """

    attributes: list[ColumnSpec] = Field(default_factory=list)
    class_vars: list[ColumnSpec] = Field(default_factory=list)
    metas: list[ColumnSpec] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Signal descriptors (used by the registry & orchestrator)
# ---------------------------------------------------------------------------

class SignalDesc(BaseModel):
    """Machine-readable description of one widget input or output."""

    name: str                       # e.g. "Data", "Learner"
    type: str                       # e.g. "Orange.data.Table"
    flags: dict[str, bool] = Field(default_factory=dict)


class SettingSpec(BaseModel):
    """Description of one user-configurable widget setting."""

    name: str
    type: str                       # "int" | "float" | "bool" | "str" | "enum"
    default: Any = None
    choices: Optional[list[Any]] = None
    description: str = ""


class WidgetDescriptor(BaseModel):
    """Full description of a widget type exposed by the registry."""

    id: str                         # e.g. "data.HLDataSampler"
    name: str                       # e.g. "Data Sampler"
    category: str                   # e.g. "Transform"
    inputs: list[SignalDesc]
    outputs: list[SignalDesc]
    settings: list[SettingSpec] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# REST request / response models
# ---------------------------------------------------------------------------

class CreateWorkflowRequest(BaseModel):
    name: str = "Untitled Workflow"


class AddNodeRequest(BaseModel):
    widget_type: str                # registry id, e.g. "data.HLDataSampler"
    settings: dict[str, Any] = Field(default_factory=dict)


class UpdateSettingsRequest(BaseModel):
    settings: dict[str, Any]


class AddLinkRequest(BaseModel):
    source_node: str
    source_output: str
    sink_node: str
    sink_input: str


class NodeSpec(BaseModel):
    id: str  # The client-provided ID (Node-RED ID)
    widget_type: str
    settings: dict[str, Any] = Field(default_factory=dict)


class LinkSpec(BaseModel):
    source_node: str  # The client-provided ID (Node-RED ID)
    source_output: str
    sink_node: str    # The client-provided ID (Node-RED ID)
    sink_input: str


class BatchSetupRequest(BaseModel):
    nodes: list[NodeSpec]
    links: list[LinkSpec]


class InjectDataRequest(BaseModel):
    """Payload for pushing a DataFrame + optional schema into a node."""

    data: list[dict[str, Any]]      # JSON rows  (orient="records")
    schema_: Optional[DomainSchema] = Field(None, alias="schema")


class NodeStatusResponse(BaseModel):
    node_id: str
    status: str
    error: Optional[str] = None


class TableOutputResponse(BaseModel):
    """A Table-type output serialised for the API consumer."""

    data: list[dict[str, Any]]      # DataFrame rows (orient="records")
    schema_: DomainSchema = Field(alias="schema")

    model_config = {"populate_by_name": True}


class ColumnStats(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    std: Optional[float] = None
    distribution: Optional[dict[str, int]] = None
    missing: int = 0


class TablePreviewResponse(BaseModel):
    """Paginated preview of a Table output with summary stats."""

    total_rows: int
    total_cols: int
    schema_: DomainSchema = Field(alias="schema")
    rows: list[dict[str, Any]]
    column_stats: dict[str, ColumnStats]

    model_config = {"populate_by_name": True}


class MetricsResponse(BaseModel):
    """Evaluation metrics for one or more learners."""
    learners: list[str]
    scores: dict[str, list[float]]  # e.g., "CA": [0.95, 0.96]
    confusion_matrix: dict[str, list[list[int]]]
    class_names: list[str]
