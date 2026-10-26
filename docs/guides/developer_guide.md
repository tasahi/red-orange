# 2. OrangeRed — Developer Guide

[⬅ Back to README](../README.md) | * English | [Español](es/2_developer_guide_es.md)

> **Audience:** Backend and frontend developers maintaining, extending, or integrating OrangeRed.  
> **Pre-requisite:** Read [1_concepts_and_introduction.md](1_concepts_and_introduction.md) first.

---

## 1. System Overview & Repository Structure

OrangeRed is structured into a Python FastAPI computation backend and a Node-RED custom nodes package:

```text
orangered/
├── docs/                        # Project documentation (EN & ES)
│   ├── 1_concepts_and_introduction.md
│   ├── 2_developer_guide.md
│   ├── 3_user_guide.md
│   └── es/                      # Spanish documentation mirror
├── frontend/                    # Node-RED custom nodes package
│   ├── nodes/                   # Node UI templates (.html) and runtime scripts (.js)
│   ├── orangered-client.js      # Client communication module for FastAPI
│   └── package.json             # Node-RED node registration definitions
├── src/                         # FastAPI Backend Engine
│   ├── main.py                  # ASGI entrypoint
│   ├── api.py                   # REST endpoints and WebSocket handlers
│   ├── orchestrator.py          # DAG dependency graph, topological sort, execution engine
│   ├── headless_widget.py       # Qt-free abstract base classes for widgets and learners
│   ├── registry.py              # Master catalogue of all registered widget classes
│   ├── conversion.py            # Data gateway between pandas DataFrames and Orange Tables
│   ├── schemas.py               # Pydantic data models and schemas
│   ├── tracker.py               # MLflow-compatible experiment and run tracking
│   └── widgets/                 # Widget domain implementations:
│       ├── bridge.py            # Bridge nodes (NodeRedIn, NodeRedOut)
│       ├── or_data.py           # Data loading, sampling, selection, merge, concatenate
│       ├── or_model.py          # Classifiers, regressors, ensemble, baseline models
│       ├── or_preprocess.py     # Imputation, scaling, discretization, PCA, outliers
│       ├── or_unsupervised.py   # Clustering (k-Means, DBSCAN), manifold embeddings (t-SNE, MDS)
│       ├── or_evaluate.py       # Test & Score, Predictions, Confusion Matrix, ROC Analysis
│       ├── or_scripting.py      # Interactive Python script executor with state persistence
│       ├── sp_image.py          # SciPy n-dimensional image filters, morphology, Fourier
│       └── sp_audio.py          # SciPy audio processing and spectrogram generation
└── tests/                       # Automated test suite and environment probes
```

---

## 2. Data Contracts & Serialization

OrangeRed operates across distinct data boundaries. Internally, algorithms require specific in-memory structures, while HTTP APIs require JSON-serializable payloads.

### 2.1 Tabular Data: `Orange.data.Table` & `DomainSchema`
Orange algorithms require rich column semantics (Continuous, Discrete with defined categories, Class targets, and Meta attributes). Standard pandas DataFrames lack these distinctions.

To bridge this gap without data loss, `src/conversion.py` and `src/schemas.py` enforce a dual-contract mechanism:
* **`DomainSchema`**: Sidecar metadata defining:
  * `attributes`: List of input feature variables (`VariableSpec`).
  * `class_vars`: List of target / label variables.
  * `metas`: Ancillary columns (identifiers, textual annotations).
* **Ingestion (`dataframe_to_table`)**: Parses inbound tabular JSON records, constructs an explicit `Orange.data.Domain`, and instantiates an `Orange.data.Table`.
* **Egestion (`table_to_dataframe`)**: Converts `Orange.data.Table` instances into pandas DataFrames along with the exported `DomainSchema` for frontend consumption.

