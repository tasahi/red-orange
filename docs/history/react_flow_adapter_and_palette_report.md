---
title: React Flow UI Implementation Report (Phases 1 & 2)
document_type: Technical Implementation Report
project: red-orange
host_framework: red-fastapi
status: Completed
phases_completed:
  - Phase 1: RPC Client & Bidirectional Flow Adapter
  - Phase 2: React Flow Foundation, Node-RED Palette Mirroring & Custom Nodes
date: October 2026
---

# React Flow UI Implementation Report (Phases 1 & 2)

**Project:** `red-orange`  
**Host Framework:** `red-fastapi`  
**Target Module:** `src/flow/`  
**Status:** Phases 1 & 2 Fully Implemented and Tested (8/8 automated tests passing)  
**Date:** October 2026  

---

## 1. Overview

To expand `red-orange` beyond the static confines of Node-RED's legacy editor without disrupting existing users, we implemented the foundational architecture for an alternate **React Flow** interface. This interface directly communicates with `red-fastapi` via **JSON-RPC 2.0** and preserves the exact spatial and mental model of Node-RED.

This document details the architectural components, source modules, and verification tests completed across **Phase 1** and **Phase 2**.

---

## 2. Phase 1 Implementation: RPC Client & Bidirectional Flow Adapter

Phase 1 established the communication and data translation backbone required for `red-fastapi` interoperability.

### 2.1 Type Definitions (`src/flow/types.ts`)
Defines TypeScript contracts for:
- **JSON-RPC 2.0 Protocol:** `JsonRpcRequest`, `JsonRpcResponse`, `JsonRpcError`, `JsonRpcNotification`, standard error codes (`-32700` to `-32603`).
- **Node-RED Canonical Flow Model:** `NodeRedTabNode`, `NodeRedFlowNode` with nested multi-output wire arrays (`wires: string[][]`), workspace assignments (`z`), and positional coordinates (`x, y`).
- **React Flow Canvas Model:** `ReactFlowNode`, `ReactFlowEdge`, `ReactFlowGraph`, `FlowWorkspace`, and handles (`sourceHandle`, `targetHandle`).

### 2.2 Bidirectional Flow Adapter (`src/flow/flowAdapter.ts`)
Ensures flows can be opened, edited, and saved across either editor without data loss:
- `convertNodeRedToReactFlow(nrNodes)`:
  - Extracts workspace tabs (`type === "tab"`).
  - Normalizes Node-RED coordinate systems into React Flow positions.
  - Transforms multidimensional output wire arrays (`wires[portIndex][targetIndex]`) into React Flow edges with stacked handle anchors (`out-0`, `out-1`, etc.).
- `convertReactFlowToNodeRed(graph)`:
  - Reconstructs Node-RED `tab` objects and `flowNode` representations.
  - Groups outgoing edges by source handle index back into Node-RED's canonical `wires` arrays.
  - Preserves all custom node configuration attributes in `nodeData.config`.

### 2.3 JSON-RPC 2.0 Client (`src/flow/rpcClient.ts`)
Provides a clean, async TypeScript client for `red-fastapi`:
- **HTTP POST Dispatch:** `.call<TResult>(method, params)` with typed payloads and `JsonRpcException` propagation.
- **Batch Processing:** `.batch(calls)` for atomic multi-request updates.
- **Notification Subscriptions:** `.onNotification(method, callback)` and `.handleIncomingMessage(data)` for real-time WebSocket event streaming (e.g. node execution status, debug outputs).

---

## 3. Phase 2 Implementation: Palette Mirroring, Custom Nodes & DnD

Phase 2 replicated Node-RED's visual language and drag-and-drop ergonomics on top of React Flow.

