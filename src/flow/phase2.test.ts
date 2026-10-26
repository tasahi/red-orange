import test from "node:test";
import assert from "node:assert/strict";
import {
  NODE_CATALOG,
  getNodeCatalogItem,
  getCatalogGroupedByCategory,
} from "./catalog.ts";
import type { NodeCatalogItem } from "./catalog.ts";
import {
  computeNodeViewModel,
  validateConnection,
} from "./nodeViewModel.ts";
import {
  createDragPayload,
  instantiateDroppedNode,
} from "./paletteDnd.ts";

test("NodeCatalog: Catalog Items and Fallbacks", () => {
  const fileItem = getNodeCatalogItem("or-file-loader");
  assert.equal(fileItem.label, "File");
  assert.equal(fileItem.category, "OR Data");
  assert.equal(fileItem.outputs, 1);
  assert.equal(fileItem.color, "#FFAA00");

  const unknownItem = getNodeCatalogItem("non-existent-type");
  assert.equal(unknownItem.type, "non-existent-type");
  assert.equal(unknownItem.category, "common");

  const grouped = getCatalogGroupedByCategory();
  assert.ok(grouped["OR Data"].length > 0);
  assert.ok(grouped["OR Model"].length > 0);
});

test("NodeViewModel: Compute Stacked Port Handles and Badge Colors", () => {
  // Test single output node
  const vmSingle = computeNodeViewModel({
    type: "or-file-loader",
    config: {},
  });
  assert.equal(vmSingle.badgeColor, "#FFAA00");
  assert.equal(vmSingle.inputPorts.length, 0);
  assert.equal(vmSingle.outputPorts.length, 1);
  assert.equal(vmSingle.outputPorts[0].topPercent, 50);

  // Test multi-output node (or-data-sampler has 2 outputs)
  const vmSampler = computeNodeViewModel({
    type: "or-data-sampler",
    config: {},
  });
  assert.equal(vmSampler.outputPorts.length, 2);
  assert.equal(vmSampler.outputPorts[0].id, "out-0");
  assert.equal(vmSampler.outputPorts[1].id, "out-1");
  assert.ok(vmSampler.outputPorts[0].topPercent < vmSampler.outputPorts[1].topPercent);

  // Test trigger button presence
  const vmInject = computeNodeViewModel({
    type: "inject",
    config: {},
  });
  assert.equal(vmInject.hasTriggerButton, true);
});

test("NodeViewModel: Connection Validation Logic", () => {
  // Self connection
  const resSelf = validateConnection("node1", "node1", "out-0", "in-0");
  assert.equal(resSelf.valid, false);

  // Invalid source (not an output handle)
  const resBadSource = validateConnection("node1", "node2", "in-0", "in-0");
  assert.equal(resBadSource.valid, false);

  // Valid connection
  const resValid = validateConnection("node1", "node2", "out-0", "in-0");
  assert.equal(resValid.valid, true);
});

test("PaletteDnD: Drag Payload creation and canvas node instantiation", () => {
  const payload = createDragPayload("or-random-forest");
  assert.equal(payload.type, "or-random-forest");
  assert.equal(payload.category, "OR Model");
  assert.equal(payload.defaultConfig.n_estimators, 100);

  const newNode = instantiateDroppedNode(payload, { x: 250.7, y: 310.2 }, "tab1", "custom_rf_id");
  assert.equal(newNode.id, "custom_rf_id");
  assert.equal(newNode.type, "orangeNode");
  assert.equal(newNode.position.x, 251);
  assert.equal(newNode.position.y, 310);
  assert.equal(newNode.data.type, "or-random-forest");
  assert.equal(newNode.data.z, "tab1");
  assert.equal(newNode.data.config.n_estimators, 100);
});