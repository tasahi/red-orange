# React Flow UI Integration & Dual-UI Architecture Proposal

**Project:** `red-orange`  
**Document Type:** Architectural Proposal & Design Specification  
**Status:** Draft / Proposal  
**Date:** October 2026  

---

## 1. Executive Summary

`red-orange` currently runs as a first-class plugin inside `red-fastapi`, relying on the **Node-RED** HTML/jQuery-based web UI for authoring and viewing data science workflows.

While Node-RED provides a robust workflow canvas, modern scientific data workflows benefit significantly from the flexibility of modern web frameworks—specifically **React Flow**. React Flow allows for:
- Rich, in-node embedded previews (e.g., interactive data tables, inline mini-plots, distribution histograms).
- Strongly-typed ports with named connection handles (Orange Data, Learner, Model, Preprocessor).
- Modern component ecosystem support (React, Tailwind CSS, shadcn/ui, Radix UI).
- Flexible node layout customization, nested subflows, and expandable groups.

This proposal defines an architecture where **both the Node-RED UI and the React Flow UI can coexist**, allowing the user to select their interface of choice (non-concurrently) while sharing the same underlying Python execution runtime and in-memory Orange3/SciPy data structures.

---

## 2. High-Level Architecture: Headless Kernel & Flow Adapter

The core principle is **decoupling execution and node metadata from the frontend canvas format**.

```
                           +-----------------------------------------------+
                           |       User UI Selection / Mode Switch         |
                           +-----------------------------------------------+
                                          /                 \
                                         v                   v
                     +-----------------------+   +-------------------------+
                     | Node-RED UI (Classic) |   | React Flow Canvas (New) |
                     | (/red or /ui/node-red)|   | (/ui/react-flow)        |
                     +-----------------------+   +-------------------------+
                                 \                           /
                                  \                         /
                                   v                       v
                           +-----------------------------------------------+
                           |            Flow Translation Layer             |
                           |  Node-RED Flow JSON  <===> React Flow Graph   |
                           +-----------------------------------------------+
                                                   |
                                                   v
                           +-----------------------------------------------+
                           |      red-orange Python Core Engine            |
                           |  - Node execution logic (FileLoader, PCA, etc)|
                           |  - Zero-copy in-memory tables & learners      |
                           |  - REST / WebSocket runtime APIs (red-fastapi)|
                           +-----------------------------------------------+
```

### 2.1 Preserving the Core Python Runtime
The Python engine in `red-orange` (`base_node.py`, `nodes/`, `widgets/`, `tracker.py`, and `api.py`) remains agnostic of the authoring frontend. Nodes operate on input/output messages and property configurations.

### 2.2 Bi-directional Flow Translation Layer
To ensure flows authored in either interface are interchangeable, a translation layer bridges the graph schemas:

| Property | Node-RED Flow Model | React Flow Model |
| :--- | :--- | :--- |
| **Graph Structure** | Flat list of node objects; wires stored as array of target node IDs inside the source node (`wires: [[target_id]]`). | Distinct `nodes` array and `edges` array (`{ id, source, target, sourceHandle, targetHandle }`). |
| **Positions** | `{ x: number, y: number }` top-level properties on each node. | `{ position: { x: number, y: number } }`. |
| **Node Configuration** | Custom node properties directly at node root level. | Stored cleanly inside the `data` object (`node.data`). |
| **Ports & Handles** | Indexed outputs (`wires[0]`, `wires[1]`), implicit single input. | Explicit named source and target handles (`sourceHandle="data"`, `targetHandle="model"`). |

A translation service (available in Python and/or TypeScript) converts between both formats losslessly:
- `convert_nodered_to_reactflow(nr_flow) -> rf_graph`
- `convert_reactflow_to_nodered(rf_graph) -> nr_flow`

---

## 3. UI Selection & Coexistence Strategy

Both user interfaces will be hosted by the `red-fastapi` server, enabling users to choose their workflow environment without maintaining two independent server deployments.