### 2.2 N-Dimensional Matrices: `xarray.DataArray`
SciPy image and audio nodes operate on multi-dimensional tensors. OrangeRed uses `xarray.DataArray` as the canonical format because it wraps raw NumPy arrays with labeled coordinate dimensions (e.g., `['height', 'width', 'channel']` or `['time', 'frequency']`).
* Images are streamed directly to the browser via dedicated `/image_preview` endpoints using PNG byte arrays.

### 2.3 Bridge & Scripting Payloads: Native JSON
Bridge nodes and the Python Scripting node accept arbitrary JSON dictionaries and lists from native Node-RED messages, allowing unstructured data ingestion and inter-node dictionary state passing.

---

## 3. Headless Widget Architecture

OrangeRed completely eliminates PyQt dependencies through the `HeadlessWidget` base class in `src/headless_widget.py`.

```python
class HeadlessWidget:
    def __init__(self, node_id: str, orchestrator: Orchestrator, settings: dict):
        self.node_id = node_id
        self._orchestrator = orchestrator
        self._settings = settings
        self._inputs = {}
        self._outputs = {}

    @classmethod
    def get_input_signals(cls) -> list[SignalDesc]:
        """Declared input ports and accepted types."""
        return []

    @classmethod
    def get_output_signals(cls) -> list[SignalDesc]:
        """Declared output ports and emitted types."""
        return []

    def receive(self, input_name: str, value: Any) -> None:
        """Invoked by orchestrator when incoming signals arrive."""
        self._inputs[input_name] = value

    def handle_new_signals(self) -> None:
        """Executes the computation and emits results via self.send()."""
        raise NotImplementedError

    def send(self, output_name: str, value: Any) -> None:
        """Publishes output to downstream links."""
        self._outputs[output_name] = value
```

### Base Learner Architecture (`_HLBaseLearner`)
Machine learning models subclass `_HLBaseLearner`. It automatically wraps Orange learners, trains models when connected to training data, tracks hyperparameters, and logs training run metadata into the MLflow-compatible tracker (`src/tracker.py`).

---

## 4. The DAG Orchestrator Engine (`src/orchestrator.py`)

The `Orchestrator` manages workflow execution:

1. **Topology & Graph Validation**: Maintains nodes and directed links. It verifies that connected ports match compatible types.
2. **Topological Sort**: Computes the linear execution order using Kahn's algorithm, guaranteeing that upstream dependencies execute prior to downstream consumers.
3. **Signal Propagation**: Iterates through sorted nodes:
   - Feeds cached inputs via `receive()`.
   - Triggers `handle_new_signals()`.
   - Routes emitted outputs through registered links to connected downstream inputs.
4. **Execution Status & Callbacks**: Fires state transition hooks (`idle` → `running` → `completed` or `error`) broadcast to WebSocket subscribers.

---

## 5. Complete REST & WebSocket API Reference

The backend exposes a full suite of REST endpoints on `http://127.0.0.1:8000`:

### 5.1 Registry & Workflow Lifecycle
* **`GET /api/registry`**: Returns metadata and input/output signal specifications for all registered widget types.
* **`POST /api/workflows`**: Creates a new isolated workflow execution session.
  * *Request:* `{"name": "string"}`
  * *Response:* `{"id": "string", "name": "string"}`
* **`GET /api/workflows/{wf_id}`**: Retrieves current workflow graph structure, node configurations, and execution states.
* **`POST /api/workflows/{wf_id}/batch_setup`**: Atomically registers all nodes and connections from a Node-RED deployment in a single transaction.
* **`POST /api/workflows/{wf_id}/execute`**: Asynchronously executes the entire DAG top-to-bottom.
* **`WS /api/workflows/{wf_id}/ws`**: Real-time WebSocket stream broadcasting execution status events (`node_id`, `status`, `error`).

