/**
 * OrangeNode Model and Style Computations for React Flow
 * Emulates the exact visual layout and port semantics of Node-RED nodes.
 */

import { getNodeCatalogItem } from "./catalog.ts";
import type { NodeCatalogItem } from "./catalog.ts";
import type { ReactFlowNodeData } from "./types.ts";

export interface NodePortLayout {
  id: string;
  type: "source" | "target";
  topPercent: number; // Vertical offset percentage
  label?: string;
}

export interface ComputedNodeViewModel {
  catalogItem: NodeCatalogItem;
  badgeColor: string;
  label: string;
  subtitle?: string;
  inputPorts: NodePortLayout[];
  outputPorts: NodePortLayout[];
  hasTriggerButton: boolean;
}

/**
 * Computes handle positions and styling parameters for a node.
 */
export function computeNodeViewModel(nodeData: ReactFlowNodeData): ComputedNodeViewModel {
  const item = getNodeCatalogItem(nodeData.type);
  const badgeColor = item.color;
  const label = nodeData.label || nodeData.name || item.label;

  const inputsCount = typeof nodeData.inputs === "number" ? nodeData.inputs : item.inputs;
  const outputsCount = typeof nodeData.outputs === "number" ? nodeData.outputs : item.outputs;

  // Compute input port placements
  const inputPorts: NodePortLayout[] = [];
  if (inputsCount === 1) {
    inputPorts.push({ id: "in-0", type: "target", topPercent: 50 });
  } else if (inputsCount > 1) {
    for (let i = 0; i < inputsCount; i++) {
      const top = ((i + 1) / (inputsCount + 1)) * 100;
      inputPorts.push({ id: `in-${i}`, type: "target", topPercent: top });
    }
  }

  // Compute output port placements
  const outputPorts: NodePortLayout[] = [];
  if (outputsCount === 1) {
    const label = item.outputLabels ? item.outputLabels[0] : undefined;
    outputPorts.push({ id: "out-0", type: "source", topPercent: 50, label });
  } else if (outputsCount > 1) {
    for (let i = 0; i < outputsCount; i++) {
      const top = ((i + 1) / (outputsCount + 1)) * 100;
      const label = item.outputLabels ? item.outputLabels[i] : undefined;
      outputPorts.push({ id: `out-${i}`, type: "source", topPercent: top, label });
    }
  }

  // Nodes like inject or manual triggers have a left action button
  const hasTriggerButton = nodeData.type === "inject" || nodeData.type === "or-bridge-in";

  return {
    catalogItem: item,
    badgeColor,
    label,
    inputPorts,
    outputPorts,
    hasTriggerButton,
  };
}

/**
 * Validates connection compatibility between two ports
 * Enforces basic port rules (prevent connecting outputs to outputs, self-loop prevention)
 */
export function validateConnection(
  sourceId: string,
  targetId: string,
  sourceHandle?: string,
  targetHandle?: string
): { valid: boolean; reason?: string } {
  if (sourceId === targetId) {
    return { valid: false, reason: "Self-connections are not allowed." };
  }

  if (sourceHandle && !sourceHandle.startsWith("out-")) {
    return { valid: false, reason: "Connections must originate from an output port." };
  }

  if (targetHandle && !targetHandle.startsWith("in-")) {
    return { valid: false, reason: "Connections must terminate at an input port." };
  }

  return { valid: true };
}