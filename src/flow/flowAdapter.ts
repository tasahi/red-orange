/**
 * Bidirectional Flow Adapter
 * Converts between canonical Node-RED flow JSON and React Flow graph representations.
 */

import type {
  NodeRedNode,
  NodeRedTabNode,
  NodeRedFlowNode,
  ReactFlowNode,
  ReactFlowEdge,
  ReactFlowGraph,
  FlowWorkspace,
} from "./types.ts";

/**
 * Check if a Node-RED node is a Tab (workspace container)
 */
export function isTabNode(node: NodeRedNode): node is NodeRedTabNode {
  return node.type === "tab";
}

/**
 * Converts a canonical Node-RED flow list into React Flow nodes, edges, and tab workspaces.
 */
export function convertNodeRedToReactFlow(nrNodes: NodeRedNode[]): ReactFlowGraph {
  const tabs: FlowWorkspace[] = [];
  const nodes: ReactFlowNode[] = [];
  const edges: ReactFlowEdge[] = [];

  // 1. Separate tabs and flow nodes
  for (const item of nrNodes) {
    if (isTabNode(item)) {
      tabs.push({
        id: item.id,
        label: item.label || item.id,
        disabled: Boolean(item.disabled),
        info: item.info,
      });
    }
  }

  const activeTabId = tabs.length > 0 ? tabs[0].id : undefined;

  // 2. Convert standard flow nodes
  for (const item of nrNodes) {
    if (isTabNode(item)) {
      continue;
    }

    const flowNode = item as NodeRedFlowNode;
    const { id, type, x, y, z, name, wires, inputs, outputs, ...customProps } = flowNode;

    nodes.push({
      id,
      type: "orangeNode",
      position: {
        x: typeof x === "number" ? x : 0,
        y: typeof y === "number" ? y : 0,
      },
      data: {
        type,
        name: name || type,
        label: name || type,
        z: z || activeTabId,
        inputs: typeof inputs === "number" ? inputs : 1,
        outputs: typeof outputs === "number" ? outputs : 1,
        config: customProps,
      },
    });

    // 3. Extract edges from wires array
    if (Array.isArray(wires)) {
      wires.forEach((portTargets, portIndex) => {
        if (Array.isArray(portTargets)) {
          portTargets.forEach((targetId) => {
            edges.push({
              id: `edge-${id}-p${portIndex}-${targetId}`,
              source: id,
              target: targetId,
              sourceHandle: `out-${portIndex}`,
              targetHandle: "in-0",
              type: "default",
            });
          });
        }
      });
    }
  }

  return {
    tabs,
    nodes,
    edges,
    activeTabId,
  };
}

/**
 * Converts React Flow nodes, edges, and tab workspaces back into canonical Node-RED flow JSON.
 */
export function convertReactFlowToNodeRed(graph: ReactFlowGraph): NodeRedNode[] {
  const result: NodeRedNode[] = [];

  // 1. Recreate tab nodes
  for (const tab of graph.tabs) {
    result.push({
      id: tab.id,
      type: "tab",
      label: tab.label,
      disabled: tab.disabled ?? false,
      info: tab.info ?? "",
    });
  }

  // 2. Reconstruct flow nodes and wires
  for (const rfNode of graph.nodes) {
    const outgoingEdges = graph.edges.filter((e) => e.source === rfNode.id);

    // Compute wires grouped by source port index
    const wires: string[][] = [];
    for (const edge of outgoingEdges) {
      let portIndex = 0;
      if (edge.sourceHandle && edge.sourceHandle.startsWith("out-")) {
        const parsed = parseInt(edge.sourceHandle.slice(4), 10);
        if (!isNaN(parsed) && parsed >= 0) {
          portIndex = parsed;
        }
      }

      while (wires.length <= portIndex) {
        wires.push([]);
      }
      wires[portIndex].push(edge.target);
    }

    const nodeData = rfNode.data;
    const config = (nodeData.config as Record<string, unknown>) || {};

    const nrNode: NodeRedFlowNode = {
      ...config,
      id: rfNode.id,
      type: nodeData.type,
      name: nodeData.name,
      x: Math.round(rfNode.position.x),
      y: Math.round(rfNode.position.y),
      z: nodeData.z || graph.activeTabId || (graph.tabs[0]?.id ?? ""),
      wires,
    };

    if (typeof nodeData.inputs === "number") {
      nrNode.inputs = nodeData.inputs;
    }
    if (typeof nodeData.outputs === "number") {
      nrNode.outputs = nodeData.outputs;
    }

    result.push(nrNode);
  }

  return result;
}