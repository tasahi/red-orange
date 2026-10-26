---
title: React Flow UI Phase 3 Implementation Plan - Canvas Workspace, Tabs & Deployment
document_type: Technical Implementation Plan
project: red-orange
host_framework: red-fastapi
status: Ready for Implementation
target_phase: Phase 3
date: October 2026
---

# React Flow UI Phase 3 Implementation Plan: Canvas Workspace, Tabs & Deployment

**Project:** `red-orange`  
**Host Framework:** `red-fastapi`  
**Target Module:** `src/flow/`  
**Status:** Ready for Implementation  
**Date:** October 2026  

---

## 1. Objective & Scope

With **Phase 1** (JSON-RPC 2.0 client & flow adapter) and **Phase 2** (declarative palette, drag-and-drop, and custom Orange node models) completed, **Phase 3** integrates these elements into a working **Canvas Workspace**.

The goal of Phase 3 is to deliver:
1. **Multi-Tab Workspace Management:** Supporting multiple flow tabs (mirroring Node-RED workspaces/tabs) with tab creation, renaming, switching, and deletion.
2. **Interactive Canvas Surface:** Connecting React Flow's state store (nodes, edges, selection, viewport) with the active tab.
3. **Deploy Workflow over JSON-RPC 2.0:** Triggering atomic flow deployments using `flows.set` via the JSON-RPC client, tracking deployment revisions (`rev`), and handling deployment errors.
4. **Header Navigation & UI Mode Switcher:** Providing top-level actions (Deploy button with deployment state, flow status pill, and a seamless toggle to switch to Node-RED).
5. **Real-time Runtime Status Streaming:** Handling engine status notifications (`flows.status`, `node.status`) streamed over JSON-RPC notifications / WebSocket to update node badges and canvas health indicators.

---

## 2. Architecture & Component Blueprint

```
+------------------------------------------------------------------------------------------------------+
| [Logo] Red-Orange | [Tab 1: Iris Classification] [Tab 2: Clustering] [+] | [Deploy v] [Switch to NR] |
+------------------------------------------------------------------------------------------------------+
|                                            WorkspaceStore                                            |
|   - activeTabId: string                                                                              |
|   - tabs: FlowWorkspace[] (addTab, removeTab, renameTab, selectTab)                                 |
|   - nodesByTab: Map<string, ReactFlowNode[]>                                                         |
|   - edgesByTab: Map<string, ReactFlowEdge[]>                                                         |
|   - isDirty: boolean                                                                                 |
|   - deployStatus: 'idle' | 'deploying' | 'success' | 'error'                                         |
+------------------------------------------------------------------------------------------------------+
                                   |                                     |
                                   v                                     v
                 +-----------------------------------+ +-----------------------------------+
                 |         React Flow Canvas         | |        Deploy & RPC Manager       |
                 | - Custom node types (orangeNode)  | | - loadFlows() -> flows.get        |
                 | - Handle drops from Palette       | | - deployFlows() -> flows.set      |
                 | - Edge connection validation      | | - triggerNode() -> nodes.trigger  |
                 | - Selection & delete management   | | - syncStatus() -> WS notifications|
                 +-----------------------------------+ +-----------------------------------+
```

---

## 3. Detailed Deliverables & Modules

### 3.1 Workspace State Store (`src/flow/workspaceStore.ts`)
A dedicated, framework-agnostic reactive state manager for multi-tab flow workflows:
- **State Properties:**
  - `tabs: FlowWorkspace[]`: List of open workspace tabs (`id`, `label`, `disabled`, `info`).
  - `activeTabId: string`: Currently active canvas tab.
  - `nodes: ReactFlowNode[]`: All active nodes across all tabs.
  - `edges: ReactFlowEdge[]`: All active edges across all tabs.
  - `isDirty: boolean`: Unsaved changes flag (turns yellow/active when nodes are moved, edited, or deleted).
  - `deployState: { status: 'idle' | 'deploying' | 'success' | 'error', message?: string, rev?: string }`.
- **Core Actions:**
  - `setGraph(graph: ReactFlowGraph)`: Populates state from converted Node-RED flow.
  - `getGraph(): ReactFlowGraph`: Prepares clean graph state for saving or conversion back to Node-RED.
  - `createTab(label?: string)`: Appends a new workspace tab and sets it active.
  - `removeTab(tabId: string)`: Removes a workspace tab and associated nodes/edges.
  - `renameTab(tabId: string, newLabel: string)`: Updates tab label.
  - `setActiveTab(tabId: string)`: Switches visible canvas tab.
  - `addNode(node: ReactFlowNode)`: Inserts a new node into the active tab.
  - `removeNodes(nodeIds: string[])`: Deletes nodes and cascades edge deletion.
  - `updateNodeConfig(nodeId: string, newConfig: Record<string, unknown>)`: Updates node properties.
  - `setNodeStatus(nodeId: string, status: { fill: string, text: string })`: Updates node status pill.

