/**
 * JSON-RPC 2.0 and MCP Core Types
 * Compatible with red-fastapi JSON-RPC 2.0 specifications.
 */

export interface JsonRpcRequest<T = unknown> {
  jsonrpc: "2.0";
  id: string | number;
  method: string;
  params?: T;
}

export interface JsonRpcNotification<T = unknown> {
  jsonrpc: "2.0";
  method: string;
  params?: T;
}

export interface JsonRpcError {
  code: number;
  message: string;
  data?: unknown;
}

export interface JsonRpcResponse<T = unknown> {
  jsonrpc: "2.0";
  id: string | number;
  result?: T;
  error?: JsonRpcError;
}

/** Standard JSON-RPC 2.0 error codes */
export const JsonRpcErrorCodes = {
  PARSE_ERROR: -32700,
  INVALID_REQUEST: -32600,
  METHOD_NOT_FOUND: -32601,
  INVALID_PARAMS: -32602,
  INTERNAL_ERROR: -32603,
} as const;

// Ensure runtime export for type-stripping runtimes
export const FlowWorkspacePlaceholder = true;

/**
 * Red-Cyan Semantic Prompt & Knowledge Base Types
 */
export interface NodeAttributeSet {
  static: Record<string, unknown>;
  dynamic: Record<string, unknown>;
}

export interface SemanticPayload {
  node_id: string;
  run_id: string;
  text_content: string;
  structured_data?: Record<string, unknown>;
  attributes: NodeAttributeSet;
  parent_node_ids?: string[];
  embedding?: number[];
}

/**
 * Node-RED canonical Flow and Node schema
 */
export interface NodeRedBaseNode {
  id: string;
  type: string;
  z?: string; // Tab / workspace id
  name?: string;
  [key: string]: unknown;
}

export interface NodeRedTabNode extends NodeRedBaseNode {
  type: "tab";
  label: string;
  disabled?: boolean;
  info?: string;
}

export interface NodeRedFlowNode extends NodeRedBaseNode {
  x: number;
  y: number;
  wires: string[][]; // Array of port output target arrays
  inputs?: number;
  outputs?: number;
}

export type NodeRedNode = NodeRedTabNode | NodeRedFlowNode;

/**
 * React Flow canvas schema
 */
export interface ReactFlowXYPosition {
  x: number;
  y: number;
}

export interface NodeStatus {
  fill?: "green" | "red" | "yellow" | "blue" | "grey" | string;
  shape?: "dot" | "ring";
  text?: string;
}

export interface ReactFlowNodeData {
  type: string;
  name?: string;
  label?: string;
  z?: string;
  inputs?: number;
  outputs?: number;
  category?: string;
  config: Record<string, unknown>;
  status?: NodeStatus;
  [key: string]: unknown;
}

export interface ReactFlowNode {
  id: string;
  type: string;
  position: ReactFlowXYPosition;
  data: ReactFlowNodeData;
  selected?: boolean;
}

export interface ReactFlowEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  type?: string;
  animated?: boolean;
  data?: Record<string, unknown>;
}

export interface FlowWorkspace {
  id: string;
  label: string;
  disabled?: boolean;
  info?: string;
}

export interface ReactFlowGraph {
  tabs: FlowWorkspace[];
  nodes: ReactFlowNode[];
  edges: ReactFlowEdge[];
  activeTabId?: string;
}