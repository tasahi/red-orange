"""
Headless unsupervised learning widgets — pure-Python replacements for the
Orange unsupervised category widgets, without any Qt dependency.
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np

from Orange.data import Table, Domain, DiscreteVariable
from Orange.clustering.kmeans import KMeansModel

from ..headless_widget import HeadlessWidget
from ..schemas import SignalDesc


# ======================================================================
# k-Means Clustering
# ======================================================================

class HLKMeans(HeadlessWidget):
    """
    Headless version of ``OWKMeans``.

    Performs k-Means clustering and outputs:
    - **Annotated Data**: the input table with a new "Cluster" meta column
    - **Centroids**: a table of cluster centroid coordinates

    Settings
    --------
    k : int
        Number of clusters (default 3).
    max_iterations : int
        Maximum number of iterations (default 300).
    n_init : int
        Number of restarts with different seeds (default 10).
    init_method : str
        Initialization method: ``"k-means++"`` or ``"random"``.
    """

    def get_input_signals(self) -> list[SignalDesc]:
        return [
            SignalDesc(name="Data", type="Orange.data.Table", flags={}),
        ]

    def get_output_signals(self) -> list[SignalDesc]:
        return [
            SignalDesc(
                name="Annotated Data",
                type="Orange.data.Table",
                flags={"default": True},
            ),
            SignalDesc(
                name="Centroids",
                type="Orange.data.Table",
                flags={},
            ),
        ]

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self.data: Optional[Table] = None
        self._settings: dict[str, Any] = {
            "k": 3,
            "max_iterations": 300,
            "n_init": 10,
            "init_method": "k-means++",
        }

    def receive(self, input_name: str, value: Any) -> None:
        if input_name == "Data":
            self.data = value

    def handle_new_signals(self) -> None:
        if self.data is None or len(self.data) == 0:
            self.send("Annotated Data", None)
            self.send("Centroids", None)
            return

        from sklearn.cluster import KMeans

        s = self._settings
        k = s.get("k", 3)
        max_iter = s.get("max_iterations", 300)
        n_init = s.get("n_init", 10)
        init = s.get("init_method", "k-means++")

        # Run k-Means on the numeric features
        X = self.data.X
        if X.size == 0:
            self.send("Annotated Data", None)
            self.send("Centroids", None)
            return

        # Handle NaN by replacing with column means
        col_means = np.nanmean(X, axis=0)
        nan_mask = np.isnan(X)
        X_clean = X.copy()
        for j in range(X.shape[1]):
            X_clean[nan_mask[:, j], j] = col_means[j]

        km = KMeans(
            n_clusters=k,
            max_iter=max_iter,
            n_init=n_init,
            init=init,
            random_state=42,
        )
        labels = km.fit_predict(X_clean)

        # Build annotated data with a "Cluster" meta column
        cluster_values = [f"C{i+1}" for i in range(k)]
        cluster_var = DiscreteVariable("Cluster", values=cluster_values)

        new_domain = Domain(
            self.data.domain.attributes,
            self.data.domain.class_vars,
            list(self.data.domain.metas) + [cluster_var],
        )

        # Build metas array
        cluster_col = labels.reshape(-1, 1).astype(float)
        if self.data.metas.size:
            new_metas = np.hstack([self.data.metas, cluster_col])
        else:
            new_metas = cluster_col

        annotated = Table.from_numpy(
            new_domain,
            self.data.X,
            self.data.Y if self.data.Y.size else None,
            metas=new_metas,
        )
        self.send("Annotated Data", annotated)

        # Build centroids table
        centroid_domain = Domain(
            self.data.domain.attributes,
        )
        centroids_table = Table.from_numpy(
            centroid_domain,
            km.cluster_centers_,
        )
        centroids_table.name = "Centroids"
        self.send("Centroids", centroids_table)


# ======================================================================
# DBSCAN Clustering
# ======================================================================

class HLDBSCAN(HeadlessWidget):
    """
    Headless version of ``OWDBSCAN``.

    Performs DBSCAN clustering and outputs:
    - **Annotated Data**: the input table with a new "Cluster" meta column

    Settings
    --------
    eps : float
        The maximum distance between two samples for one to be considered as in the neighborhood of the other.
    min_samples : int
        The number of samples in a neighborhood for a point to be considered as a core point.
    metric : str
        The metric to use when calculating distance between instances (e.g. "euclidean", "manhattan", "cosine").
    """

    def get_input_signals(self) -> list[SignalDesc]:
        return [
            SignalDesc(name="Data", type="Orange.data.Table", flags={}),
        ]

    def get_output_signals(self) -> list[SignalDesc]:
        return [
            SignalDesc(
                name="Annotated Data",
                type="Orange.data.Table",
                flags={"default": True},
            ),
        ]

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self.data: Optional[Table] = None
        self._settings: dict[str, Any] = {
            "eps": 0.5,
            "min_samples": 5,
            "metric": "euclidean",
        }

    def receive(self, input_name: str, value: Any) -> None:
        if input_name == "Data":
            self.data = value

    def handle_new_signals(self) -> None:
        if self.data is None or len(self.data) == 0:
            self.send("Annotated Data", None)
            return

        from sklearn.cluster import DBSCAN

        s = self._settings
        eps = s.get("eps", 0.5)
        min_samples = s.get("min_samples", 5)
        metric = s.get("metric", "euclidean")

        # Run DBSCAN on the numeric features
        X = self.data.X
        if X.size == 0:
            self.send("Annotated Data", None)
            return

        # Handle NaN by replacing with column means
        col_means = np.nanmean(X, axis=0)
        nan_mask = np.isnan(X)
        X_clean = X.copy()
        for j in range(X.shape[1]):
            X_clean[nan_mask[:, j], j] = col_means[j]

        dbscan = DBSCAN(
            eps=eps,
            min_samples=min_samples,
            metric=metric,
        )
        labels = dbscan.fit_predict(X_clean)

        # DBSCAN returns -1 for noise, and 0, 1, ... for clusters.
        # We need to map these to string labels like "C1", "C2", ..., and "Noise"
        unique_labels = sorted(set(labels))
        cluster_values = []
        for val in unique_labels:
            if val == -1:
                cluster_values.append("Noise")
            else:
                cluster_values.append(f"C{val + 1}")

        cluster_var = DiscreteVariable("Cluster", values=cluster_values)

        # Map integer labels to the discrete variable value indices
        val_to_idx = {val: idx for idx, val in enumerate(unique_labels)}
        mapped_labels = np.array([val_to_idx[l] for l in labels])

        new_domain = Domain(
            self.data.domain.attributes,
            self.data.domain.class_vars,
            list(self.data.domain.metas) + [cluster_var],
        )

        # Build metas array
        cluster_col = mapped_labels.reshape(-1, 1).astype(float)
        if self.data.metas.size:
            new_metas = np.hstack([self.data.metas, cluster_col])
        else:
            new_metas = cluster_col

        annotated = Table.from_numpy(
            new_domain,
            self.data.X,
            self.data.Y if self.data.Y.size else None,
            metas=new_metas,
        )
        self.send("Annotated Data", annotated)
