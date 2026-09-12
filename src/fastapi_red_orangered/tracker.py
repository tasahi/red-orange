"""
MLflow-compatible experiment tracker — zero external dependencies.

Writes training runs to the ``mlruns/`` directory in the exact same
folder layout that MLflow uses, so that running::

    mlflow ui --backend-store-uri ./mlruns

instantly picks up all historical data without any migration.

Usage inside OrangeRed is fully automatic: the ``_HLBaseLearner`` calls
:func:`log_training_run` after every successful model fit.
"""

from __future__ import annotations

import logging
import os
import pickle
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)

# Root directory for all experiment data (relative to the project)
_MLRUNS_ROOT: Path | None = None


def _root() -> Path:
    """Return the mlruns root directory, creating it if needed."""
    global _MLRUNS_ROOT
    if _MLRUNS_ROOT is None:
        _MLRUNS_ROOT = Path(os.environ.get("ORANGERED_MLRUNS", "mlruns"))
    _MLRUNS_ROOT.mkdir(parents=True, exist_ok=True)
    return _MLRUNS_ROOT


# ======================================================================
# Experiment management
# ======================================================================

def _ensure_experiment(experiment_id: str = "0", name: str = "OrangeRed") -> Path:
    """Create the experiment folder and meta.yaml if missing."""
    exp_dir = _root() / experiment_id
    exp_dir.mkdir(parents=True, exist_ok=True)
    meta_path = exp_dir / "meta.yaml"
    if not meta_path.exists():
        meta_path.write_text(
            f"artifact_location: {exp_dir / 'artifacts'}\n"
            f"experiment_id: '{experiment_id}'\n"
            f"lifecycle_stage: active\n"
            f"name: {name}\n",
            encoding="utf-8",
        )
    return exp_dir


# ======================================================================
# Run management
# ======================================================================

def _create_run_dir(experiment_id: str = "0") -> tuple[str, Path]:
    """Create a new run folder and return (run_id, run_path)."""
    exp_dir = _ensure_experiment(experiment_id)
    run_id = uuid.uuid4().hex[:16]
    run_dir = exp_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "params").mkdir(exist_ok=True)
    (run_dir / "metrics").mkdir(exist_ok=True)
    (run_dir / "tags").mkdir(exist_ok=True)
    (run_dir / "artifacts").mkdir(exist_ok=True)
    return run_id, run_dir


def _write_run_meta(
    run_dir: Path,
    run_id: str,
    experiment_id: str,
    status: str,
    start_time: int,
    end_time: int = 0,
    run_name: str = "",
) -> None:
    """Write or overwrite the run's meta.yaml."""
    meta = (
        f"artifact_uri: {run_dir / 'artifacts'}\n"
        f"end_time: {end_time}\n"
        f"experiment_id: '{experiment_id}'\n"
        f"lifecycle_stage: active\n"
        f"run_id: '{run_id}'\n"
        f"run_name: '{run_name}'\n"
        f"start_time: {start_time}\n"
        f"status: {status}\n"
    )
    (run_dir / "meta.yaml").write_text(meta, encoding="utf-8")


def _log_param(run_dir: Path, key: str, value: Any) -> None:
    """Write a single parameter file."""
    (run_dir / "params" / key).write_text(str(value), encoding="utf-8")


def _log_metric(run_dir: Path, key: str, value: float, step: int = 0) -> None:
    """Append a metric entry (MLflow format: timestamp value step)."""
    ts = int(time.time() * 1000)
    line = f"{ts} {value} {step}\n"
    metric_file = run_dir / "metrics" / key
    with metric_file.open("a", encoding="utf-8") as f:
        f.write(line)


def _set_tag(run_dir: Path, key: str, value: str) -> None:
    """Write a tag file."""
    (run_dir / "tags" / key).write_text(value, encoding="utf-8")


def _save_artifact(run_dir: Path, obj: Any, name: str) -> None:
    """Pickle an object into the artifacts folder."""
    artifact_path = run_dir / "artifacts" / name
    with artifact_path.open("wb") as f:
        pickle.dump(obj, f)


# ======================================================================
# High-level API used by model widgets
# ======================================================================

