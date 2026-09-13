""" FastAPI APIRouter for RedOrange preview, metrics, and diagnostics.

Mounts routes under both /redorange/* (direct Node-RED editor compatibility)
and /api/redorange/* (standard REST API convention).
"""

from __future__ import annotations

import io
import logging
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from PIL import Image

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pathlib import Path

from red_orange.base_node import preview_cache
from red_orange.conversion import table_to_dataframe
from red_orange.schemas import ColumnStats, MetricsResponse, TablePreviewResponse

logger = logging.getLogger("red_orange.api")

router = APIRouter(tags=["RedOrange"])

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"


def _get_node_output(node_id: str, output_name: str) -> Any:
    cache = preview_cache.get(node_id)
    if not cache:
        raise HTTPException(404, f"Node '{node_id}' not found or not executed yet")
    outputs = cache.get("outputs", {})
    if output_name not in outputs:
        # Fallback to checking widget directly if output is stored on it
        widget = cache.get("widget")
        if widget and hasattr(widget, output_name.lower()):
            return getattr(widget, output_name.lower())
        raise HTTPException(404, f"Output '{output_name}' not available on node '{node_id}'")
    return outputs[output_name]


# ======================================================================
# 1. Tabulator Table Preview
# ======================================================================

@router.get("/redorange/preview/{node_id}/{output_name}")
@router.get("/api/redorange/preview/{node_id}/{output_name}")
def get_table_preview(node_id: str, output_name: str, rows: int = Query(default=50), offset: int = Query(default=0)):
    from Orange.data import Table as OrangeTable

    val = _get_node_output(node_id, output_name)
    if not isinstance(val, OrangeTable):
        raise HTTPException(400, f"Output '{output_name}' is not an Orange.data.Table")

    df, schema = table_to_dataframe(val)

    # Compute column stats for preview UI
    stats: Dict[str, ColumnStats] = {}
    for col in df.columns:
        series = df[col]
        missing = int(series.isna().sum())

        is_discrete = False
        is_numeric = False
        for spec in schema.attributes + schema.class_vars + schema.metas:
            if spec.name == col:
                if spec.var_type.value == "discrete":
                    is_discrete = True
                elif spec.var_type.value == "continuous":
                    is_numeric = True
                break

        if is_numeric:
            stats[col] = ColumnStats(
                min=float(series.min()) if not pd.isna(series.min()) else None,
                max=float(series.max()) if not pd.isna(series.max()) else None,
                mean=float(series.mean()) if not pd.isna(series.mean()) else None,
                std=float(series.std()) if not pd.isna(series.std()) else None,
                missing=missing,
            )
        elif is_discrete:
            dist = series.value_counts().to_dict()
            stats[col] = ColumnStats(
                distribution={str(k): int(v) for k, v in dist.items()},
                missing=missing,
            )
        else:
            stats[col] = ColumnStats(missing=missing)

    sliced_df = df.iloc[offset : offset + rows]
    sliced_df = sliced_df.replace({pd.NA: None, float("nan"): None})

    return TablePreviewResponse(
        total_rows=len(df),
        total_cols=len(df.columns),
        schema_=schema,
        rows=sliced_df.to_dict(orient="records"),
        column_stats=stats,
    )


# ======================================================================
# 2. SciPy Image Preview (PNG Stream)
# ======================================================================

@router.get("/redorange/image/{node_id}/{output_name}")
@router.get("/api/redorange/image/{node_id}/{output_name}")
def get_image_preview(node_id: str, output_name: str, t: Optional[str] = None):
    import xarray as xr

    val = _get_node_output(node_id, output_name)
    if not isinstance(val, xr.DataArray):
        raise HTTPException(400, f"Output '{output_name}' is not an xarray.DataArray")

    try:
        arr = val.values
        if arr.dtype != np.uint8:
            ptp = arr.ptp()
            if ptp > 0:
                arr = (255.0 * (arr - arr.min()) / ptp).astype(np.uint8)
            else:
                arr = arr.astype(np.uint8)

        img = Image.fromarray(arr)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)

        return StreamingResponse(img_byte_arr, media_type="image/png")
    except Exception as e:
        raise HTTPException(500, f"Failed to generate image preview: {e}")


# ======================================================================
# 3. Model Evaluation Metrics & Confusion Matrix
# ======================================================================

