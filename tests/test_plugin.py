""" Test suite for the OrangeRed FastAPI-Red plugin.
"""

import asyncio
import pytest
from fastapi.testclient import TestClient

from fastapi_red.main import app
from fastapi_red.runtime.engine import engine
from fastapi_red.runtime import registry
from fastapi_red_orangered.base_node import preview_cache


@pytest.fixture(scope="module", autouse=True)
def init_lifespan():
    with TestClient(app) as client:
        yield client


def test_plugin_discovery_and_registry(init_lifespan):
    """ Test that plugin nodes and HTML templates are registered into FastAPI-Red. """
    client = init_lifespan

    # 1. Verify node list contains Orange nodes
    node_list = registry.get_node_list()
    module_names = {n["module"] for n in node_list}
    assert "node-red-contrib-orangered" in module_names

    or_nodes = [n for n in node_list if n["module"] == "node-red-contrib-orangered"]
    assert len(or_nodes) >= 40

    # 2. Verify HTML template endpoints return valid content
    res = client.get("/nodes", headers={"Accept": "text/html"})
    assert res.status_code == 200
    assert "or-file-loader" in res.text
    assert "or-random-forest" in res.text
    assert "or-tree" in res.text
    assert "or-scatter-plot" in res.text


@pytest.mark.asyncio
async def test_in_memory_ml_pipeline():
    """ Test building and executing an ML pipeline:
    FileLoader (iris) -> DataSampler -> RandomForest -> TestAndScore
    """
    flow_config = [
        {
            "id": "node_loader",
            "type": "or-file-loader",
            "filePath": "iris",
            "wires": [["node_sampler"]],
        },
        {
            "id": "node_sampler",
            "type": "or-data-sampler",
            "sampleType": "Proportion",
            "sampleProportion": 80,
            "wires": [["node_rf", "node_eval"], []],
        },
        {
            "id": "node_rf",
            "type": "or-random-forest",
            "nEstimators": 10,
            "wires": [["node_eval"], []],
        },
        {
            "id": "node_eval",
            "type": "or-test-and-score",
            "cvFolds": 3,
            "wires": [[], []],
        },
    ]

    await engine.start(flow_config)

    # Trigger root file loader
    loader_node = engine.get_node("node_loader")
    assert loader_node is not None
    await loader_node.on_input({})

    # Allow asyncio event bus tasks to settle
    await asyncio.sleep(1.0)

    # 1. Verify FileLoader output
    assert "node_loader" in preview_cache
    loader_cache = preview_cache["node_loader"]["outputs"]
    assert "Data" in loader_cache
    assert len(loader_cache["Data"]) == 150

    # 2. Verify DataSampler output
    assert "node_sampler" in preview_cache
    sampler_cache = preview_cache["node_sampler"]["outputs"]
    assert "Data Sample" in sampler_cache
    assert len(sampler_cache["Data Sample"]) == 120

    # 3. Verify RandomForest output
    assert "node_rf" in preview_cache
    rf_cache = preview_cache["node_rf"]["outputs"]
    assert "Model" in rf_cache

    # 4. Verify Test & Score output
    assert "node_eval" in preview_cache
    eval_cache = preview_cache["node_eval"]["outputs"]
    assert "Evaluation Results" in eval_cache


@pytest.mark.asyncio
async def test_preview_api_endpoints(init_lifespan):
    """ Test preview and diagnostics REST endpoints for frontend dialogs. """
    client = init_lifespan

    # 1. Test Tabulator preview on file loader
    res = client.get("/orangered/preview/node_loader/Data?rows=10")
    assert res.status_code == 200
    data = res.json()
    assert data["total_rows"] == 150
    assert len(data["rows"]) == 10
    assert "sepal length" in data["rows"][0]
    assert "column_stats" in data

    # 2. Test metrics endpoint on test & score node
    res_m = client.get("/orangered/metrics/node_eval")
    assert res_m.status_code == 200
    metrics = res_m.json()
    assert "scores" in metrics
    assert "CA" in metrics["scores"]
    assert len(metrics["scores"]["CA"]) > 0


@pytest.mark.asyncio
async def test_native_bridge_pipeline():
    """ Test interoperability between standard Node-RED streams and Orange nodes:
    inject (or simulated stream) -> or-bridge-in -> or-bridge-out -> debug
    """
    records = [
        {"x": 1.0, "y": 2.0, "label": "A"},
        {"x": 3.0, "y": 4.0, "label": "B"},
        {"x": 5.0, "y": 6.0, "label": "A"},
    ]

    flow_config = [
        {
            "id": "node_bridge_in",
            "type": "or-bridge-in",
            "wires": [["node_bridge_out"]],
        },
        {
            "id": "node_bridge_out",
            "type": "or-bridge-out",
            "wires": [["node_debug"]],
        },
        {
            "id": "node_debug",
            "type": "debug",
            "wires": [],
        },
    ]

    await engine.start(flow_config)

    bridge_in = engine.get_node("node_bridge_in")
    debug_node = engine.get_node("node_debug")

    received_msgs = []
    async def capture_receive(msg):
        received_msgs.append(msg)
    debug_node.receive = capture_receive

    # Inject standard Python dictionaries into bridge-in
    await bridge_in.on_input({"payload": records})
    await asyncio.sleep(0.5)

    assert len(received_msgs) == 1
    out_payload = received_msgs[0]["payload"]
    assert isinstance(out_payload, list)
    assert len(out_payload) == 3
    assert out_payload[0]["x"] == 1.0
    assert out_payload[0]["label"] == "A"
