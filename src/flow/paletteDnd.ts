/**
 * Drag and Drop Manager for React Flow Palette
 * Handles packaging node metadata on drag start and computing insertion coordinates on drop.
 */

import { getNodeCatalogItem } from "./catalog.ts";
import type { NodeCatalogItem } from "./catalog.ts";
import type { ReactFlowNode } from "./types.ts";

export const RED_ORANGE_DND_MIME = "application/x-red-orange-node";

export interface DraggedNodePayload {
  type: string;
  category: string;
  label: string;
  inputs: number;
  outputs: number;
  defaultConfig: Record<string, unknown>;
}

/**
 * Creates drag data transfer payload
 */
export function createDragPayload(nodeType: string): DraggedNodePayload {
  const item = getNodeCatalogItem(nodeType);
  return {
    type: item.type,
    category: item.category,
    label: item.label,
    inputs: item.inputs,
    outputs: item.outputs,
    defaultConfig: { ...(item.defaultConfig || {}) },
  };
}

/**
 * Instantiates a new React Flow node on the canvas from dropped payload
 */
let nodeIdCounter = 1;

export function instantiateDroppedNode(
  payload: DraggedNodePayload,
  position: { x: number; y: number },
  activeTabId?: string,
  customId?: string
): ReactFlowNode {
  const id = customId || `node_${Date.now().toString(36)}_${nodeIdCounter++}`;
  const isCyanNode = payload.category === "Cyan Prompt" || payload.type.startsWith("cyan-");

  return {
    id,
    type: isCyanNode ? "cyanPromptNode" : "orangeNode",
    position: {
      x: Math.round(position.x),
      y: Math.round(position.y),
    },
    data: {
      type: payload.type,
      name: payload.label,
      label: payload.label,
      category: payload.category,
      inputs: payload.inputs,
      outputs: payload.outputs,
      z: activeTabId,
      config: { ...payload.defaultConfig },
    },
  };
}