import { describe, it } from "node:test";
import assert from "node:assert";
import { NODE_CATALOG, getNodeCatalogItem, getCatalogGroupedByCategory } from "./catalog.ts";
import type { SemanticPayload, NodeAttributeSet } from "./types.ts";

describe("Red-Cyan Node Catalog & Type Integration", () => {
  it("includes Cyan Prompt category and defined nodes", () => {
    const item = getNodeCatalogItem("cyan-prompt-transform");
    assert.strictEqual(item.category, "Cyan Prompt");
    assert.strictEqual(item.label, "Prompt Transform");
    assert.strictEqual(item.color, "#06B6D4");
    assert.ok(item.defaultConfig);
    assert.strictEqual((item.defaultConfig as any).model, "gpt-4o");
  });

  it("groups cyan nodes into Cyan Prompt category in catalog", () => {
    const grouped = getCatalogGroupedByCategory();
    assert.ok(grouped["Cyan Prompt"]);
    const cyanTypes = grouped["Cyan Prompt"].map((n) => n.type);
    assert.ok(cyanTypes.includes("cyan-prompt-transform"));
    assert.ok(cyanTypes.includes("cyan-tabular-context"));
    assert.ok(cyanTypes.includes("cyan-synthesis-node"));
  });

  it("validates SemanticPayload contract instantiation", () => {
    const attrs: NodeAttributeSet = {
      static: { domain: "churn" },
      dynamic: { sentiment: "negative", confidence: 0.92 },
    };
    const payload: SemanticPayload = {
      node_id: "node_01",
      run_id: "run_01",
      text_content: "High churn rate in cohort Q2",
      structured_data: { churn_rate: 0.18 },
      attributes: attrs,
      parent_node_ids: ["orange_data_01"],
    };
    assert.strictEqual(payload.node_id, "node_01");
    assert.strictEqual(payload.attributes.static.domain, "churn");
    assert.strictEqual(payload.parent_node_ids?.[0], "orange_data_01");
  });
});

import { inferTemplatePorts, computeDynamicPortLayouts } from "./cyanViewModel.ts";
import { instantiateDroppedNode, createDragPayload } from "./paletteDnd.ts";

describe("Red-Cyan Dynamic Ports & DnD Instantiation", () => {
  it("extracts template variable names from Jinja syntax", () => {
    const template = "Summarize {{ inputs.sales_data.text }} and evaluate {{ inputs.customer_reviews.summary }}";
    const ports = inferTemplatePorts(template);
    assert.deepStrictEqual(ports, ["customer_reviews", "sales_data"]);
  });

  it("handles empty or variable-free templates with fallback port", () => {
    const ports = inferTemplatePorts("Static instruction with no dynamic variables");
    assert.deepStrictEqual(ports, []);
    const layouts = computeDynamicPortLayouts(ports);
    assert.strictEqual(layouts.length, 1);
    assert.strictEqual(layouts[0].id, "in-0");
  });

  it("computes stacked port positions for dynamic handles", () => {
    const ports = ["alpha", "beta", "gamma"];
    const layouts = computeDynamicPortLayouts(ports);
    assert.strictEqual(layouts.length, 3);
    assert.strictEqual(layouts[0].id, "in-alpha");
    assert.strictEqual(layouts[1].id, "in-beta");
    assert.strictEqual(layouts[2].id, "in-gamma");
    assert.strictEqual(layouts[0].topPercent, 25);
    assert.strictEqual(layouts[1].topPercent, 50);
    assert.strictEqual(layouts[2].topPercent, 75);
  });

  it("instantiates cyanPromptNode React Flow node when dropped from palette", () => {
    const payload = createDragPayload("cyan-prompt-transform");
    const node = instantiateDroppedNode(payload, { x: 300, y: 400 }, "tab_main");
    assert.strictEqual(node.type, "cyanPromptNode");
    assert.strictEqual(node.data.category, "Cyan Prompt");
    assert.strictEqual(node.position.x, 300);
    assert.strictEqual(node.position.y, 400);
  });
});

import { McpBridgeClient } from "./mcpBridgeClient.ts";
import { JsonRpcClient } from "./rpcClient.ts";

describe("Red-Cyan MCP Bridge Client", () => {
  it("queries MCP tabular resources over JSON-RPC mock transport", async () => {
    const mockRpc = new JsonRpcClient();
    (mockRpc as any).call = async (method: string, params: any) => {
      if (method === "resources/list") {
        return {
          resources: [
            {
              uri: "resource://red-orange/datasets/iris/summary",
              name: "Iris Summary",
            },
          ],
        };
      }
      if (method === "resources/read" && params?.uri === "resource://red-orange/datasets/iris/summary") {
        return {
          contents: [
            {
              uri: params.uri,
              mimeType: "application/json",
              text: JSON.stringify({ row_count: 150, target: "species" }),
            },
          ],
        };
      }
      throw new Error(`Unexpected method: ${method}`);
    };

    const bridge = new McpBridgeClient(mockRpc);
    const resources = await bridge.listResources();
    assert.strictEqual(resources.length, 1);
    assert.strictEqual(resources[0].uri, "resource://red-orange/datasets/iris/summary");

    const dataset = await bridge.readResource(resources[0].uri);
    assert.strictEqual(dataset.row_count, 150);
    assert.strictEqual(dataset.target, "species");
  });

  it("invokes quantitative MCP tools for agentic feedback loop", async () => {
    const mockRpc = new JsonRpcClient();
    (mockRpc as any).call = async (method: string, params: any) => {
      if (method === "tools/call" && params?.name === "orange_filter_rows") {
        return {
          isError: false,
          content: [
            {
              type: "text",
              text: JSON.stringify({ status: "filtered", retained_count: 85 }),
            },
          ],
        };
      }
      throw new Error(`Unexpected method: ${method}`);
    };

    const bridge = new McpBridgeClient(mockRpc);
    const result: any = await bridge.callTool("orange_filter_rows", {
      column: "petal_length",
      threshold: 1.5,
    });
    assert.strictEqual(result.status, "filtered");
    assert.strictEqual(result.retained_count, 85);
  });
});

