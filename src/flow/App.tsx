import React, { useState, useCallback, useRef } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  Node,
  ReactFlowProvider,
  ReactFlowInstance,
} from "@xyflow/react";
import { Palette } from "./Palette.tsx";
import { OrangeNode } from "./OrangeNode.tsx";
import { RED_ORANGE_DND_MIME, DraggedNodePayload, instantiateDroppedNode } from "./paletteDnd.ts";
import { validateConnection } from "./nodeViewModel.ts";
import { ReactFlowNode } from "./types.ts";

const nodeTypes = {
  orangeNode: OrangeNode,
};

// Default starter nodes
const initialNodes: Node[] = [
  {
    id: "node_1",
    type: "orangeNode",
    position: { x: 100, y: 150 },
    data: {
      type: "or-file-loader",
      name: "Iris Data",
      label: "File",
      inputs: 0,
      outputs: 1,
      config: { filename: "iris.tab" },
    },
  },
  {
    id: "node_2",
    type: "orangeNode",
    position: { x: 340, y: 150 },
    data: {
      type: "or-data-sampler",
      name: "70% Sample",
      label: "Data Sampler",
      inputs: 1,
      outputs: 2,
      config: { sample_size: 70 },
    },
  },
  {
    id: "node_3",
    type: "orangeNode",
    position: { x: 580, y: 100 },
    data: {
      type: "or-tree",
      name: "Decision Tree",
      label: "Tree",
      inputs: 1,
      outputs: 1,
      config: { max_depth: 5 },
    },
  },
  {
    id: "node_4",
    type: "orangeNode",
    position: { x: 580, y: 220 },
    data: {
      type: "or-data-table",
      name: "Remaining Data",
      label: "Data Table",
      inputs: 1,
      outputs: 1,
      config: {},
    },
  },
];

const initialEdges: Edge[] = [
  {
    id: "e1-2",
    source: "node_1",
    target: "node_2",
    sourceHandle: "out-0",
    targetHandle: "in-0",
  },
  {
    id: "e2-3",
    source: "node_2",
    target: "node_3",
    sourceHandle: "out-0",
    targetHandle: "in-0",
  },
  {
    id: "e2-4",
    source: "node_2",
    target: "node_4",
    sourceHandle: "out-1",
    targetHandle: "in-0",
  },
];

export const AppContent: React.FC = () => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [rfInstance, setRfInstance] = useState<ReactFlowInstance | null>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  const onConnect = useCallback(
    (connection: Connection) => {
      const check = validateConnection(
        connection.source || "",
        connection.target || "",
        connection.sourceHandle || undefined,
        connection.targetHandle || undefined
      );

      if (!check.valid) {
        alert(`Invalid connection: ${check.reason}`);
        return;
      }

      setEdges((eds) => addEdge(connection, eds));
    },
    [setEdges]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const raw = event.dataTransfer.getData(RED_ORANGE_DND_MIME);
      if (!raw || !rfInstance) return;

      try {
        const payload = JSON.parse(raw) as DraggedNodePayload;
        const position = rfInstance.screenToFlowPosition({
          x: event.clientX,
          y: event.clientY,
        });

        const newNode = instantiateDroppedNode(payload, position);
        setNodes((nds) => nds.concat(newNode as unknown as Node));
      } catch (err) {
        console.error("Drop failed:", err);
      }
    },
    [rfInstance, setNodes]
  );

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
  }, []);

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden font-sans">
      {/* Top Header */}
      <header className="h-11 bg-[#b22222] text-white flex items-center justify-between px-4 shadow-sm z-10 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="font-bold text-sm tracking-wide flex items-center gap-1.5">
            <span className="bg-orange-500 text-white text-[11px] font-black px-1.5 py-0.5 rounded">
              OR
            </span>
            <span>Red-Orange Flow</span>
          </div>
          <span className="text-xs bg-black/20 text-red-100 px-2 py-0.5 rounded">
            React Flow Canvas
          </span>
        </div>

        <div className="flex items-center gap-3 text-xs">
          <button
            type="button"
            onClick={() => alert("Flow deployed successfully over JSON-RPC 2.0 (flows.set)")}
            className="bg-[#d9534f] hover:bg-[#c9302c] active:bg-[#ac2925] text-white font-semibold px-3 py-1 rounded shadow-sm border border-red-400 cursor-pointer transition-all"
          >
            Deploy
          </button>
          <a
            href="/"
            className="text-red-100 hover:text-white bg-black/20 hover:bg-black/30 px-2.5 py-1 rounded transition-colors no-underline"
            title="Switch to standard Node-RED interface"
          >
            ⮀ Switch to Node-RED
          </a>
        </div>
      </header>

      {/* Main Workspace Body */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* Left Palette */}
        <Palette />

        {/* Center Canvas */}
        <div className="flex-1 h-full relative" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onInit={setRfInstance}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            fitView
          >
            <Background gap={16} size={1} color="#d4d4d4" />
            <Controls />
            <MiniMap
              nodeColor={(n) => {
                const data = n.data as any;
                return data?.type?.startsWith("or-") ? "#FFAA00" : "#87A987";
              }}
              className="bg-white/80 border border-gray-300 rounded shadow"
            />
          </ReactFlow>
        </div>

        {/* Right Info Sidebar (when node is selected) */}
        {selectedNode && (
          <aside className="w-64 h-full bg-white dark:bg-[#252525] border-l border-gray-300 dark:border-gray-700 p-3 text-xs flex flex-col justify-between shadow-lg z-10">
            <div>
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-gray-200 dark:border-gray-700">
                <span className="font-bold text-gray-800 dark:text-gray-100">Node Properties</span>
                <button
                  type="button"
                  onClick={() => setSelectedNode(null)}
                  className="text-gray-400 hover:text-gray-600 cursor-pointer text-sm"
                >
                  ✕
                </button>
              </div>
              <div className="space-y-2">
                <div>
                  <label className="text-gray-500 font-medium">Type:</label>
                  <p className="font-mono text-gray-800 dark:text-gray-200">
                    {String(selectedNode.data?.type)}
                  </p>
                </div>
                <div>
                  <label className="text-gray-500 font-medium">Name:</label>
                  <p className="text-gray-800 dark:text-gray-200">
                    {String(selectedNode.data?.name || selectedNode.data?.label || selectedNode.id)}
                  </p>
                </div>
                <div>
                  <label className="text-gray-500 font-medium">ID:</label>
                  <p className="font-mono text-[10px] text-gray-400">{selectedNode.id}</p>
                </div>
                <div>
                  <label className="text-gray-500 font-medium">Config:</label>
                  <pre className="bg-gray-100 dark:bg-black/30 p-1.5 rounded text-[10px] overflow-auto max-h-40">
                    {JSON.stringify(selectedNode.data?.config, null, 2)}
                  </pre>
                </div>
              </div>
            </div>

            <div className="pt-2 border-t border-gray-200 dark:border-gray-700 flex justify-end">
              <button
                type="button"
                onClick={() => {
                  setNodes((nds) => nds.filter((n) => n.id !== selectedNode.id));
                  setEdges((eds) =>
                    eds.filter(
                      (e) => e.source !== selectedNode.id && e.target !== selectedNode.id
                    )
                  );
                  setSelectedNode(null);
                }}
                className="px-2.5 py-1 bg-red-100 text-red-700 hover:bg-red-200 rounded cursor-pointer transition-all"
              >
                Delete Node
              </button>
            </div>
          </aside>
        )}
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <ReactFlowProvider>
      <AppContent />
    </ReactFlowProvider>
  );
};
