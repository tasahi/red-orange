"""
Headless evaluation widgets — pure-Python replacements for the Orange
evaluate category widgets, without any Qt dependency.
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np

from Orange.base import Learner, Model
from Orange.data import Table, Domain
from Orange.data.table import DomainTransformationError
from Orange.evaluation import Results
import Orange.evaluation

from ..headless_widget import HeadlessWidget
from ..schemas import SignalDesc


# ======================================================================
# Test & Score
# ======================================================================

class HLTestAndScore(HeadlessWidget):
    """
    Headless version of ``OWTestAndScore``.

    Performs cross-validation (or other resampling) of one or more
    learners on a dataset and emits evaluation results.
    """

    # Resampling constants
    KFold, ShuffleSplit, LeaveOneOut, TestOnTrain, TestOnTest = range(5)

    def get_input_signals(self) -> list[SignalDesc]:
        return [
            SignalDesc(name="Data", type="Orange.data.Table", flags={}),
            SignalDesc(name="Test Data", type="Orange.data.Table", flags={}),
            SignalDesc(name="Learner", type="Orange.base.Learner", flags={"multi": True}),
        ]

    def get_output_signals(self) -> list[SignalDesc]:
        return [
            SignalDesc(name="Predictions", type="Orange.data.Table", flags={}),
            SignalDesc(name="Evaluation Results", type="Orange.evaluation.Results", flags={}),
        ]

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self.data: Optional[Table] = None
        self.test_data: Optional[Table] = None
        self.learners: list[Learner] = []
        self._settings: dict[str, Any] = {
            "resampling": self.KFold,
            "n_folds": 5,
            "n_repeats": 3,
            "sample_size": 75,       # percentage for ShuffleSplit
            "stratified": True,
        }

    def receive(self, input_name: str, value: Any) -> None:
        if input_name == "Data":
            self.data = value
        elif input_name == "Test Data":
            self.test_data = value
        elif input_name == "Learner":
            # Multi-input: value may be a single Learner (append) or None (clear)
            if value is None:
                self.learners.clear()
            elif isinstance(value, list):
                self.learners = list(value)
            else:
                # Append if not already present
                if value not in self.learners:
                    self.learners.append(value)

    def handle_new_signals(self) -> None:
        if self.data is None or not self.learners:
            self.send("Predictions", None)
            self.send("Evaluation Results", None)
            return

        s = self._settings
        resampling = s["resampling"]

        try:
            if resampling == self.KFold:
                results = Orange.evaluation.CrossValidation(
                    self.data,
                    self.learners,
                    k=s.get("n_folds", 5),
                    stratified=s.get("stratified", True),
                )
            elif resampling == self.ShuffleSplit:
                results = Orange.evaluation.ShuffleSplit(
                    self.data,
                    self.learners,
                    n_resamples=s.get("n_repeats", 3),
                    train_size=s.get("sample_size", 75) / 100,
                    stratified=s.get("stratified", True),
                )
            elif resampling == self.LeaveOneOut:
                results = Orange.evaluation.LeaveOneOut(
                    self.data,
                    self.learners,
                )
            elif resampling == self.TestOnTrain:
                results = Orange.evaluation.TestOnTrainingData(
                    self.data,
                    self.learners,
                )
            elif resampling == self.TestOnTest:
                if self.test_data is None:
                    self.send("Predictions", None)
                    self.send("Evaluation Results", None)
                    return
                results = Orange.evaluation.TestOnTestData(
                    self.data,
                    self.test_data,
                    self.learners,
                )
            else:
                self.send("Predictions", None)
                self.send("Evaluation Results", None)
                return

        except Exception:
            self.send("Predictions", None)
            self.send("Evaluation Results", None)
            raise

        self.send("Evaluation Results", results)

        # Build predictions table
        predictions_table = self._build_predictions_table(results)
        self.send("Predictions", predictions_table)

    @staticmethod
    def _build_predictions_table(results: Results) -> Optional[Table]:
        """Create a summary table from evaluation results."""
        if results.data is None:
            return None
        return results.data


# ======================================================================
# Predictions
# ======================================================================

class HLPredictions(HeadlessWidget):
    """
    Headless version of ``OWPredictions``.

    Applies one or more predictors (models) to a dataset and outputs
    the predictions as columns appended to the data.
    """

    def get_input_signals(self) -> list[SignalDesc]:
        return [
            SignalDesc(name="Data", type="Orange.data.Table", flags={}),
            SignalDesc(name="Predictors", type="Orange.base.Model", flags={"multi": True}),
        ]

    def get_output_signals(self) -> list[SignalDesc]:
        return [
            SignalDesc(
                name="Predictions",
                type="Orange.data.Table",
                flags={"default": True},
            ),
            SignalDesc(
                name="Evaluation Results",
                type="Orange.evaluation.Results",
                flags={},
            ),
        ]

    def __init__(self, node_id, orchestrator):
        super().__init__(node_id, orchestrator)
        self.data: Optional[Table] = None
        self.predictors: list[Model] = []

    def receive(self, input_name: str, value: Any) -> None:
        if input_name == "Data":
            self.data = value
        elif input_name == "Predictors":
            if value is None:
                self.predictors.clear()
            elif isinstance(value, list):
                self.predictors = list(value)
            else:
                if value not in self.predictors:
                    self.predictors.append(value)

    def handle_new_signals(self) -> None:
        if self.data is None or not self.predictors:
            self.send("Predictions", None)
            self.send("Evaluation Results", None)
            return

        from Orange.data import ContinuousVariable, DiscreteVariable, StringVariable
        from Orange.data.util import get_unique_names

        all_predictions = []
        all_probabilities = []
        valid_predictors = []

        domain = self.data.domain
        # Strip target to avoid leaking the answer
        classless_domain = Domain(domain.attributes, None, domain.metas)
        classless_data = self.data.transform(classless_domain)

        for predictor in self.predictors:
            try:
                class_var = predictor.domain.class_var
                if class_var and class_var.is_discrete:
                    pred, prob = predictor(classless_data, Model.ValueProbs)
                else:
                    pred = predictor(classless_data, Model.Value)
                    prob = np.zeros((len(pred), 0))
                all_predictions.append(pred)
                all_probabilities.append(prob)
                valid_predictors.append(predictor)
            except (ValueError, DomainTransformationError):
                continue

        if not valid_predictors:
            self.send("Predictions", None)
            self.send("Evaluation Results", None)
            return

        # Build augmented table with prediction columns as metas
        existing_names = [v.name for v in domain.attributes + domain.class_vars + domain.metas]
        new_metas = list(domain.metas)

        for predictor, preds in zip(valid_predictors, all_predictions):
            pred_name = get_unique_names(existing_names, predictor.name)
            existing_names.append(pred_name)
            class_var = predictor.domain.class_var
            if class_var and class_var.is_discrete:
                new_var = DiscreteVariable(pred_name, values=class_var.values)
            elif class_var and class_var.is_continuous:
                new_var = ContinuousVariable(pred_name)
            else:
                new_var = StringVariable(pred_name)
            new_metas.append(new_var)

        new_domain = Domain(domain.attributes, domain.class_vars, new_metas)

        # Build metas array
        old_metas = self.data.metas
        pred_arrays = []
        for preds in all_predictions:
            col = preds.reshape(-1, 1) if preds.ndim == 1 else preds
            pred_arrays.append(col)

        if old_metas.size:
            new_metas_arr = np.hstack([old_metas] + pred_arrays)
        else:
            new_metas_arr = np.hstack(pred_arrays) if pred_arrays else old_metas

        predictions_table = Table.from_numpy(
            new_domain,
            self.data.X,
            self.data.Y,
            metas=new_metas_arr,
        )

        # Build evaluation results
        results = Results()
        results.data = self.data
        results.domain = self.data.domain
        results.row_indices = np.arange(len(self.data))
        results.folds = (Ellipsis,)
        results.actual = self.data.Y
        if all_predictions:
            results.predicted = np.vstack(
                [p.reshape(1, -1) for p in all_predictions]
            )
        if all_probabilities and all_probabilities[0].shape[1] > 0:
            results.probabilities = np.array(all_probabilities)

        self.send("Predictions", predictions_table)
        self.send("Evaluation Results", results)
