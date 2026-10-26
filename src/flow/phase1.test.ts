import test from "node:test";
import assert from "node:assert/strict";
import {
  convertNodeRedToReactFlow,
  convertReactFlowToNodeRed,
} from "./flowAdapter.ts";
import type { NodeRedNode } from "./types.ts";
import { JsonRpcClient, JsonRpcException } from "./rpcClient.ts";

test("FlowAdapter: Bidirectional Conversion (Round-Trip) Fidelity", () => {
  const originalFlow: NodeRedNode[] = [
    {
      id: "tab1",
      type: "tab",
      label: "Iris Workflow",
      disabled: false,
      info: "Test tab description",
    },
    {
      id: "node_loader",
      type: "or-file-loader",
      z: "tab1",
      name: "Load Iris",
      x: 120,
      y: 180,
      filename: "iris.tab",
      sheet: "Sheet1",
      inputs: 0,
      outputs: 1,
      wires: [["node_sampler"]],
    },
    {
      id: "node_sampler",
      type: "or-data-sampler",
      z: "tab1",
      name: "Sample 70/30",
      x: 340,
      y: 180,
      sample_type: "percentage",
      sample_size: 70,
      inputs: 1,
      outputs: 2,
      wires: [["node_tree"], ["node_table"]],
    },
    {
      id: "node_tree",
      type: "or-tree",
      z: "tab1",
      name: "Decision Tree",
      x: 560,
      y: 140,
      max_depth: 5,
      inputs: 1,
      outputs: 1,
      wires: [[]],
    },
    {
      id: "node_table",
      type: "or-data-table",
      z: "tab1",
      name: "Inspect Data",
      x: 560,
      y: 240,
      inputs: 1,
      outputs: 0,
      wires: [],
    },
  ];

  // 1. Node-RED -> React Flow
  const reactFlowGraph = convertNodeRedToReactFlow(originalFlow);

  assert.equal(reactFlowGraph.tabs.length, 1);
  assert.equal(reactFlowGraph.tabs[0].id, "tab1");
  assert.equal(reactFlowGraph.nodes.length, 4);
  assert.equal(reactFlowGraph.edges.length, 3);

  // Check edge bindings
  const edgeLoaderToSampler = reactFlowGraph.edges.find(
    (e) => e.source === "node_loader" && e.target === "node_sampler"
  );
  assert.ok(edgeLoaderToSampler);
  assert.equal(edgeLoaderToSampler?.sourceHandle, "out-0");
  assert.equal(edgeLoaderToSampler?.targetHandle, "in-0");

  const edgeSamplerToTable = reactFlowGraph.edges.find(
    (e) => e.source === "node_sampler" && e.target === "node_table"
  );
  assert.ok(edgeSamplerToTable);
  assert.equal(edgeSamplerToTable?.sourceHandle, "out-1"); // 2nd output port!

  // 2. React Flow -> Node-RED (Round-Trip)
  const roundTripFlow = convertReactFlowToNodeRed(reactFlowGraph);

  assert.equal(roundTripFlow.length, originalFlow.length);

  const tabNode = roundTripFlow.find((n) => n.id === "tab1") as any;
  assert.ok(tabNode);
  assert.equal(tabNode.type, "tab");
  assert.equal(tabNode.label, "Iris Workflow");

  const samplerNode = roundTripFlow.find((n) => n.id === "node_sampler") as any;
  assert.ok(samplerNode);
  assert.equal(samplerNode.sample_size, 70);
  assert.equal(samplerNode.sample_type, "percentage");
  assert.equal(samplerNode.wires.length, 2);
  assert.deepEqual(samplerNode.wires[0], ["node_tree"]);
  assert.deepEqual(samplerNode.wires[1], ["node_table"]);

  const loaderNode = roundTripFlow.find((n) => n.id === "node_loader") as any;
  assert.ok(loaderNode);
  assert.equal(loaderNode.filename, "iris.tab");
  assert.deepEqual(loaderNode.wires, [["node_sampler"]]);
});

test("JsonRpcClient: Successful Method Call over Mock Fetch", async () => {
  const mockFetch: typeof fetch = async (url, init) => {
    const body = JSON.parse(init?.body as string);
    assert.equal(body.jsonrpc, "2.0");
    assert.equal(body.method, "flows.get");

    return {
      ok: true,
      status: 200,
      json: async () => ({
        jsonrpc: "2.0",
        id: body.id,
        result: { flows: [{ id: "tab1", type: "tab" }], rev: "abc-123" },
      }),
    } as any;
  };

  const client = new JsonRpcClient({
    httpUrl: "/api/rpc",
    fetchFn: mockFetch,
  });

  const res = await client.call<{ flows: any[]; rev: string }>("flows.get");
  assert.equal(res.rev, "abc-123");
  assert.equal(res.flows.length, 1);
});

test("JsonRpcClient: Error Handling with Standard Exception", async () => {
  const mockFetch: typeof fetch = async (url, init) => {
    const body = JSON.parse(init?.body as string);
    return {
      ok: true,
      status: 200,
      json: async () => ({
        jsonrpc: "2.0",
        id: body.id,
        error: {
          code: -32601,
          message: "Method not found",
        },
      }),
    } as any;
  };

  const client = new JsonRpcClient({
    httpUrl: "/api/rpc",
    fetchFn: mockFetch,
  });

  await assert.rejects(
    async () => {
      await client.call("unknown.method");
    },
    (err: any) => {
      assert.ok(err instanceof JsonRpcException);
      assert.equal(err.code, -32601);
      assert.equal(err.message, "Method not found");
      return true;
    }
  );
});

test("JsonRpcClient: Notification handling", () => {
  const client = new JsonRpcClient();
  let receivedParams: any = null;

  const unsubscribe = client.onNotification("node.status", (params) => {
    receivedParams = params;
  });

  client.handleIncomingMessage({
    jsonrpc: "2.0",
    method: "node.status",
    params: { node_id: "node_123", status: "running" },
  });

  assert.deepEqual(receivedParams, {
    node_id: "node_123",
    status: "running",
  });

  // Test unsubscribe
  unsubscribe();
  receivedParams = null;
  client.handleIncomingMessage({
    jsonrpc: "2.0",
    method: "node.status",
    params: { node_id: "node_123", status: "idle" },
  });
  assert.equal(receivedParams, null);
});