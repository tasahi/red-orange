# 1. OrangeRed — Concepts & Architecture

[⬅ Back to README](../README.md) | * English | [Español](es/1_concepts_and_introduction_es.md)

> **Purpose of this document:** Establish the conceptual foundations, architectural principles, and functional organization of OrangeRed. Read this document first before proceeding to the [Developer Guide](2_developer_guide.md) or [User Guide](3_user_guide.md).

---

## 1. What is OrangeRed?

**OrangeRed** is a hybrid visual data mining, machine learning, and scientific computing toolkit. It combines the data mining algorithms of **Orange3** (a Python-based data science platform) and the n-dimensional array processing of **SciPy/xarray**, with the web-based visual flow orchestration of **Node-RED**.

OrangeRed allows data scientists, engineers, and analysts to construct complex data pipelines, train machine learning models, inspect interactive charts, and run scientific array manipulations by wiring nodes on a browser canvas—without mandatory code writing.

```
┌────────────────────────────────────────────────────────┐
│               Frontend: Node-RED Canvas                │
│   • Visual DAG composition & palette (OR categories)   │
│   • Inline Tabulator previews & interactive charts     │
│   • Lightweight reference pointers across wires        │
└───────────────────────────┬────────────────────────────┘
                            │ REST / WebSockets / JSON
┌───────────────────────────▼────────────────────────────┐
│              Backend: FastAPI + Python Engine          │
│   • Headless DAG Orchestrator (Topological Sort)       │
│   • Orange3 Data Engine (Table, DomainSchema, Models)  │
│   • SciPy & xarray N-D Array & Image/Audio Processing  │
│   • MLflow-compatible Experiment Tracking              │
└────────────────────────────────────────────────────────┘
```

### The Challenge
**Orange Data Mining** is traditionally a desktop desktop-only application. Its execution engine is deeply entangled with the PyQt/Qt GUI framework, preventing it from running natively in headless cloud, containerized, or web environments. Furthermore, standard visual flow tools either lack native data science semantics or struggle to manage high-dimensional arrays efficiently.

### The Solution
OrangeRed solves this by completely decoupling the **Visual Canvas** from the **Execution Engine**:
- **Frontend (Node-RED):** Serves as the UI and flow orchestration canvas. It is responsible for node layouts, configuration dialogs, parameter inspection, and rendering data visualizations (scatter plots, distributions, decision trees, confusion matrices, and images).
- **Backend (FastAPI):** Serves as the headless computation engine. It receives the Directed Acyclic Graph (DAG) specification, topologically sorts and executes the analytical pipeline in Python, manages datasets in memory, and logs model training runs.

---

## 2. Core Architecture: Passing Pointers, Not Data

A central design principle in OrangeRed is how data moves between connected nodes.

In standard Node-RED flows, complete messages containing entire payloads (`msg.payload`) pass through wires between nodes. For large machine learning datasets (tens or hundreds of thousands of rows) or heavy serialized models, passing raw data over Node.js event loops and WebSocket connections causes severe serialization bottlenecks, memory bloat, and browser crashes.

In OrangeRed, **heavy datasets and models never traverse the Node-RED wires**.

Instead, OrangeRed passes **Lightweight Reference Pointers**:

1. **Backend Storage:** When an upstream node finishes execution, its output (e.g., an `Orange.data.Table` or `xarray.DataArray`) is retained in memory by the backend orchestrator.
2. **Wire Signals:** The Node-RED wire conveys a lightweight reference envelope containing the `Workflow ID`, `Node ID`, and the output port identifier.
3. **Downstream Execution:** The downstream node sends this pointer back to the backend, directing the execution engine to fetch the exact memory-mapped data structure for the next analytical step.

---

## 3. The Bridge Concept: Merging Event-Driven & Analytical Computing

Traditional Node-RED is fundamentally **event-driven** (handling individual sensor pulses, webhooks, or MQTT packets as they arrive), whereas Orange Data Mining is fundamentally **batch/analytical** (processing tabular datasets, training models, and computing statistical matrices).

OrangeRed bridges these two paradigms using dedicated **Bridge Nodes**:

* **`OR Bridge In` (`or-bridge-in`):** Accepts standard event-driven `msg.payload` data (JSON arrays, database query results, incoming REST requests) from native Node-RED nodes, converts them into tabular datasets on the backend, and triggers the analytical pipeline.
* **`OR Bridge Out` (`or-bridge-out`):** Extracts model predictions, filtered subsets, or computed evaluation metrics from the analytical pipeline and emits them as standard Node-RED `msg.payload` objects into the native flow (e.g., to trigger MQTT alerts, update dashboard gauges, or write to external databases).

This architecture allows you to create end-to-end intelligent systems: ingest IoT sensor telemetry via MQTT, run preprocessing and real-time anomaly detection or model inference in OrangeRed, and forward alerts downstream via standard Node-RED integrations.

---

## 4. Multi-Layer Visualization Strategy

Since the backend holds the underlying data in memory, OrangeRed utilizes a dual-tier visualization model:

1. **Inline Tabular Previews:** Every node producing tabular data features an embedded **Preview** tab. When opened, the frontend queries a paginated API endpoint to retrieve a small slice (e.g., the first 50 rows) along with variable role metadata (continuous, discrete, meta, target), rendered with the `Tabulator` engine.
2. **Dedicated Interactive Visualizations:**
   * **Plotly.js Visualizations:** Nodes such as `Scatter Plot`, `Histogram`, `Box Plot`, and `Line Plot` dynamically fetch data slices (up to configurable limits, e.g., 10,000 points) and generate responsive visualizations with zoom, pan, and hover tooltips.
   * **D3.js Hierarchical Trees:** The `Tree Viewer` node extracts the nested splitting rules of trained Decision Trees and renders interactive, collapsible tree diagrams.
   * **Diagnostic Heatmaps & Curves:** `Confusion Matrix` and `ROC Analysis` nodes retrieve cross-validation probabilities and render interactive heatmaps and multi-class ROC curves.
   * **Image & Audio Inspection:** Dedicated viewers render multi-dimensional image arrays and audio spectrograms directly within the canvas.

---

## 5. Storage, State & Execution Modes

### Workflow Persistence
* **Design-Time Storage (Node-RED):** The canonical flow configuration, node positions, hyperparameter settings, and wiring are saved in Node-RED's standard flow storage (`flows.json` in the user's Node-RED user directory, typically `~/.node-red/` or `%USERPROFILE%\.node-red\`).
* **Runtime State (FastAPI Backend):** When the user deploys a flow, the graph topology and settings are synchronized to the Python backend via atomic batch setup endpoints. Workflows exist as active execution sessions in memory.

### Headless & Programmatic Execution
OrangeRed does not require an active browser session to execute pipelines:

1. **REST API-Driven:** Trigger executions, inject data, and extract outputs programmatically via standard HTTP endpoints (e.g., `POST /api/workflows/{id}/execute`).
2. **Pure Python Embed:** Import the `Orchestrator` (`src/orchestrator.py`) directly into automated Python services or batch jobs without launching the HTTP server.
3. **Headless Node-RED:** Run Node-RED in daemon mode (`node-red -u /path/to/data`) on edge devices or servers to orchestrate pipelines in the background.

---

## 6. Next Steps

* To learn how OrangeRed is implemented, how the DAG engine functions, and how to write custom nodes or call REST endpoints, see the [Developer Guide](2_developer_guide.md).
* To learn how to build workflows, configure models, and explore the complete 40+ node catalog, see the [User Guide](3_user_guide.md).
