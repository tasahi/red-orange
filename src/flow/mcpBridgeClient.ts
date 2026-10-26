/**
 * MCP Bridge Client and Helper for React Flow
 * Exposes methods to read tabular datasets via MCP resources and trigger quantitative tools.
 */

import { JsonRpcClient } from "./rpcClient.ts";

export interface McpResourceItem {
  uri: string;
  name: string;
  description?: string;
  mimeType?: string;
}

export interface McpToolItem {
  name: string;
  description?: string;
  inputSchema?: Record<string, unknown>;
}

export class McpBridgeClient {
  private rpc: JsonRpcClient;

  constructor(rpcClient?: JsonRpcClient) {
    this.rpc = rpcClient || new JsonRpcClient();
  }

  /**
   * Discovers exposed tabular datasets and flow resources
   */
  async listResources(): Promise<McpResourceItem[]> {
    const res = await this.rpc.call<{ resources: McpResourceItem[] }>("resources/list");
    return res.resources || [];
  }

  /**
   * Reads the profile and statistical summary of an Orange dataset
   */
  async readResource(uri: string): Promise<Record<string, unknown>> {
    const res = await this.rpc.call<{
      contents: Array<{ uri: string; mimeType: string; text: string }>;
    }>("resources/read", { uri });

    if (!res.contents || res.contents.length === 0) {
      throw new Error(`Empty resource content for ${uri}`);
    }

    try {
      return JSON.parse(res.contents[0].text);
    } catch {
      return { raw: res.contents[0].text };
    }
  }

  /**
   * Lists exposed quantitative tools (filters, clustering, samplers)
   */
  async listTools(): Promise<McpToolItem[]> {
    const res = await this.rpc.call<{ tools: McpToolItem[] }>("tools/list");
    return res.tools || [];
  }

  /**
   * Invokes a tool (e.g. feedback loop from an LLM node to an Orange node)
   */
  async callTool(name: string, argumentsMap: Record<string, unknown>): Promise<unknown> {
    const res = await this.rpc.call<{
      content: Array<{ type: string; text: string }>;
      isError: boolean;
    }>("tools/call", { name, arguments: argumentsMap });

    if (res.isError) {
      throw new Error(res.content?.[0]?.text || `Error executing tool ${name}`);
    }

    const text = res.content?.[0]?.text || "";
    try {
      return JSON.parse(text);
    } catch {
      return text;
    }
  }
}
