---
title: React Flow UI Implementation & Migration Plan (JSON-RPC 2.0 & MCP Powered)
document_type: Technical Architecture & Detailed Implementation Plan
project: red-orange
host_framework: red-fastapi
status: Ready for Implementation
phases: 5 (Phases 1 through 5)
date: October 2026
---

# React Flow UI Implementation & Migration Plan (JSON-RPC 2.0 & MCP Powered)

**Project:** `red-orange`  
**Host Framework:** `red-fastapi` (featuring JSON-RPC 2.0 & MCP Adapter)  
**Target Architecture:** Dual-Interface Canvas (Node-RED Classic & React Flow Modern)  
**Document Type:** Detailed Implementation Blueprint  
**Status:** Approved for Implementation  

---

## 1. Executive Summary & Design Vision

The objective of this plan is to deliver a modern, high-performance **React Flow** web interface for `red-orange` that works seamlessly alongside the existing **Node-RED** editor.

### Core Goals:
1. **Familiarity & Spatial Continuity:** The React Flow UI must preserve the classic Node-RED layout—3-column workspace (Left Palette, Center Canvas with Tabbed Workspaces, Right Configuration/Debug Sidebar), standard node color palettes, handle placements, and wire ergonomics. A Node-RED user must feel immediately at home.
2. **Powered by JSON-RPC 2.0 & MCP:** Leverage `red-fastapi`'s native JSON-RPC 2.0 management API (`flows.get`, `flows.set`, `nodes.trigger`, `nodes.list`) and MCP tool integration rather than fragmented REST calls.
3. **Non-Concurrent Dual-UI Selection:** Allow users to dynamically switch between the Node-RED UI and the React Flow UI via a top-bar toggle or configuration preference, with both frontends operating on the exact same flows and in-memory Python runtime.
4. **Enhanced Data Science Capabilities:** Leverage React Flow's modular rendering to support in-node mini previews (e.g. data shapes, distributions, miniature confusion matrices), type-safe port validation, and collapsible subflow groups.

---

## 2. High-Level System Architecture

```
+-----------------------------------------------------------------------------------------+
|                                    User Browser                                         |
|    +--------------------------------+             +--------------------------------+    |
|    |      Node-RED Classic UI       |   Switch    |      React Flow Modern UI      |    |
|    |    Route: /ui/node-red or /    |<----------->|      Route: /ui/react-flow     |    |
|    +--------------------------------+             +--------------------------------+    |
|                    \                                              /                     |
+---------------------\--------------------------------------------/----------------------+
                       \                                          /
                        v                                        v
+-----------------------------------------------------------------------------------------+
|                                   red-fastapi Gateway                                   |
|  - JSON-RPC 2.0 Router: POST /api/rpc & WS /api/rpc/ws                                  |
|  - MCP Server & SSE Transport: GET /mcp/sse & POST /mcp/messages                        |
|  - Static File Server: Mounts React Flow SPA bundle and Node-RED editor client          |
+-----------------------------------------------------------------------------------------+
                                             |
                                             v
+-----------------------------------------------------------------------------------------+
|                                red-orange Plugin Core                                   |
|  - Flow Translation Engine: Bidirectional Node-RED Flow <===> React Flow Graph          |
|  - Python Flow Engine: FileLoaderNode, PCANode, RandomForestNode, etc.                  |
|  - Shared In-Memory State: Orange Tables, Learners, SciPy ndarrays (Zero-Copy)          |
+-----------------------------------------------------------------------------------------+
```

---

## 3. UI Layout & Spatial Ergonomics Specification

To maintain complete workflow continuity for Node-RED users, the interface layout adheres to the canonical three-section layout:

```
+------------------------------------------------------------------------------------------------------+
| [Logo] Red-Orange | [Tab 1: Iris Classification] [Tab 2: Image FFT] [+] | [Deploy v] [Switch to NR]  |
+----------------------+-------------------------------------------------------+-----------------------+
| PALETTE (Left)       | CANVAS (Center)                                       | SIDEBAR (Right)       |
| -------------------- | ----------------------------------------------------- | --------------------- |
| 🔍 Filter nodes...  |   +--------------------+      +--------------------+  | [Config] [Debug] [Data]|
|                      |   | File Loader (Iris) |      | Select Columns     |  |                       |
| > OR Data            |   | [150 rows, 4 cols] |-(D)->| [3 Features]       |  | Node: File Loader     |
|   (o) File Loader    |   +--------------------+      +--------------------+  | --------------------- |
|   (o) Data Sampler   |                                       | (D)           | Name: Iris Data       |
|   (o) Select Columns |                                       v               | File: data/iris.tab   |
| > OR Transform       |                             +--------------------+    | Sheet: Sheet 1        |
|   (o) Normalize      |                             | Random Forest      |    | --------------------- |
|   (o) PCA            |                             | [100 Trees]        |    | [ Done ] [ Cancel ]   |
| > OR Model           |                             +--------------------+    | --------------------- |
|   (o) Random Forest  |                                                       | Debug Messages (RPC): |
|   (o) Logistic Reg   |                                                       | [12:30:01] 150 rows   |
+----------------------+-------------------------------------------------------+-----------------------+
| FOOTER: Engine: Active | Active Nodes: 14 | Protocol: JSON-RPC 2.0 (WS Connected) | Latency: 4ms     |
+------------------------------------------------------------------------------------------------------+
```

### 3.1 Left Palette (Node Catalog)
- **Categories:** Preserves existing Red-Orange categories (`OR Data`, `OR Transform`, `OR Model`, `OR Evaluate`, `OR Visualize`, `OR Scripting`, `OR Bridge`, `OR SciPy`).
- **Drag-and-Drop:** Uses HTML5 Drag and Drop (`onDragStart` transferring node type and default parameters; `onDrop` onto the React Flow canvas resolving canvas coordinate offsets via `reactFlowInstance.screenToFlowPosition`).

### 3.2 Center Canvas (React Flow Surface)
- **Multi-Tab Workspaces:** Top navigation bar displays open workspaces (corresponding to Node-RED `tab` nodes). Adding or renaming a tab updates the flow manifest.
- **Node Appearance:**
  - Classic Node-RED dimensions (~140px width, ~36px height base).
  - Categorical color-coded left icon badges (e.g., `#FFAA00` for OR Data, `#87A987` for OR Model).
  - Smooth Bezier or Step curves for connecting wires.
- **Ports & Handles:**
  - Left handle: Target (`input`).
  - Right handle: Source (`output`). For multi-output nodes (e.g. `Data Sampler`), handles are vertically stacked on the right edge.
- **Interactive Trigger Buttons:**
  - Inject nodes and manually triggered Orange nodes feature an integrated left-side trigger button that executes `nodes.trigger` via JSON-RPC.

### 3.3 Right Sidebar (Properties & Observability)
- **Double-Click Edit:** Double-clicking a node opens its configuration pane in the sidebar (or drawer modal).
- **Tabs:**
  - **Node Properties:** Dynamically rendered form inputs based on the node schema.
  - **Debug Console:** Live feed connected to `comms` / RPC events displaying runtime messages.
  - **Data Viewer:** Dedicated tab embedding Tabulator tables or Plotly charts fetched on-demand.

---

## 4. JSON-RPC 2.0 Integration & State Management

All operations between the React Flow UI and the backend engine run over JSON-RPC 2.0 (`/api/rpc` or WebSocket `/api/rpc/ws`):

### 4.1 RPC Methods Used by React Flow UI

| RPC Method | Parameters | Return Value | Purpose |
| :--- | :--- | :--- | :--- |
| `system.info` | `{}` | `{ version, active_nodes, engine_state }` | Initial connection handshake and runtime status verification. |
| `nodes.list` | `{}` | `List[NodeDefinition]` | Populates the Left Palette with available nodes, schemas, icons, and default configs. |
| `flows.get` | `{}` | `{ flows: List[NodeRedNode], rev: str }` | Fetches the active flow definitions on canvas load. |
| `flows.set` | `{ flows: List[NodeRedNode] }` | `{ status: "ok", rev: str }` | Deploys the converted flow when user clicks **Deploy**. |
| `nodes.trigger` | `{ node_id: str, payload?: dict }` | `{ status: "ok" }` | Triggers a manual node execution (e.g. File re-read or Inject). |
| `tools.list` | `{}` | `List[MCPTool]` | Highlights/badges nodes that are currently exposed as MCP tools to AI agents. |
| `redorange.preview` | `{ node_id: str, limit?: int }` | `{ columns: [...], rows: [...], stats: {...} }` | Fetches data table or visualization preview without full page refresh. |

---

## 5. Bidirectional Flow Translation Specification

A core requirement is that flows can be opened, edited, and saved in either editor without data loss.