@router.get("/redorange/metrics/{node_id}")
@router.get("/api/redorange/metrics/{node_id}")
def get_metrics(node_id: str):
    from Orange.evaluation import Results
    import Orange.evaluation as eval_mod

    results = _get_node_output(node_id, "Evaluation Results")
    if not isinstance(results, Results):
        raise HTTPException(400, "Output is not an Evaluation Results object")

    if getattr(results, "data", None) is not None:
        is_classification = results.data.domain.has_discrete_class
        class_names = list(results.data.domain.class_var.values) if results.data.domain.class_var else []
    else:
        is_classification = True
        class_names = []

    learners = [getattr(l, "name", f"Model {i}") for i, l in enumerate(results.learners or [])]
    scores: Dict[str, List[float]] = {}

    if is_classification:
        try:
            scores["CA"] = eval_mod.CA(results).tolist()
            scores["F1"] = eval_mod.F1(results, average="weighted").tolist()
            scores["AUC"] = eval_mod.AUC(results, average="weighted").tolist()
            scores["Precision"] = eval_mod.Precision(results, average="weighted").tolist()
            scores["Recall"] = eval_mod.Recall(results, average="weighted").tolist()
        except Exception:
            pass

        try:
            cm = eval_mod.ConfusionMatrix(results)
            confusion_matrix = {learners[i]: m.tolist() for i, m in enumerate(cm)}
        except Exception:
            confusion_matrix = {}
    else:
        scores["RMSE"] = eval_mod.RMSE(results).tolist()
        scores["MAE"] = eval_mod.MAE(results).tolist()
        scores["R2"] = eval_mod.R2(results).tolist()
        confusion_matrix = {}
        class_names = []

    return MetricsResponse(
        learners=learners,
        scores=scores,
        confusion_matrix=confusion_matrix,
        class_names=class_names,
    )


# ======================================================================
# 4. Coefficients (Linear & Logistic Regression)
# ======================================================================

@router.get("/redorange/coefficients/{node_id}")
@router.get("/api/redorange/coefficients/{node_id}")
def get_coefficients(node_id: str):
    model = _get_node_output(node_id, "Model")
    if not (hasattr(model, "coefficients") and hasattr(model, "intercept")):
        raise HTTPException(400, "Model does not expose coefficients and intercept")

    try:
        coef = np.asarray(model.coefficients)
        intercept = model.intercept
        domain = model.domain

        attributes = [v.name for v in domain.attributes]
        classes = list(domain.class_var.values) if domain.class_var and domain.class_var.is_discrete else []

        rows: List[Dict[str, Any]] = []
        if coef.ndim == 1 or coef.shape[0] == 1:
            c_vals = coef[0] if coef.ndim == 2 else coef
            inter = float(intercept[0]) if isinstance(intercept, (list, tuple, np.ndarray)) else float(intercept)
            rows.append({"feature": "Intercept", "coef": inter})
            for i, attr in enumerate(attributes):
                if i < len(c_vals):
                    rows.append({"feature": attr, "coef": float(c_vals[i])})
        else:
            for class_idx, class_name in enumerate(classes):
                c_vals = coef[class_idx]
                rows.append({"class": class_name, "feature": "Intercept", "coef": float(intercept[class_idx])})
                for i, attr in enumerate(attributes):
                    if i < len(c_vals):
                        rows.append({"class": class_name, "feature": attr, "coef": float(c_vals[i])})

        return {"rows": rows}
    except Exception as e:
        raise HTTPException(500, f"Error getting coefficients: {e}")


# ======================================================================
# 5. ROC Curves
# ======================================================================

@router.get("/redorange/roc/{node_id}")
@router.get("/api/redorange/roc/{node_id}")
def get_roc(node_id: str):
    from Orange.evaluation import Results

    results = _get_node_output(node_id, "Evaluation Results")
    if not isinstance(results, Results):
        raise HTTPException(400, "Output is not an Evaluation Results object")

    if not hasattr(results, "probabilities") or results.probabilities is None:
        raise HTTPException(400, "No probability data available for ROC curves")

    class_names = []
    if getattr(results, "data", None) is not None and results.data.domain.class_var:
        class_names = list(results.data.domain.class_var.values)

    learner_names = [getattr(l, "name", f"Model {i}") for i, l in enumerate(results.learners or [])]
    roc_data: Dict[str, Any] = {}
    n_learners = results.probabilities.shape[0]
    n_classes = len(class_names) if class_names else results.probabilities.shape[2]

    for li in range(n_learners):
        learner_name = learner_names[li] if li < len(learner_names) else f"Model {li}"
        curves = []
        for ci in range(n_classes):
            y_true = (results.actual == ci).astype(int)
            y_score = results.probabilities[li, :, ci]

            order = np.argsort(-y_score)
            y_true_sorted = y_true[order]
            y_score_sorted = y_score[order]

            tps = np.cumsum(y_true_sorted)
            fps = np.cumsum(1 - y_true_sorted)
            tpr = tps / tps[-1] if tps[-1] > 0 else tps
            fpr = fps / fps[-1] if fps[-1] > 0 else fps

            tpr = np.concatenate([[0], tpr])
            fpr = np.concatenate([[0], fpr])

            if len(tpr) > 200:
                idx = np.linspace(0, len(tpr) - 1, 200, dtype=int)
                tpr = tpr[idx]
                fpr = fpr[idx]

            class_label = class_names[ci] if ci < len(class_names) else f"Class {ci}"
            curves.append({
                "class_name": class_label,
                "fpr": fpr.tolist(),
                "tpr": tpr.tolist(),
            })
        roc_data[learner_name] = curves

    return {"learners": learner_names, "class_names": class_names, "roc_curves": roc_data}


# ======================================================================
# 6. Tree Structure Visualization
# ======================================================================