### 3.1 Declarative Node Catalog (`src/flow/catalog.ts`)
Provides full registry coverage of `red-orange` nodes categorized under:
- `OR Data` (`#FFAA00`): File Loader, Data Sampler, Select Columns, Select Rows, Data Table, Merge Data, Concatenate, Save Data, Edit Domain.
- `OR Transform` (`#52C41A`): Impute, Normalize, Continuize, Discretize, PCA, Outliers, Correlations, Rank.
- `OR Model` (`#1890FF`): Logistic Regression, Random Forest, Tree, k-NN, Naive Bayes, SVM, Neural Network, Linear Regression.
- `OR Unsupervised` (`#13C2C2`): k-Means, DBSCAN.
- `OR Evaluate` (`#722ED1`): Test & Score, Predictions, Confusion Matrix, ROC Analysis.
- `OR Visualize` (`#EB2F96`): Scatter Plot, Histogram, Box Plot, Tree Viewer.
- `common` (`#A0A0A0`): Inject, Debug.

Includes helper functions `getNodeCatalogItem(type)` with fallback defaults and `getCatalogGroupedByCategory()`.

### 3.2 Node View Model & Connection Validator (`src/flow/nodeViewModel.ts`)
- `computeNodeViewModel(nodeData)`: Computes vertical handle percentage offsets (`topPercent`) for stacked multi-input and multi-output ports. Identifies action nodes that require left-hand manual trigger buttons (e.g., `inject`).
- `validateConnection(sourceId, targetId, sourceHandle, targetHandle)`: Enforces directional graph integrity (rejects self-loops, validates source vs. target handle prefixes).

### 3.3 HTML5 Drag-and-Drop Manager (`src/flow/paletteDnd.ts`)
- Manages drag transfer payloads using MIME type `application/x-red-orange-node`.
- `instantiateDroppedNode(payload, position, activeTabId)`: Instantiates a canvas node at the dropped cursor location with default configurations and tab assignments.

### 3.4 React Flow Components
- `OrangeNode.tsx` ([`src/flow/OrangeNode.tsx`](file:///c:/Documents/Programming/red-orange/src/flow/OrangeNode.tsx)): Recreates Node-RED's rounded pill design, categorical color badge, stacked input/output handles, status indicator pill, and manual trigger button.
- `Palette.tsx` ([`src/flow/Palette.tsx`](file:///c:/Documents/Programming/red-orange/src/flow/Palette.tsx)): Recreates Node-RED's left sidebar accordion palette with text filtering and draggable node items.

---

## 4. Verification & Automated Test Results

The implementation is verified via native Node.js test runner suites:

```bash
node --experimental-strip-types --test src/flow/phase1.test.ts src/flow/phase2.test.ts
```

### Test Suite Summary:
```text
TAP version 13
# Subtest: FlowAdapter: Bidirectional Conversion (Round-Trip) Fidelity
ok 1 - FlowAdapter: Bidirectional Conversion (Round-Trip) Fidelity
# Subtest: JsonRpcClient: Successful Method Call over Mock Fetch
ok 2 - JsonRpcClient: Successful Method Call over Mock Fetch
# Subtest: JsonRpcClient: Error Handling with Standard Exception
ok 3 - JsonRpcClient: Error Handling with Standard Exception
# Subtest: JsonRpcClient: Notification handling
ok 4 - JsonRpcClient: Notification handling
# Subtest: NodeCatalog: Catalog Items and Fallbacks
ok 5 - NodeCatalog: Catalog Items and Fallbacks
# Subtest: NodeViewModel: Compute Stacked Port Handles and Badge Colors
ok 6 - NodeViewModel: Compute Stacked Port Handles and Badge Colors
# Subtest: NodeViewModel: Connection Validation Logic
ok 7 - NodeViewModel: Connection Validation Logic
# Subtest: PaletteDnD: Drag Payload creation and canvas node instantiation
ok 8 - PaletteDnD: Drag Payload creation and canvas node instantiation

1..8
# tests 8
# pass 8
# fail 0
```

---

## 5. Next Steps (Phase 3 & Beyond)

With Phase 1 and Phase 2 complete, the foundation is ready for:
1. **Phase 3: Canvas Workspace, Tabs & Deployment:** Wiring React Flow canvas with tabbed workspaces, top Deploy action, and WebSocket status updates.
2. **Phase 4: Properties Drawer, Debug Console & Preview Widgets:** Interactive node configuration drawer, live debug console, and embedded Tabulator/Plotly previews.
3. **Phase 5: Packaging & FastApi Mounting:** Compiling static assets and serving the UI toggle inside `red-fastapi`.

