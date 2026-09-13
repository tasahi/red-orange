""" Comprehensive test suite covering regression, correlation, rank, tree, and image nodes in Red-Fastapi.
"""

import asyncio
import pytest
from fastapi.testclient import TestClient

from fastapi_red.main import app
from fastapi_red.runtime.engine import engine
from red_orange.base_node import preview_cache


@pytest.fixture(scope="module", autouse=True)
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.asyncio
async def test_linear_regression_and_coefficients(client):
    """ Test Linear Regression node training and coefficients endpoint. """
    flow = [
        {"id": "fl", "type": "or-file-loader", "filePath": "housing", "wires": [["lr"]]},
        {
            "id": "lr",
            "type": "or-linear-regression",
            "regularization": "ridge",
            "alpha": 0.5,
            "wires": [[], []],
        },
    ]

    await engine.start(flow)
    loader = engine.get_node("fl")
    await loader.on_input({})
    await asyncio.sleep(1.0)

    assert "lr" in preview_cache
    outputs = preview_cache["lr"]["outputs"]
    assert "Model" in outputs

    res = client.get("/redorange/coefficients/lr")
    assert res.status_code == 200
    coef_data = res.json()
    assert "rows" in coef_data
    assert len(coef_data["rows"]) > 0
    assert coef_data["rows"][0]["feature"] == "Intercept"


@pytest.mark.asyncio
async def test_correlations_and_rank(client):
    """ Test Correlations and Rank feature importance nodes. """
    flow = [
        {"id": "fl", "type": "or-file-loader", "filePath": "iris", "wires": [["corr", "rk"]]},
        {"id": "corr", "type": "or-correlations", "method": "pearson", "wires": [[], []]},
        {"id": "rk", "type": "or-rank", "scorer": "auto", "topK": 2, "wires": [[], []]},
    ]

    await engine.start(flow)
    loader = engine.get_node("fl")
    await loader.on_input({})
    await asyncio.sleep(1.0)

    # 1. Test Correlations endpoint
    res_c = client.get("/redorange/correlations/corr")
    assert res_c.status_code == 200
    corr_data = res_c.json()
    assert "features" in corr_data
    assert "matrix" in corr_data
    assert len(corr_data["matrix"]) == 4

    # 2. Test Rank endpoint
    res_r = client.get("/redorange/rank_scores/rk")
    assert res_r.status_code == 200
    rank_data = res_r.json()
    assert "ranked_features" in rank_data
    assert len(rank_data["ranked_features"]) == 4
    assert rank_data["n_selected"] == 2


@pytest.mark.asyncio
async def test_tree_hierarchy_endpoint(client):
    """ Test Tree node structure visualization hierarchy. """
    flow = [
        {"id": "fl", "type": "or-file-loader", "filePath": "iris", "wires": [["tr"]]},
        {"id": "tr", "type": "or-tree", "maxDepth": 3, "wires": [[], []]},
    ]

    await engine.start(flow)
    loader = engine.get_node("fl")
    await loader.on_input({})
    await asyncio.sleep(1.0)

    res_t = client.get("/redorange/tree/tr")
    assert res_t.status_code == 200
    tree_data = res_t.json()
    assert "name" in tree_data
    assert "children" in tree_data
    assert len(tree_data["children"]) == 2
