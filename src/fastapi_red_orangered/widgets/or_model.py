"""
Headless model (learner) widgets — pure-Python replacements for the
Orange model category widgets, without any Qt dependency.

Each widget follows the ``OWBaseLearner`` pattern:
  * Always emits a ``Learner`` (configured but unfitted algorithm).
  * Emits a ``Model`` only when data is connected — calls
    ``learner(data)`` internally.
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np

from Orange.data import (
    Table,
    Domain,
    ContinuousVariable,
    StringVariable,
)
from Orange.base import Learner, Model
from Orange.preprocess.preprocess import Preprocess

from ..headless_widget import HeadlessWidget
from ..schemas import SignalDesc


# ======================================================================
# Base learner widget
# ======================================================================

class _HLBaseLearner(HeadlessWidget):
    """
    Shared base for all headless learner widgets, mirroring the
    ``OWBaseLearner`` pattern.
    """

    LEARNER_CLS: type[Learner] | None = None

    def get_input_signals(self) -> list[SignalDesc]:
        return [
            SignalDesc(name="Data", type="Orange.data.Table", flags={}),
            SignalDesc(name="Preprocessor", type="Orange.preprocess.Preprocess", flags={}),
        ]

    def get_output_signals(self) -> list[SignalDesc]:
        return [
            SignalDesc(name="Learner", type="Orange.base.Learner", flags={}),
            SignalDesc(name="Model", type="Orange.base.Model", flags={}),
        ]

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self.data: Optional[Table] = None
        self.preprocessors: Optional[Preprocess] = None
        self.learner: Optional[Learner] = None
        self.model: Optional[Model] = None
        self._settings: dict[str, Any] = {"learner_name": ""}

    def receive(self, input_name: str, value: Any) -> None:
        if input_name == "Data":
            self.data = value
        elif input_name == "Preprocessor":
            self.preprocessors = value

    def handle_new_signals(self) -> None:
        self.learner = self.create_learner()
        if self.learner is not None:
            name = self._settings.get("learner_name") or type(self).__name__
            self.learner.name = name
        self.send("Learner", self.learner)

        self.model = None
        if self.data is not None and self.learner is not None:
            if self._data_is_valid():
                self.model = self.learner(self.data)
                self.model.name = self.learner.name
                self._log_run()
        self.send("Model", self.model)

    def _log_run(self) -> None:
        """Auto-log the training run to the MLflow-compatible tracker."""
        from ..tracker import log_training_run
        import logging
        _log = logging.getLogger(__name__)

        try:
            # Collect training-time metrics via quick evaluation
            metrics = self._compute_quick_metrics()

            # Filter settings to only include learner-relevant params
            params = {
                k: v for k, v in self._settings.items()
                if k != "learner_name" and v is not None
            }

            log_training_run(
                model_type=type(self).__name__,
                model_name=self.learner.name if self.learner else "unknown",
                params=params,
                metrics=metrics,
                model_obj=self.model,
                data_rows=len(self.data) if self.data else 0,
                data_cols=self.data.X.shape[1] if self.data is not None else 0,
                node_id=self.node_id,
            )
        except Exception as exc:
            _log.warning("Failed to log training run: %s", exc)

    def _compute_quick_metrics(self) -> dict[str, float]:
        """Compute a quick set of evaluation metrics on the training data."""
        if self.data is None or self.model is None:
            return {}

        from Orange.base import Model as OrangeModel
        import numpy as np

        try:
            is_classification = self.data.domain.has_discrete_class

            if is_classification:
                predictions = self.model(self.data, OrangeModel.Value)
                actual = self.data.Y
                correct = np.sum(predictions == actual)
                ca = correct / len(actual) if len(actual) > 0 else 0.0
                return {"train_CA": round(ca, 4)}
            else:
                predictions = self.model(self.data, OrangeModel.Value)
                actual = self.data.Y
                ss_res = np.sum((actual - predictions) ** 2)
                ss_tot = np.sum((actual - np.mean(actual)) ** 2)
                r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
                rmse = np.sqrt(np.mean((actual - predictions) ** 2))
                return {
                    "train_RMSE": round(rmse, 4),
                    "train_R2": round(r2, 4),
                }
        except Exception:
            return {}

    def create_learner(self) -> Learner | None:
        if self.LEARNER_CLS is None:
            return None
        return self.LEARNER_CLS(preprocessors=self.preprocessors)

    def _data_is_valid(self) -> bool:
        if self.data is None or len(self.data) == 0:
            return False
        if self.data.domain.class_var is None:
            return False
        if self.data.X.size == 0:
            return False
        from Orange.statistics.util import unique
        if len(unique(self.data.Y)) < 2:
            return False
        return True


# ======================================================================
# Logistic Regression
# ======================================================================

class HLLogisticRegression(_HLBaseLearner):
    """
    Headless Logistic Regression learner.

    Core logic from ``Orange.widgets.model.owlogisticregression``.
    """

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self._settings.update({
            "penalty": "l2",
            "C": 1.0,
            "class_weight": False,
            "max_iter": 10000,
        })

    def get_output_signals(self) -> list[SignalDesc]:
        base = super().get_output_signals()
        base.append(
            SignalDesc(name="Coefficients", type="Orange.data.Table", flags={"explicit": True}),
        )
        return base

    def create_learner(self):
        from Orange.classification.logistic_regression import LogisticRegressionLearner

        s = self._settings
        penalty = s.get("penalty", "l2")
        C = s.get("C", 1.0)
        class_weight = "balanced" if s.get("class_weight") else None

        return LogisticRegressionLearner(
            penalty=penalty,
            C=C,
            class_weight=class_weight,
            max_iter=s.get("max_iter", 10000),
            preprocessors=self.preprocessors,
        )

    def handle_new_signals(self) -> None:
        super().handle_new_signals()

        # Emit coefficients table
        coef_table = None
        if self.model is not None:
            coef_table = _create_coef_table(self.model)
        self.send("Coefficients", coef_table)


def _create_coef_table(classifier) -> Table:
    """Reproduce ``owlogisticregression.create_coef_table``."""
    i = classifier.intercept
    c = classifier.coefficients
    if c.shape[0] > 2:
        values = [
            classifier.domain.class_var.values[int(v)]
            for v in classifier.used_vals[0]
        ]
    else:
        values = [
            classifier.domain.class_var.values[int(classifier.used_vals[0][1])]
        ]
    domain = Domain(
        [ContinuousVariable(v) for v in values],
        metas=[StringVariable("name")],
    )
    coefs = np.vstack((i.reshape(1, len(i)), c.T))
    names = [["intercept"]] + [[attr.name] for attr in classifier.domain.attributes]
    names = np.array(names, dtype=object)
    coef_table = Table.from_numpy(domain, X=coefs, metas=names)
    coef_table.name = "coefficients"
    return coef_table


# ======================================================================
# Random Forest
# ======================================================================

class HLRandomForest(_HLBaseLearner):
    """
    Headless Random Forest learner.

    Core logic from ``Orange.widgets.model.owrandomforest``.
    """

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self._settings.update({
            "n_estimators": 10,
            "max_depth": None,
            "max_features": 0.5,
            "min_samples_split": 5,
        })

    def create_learner(self):
        from Orange.classification.random_forest import RandomForestLearner

        s = self._settings
        return RandomForestLearner(
            n_estimators=s.get("n_estimators", 10),
            max_depth=s.get("max_depth"),
            max_features=s.get("max_features", 0.5),
            min_samples_split=s.get("min_samples_split", 5),
            preprocessors=self.preprocessors,
        )


# ======================================================================
# Decision Tree
# ======================================================================

class HLTree(_HLBaseLearner):
    """
    Headless Decision Tree learner.

    Core logic from ``Orange.widgets.model.owtree``.
    """

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self._settings.update({
            "max_depth": 5,
            "min_samples_split": 5,
            "min_samples_leaf": 2,
        })

    def create_learner(self):
        from Orange.classification.tree import TreeLearner

        s = self._settings
        return TreeLearner(
            max_depth=s.get("max_depth", 5),
            min_samples_split=s.get("min_samples_split", 5),
            min_samples_leaf=s.get("min_samples_leaf", 2),
            preprocessors=self.preprocessors,
        )


# ======================================================================
# k-Nearest Neighbors
# ======================================================================

class HLkNN(_HLBaseLearner):
    """
    Headless k-Nearest Neighbors learner.

    Core logic from ``Orange.widgets.model.owknn``.
    """

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self._settings.update({
            "n_neighbors": 5,
            "metric": "euclidean",
            "weight_type": "uniform",
        })

    def create_learner(self):
        from Orange.classification.knn import KNNLearner

        s = self._settings
        return KNNLearner(
            n_neighbors=s.get("n_neighbors", 5),
            metric=s.get("metric", "euclidean"),
            weights=s.get("weight_type", "uniform"),
            preprocessors=self.preprocessors,
        )


# ======================================================================
# Naive Bayes
# ======================================================================

class HLNaiveBayes(_HLBaseLearner):
    """
    Headless Naive Bayes learner.

    Core logic from ``Orange.widgets.model.ownaivebayes``.
    """

    def create_learner(self):
        from Orange.classification.naive_bayes import NaiveBayesLearner

        return NaiveBayesLearner(
            preprocessors=self.preprocessors,
        )


# ======================================================================
# Support Vector Machine (SVM)
# ======================================================================

class HLSVM(_HLBaseLearner):
    """
    Headless SVM learner.

    Core logic from ``Orange.widgets.model.owsvm``.
    """

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self._settings.update({
            "svm_type": "C-SVC",
            "C": 1.0,
            "kernel": "rbf",
            "gamma": 0.0,       # 0 means 'auto' (1/n_features)
            "degree": 3,
            "max_iter": 100,
        })

    def create_learner(self):
        from Orange.classification.svm import SVMLearner

        s = self._settings
        kernel_map = {
            "linear": 0,
            "poly": 1,
            "rbf": 2,
            "sigmoid": 3,
        }
        return SVMLearner(
            C=s.get("C", 1.0),
            kernel_type=kernel_map.get(s.get("kernel", "rbf"), 2),
            gamma=s.get("gamma", 0.0) or 0.0,
            degree=s.get("degree", 3),
            max_iter=s.get("max_iter", 100),
            preprocessors=self.preprocessors,
        )


# ======================================================================
# Neural Network
# ======================================================================

class HLNeuralNetwork(_HLBaseLearner):
    """
    Headless Neural Network learner.
    """

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self._settings.update({
            "hidden_layer_sizes": "100",
            "activation": "relu",
            "solver": "adam",
            "alpha": 0.0001,
            "max_iter": 200,
        })

    def create_learner(self):
        from Orange.modelling.neuralnetwork import NNLearner
        
        s = self._settings
        
        # Parse hidden layer sizes
        hidden_layer_str = s.get("hidden_layer_sizes", "100")
        try:
            hidden_layer_sizes = tuple(int(x.strip()) for x in hidden_layer_str.split(",") if x.strip())
        except ValueError:
            hidden_layer_sizes = (100,)
            
        if not hidden_layer_sizes:
            hidden_layer_sizes = (100,)

        return NNLearner(
            hidden_layer_sizes=hidden_layer_sizes,
            activation=s.get("activation", "relu"),
            solver=s.get("solver", "adam"),
            alpha=s.get("alpha", 0.0001),
            max_iter=s.get("max_iter", 200),
            preprocessors=self.preprocessors,
        )


# ======================================================================
# AdaBoost
# ======================================================================

class HLAdaBoost(_HLBaseLearner):
    """
    Headless AdaBoost learner.
    """

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self._settings.update({
            "n_estimators": 50,
            "learning_rate": 1.0,
        })

    def create_learner(self):
        # Orange uses SklAdaBoostLearner for classification/regression
        # Or Orange.modelling.AdaBoostLearner
        from Orange.modelling.adaboost import AdaBoostLearner

        s = self._settings
        return AdaBoostLearner(
            n_estimators=s.get("n_estimators", 50),
            learning_rate=s.get("learning_rate", 1.0),
            preprocessors=self.preprocessors,
        )


# ======================================================================
# Stochastic Gradient Descent (SGD)
# ======================================================================

class HLSGD(_HLBaseLearner):
    """
    Headless Stochastic Gradient Descent learner.
    """

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self._settings.update({
            "loss": "hinge",
            "penalty": "l2",
            "alpha": 0.0001,
            "max_iter": 1000,
        })

    def create_learner(self):
        from Orange.modelling.sgd import SGDLearner

        s = self._settings
        return SGDLearner(
            loss=s.get("loss", "hinge"),
            penalty=s.get("penalty", "l2"),
            alpha=s.get("alpha", 0.0001),
            max_iter=s.get("max_iter", 1000),
            preprocessors=self.preprocessors,
        )


# ======================================================================
# Constant (Dummy)
# ======================================================================

class HLConstant(_HLBaseLearner):
    """
    Headless Constant (Dummy) learner.
    Predicts the majority class (classification) or mean (regression).
    """

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)

    def create_learner(self):
        from Orange.modelling.constant import ConstantLearner

        return ConstantLearner(
            preprocessors=self.preprocessors,
        )


# ======================================================================
# Linear Regression (OLS, Ridge, Lasso, Elastic Net)
# ======================================================================

class HLLinearRegression(_HLBaseLearner):
    """
    Headless Linear Regression learner.
    Supports Ordinary Least Squares, Ridge (L2), Lasso (L1), and Elastic Net.
    """

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self._settings.update({
            "regularization": "none",  # "none", "ridge", "lasso", "elastic_net"
            "alpha": 1.0,
            "l1_ratio": 0.5,
            "fit_intercept": True,
        })

    def create_learner(self):
        from Orange.regression import (
            LinearRegressionLearner,
            RidgeRegressionLearner,
            LassoRegressionLearner,
            ElasticNetLearner,
        )

        s = self._settings
        reg = str(s.get("regularization", "none")).lower()
        fit_intercept = bool(s.get("fit_intercept", True))
        alpha = float(s.get("alpha", 1.0))
        l1_ratio = float(s.get("l1_ratio", 0.5))

        if reg == "ridge":
            return RidgeRegressionLearner(
                alpha=alpha,
                fit_intercept=fit_intercept,
                preprocessors=self.preprocessors,
            )
        elif reg == "lasso":
            return LassoRegressionLearner(
                alpha=alpha,
                fit_intercept=fit_intercept,
                preprocessors=self.preprocessors,
            )
        elif reg == "elastic_net":
            return ElasticNetLearner(
                alpha=alpha,
                l1_ratio=l1_ratio,
                fit_intercept=fit_intercept,
                preprocessors=self.preprocessors,
            )
        else:
            return LinearRegressionLearner(
                fit_intercept=fit_intercept,
                preprocessors=self.preprocessors,
            )