### 5.2 Node & Link Manipulation
* **`POST /api/workflows/{wf_id}/nodes`**: Adds an individual node.
* **`PATCH /api/workflows/{wf_id}/nodes/{node_id}/settings`**: Updates hyperparameters or configuration properties for a node.
* **`DELETE /api/workflows/{wf_id}/nodes/{node_id}`**: Removes a node and all attached connections.
* **`POST /api/workflows/{wf_id}/links`**: Connects an output port of a source node to an input port of a sink node.
* **`DELETE /api/workflows/{wf_id}/links/{link_id}`**: Removes a connection.

### 5.3 Ingestion & Bridge Endpoints
* **`POST /api/workflows/{wf_id}/nodes/{node_id}/inject`**: Pushes a tabular JSON dataset directly into a node's input.
* **`POST /api/workflows/{wf_id}/nodes/{node_id}/bridge_inject`**: Receives an event-driven payload from `or-bridge-in`, converts it to an Orange Table, and triggers execution.
* **`GET /api/workflows/{wf_id}/nodes/{node_id}/bridge_export`**: Extracts exported data from an `or-bridge-out` node as JSON records.

### 5.4 Data Retrieval & Inspection
* **`GET /api/workflows/{wf_id}/nodes/{node_id}/status`**: Returns execution state (`idle`, `running`, `completed`, `error`).
* **`GET /api/workflows/{wf_id}/nodes/{node_id}/output/{output_name}`**: Returns full output table or object summary.
* **`GET /api/workflows/{wf_id}/nodes/{node_id}/preview/{output_name}?rows=50&offset=0`**: Returns a paginated slice of tabular data including column summary statistics (min, max, mean, std, distinct distributions, missing counts).
* **`GET /api/workflows/{wf_id}/nodes/{node_id}/metrics`**: Retrieves classification (CA, F1, AUC, Precision, Recall) or regression (RMSE, MAE, R²) metrics and confusion matrices from `Test & Score`.
* **`GET /api/workflows/{wf_id}/nodes/{node_id}/coefficients`**: Retrieves feature coefficients and intercepts from trained Logistic Regression or Linear Regression models.
* **`GET /api/workflows/{wf_id}/nodes/{node_id}/correlations`**: Returns the correlation matrix, p-values, and sorted pair list from a Correlations node.
* **`GET /api/workflows/{wf_id}/nodes/{node_id}/rank_scores`**: Returns feature ranking scores and selection metadata from a Rank node.
* **`GET /api/workflows/{wf_id}/nodes/{node_id}/roc`**: Computes multi-class ROC curve coordinate arrays (FPR vs TPR) for evaluated classifiers.
* **`GET /api/workflows/{wf_id}/nodes/{node_id}/tree_structure`**: Returns the nested decision tree JSON hierarchy for D3 visualization.
* **`GET /api/workflows/{wf_id}/nodes/{node_id}/console`**: Returns stdout/stderr streams captured during execution of a Python Script node.
* **`GET /api/workflows/{wf_id}/nodes/{node_id}/image_preview/{output_name}`**: Streams rendered PNG byte representation of an `xarray.DataArray`.

### 5.5 MLflow-Compatible Experiment Tracking
* **`GET /api/tracker/runs?node_id={node_id}`**: Lists historical training runs filtered optionally by node.
* **`GET /api/tracker/runs/{run_id}`**: Retrieves parameters, execution metrics, and artifacts for a specific training run.

---

## 6. Bridge Subsystem Protocol

The Bridge subsystem establishes bidirectional communication between Node-RED's Node.js engine and the Python backend:

```
[Node-RED Standard Nodes]
         │ (msg.payload JSON)
         ▼
[or-bridge-in Node] ──(HTTP POST /bridge_inject)──► [NodeRedIn Headless Widget]
                                                             │
                                                    (Orange Pipeline DAG)
                                                             │
[Node-RED Standard Nodes]                                    ▼
         ▲                                          [NodeRedOut Headless Widget]
         │ (msg.payload JSON)                                │
[or-bridge-out Node] ◄──(HTTP GET /bridge_export)────────────┘
```