def log_training_run(
    *,
    model_type: str,
    model_name: str,
    params: dict[str, Any],
    metrics: dict[str, float],
    model_obj: Any,
    data_rows: int,
    data_cols: int,
    node_id: str = "",
    experiment_id: str = "0",
) -> str:
    """
    Log a complete training run to the MLflow-compatible store.

    Returns the run_id for reference.
    """
    start_ms = int(time.time() * 1000)
    run_id, run_dir = _create_run_dir(experiment_id)

    run_name = f"{model_name} @ {datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"

    # Meta
    _write_run_meta(
        run_dir, run_id, experiment_id,
        status="RUNNING",
        start_time=start_ms,
        run_name=run_name,
    )

    # Tags
    _set_tag(run_dir, "mlflow.runName", run_name)
    _set_tag(run_dir, "model_type", model_type)
    _set_tag(run_dir, "model_name", model_name)
    _set_tag(run_dir, "orangered.node_id", node_id)

    # Parameters
    for k, v in params.items():
        _log_param(run_dir, k, v)
    _log_param(run_dir, "data_rows", data_rows)
    _log_param(run_dir, "data_cols", data_cols)

    # Metrics
    for k, v in metrics.items():
        _log_metric(run_dir, k, float(v))

    # Artifact: pickled model
    try:
        _save_artifact(run_dir, model_obj, "model.pkl")
    except Exception as exc:
        log.warning("Could not pickle model: %s", exc)

    # Finalize
    end_ms = int(time.time() * 1000)
    _write_run_meta(
        run_dir, run_id, experiment_id,
        status="FINISHED",
        start_time=start_ms,
        end_time=end_ms,
        run_name=run_name,
    )

    log.info("Training run logged: %s (%s) → %s", model_name, model_type, run_id)
    return run_id


# ======================================================================
# Query API (read back stored runs)
# ======================================================================

def list_runs(experiment_id: str = "0") -> list[dict[str, Any]]:
    """Return a list of all runs in the experiment, newest first."""
    exp_dir = _root() / experiment_id
    if not exp_dir.exists():
        return []

    runs = []
    for run_dir in sorted(exp_dir.iterdir(), reverse=True):
        if not run_dir.is_dir():
            continue
        meta_path = run_dir / "meta.yaml"
        if not meta_path.exists():
            continue

        run_info = _parse_run(run_dir)
        if run_info:
            runs.append(run_info)

    # Sort by start_time descending
    runs.sort(key=lambda r: r.get("start_time", 0), reverse=True)
    return runs


def get_run(run_id: str, experiment_id: str = "0") -> Optional[dict[str, Any]]:
    """Return full details for a single run."""
    run_dir = _root() / experiment_id / run_id
    if not run_dir.exists():
        return None
    return _parse_run(run_dir)


def _parse_run(run_dir: Path) -> Optional[dict[str, Any]]:
    """Parse a run directory into a dict."""
    meta_path = run_dir / "meta.yaml"
    if not meta_path.exists():
        return None

    # Parse meta.yaml (simple key: value format)
    meta = {}
    for line in meta_path.read_text(encoding="utf-8").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip("'\"")

    # Read params
    params = {}
    params_dir = run_dir / "params"
    if params_dir.exists():
        for pfile in params_dir.iterdir():
            if pfile.is_file():
                params[pfile.name] = pfile.read_text(encoding="utf-8").strip()

    # Read metrics (take the last value for each metric)
    metrics = {}
    metrics_dir = run_dir / "metrics"
    if metrics_dir.exists():
        for mfile in metrics_dir.iterdir():
            if mfile.is_file():
                lines = mfile.read_text(encoding="utf-8").strip().splitlines()
                if lines:
                    parts = lines[-1].split()
                    if len(parts) >= 2:
                        try:
                            metrics[mfile.name] = float(parts[1])
                        except ValueError:
                            pass

    # Read tags
    tags = {}
    tags_dir = run_dir / "tags"
    if tags_dir.exists():
        for tfile in tags_dir.iterdir():
            if tfile.is_file():
                tags[tfile.name] = tfile.read_text(encoding="utf-8").strip()

    # Check artifact existence
    has_model = (run_dir / "artifacts" / "model.pkl").exists()

    return {
        "run_id": meta.get("run_id", run_dir.name),
        "run_name": meta.get("run_name", ""),
        "status": meta.get("status", "UNKNOWN"),
        "start_time": int(meta.get("start_time", 0)),
        "end_time": int(meta.get("end_time", 0)),
        "params": params,
        "metrics": metrics,
        "tags": tags,
        "has_model_artifact": has_model,
    }


def load_model(run_id: str, experiment_id: str = "0") -> Any:
    """Load a pickled model from a past run."""
    model_path = _root() / experiment_id / run_id / "artifacts" / "model.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"No model artifact for run {run_id}")
    with model_path.open("rb") as f:
        return pickle.load(f)