@router.get("/redorange/tree/{node_id}")
@router.get("/api/redorange/tree/{node_id}")
def get_tree_structure(node_id: str, max_depth: int = Query(default=100)):
    model = _get_node_output(node_id, "Model")

    # 1. Check if model is an Orange TreeModel (model.root)
    if hasattr(model, "root") and model.root is not None:
        classes = [str(c) for c in model.domain.class_var.values] if (model.domain is not None and model.domain.class_var and model.domain.class_var.is_discrete) else []

        def build_orange_node(node, current_depth: int) -> Dict[str, Any]:
            children = getattr(node, "children", []) or []
            is_leaf = len(children) == 0
            val = node.value.tolist() if (hasattr(node, "value") and node.value is not None) else []
            majority = classes[int(np.argmax(val))] if (classes and val) else "Unknown"
            attr_name = str(node.attr.name) if getattr(node, "attr", None) is not None else "Leaf"

            node_info: Dict[str, Any] = {
                "name": f"Node ({attr_name})" if not is_leaf else f"Leaf ({majority})",
                "samples": len(node.subset) if getattr(node, "subset", None) is not None else 0,
                "value": val,
                "class_name": majority,
            }
            if hasattr(node, "description") and node.description:
                node_info["condition"] = str(node.description)

            if not is_leaf and current_depth < max_depth:
                node_info["children"] = [
                    build_orange_node(c, current_depth + 1) for c in children
                ]
            return node_info

        try:
            return build_orange_node(model.root, 0)
        except Exception as e:
            raise HTTPException(500, f"Error parsing Orange tree structure: {e}")

    # 2. Check if model wraps a scikit-learn tree (skl_model.tree_)
    if hasattr(model, "skl_model") and hasattr(model.skl_model, "tree_"):
        tree = model.skl_model.tree_
        domain = model.domain
        features = [a.name for a in domain.attributes]
        classes = [str(c) for c in domain.class_var.values] if domain.class_var and domain.class_var.is_discrete else []

        def build_skl_node(node_idx: int, current_depth: int) -> Dict[str, Any]:
            is_leaf = tree.children_left[node_idx] == -1 and tree.children_right[node_idx] == -1
            value = tree.value[node_idx][0]
            if len(classes) > 0:
                class_idx = np.argmax(value)
                majority_class = classes[class_idx]
            else:
                majority_class = f"Value: {value[0]:.3f}"

            node_info: Dict[str, Any] = {
                "name": f"Node {node_idx}",
                "samples": int(tree.n_node_samples[node_idx]),
                "value": value.tolist(),
                "class_name": majority_class,
                "impurity": float(tree.impurity[node_idx]),
            }

            if not is_leaf and current_depth < max_depth:
                feature_idx = tree.feature[node_idx]
                feature_name = features[feature_idx] if feature_idx < len(features) else f"Feature {feature_idx}"
                threshold = float(tree.threshold[node_idx])
                node_info["condition"] = f"{feature_name} <= {threshold:.3f}"
                node_info["children"] = [
                    build_skl_node(tree.children_left[node_idx], current_depth + 1),
                    build_skl_node(tree.children_right[node_idx], current_depth + 1),
                ]
            return node_info

        try:
            return build_skl_node(0, 0)
        except Exception as e:
            raise HTTPException(500, f"Error parsing scikit-learn tree structure: {e}")

    raise HTTPException(400, "Model is not a Decision Tree or does not expose tree structure")


# ======================================================================
# 7. Correlations & Rank
# ======================================================================

@router.get("/redorange/correlations/{node_id}")
@router.get("/api/redorange/correlations/{node_id}")
def get_correlations(node_id: str):
    cache = preview_cache.get(node_id)
    if not cache:
        raise HTTPException(404, f"Node '{node_id}' not found")
    widget = cache.get("widget")
    if not hasattr(widget, "matrix_data"):
        raise HTTPException(400, "Node is not a Correlations node")
    return widget.matrix_data


@router.get("/redorange/rank_scores/{node_id}")
@router.get("/api/redorange/rank_scores/{node_id}")
def get_rank_scores(node_id: str):
    cache = preview_cache.get(node_id)
    if not cache:
        raise HTTPException(404, f"Node '{node_id}' not found")
    widget = cache.get("widget")
    if not hasattr(widget, "scores_data"):
        raise HTTPException(400, "Node is not a Rank node")
    return widget.scores_data


# ======================================================================
# 8. Tracker Runs & UI Asset
# ======================================================================

@router.get("/redorange/tracker/runs")
@router.get("/api/redorange/tracker/runs")
def get_tracker_runs(node_id: str = Query(default="")):
    from red_orange.tracker import list_runs

    runs = list_runs()
    if node_id:
        runs = [r for r in runs if r.get("tags", {}).get("redorange.node_id") == node_id]
    return {"runs": runs}


@router.get("/redorange/tracker-ui.js")
def get_tracker_ui():
    ui_path = TEMPLATES_DIR / "nodes" / "or-tracker-ui.js"
    if ui_path.is_file():
        return FileResponse(ui_path, media_type="application/javascript")
    return Response(status_code=404)
