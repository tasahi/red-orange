---
title: React Flow Interface Integration & Architecture
document_type: Technical Architecture Specification
project: red-orange
status: Operational & Extending
date: October 2026
---

# React Flow Interface Integration & Architecture

**Project:** `red-orange`  
**Host Framework:** `red-fastapi`  
**Document Type:** Technical Architecture Specification  
**Status:** Architecture Specification  

---

## 1. System Overview & Dual-UI Architecture

`red-orange` supports two complementary frontend interfaces running against a shared, in-process Python runtime:
1. **Node-RED Editor (Classic):** The battle-tested canvas with existing palette nodes and configuration dialogs.
2. **React Flow Editor (Modern):** A dynamic, React-based web canvas tailored for advanced data science workflows, rich inline data previews, and typed multi-port connections.

Both interfaces communicate with the same `red-fastapi` backend, sharing the same underlying flow files and zero-copy in-memory Orange3/SciPy data tables.

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
                           |  - JSON-RPC 2.0 & WebSocket APIs              |
                           +-----------------------------------------------+
```

---

## 2. Core Modules (`src/flow/`)

The React Flow subsystem is cleanly separated into modular TypeScript layers:

| Module | Responsibility | Key Exports |
| :--- | :--- | :--- |
| [`types.ts`](file:///c:/Documents/Programming/red-orange/src/flow/types.ts) | Canonical schemas for JSON-RPC 2.0 messages, Node-RED flows, and React Flow graphs. | `JsonRpcRequest`, `NodeRedFlowNode`, `ReactFlowNode`, `ReactFlowGraph` |
| [`rpcClient.ts`](file:///c:/Documents/Programming/red-orange/src/flow/rpcClient.ts) | Low-latency async JSON-RPC 2.0 client supporting HTTP POST, batching, and WebSocket notifications. | `JsonRpcClient`, `JsonRpcException` |
| [`flowAdapter.ts`](file:///c:/Documents/Programming/red-orange/src/flow/flowAdapter.ts) | Lossless bidirectional converter between Node-RED flat flows and React Flow structured graphs. | `convertNodeRedToReactFlow`, `convertReactFlowToNodeRed` |
| [`catalog.ts`](file:///c:/Documents/Programming/red-orange/src/flow/catalog.ts) | Declarative registry of all 40+ Red-Orange nodes, categories, default configurations, and color palettes. | `NODE_CATALOG`, `getNodeCatalogItem`, `getCatalogGroupedByCategory` |
| [`nodeViewModel.ts`](file:///c:/Documents/Programming/red-orange/src/flow/nodeViewModel.ts) | Visual coordinate calculations for stacked multi-input/output ports and connection direction validation. | `computeNodeViewModel`, `validateConnection` |
| [`paletteDnd.ts`](file:///c:/Documents/Programming/red-orange/src/flow/paletteDnd.ts) | HTML5 Drag-and-Drop coordinator from sidebar palette to canvas coordinates. | `createDragPayload`, `instantiateDroppedNode` |
| [`OrangeNode.tsx`](file:///c:/Documents/Programming/red-orange/src/flow/OrangeNode.tsx) | Custom React Flow node component replicating Node-RED pill styling, category badge, and status pill. | `OrangeNode` |
| [`Palette.tsx`](file:///c:/Documents/Programming/red-orange/src/flow/Palette.tsx) | Left sidebar accordion palette with node search filter and drag handle registration. | `Palette` |

---

## 3. Communication Protocols: JSON-RPC 2.0 & MCP

Rather than relying on ad-hoc REST routes, all interactions between the React Flow canvas and the runtime occur over **JSON-RPC 2.0** (`/api/rpc` and WebSocket `/api/rpc/ws`):

- **Flow Lifecycle:**
  - `flows.get`: Fetches current deployed flows.
  - `flows.set`: Deploys new or modified flow topologies atomically.
  - `flows.status`: Queries engine running state.
- **Node Execution & Control:**
  - `nodes.trigger`: Programmatically triggers manual input or inject nodes.
  - `nodes.list`: Queries active runtime instances and catalog schemas.
- **AI Agent & MCP Integration:**
  - `tools/list` & `tools/call`: Flows designated as Model Context Protocol (MCP) tools can be called directly or inspected on the canvas with distinct visual badges.

---

## 4. Node-RED Parity & Spatial Ergonomics

The React Flow interface preserves the standard spatial ergonomics that users expect from Node-RED:
1. **Left Column (Palette):** Category accordions (`OR Data`, `OR Transform`, `OR Model`, etc.) matching standard Node-RED color conventions.
2. **Center Column (Canvas):** Multi-tabbed workspaces, rounded node pills with category badges, stacked input/output handles, and Bezier connection wires.
3. **Right Column (Sidebar):** Node configuration drawers, live debug message console, and interactive Tabulator / Plotly data previews.
4. **Header Navigation:** One-click Deploy action with dirty-state indicator, flow status indicator, and a direct switch button to return to the classic Node-RED editor.

