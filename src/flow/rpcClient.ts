/**
 * Lightweight JSON-RPC 2.0 Client
 * Works over HTTP POST (fetch) and WebSocket for red-fastapi communication.
 */

import type {
  JsonRpcRequest,
  JsonRpcResponse,
  JsonRpcError,
  JsonRpcNotification,
} from "./types.ts";

export interface JsonRpcClientOptions {
  httpUrl?: string;
  wsUrl?: string;
  fetchFn?: typeof fetch;
  headers?: Record<string, string>;
}

export class JsonRpcException extends Error {
  public code: number;
  public data?: unknown;

  constructor(error: JsonRpcError) {
    super(error.message);
    this.name = "JsonRpcException";
    this.code = error.code;
    this.data = error.data;
  }
}

export class JsonRpcClient {
  private httpUrl: string;
  private wsUrl?: string;
  private fetchFn: typeof fetch;
  private headers: Record<string, string>;
  private nextId = 1;
  private ws?: WebSocket;
  private pendingRequests = new Map<
    string | number,
    {
      resolve: (value: unknown) => void;
      reject: (reason: unknown) => void;
    }
  >();
  private notificationListeners = new Map<
    string,
    Set<(params: unknown) => void>
  >();

  constructor(options: JsonRpcClientOptions = {}) {
    this.httpUrl = options.httpUrl || "/api/rpc";
    this.wsUrl = options.wsUrl;
    this.fetchFn = options.fetchFn || (typeof fetch !== "undefined" ? fetch.bind(globalThis) : (undefined as unknown as typeof fetch));
    this.headers = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };
  }

  /**
   * Execute an RPC call over HTTP POST.
   */
  async call<TResult = unknown, TParams = unknown>(
    method: string,
    params?: TParams
  ): Promise<TResult> {
    const id = this.nextId++;
    const payload: JsonRpcRequest<TParams> = {
      jsonrpc: "2.0",
      id,
      method,
      params,
    };

    if (!this.fetchFn) {
      throw new Error("No fetch implementation available in this environment.");
    }

    const res = await this.fetchFn(this.httpUrl, {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      throw new Error(`HTTP error ${res.status}: ${res.statusText}`);
    }

    const rpcResponse = (await res.json()) as JsonRpcResponse<TResult>;

    if (rpcResponse.error) {
      throw new JsonRpcException(rpcResponse.error);
    }

    return rpcResponse.result as TResult;
  }

  /**
   * Send a JSON-RPC batch request over HTTP POST.
   */
  async batch(
    calls: Array<{ method: string; params?: unknown }>
  ): Promise<Array<JsonRpcResponse>> {
    const requests: JsonRpcRequest[] = calls.map((c) => ({
      jsonrpc: "2.0",
      id: this.nextId++,
      method: c.method,
      params: c.params,
    }));

    if (!this.fetchFn) {
      throw new Error("No fetch implementation available.");
    }

    const res = await this.fetchFn(this.httpUrl, {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify(requests),
    });

    if (!res.ok) {
      throw new Error(`HTTP error ${res.status}: ${res.statusText}`);
    }

    return (await res.json()) as Array<JsonRpcResponse>;
  }

  /**
   * Subscribe to JSON-RPC notifications (e.g. over WebSocket).
   */
  onNotification(method: string, listener: (params: unknown) => void): () => void {
    if (!this.notificationListeners.has(method)) {
      this.notificationListeners.set(method, new Set());
    }
    this.notificationListeners.get(method)!.add(listener);

    return () => {
      this.notificationListeners.get(method)?.delete(listener);
    };
  }

  /**
   * Dispatch an incoming notification message to registered listeners.
   */
  handleIncomingMessage(data: string | object): void {
    const msg = (typeof data === "string" ? JSON.parse(data) : data) as
      | JsonRpcResponse
      | JsonRpcNotification;

    // Check if it's a response to a pending request
    if ("id" in msg && msg.id !== undefined && this.pendingRequests.has(msg.id)) {
      const pending = this.pendingRequests.get(msg.id)!;
      this.pendingRequests.delete(msg.id);
      if ("error" in msg && msg.error) {
        pending.reject(new JsonRpcException(msg.error));
      } else {
        pending.resolve(msg.result);
      }
      return;
    }

    // Check if it's a notification
    if ("method" in msg && typeof msg.method === "string") {
      const listeners = this.notificationListeners.get(msg.method);
      if (listeners) {
        listeners.forEach((fn) => fn(msg.params));
      }
    }
  }
}