### 5.1 Node-RED to React Flow (`nr_to_rf`)
```typescript
function convertNodeRedToReactFlow(nrNodes: NodeRedNode[]): { nodes: RFNode[], edges: RFEdge[], tabs: RFTab[] } {
  const tabs = nrNodes.filter(n => n.type === 'tab');
  const regularNodes = nrNodes.filter(n => n.type !== 'tab');
  
  const nodes: RFNode[] = regularNodes.map(n => ({
    id: n.id,
    type: 'orangeNode',
    position: { x: n.x, y: n.y },
    data: {
      type: n.type,
      name: n.name || n.type,
      z: n.z, // Tab workspace ID
      config: { ...n } // Retain all custom attributes
    }
  }));

  const edges: RFEdge[] = [];
  regularNodes.forEach(sourceNode => {
    if (Array.isArray(sourceNode.wires)) {
      sourceNode.wires.forEach((wireGroup, portIndex) => {
        wireGroup.forEach(targetId => {
          edges.push({
            id: `e-${sourceNode.id}-${portIndex}-${targetId}`,
            source: sourceNode.id,
            target: targetId,
            sourceHandle: `out-${portIndex}`,
            targetHandle: 'in-0'
          });
        });
      });
    }
  });

  return { nodes, edges, tabs };
}
```

### 5.2 React Flow to Node-RED (`rf_to_nr`)
```typescript
function convertReactFlowToNodeRed(nodes: RFNode[], edges: RFEdge[], tabs: RFTab[]): NodeRedNode[] {
  const nrNodes: NodeRedNode[] = [...tabs];

  nodes.forEach(rfNode => {
    const outgoingEdges = edges.filter(e => e.source === rfNode.id);
    
    // Group wires by output port index
    const wires: string[][] = [];
    outgoingEdges.forEach(edge => {
      const portIndex = edge.sourceHandle ? parseInt(edge.sourceHandle.replace('out-', ''), 10) : 0;
      while (wires.length <= portIndex) wires.push([]);
      wires[portIndex].push(edge.target);
    });

    nrNodes.push({
      ...rfNode.data.config,
      id: rfNode.id,
      type: rfNode.data.type,
      name: rfNode.data.name,
      x: Math.round(rfNode.position.x),
      y: Math.round(rfNode.position.y),
      z: rfNode.data.z,
      wires: wires
    });
  });

  return nrNodes;
}
```

---

## 6. Phased Implementation Roadmap

### Phase 1: RPC Client & Bidirectional Flow Adapter
- **Deliverables:**
  1. Lightweight TypeScript JSON-RPC 2.0 client (`src/client/rpcClient.ts`) connecting to `red-fastapi`'s `/api/rpc` and `/api/rpc/ws`.
  2. Pure bidirectional translation utility (`src/utils/flowAdapter.ts`) with 100% test coverage validating round-trip fidelity between Node-RED JSON and React Flow state.

### Phase 2: React Flow Foundation & Node-RED Palette Mirroring
- **Deliverables:**
  1. Vite + React + React Flow application scaffolded in `frontend/`.
  2. Left Palette rendering node categories (`OR Data`, `OR Model`, etc.) fetched via `nodes.list` RPC.
  3. Drag-and-drop registration placing nodes onto canvas.
  4. Custom `OrangeNode` component replicating Node-RED's visual styling (icon badge, label, status pill, stacked output ports).

### Phase 3: Canvas Workspace, Tabs & Deployment
- **Deliverables:**
  1. Top Tab Bar supporting multiple workspaces (`tab` nodes).
  2. Global **Deploy** button executing `flows.set` via JSON-RPC.
  3. Real-time runtime status indicators (running, stopped, error) updated via WebSocket RPC notifications.
  4. Header UI Switcher button navigating between `/ui/node-red` and `/ui/react-flow`.

### Phase 4: Properties Drawer, Debug Console & Preview Widgets
- **Deliverables:**
  1. Right sidebar with property editors dynamically constructed for Orange nodes.
  2. Live Debug output viewer connected to RPC event stream.
  3. Data table preview drawer embedding Tabulator / Plotly components via `redorange.preview` RPC calls.

### Phase 5: FastApi Packaging, Build & End-to-End Validation
- **Deliverables:**
  1. Production build workflow compiling React Flow SPA into static assets served by `red-fastapi`.
  2. Preference persistence in browser `localStorage` and backend settings.
  3. End-to-end integration tests verifying flow creation in React Flow, execution in Python, and validation in Node-RED.