1. **Ingress**: An incoming Node-RED message triggers `or-bridge-in.js`. The node calls `/bridge_inject`, which converts the payload into an `Orange.data.Table` and triggers a downstream workflow run.
2. **Egress**: When the workflow execution completes, `or-bridge-out.js` receives a completion signal, queries `/bridge_export` to fetch the processed results, and emits a standard `msg.payload` to downstream Node-RED nodes.

---

## 7. Python Scripting Sandbox Engine (`src/widgets/or_scripting.py`)

The `HLPythonScript` widget provides programmatic extensibility:
* **Inputs**: Supports two independent data tables (`in_data`, `in_data2`) and an optional input state dictionary (`in_state`).
* **Execution Environment**:
  ```python
  local_scope = {
      "in_data": in_table,
      "in_data2": in_table2,
      "in_state": in_state_dict,
      "out_data": None,
      "out_data2": None,
      "out_state": {},
      "pd": pd,
      "np": np,
      "Orange": Orange,
  }
  ```
* **Stdout/Stderr Capture**: Standard output is redirected via `io.StringIO` and stored in `_console_output` for retrieval by `/console`.
* **State Passing**: Variables saved to `out_state` are emitted to downstream nodes, allowing state persistence across sequential script cells.

---

## 8. Adding a New Custom Node (Step-by-Step)

Follow this recipe to implement and register a new OrangeRed node:

### Step 1: Implement the Headless Widget
Create or update a module in `src/widgets/` (e.g., `src/widgets/or_model.py`):

```python
from ..headless_widget import HeadlessWidget
from ..schemas import SignalDesc

class HLMyCustomNode(HeadlessWidget):
    @classmethod
    def get_input_signals(cls) -> list[SignalDesc]:
        return [SignalDesc(name="Data", type="Orange.data.Table")]

    @classmethod
    def get_output_signals(cls) -> list[SignalDesc]:
        return [SignalDesc(name="Filtered Data", type="Orange.data.Table")]

    def handle_new_signals(self) -> None:
        data = self._inputs.get("Data")
        if data is None:
            return
        
        # Perform computation
        processed = data.copy()
        self.send("Filtered Data", processed)
```

### Step 2: Register in `src/registry.py`
Add the widget to the `_WIDGETS` catalogue:

```python
_WIDGETS["transform.MyCustom"] = (HLMyCustomNode, "My Custom Node", "Transform")
```

### Step 3: Create the Node-RED Frontend Node
Create `frontend/nodes/or-my-custom.js` and `frontend/nodes/or-my-custom.html`:

```javascript
// frontend/nodes/or-my-custom.js
module.exports = function(RED) {
    const orangeredClient = require('../orangered-client');
    function MyCustomNode(config) {
        RED.nodes.createNode(this, config);
        orangeredClient.registerNode(this, config, 'transform.MyCustom');
    }
    RED.nodes.registerType('or-my-custom', MyCustomNode);
};
```

```html
<!-- frontend/nodes/or-my-custom.html -->
<script type="text/javascript">
    RED.nodes.registerType('or-my-custom', {
        category: 'OR Transform',
        color: '#ff9900',
        defaults: {
            name: { value: "" },
            threshold: { value: 0.5 }
        },
        inputs: 1,
        outputs: 1,
        icon: "font-awesome/fa-filter",
        label: function() { return this.name || "My Custom Node"; }
    });
</script>
```

### Step 4: Register in `frontend/package.json`
Add the node entry to the `"node-red"` dictionary:

```json
"node-red": {
    "nodes": {
        "or-my-custom": "nodes/or-my-custom.js"
    }
}
```

---

## 9. Testing & Quality Assurance

Run the automated test suite using Python:

```powershell
# Run the complete test suite
& 'C:\Programs\Python3\python.exe' -m pytest tests/ -v

# Run specific integration tests
& 'C:\Programs\Python3\python.exe' -m pytest tests/test_e2e_dag.py -v
& 'C:\Programs\Python3\python.exe' -m pytest tests/test_ml_api.py -v
```