### 3.1 Route-Based Switching
- **Node-RED UI**: Accessible at `/` or `/ui/node-red`.
- **React Flow UI**: Accessible at `/ui/react-flow`.
- **Global Header Switcher**: A header bar toggle button in both frontends:
  > `[ Switch to React Flow ]` ⮀ `[ Switch to Node-RED ]`

### 3.2 Workspace & Session State Management
To prevent race conditions and concurrent mutation of the same active workspace:
1. **Single Active Flow Engine**: The backend maintains a single source of truth for the deployed flow in memory/disk.
2. **Session / Lock Awareness**: When opening one interface, it queries the current engine state. Changes published from either UI trigger a deployment reload in the shared runtime.
3. **User Preference Persistence**: User choice is persisted in browser local storage or `~/.red-fastapi/settings.json` (`"preferred_ui": "react-flow"`), determining the default redirect when accessing the root URL.

---

## 4. Declarative Node Metadata (Schema-Driven Palette)

Currently, Node-RED nodes are registered via HTML template definitions (`templates/nodes/*.html`). To empower React Flow and maintain clean parity:

1. **Declarative Node Schema**: Define node metadata in a unified declarative structure (JSON/YAML or Pydantic models in Python):
   ```json
   {
     "type": "or-file-loader",
     "category": "OR Data",
     "label": "File",
     "color": "#FFAA00",
     "inputs": [],
     "outputs": [
       { "id": "data", "label": "Data", "type": "Orange.data.Table" }
     ],
     "properties": {
       "filename": { "type": "string", "label": "File Path", "widget": "file_picker" },
       "sheet": { "type": "string", "label": "Sheet Name", "default": "" }
     }
   }
   ```
2. **Dual-Consumer Generation**:
   - For **Node-RED**: Generated or matched with existing HTML script tags (`RED.nodes.registerType`).
   - For **React Flow**: Consumed by generic custom React nodes that dynamically render ports, labels, icons, and configuration sidebars/drawers.

---

## 5. Advantages of React Flow for `red-orange`

1. **Embedded In-Node Previews & Widgets**:
   - Small live sparklines, miniature confusion matrices, classification accuracy scores, or data shape indicators can be rendered directly within the node's canvas card without requiring a popup dialog.
2. **Named Multi-Port Connections**:
   - Orange3 relies heavily on semantic ports (e.g., *Learner* vs *Data* vs *Preprocessor*). React Flow natively supports custom styled handles that visually indicate compatibility and prevent invalid connections.
3. **Hierarchical & Nested Subflows**:
   - Workflows can be grouped visually into collapsible composite components (e.g., preprocessing subpipelines or model ensembles).
4. **Modern Frontend Extensibility**:
   - Direct compatibility with React component libraries (Radix UI, shadcn/ui, Tailwind CSS, TanStack Table) for data viewer inspection panels.

---

## 6. Implementation Roadmap

### Phase 1: Flow Schema & Bi-directional Adapter
- Define the canonical schema bridge.
- Implement and test `convert_nodered_to_reactflow` and `convert_reactflow_to_nodered` with round-trip unit tests covering existing test workflows (`tests/test_plugin.py`).

### Phase 2: React Flow Canvas Web Application
- Scaffold a lightweight Vite + React + React Flow application (`frontend/react-flow` or companion package).
- Implement standard custom node cards (`OrangeNode`, `VisualizerNode`, `EvaluatorNode`).
- Connect custom nodes to the existing `red-orange` REST APIs (`/api/redorange/data-table`, `/api/redorange/scatter-plot`, etc.).

### Phase 3: FastApi Hosting & Switcher Integration
- Mount the React Flow static build inside `red-fastapi`.
- Implement navigation headers allowing one-click switching between Node-RED and React Flow.
- Add user UI preference configuration.

### Phase 4: Enhanced Data Science Features in React Flow
- In-node live preview cards.
- Integrated side-drawer inspection panels for Tabulator and Plotly views.
- Type-safe edge validation preventing incompatible connections (e.g., wiring an un-trained learner directly to a scatter plot).

