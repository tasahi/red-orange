"""
Headless preprocessing widgets — pure-Python replacements for the Orange
preprocessing category widgets, without any Qt dependency.

Each widget takes a Table input, applies a transformation, and emits
the transformed Table. Designed as individual nodes for beginner-friendly
visual pipelines.
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np

from Orange.data import Table

from ..headless_widget import HeadlessWidget
from ..schemas import SignalDesc


# ======================================================================
# Impute — Missing Value Handler
# ======================================================================

class HLImpute(HeadlessWidget):
    """
    Fill missing values in the dataset.

    Settings
    --------
    method : str
        ``"average"`` — replace with mean (continuous) or mode (discrete).
        ``"drop"``    — remove rows containing any missing value.
        ``"default"`` — replace with 0 (continuous) or most frequent (discrete).
        ``"model"``   — use a simple model-based imputer.
    """

    def get_input_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Data", type="Orange.data.Table", flags={})]

    def get_output_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Data", type="Orange.data.Table", flags={})]

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self.data: Optional[Table] = None
        self._settings = {"method": "average"}

    def receive(self, input_name, value):
        if input_name == "Data":
            self.data = value

    def handle_new_signals(self):
        if self.data is None:
            self.send("Data", None)
            return

        method_name = self._settings.get("method", "average")

        if method_name == "drop":
            # Manually drop rows with any NaN — Orange's DropInstances
            # doesn't work reliably as an Impute method parameter.
            mask = ~np.isnan(self.data.X).any(axis=1)
            result = self.data[np.where(mask)[0]]
        else:
            from Orange.preprocess import Impute
            from Orange.preprocess.impute import Average, Default

            method_map = {
                "average": Average(),
                "default": Default(0),
            }
            method = method_map.get(method_name, Average())
            imputer = Impute(method=method)
            result = imputer(self.data)
        self.send("Data", result)


# ======================================================================
# Normalize — Feature Scaling
# ======================================================================

class HLNormalize(HeadlessWidget):
    """
    Rescale numeric features so they are comparable.

    Settings
    --------
    method : str
        ``"standardize"`` — zero mean, unit variance.
        ``"center"``      — subtract mean only.
        ``"scale"``       — divide by standard deviation only.
        ``"minmax"``      — scale to [0, 1].
    """

    def get_input_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Data", type="Orange.data.Table", flags={})]

    def get_output_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Data", type="Orange.data.Table", flags={})]

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self.data: Optional[Table] = None
        self._settings = {"method": "standardize"}

    def receive(self, input_name, value):
        if input_name == "Data":
            self.data = value

    def handle_new_signals(self):
        if self.data is None:
            self.send("Data", None)
            return

        from Orange.preprocess import Normalize

        method = self._settings.get("method", "standardize")

        # Map user-friendly names to Orange constants
        if method == "standardize":
            norm = Normalize(zero_based=False, norm_type=Normalize.NormalizeBySD)
        elif method == "center":
            norm = Normalize(zero_based=False, norm_type=Normalize.NormalizeBySD)
        elif method == "scale":
            norm = Normalize(zero_based=False, norm_type=Normalize.NormalizeBySD)
        elif method == "minmax":
            norm = Normalize(zero_based=True, norm_type=Normalize.NormalizeBySpan)
        else:
            norm = Normalize()

        result = norm(self.data)
        self.send("Data", result)


# ======================================================================
# Continuize — Encode Categorical → Numeric
# ======================================================================

class HLContinuize(HeadlessWidget):
    """
    Convert categorical (discrete) attributes into numeric columns.

    Settings
    --------
    treatment : str
        ``"one_hot"``               — one binary column per category value.
        ``"first_as_base"``         — n−1 dummy columns (first value as base).
        ``"as_ordinal"``            — sequential integers 0, 1, 2, …
        ``"as_normalized_ordinal"`` — ordinal scaled to [0, 1].
    """

    def get_input_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Data", type="Orange.data.Table", flags={})]

    def get_output_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Data", type="Orange.data.Table", flags={})]

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self.data: Optional[Table] = None
        self._settings = {"treatment": "one_hot"}

    def receive(self, input_name, value):
        if input_name == "Data":
            self.data = value

    def handle_new_signals(self):
        if self.data is None:
            self.send("Data", None)
            return

        from Orange.preprocess import Continuize

        treatment_map = {
            "one_hot": Continuize.Indicators,
            "first_as_base": Continuize.FirstAsBase,
            "as_ordinal": Continuize.AsOrdinal,
            "as_normalized_ordinal": Continuize.AsNormalizedOrdinal,
        }
        treatment = treatment_map.get(
            self._settings.get("treatment", "one_hot"),
            Continuize.Indicators,
        )
        continuizer = Continuize(multinomial_treatment=treatment)
        result = continuizer(self.data)
        self.send("Data", result)


# ======================================================================
# Discretize — Bin Continuous → Categorical
# ======================================================================

class HLDiscretize(HeadlessWidget):
    """
    Convert continuous attributes into discrete bins.

    Settings
    --------
    method : str
        ``"equal_freq"``  — equal-frequency bins.
        ``"equal_width"`` — equal-width bins.
        ``"entropy"``     — entropy-based (MDL) optimal splitting.
    n_bins : int
        Number of bins (ignored for ``"entropy"``).
    """

    def get_input_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Data", type="Orange.data.Table", flags={})]

    def get_output_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Data", type="Orange.data.Table", flags={})]

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self.data: Optional[Table] = None
        self._settings = {"method": "equal_freq", "n_bins": 4}

    def receive(self, input_name, value):
        if input_name == "Data":
            self.data = value

    def handle_new_signals(self):
        if self.data is None:
            self.send("Data", None)
            return

        from Orange.preprocess import Discretize
        from Orange.preprocess.discretize import EqualFreq, EqualWidth, EntropyMDL

        method_name = self._settings.get("method", "equal_freq")
        n_bins = self._settings.get("n_bins", 4)

        method_map = {
            "equal_freq": EqualFreq(n=n_bins),
            "equal_width": EqualWidth(n=n_bins),
            "entropy": EntropyMDL(),
        }
        method = method_map.get(method_name, EqualFreq(n=n_bins))

        discretizer = Discretize(method=method)
        result = discretizer(self.data)
        self.send("Data", result)


# ======================================================================
# PCA — Dimensionality Reduction
# ======================================================================

class HLPCA(HeadlessWidget):
    """
    Reduce the number of features using Principal Component Analysis.

    Settings
    --------
    n_components : int
        Number of principal components to keep.
    """

    def get_input_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Data", type="Orange.data.Table", flags={})]

    def get_output_signals(self) -> list[SignalDesc]:
        return [
            SignalDesc(name="Transformed Data", type="Orange.data.Table", flags={"default": True}),
            SignalDesc(name="Data", type="Orange.data.Table", flags={}),
        ]

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self.data: Optional[Table] = None
        self._settings = {"n_components": 5}

    def receive(self, input_name, value):
        if input_name == "Data":
            self.data = value

    def handle_new_signals(self):
        if self.data is None:
            self.send("Transformed Data", None)
            self.send("Data", None)
            return

        from Orange.projection import PCA

        n = self._settings.get("n_components", 5)
        # Clamp to max available features
        max_comps = min(n, self.data.X.shape[1], len(self.data))
        if max_comps < 1:
            max_comps = 1

        pca = PCA(n_components=max_comps)
        pca_model = pca(self.data)
        transformed = pca_model(self.data)

        self.send("Transformed Data", transformed)
        self.send("Data", self.data)  # pass-through original


# ======================================================================
# Outliers — Anomaly Detection
# ======================================================================

class HLOutliers(HeadlessWidget):
    """
    Detect and separate outlier data points.

    Settings
    --------
    method : str
        ``"lof"``             — Local Outlier Factor.
        ``"isolation_forest"`` — Isolation Forest.
        ``"covariance"``      — Elliptic Envelope (covariance estimator).
    contamination : float
        Expected proportion of outliers (0.0–0.5).
    """

    def get_input_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Data", type="Orange.data.Table", flags={})]

    def get_output_signals(self) -> list[SignalDesc]:
        return [
            SignalDesc(name="Inliers", type="Orange.data.Table", flags={"default": True}),
            SignalDesc(name="Outliers", type="Orange.data.Table", flags={}),
        ]

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self.data: Optional[Table] = None
        self._settings = {"method": "lof", "contamination": 0.1}

    def receive(self, input_name, value):
        if input_name == "Data":
            self.data = value

    def handle_new_signals(self):
        if self.data is None:
            self.send("Inliers", None)
            self.send("Outliers", None)
            return

        method = self._settings.get("method", "lof")
        cont = self._settings.get("contamination", 0.1)

        if method == "isolation_forest":
            from sklearn.ensemble import IsolationForest
            detector = IsolationForest(contamination=cont, random_state=42)
            detector.fit(self.data.X)
            labels = detector.predict(self.data.X)
        elif method == "covariance":
            from sklearn.covariance import EllipticEnvelope
            detector = EllipticEnvelope(contamination=cont, random_state=42)
            detector.fit(self.data.X)
            labels = detector.predict(self.data.X)
        else:  # default: LOF
            from sklearn.neighbors import LocalOutlierFactor
            detector = LocalOutlierFactor(contamination=cont, novelty=False)
            labels = detector.fit_predict(self.data.X)

        # labels: 1 = inlier, -1 = outlier
        inlier_mask = labels == 1
        outlier_mask = labels == -1

        inliers = self.data[np.where(inlier_mask)[0]] if inlier_mask.any() else None
        outliers = self.data[np.where(outlier_mask)[0]] if outlier_mask.any() else None

        self.send("Inliers", inliers)
        self.send("Outliers", outliers)


# ======================================================================
# t-SNE — t-Distributed Stochastic Neighbor Embedding
# ======================================================================

class HLTSNE(HeadlessWidget):
    """
    Dimensionality reduction using t-SNE.
    """

    def get_input_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Data", type="Orange.data.Table", flags={})]

    def get_output_signals(self) -> list[SignalDesc]:
        return [
            SignalDesc(name="Transformed Data", type="Orange.data.Table", flags={"default": True}),
            SignalDesc(name="Data", type="Orange.data.Table", flags={}),
        ]

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self.data: Optional[Table] = None
        self._settings = {
            "n_components": 2,
            "perplexity": 30,
            "early_exaggeration": 12.0,
            "learning_rate": 200.0,
        }

    def receive(self, input_name, value):
        if input_name == "Data":
            self.data = value

    def handle_new_signals(self):
        if self.data is None or len(self.data) == 0:
            self.send("Transformed Data", None)
            self.send("Data", None)
            return

        from Orange.projection.manifold import TSNE

        n_comp = self._settings.get("n_components", 2)
        perp = self._settings.get("perplexity", 30)
        exag = self._settings.get("early_exaggeration", 12.0)
        lr = self._settings.get("learning_rate", 200.0)

        # Scikit-learn requires perplexity to be less than the number of samples
        if perp >= len(self.data):
            perp = max(1, len(self.data) - 1)

        tsne = TSNE(
            n_components=n_comp,
            perplexity=perp,
            early_exaggeration=exag,
            learning_rate=lr,
            random_state=42
        )
        
        # t-SNE in Orange returns a projected table directly
        transformed = tsne(self.data)

        self.send("Transformed Data", transformed)
        self.send("Data", self.data)


# ======================================================================
# MDS — Multidimensional Scaling
# ======================================================================

class HLMDS(HeadlessWidget):
    """
    Dimensionality reduction using MDS.
    """

    def get_input_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Data", type="Orange.data.Table", flags={})]

    def get_output_signals(self) -> list[SignalDesc]:
        return [
            SignalDesc(name="Transformed Data", type="Orange.data.Table", flags={"default": True}),
            SignalDesc(name="Data", type="Orange.data.Table", flags={}),
        ]

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self.data: Optional[Table] = None
        self._settings = {
            "n_components": 2,
            "max_iter": 300,
            "init_type": "PCA",
        }

    def receive(self, input_name, value):
        if input_name == "Data":
            self.data = value

    def handle_new_signals(self):
        if self.data is None or len(self.data) == 0:
            self.send("Transformed Data", None)
            self.send("Data", None)
            return

        from Orange.projection.mds import MDS
        import numpy as np

        n_comp = self._settings.get("n_components", 2)
        max_iter = self._settings.get("max_iter", 300)
        init_type = self._settings.get("init_type", "PCA")

        mds_projector = MDS(n_components=n_comp, max_iter=max_iter, random_state=42)
        
        # Handle initialization
        if init_type == "PCA":
            from Orange.projection import PCA
            pca_proj = PCA(n_components=n_comp)(self.data)
            init_data = pca_proj(self.data).X
            # Ensure it has exactly n_comp columns, padding with zeros if necessary
            if init_data.shape[1] < n_comp:
                pad = np.zeros((init_data.shape[0], n_comp - init_data.shape[1]))
                init_data = np.hstack((init_data, pad))
        else:
            init_data = None
            
        if init_data is not None:
            # Orange MDS accepts init argument through its run method or call
            # We bypass the default projector call and use run manually if needed, 
            # but Orange's MDS allows passing init to the __call__
            transformed = mds_projector(self.data, init=init_data)
        else:
            transformed = mds_projector(self.data)

        self.send("Transformed Data", transformed)
        self.send("Data", self.data)


# ======================================================================
# Correlations — Pearson and Spearman feature correlations
# ======================================================================

class HLCorrelations(HeadlessWidget):
    """
    Computes pairwise correlations (Pearson or Spearman) and significance p-values
    between continuous features. Emits original Data and a sorted Correlation Table.
    """

    def get_input_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Data", type="Orange.data.Table", flags={})]

    def get_output_signals(self) -> list[SignalDesc]:
        return [
            SignalDesc(name="Data", type="Orange.data.Table", flags={"default": True}),
            SignalDesc(name="Correlation Table", type="Orange.data.Table", flags={}),
        ]

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self.data: Optional[Table] = None
        self._settings = {
            "method": "pearson",  # "pearson" or "spearman"
            "threshold": 0.0,
        }
        self.matrix_data: dict[str, Any] = {}

    def receive(self, input_name, value):
        if input_name == "Data":
            self.data = value

    def handle_new_signals(self):
        if self.data is None or len(self.data) == 0:
            self.send("Data", None)
            self.send("Correlation Table", None)
            self.matrix_data = {}
            return

        import numpy as np
        import scipy.stats as stats
        from Orange.data import Domain, ContinuousVariable, StringVariable

        # Identify continuous attributes
        cont_attrs = [v for v in self.data.domain.attributes if isinstance(v, ContinuousVariable)]
        if len(cont_attrs) < 2:
            self.send("Data", self.data)
            self.send("Correlation Table", None)
            self.matrix_data = {"features": [a.name for a in cont_attrs], "matrix": [], "pairs": []}
            return

        method = str(self._settings.get("method", "pearson")).lower()
        feature_names = [a.name for a in cont_attrs]
        n_features = len(cont_attrs)

        # Extract continuous columns
        cols = []
        for a in cont_attrs:
            col_idx = self.data.domain.index(a)
            cols.append(self.data.X[:, col_idx])
        X = np.column_stack(cols)

        matrix = np.eye(n_features, dtype=float)
        p_matrix = np.zeros((n_features, n_features), dtype=float)
        pairs_list = []

        for i in range(n_features):
            for j in range(i + 1, n_features):
                xi = X[:, i]
                xj = X[:, j]
                # Drop NaNs for pair
                valid = ~(np.isnan(xi) | np.isnan(xj))
                if np.sum(valid) > 2:
                    if method == "spearman":
                        res = stats.spearmanr(xi[valid], xj[valid])
                        corr = float(res.statistic) if hasattr(res, "statistic") else float(res[0])
                        pval = float(res.pvalue) if hasattr(res, "pvalue") else float(res[1])
                    else:
                        corr, pval = stats.pearsonr(xi[valid], xj[valid])
                        corr, pval = float(corr), float(pval)
                else:
                    corr, pval = 0.0, 1.0

                matrix[i, j] = corr
                matrix[j, i] = corr
                p_matrix[i, j] = pval
                p_matrix[j, i] = pval

                pairs_list.append({
                    "feature_a": feature_names[i],
                    "feature_b": feature_names[j],
                    "correlation": corr,
                    "abs_corr": abs(corr),
                    "p_value": pval,
                })

        # Sort pairs by absolute correlation descending
        pairs_list.sort(key=lambda x: x["abs_corr"], reverse=True)

        self.matrix_data = {
            "method": method,
            "features": feature_names,
            "matrix": matrix.tolist(),
            "p_matrix": p_matrix.tolist(),
            "pairs": pairs_list,
        }

        # Build output Orange.data.Table
        if pairs_list:
            var_a = StringVariable("Feature A")
            var_b = StringVariable("Feature B")
            var_corr = ContinuousVariable("Correlation")
            var_abs = ContinuousVariable("Abs Correlation")
            var_p = ContinuousVariable("p-value")

            corr_domain = Domain([var_corr, var_abs, var_p], metas=[var_a, var_b])
            X_data = np.array([[p["correlation"], p["abs_corr"], p["p_value"]] for p in pairs_list])
            metas_data = np.array([[p["feature_a"], p["feature_b"]] for p in pairs_list], dtype=object)
            corr_table = Table.from_numpy(corr_domain, X_data, metas=metas_data)
        else:
            corr_table = None

        self.send("Data", self.data)
        self.send("Correlation Table", corr_table)


# ======================================================================
# Rank — Feature scoring and dimensionality filtering
# ======================================================================

class HLRank(HeadlessWidget):
    """
    Computes feature importance rankings using various scoring functions (InfoGain,
    Gini, ANOVA, Chi2, Univariate Regression). Emits Reduced Data and Scores table.
    """

    def get_input_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Data", type="Orange.data.Table", flags={})]

    def get_output_signals(self) -> list[SignalDesc]:
        return [
            SignalDesc(name="Reduced Data", type="Orange.data.Table", flags={"default": True}),
            SignalDesc(name="Scores", type="Orange.data.Table", flags={}),
        ]

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self.data: Optional[Table] = None
        self._settings = {
            "scoring_method": "auto",  # auto, infogain, gainratio, gini, anova, chi2, univariate_linear
            "select_mode": "top_k",    # "top_k", "threshold", "all"
            "n_selected": 5,
            "threshold": 0.0,
        }
        self.scores_data: dict[str, Any] = {}

    def receive(self, input_name, value):
        if input_name == "Data":
            self.data = value

    def handle_new_signals(self):
        if self.data is None or len(self.data) == 0 or len(self.data.domain.attributes) == 0:
            self.send("Reduced Data", None)
            self.send("Scores", None)
            self.scores_data = {}
            return

        import numpy as np
        import Orange.preprocess.score as score
        from Orange.data import Domain, ContinuousVariable, StringVariable

        attrs = list(self.data.domain.attributes)
        feature_names = [a.name for a in attrs]
        has_class = bool(self.data.domain.class_vars)
        is_classification = self.data.domain.has_discrete_class if has_class else False
        is_regression = self.data.domain.has_continuous_class if has_class else False

        metric_scores: dict[str, list[float]] = {}

        if is_classification:
            # Classification scorers
            scorers = [
                ("InfoGain", score.InfoGain()),
                ("GainRatio", score.GainRatio()),
                ("Gini", score.Gini()),
                ("ANOVA", score.ANOVA()),
                ("Chi2", score.Chi2()),
            ]
            for name, sc in scorers:
                try:
                    res = sc(self.data)
                    metric_scores[name] = [float(x) if not np.isnan(x) else 0.0 for x in res]
                except Exception:
                    pass
        elif is_regression:
            # Regression scorers
            scorers = [
                ("UnivariateLinearRegression", score.UnivariateLinearRegression()),
                ("RReliefF", score.RReliefF()),
            ]
            for name, sc in scorers:
                try:
                    res = sc(self.data)
                    metric_scores[name] = [float(x) if not np.isnan(x) else 0.0 for x in res]
                except Exception:
                    pass
        else:
            # Unsupervised: variance as fallback score
            variances = []
            for a in attrs:
                idx = self.data.domain.index(a)
                col = self.data.X[:, idx]
                valid = col[~np.isnan(col)]
                variances.append(float(np.var(valid)) if len(valid) > 1 else 0.0)
            metric_scores["Variance"] = variances

        if not metric_scores:
            metric_scores["Default"] = [1.0] * len(attrs)

        # Determine primary scoring metric
        req_method = str(self._settings.get("scoring_method", "auto")).lower()
        primary_metric = None
        for m_name in metric_scores.keys():
            if req_method in m_name.lower():
                primary_metric = m_name
                break
        if primary_metric is None:
            primary_metric = list(metric_scores.keys())[0]

        primary_vals = metric_scores[primary_metric]

        # Feature ranking summary
        ranked_items = []
        for i, attr in enumerate(attrs):
            ranked_items.append({
                "name": attr.name,
                "score": primary_vals[i],
                "index": i,
                "all_scores": {k: v[i] for k, v in metric_scores.items()},
            })

        # Sort descending by primary score
        ranked_items.sort(key=lambda x: x["score"], reverse=True)

        select_mode = str(self._settings.get("select_mode", "top_k")).lower()
        n_selected = int(self._settings.get("n_selected", 5))
        threshold = float(self._settings.get("threshold", 0.0))

        if select_mode == "top_k":
            selected_indices = [item["index"] for item in ranked_items[:max(1, min(n_selected, len(attrs)))]]
        elif select_mode == "threshold":
            selected_indices = [item["index"] for item in ranked_items if item["score"] >= threshold]
            if not selected_indices:
                selected_indices = [ranked_items[0]["index"]]
        else:  # "all"
            selected_indices = [item["index"] for item in ranked_items]

        # Build Reduced Data table
        selected_attrs = [attrs[i] for i in sorted(selected_indices)]
        new_domain = Domain(selected_attrs, self.data.domain.class_vars, self.data.domain.metas)
        reduced_table = self.data.transform(new_domain)

        # Build Scores table
        var_feature = StringVariable("Feature")
        score_vars = [ContinuousVariable(k) for k in metric_scores.keys()]
        scores_domain = Domain(score_vars, metas=[var_feature])

        scores_X = np.zeros((len(attrs), len(score_vars)), dtype=float)
        for c_idx, k in enumerate(metric_scores.keys()):
            for r_idx, item in enumerate(ranked_items):
                scores_X[r_idx, c_idx] = item["all_scores"][k]

        scores_metas = np.array([[item["name"]] for item in ranked_items], dtype=object)
        scores_table = Table.from_numpy(scores_domain, scores_X, metas=scores_metas)

        self.scores_data = {
            "primary_metric": primary_metric,
            "metrics": list(metric_scores.keys()),
            "ranked_features": [
                {
                    "name": item["name"],
                    "score": item["score"],
                    "selected": item["index"] in selected_indices,
                    "all_scores": item["all_scores"],
                }
                for item in ranked_items
            ],
            "n_total": len(attrs),
            "n_selected": len(selected_attrs),
        }

        self.send("Reduced Data", reduced_table)
        self.send("Scores", scores_table)