### 3.2 Deployment Controller (`src/flow/deployController.ts`)
Orchestrates communication with `red-fastapi`'s JSON-RPC 2.0 endpoints:
- `loadRemoteFlows(client: JsonRpcClient, store: WorkspaceStore)`:
  - Invokes `rpc.call("flows.get")`.
  - Converts canonical Node-RED flow to React Flow graph via `convertNodeRedToReactFlow()`.
  - Updates `WorkspaceStore` and resets dirty state.
- `deployActiveFlows(client: JsonRpcClient, store: WorkspaceStore)`:
  - Validates active connections using `validateConnection()`.
  - Converts React Flow graph to canonical Node-RED flow JSON via `convertReactFlowToNodeRed()`.
  - Invokes `rpc.call("flows.set", { flows })`.
  - Updates revision hash and sets `isDirty = false`.
- `triggerNodeAction(client: JsonRpcClient, nodeId: string, payload?: unknown)`:
  - Invokes `rpc.call("nodes.trigger", { node_id: nodeId, payload })`.

### 3.3 Top Header & Tab Bar UI Components
- **`TabBar.tsx` (`src/flow/TabBar.tsx`):**
  - Horizontal tab strip matching Node-RED tab style with active tab highlight.
  - Double-click to rename tab inline.
  - Close button `(x)` on tabs with confirmation if tab contains nodes.
  - Add tab button `(+)` at the right end of the strip.
- **`Header.tsx` (`src/flow/Header.tsx`):**
  - Left branding: Red-Orange logo + version badge.
  - Center: Flow workspace title.
  - Right:
    - **Deploy Button:** Red/Disabled when clean, bright red with dropdown menu when dirty (`Full`, `Modified Nodes`, `Restart Flows`). Displays spinner while deploying.
    - **UI Mode Switcher:** Button linking directly to `/ui/node-red` or `/` with tooltip *"Switch to Node-RED Editor"*.
    - **Status Pill:** Indicates backend connection status (WebSocket connected / latency).

### 3.4 Main Canvas Integration (`src/flow/FlowCanvas.tsx`)
- Integrates `@xyflow/react` (`ReactFlow`, `Background`, `Controls`, `MiniMap`).
- Filters visible `nodes` and `edges` by `activeTabId`.
- Registers custom node types (`nodeTypes = { orangeNode: OrangeNode }`).
- Implements `onDragOver` and `onDrop` using `paletteDnd.ts` coordinates.
- Implements `onConnect` using `validateConnection()` to prevent invalid connections.

---

## 4. Verification & Testing Strategy

Phase 3 will be accompanied by comprehensive automated tests (`src/flow/phase3.test.ts`):

1. **WorkspaceStore Tests:**
   - Multi-tab management: add, rename, switch, and remove tabs with node cleanup.
   - Node insertion, deletion, edge cascade, and dirty flag tracking.
   - Status updates (`setNodeStatus`) verifying reactive notification handling.
2. **DeployController Tests (Mocked RPC):**
   - Verify `loadRemoteFlows` successfully fetches from mock RPC, runs `convertNodeRedToReactFlow`, and populates store.
   - Verify `deployActiveFlows` runs `convertReactFlowToNodeRed`, invokes `flows.set`, and updates deploy status and revision.
   - Verify deployment failure handling (e.g. RPC error response).
   - Verify `triggerNodeAction` correctly calls `nodes.trigger`.
3. **End-to-End State Integration:**
   - Verify round-trip: Remote Node-RED Flow -> Load into Workspace -> Edit in Tab -> Deploy back to RPC.

---

## 5. Phased Implementation Steps

| Step | Action | Files |
| :--- | :--- | :--- |
| **Step 3.1** | Create `WorkspaceStore` with tab and node lifecycle management. | `src/flow/workspaceStore.ts` |
| **Step 3.2** | Implement `DeployController` managing JSON-RPC deployment operations. | `src/flow/deployController.ts` |
| **Step 3.3** | Implement UI components (`TabBar.tsx`, `Header.tsx`, `FlowCanvas.tsx`). | `src/flow/TabBar.tsx`, `src/flow/Header.tsx`, `src/flow/FlowCanvas.tsx` |
| **Step 3.4** | Export public API in `src/flow/index.ts`. | `src/flow/index.ts` |
| **Step 3.5** | Write and execute automated unit tests. | `src/flow/phase3.test.ts` |
| **Step 3.6** | Update documentation and technical index. | `docs/` |

