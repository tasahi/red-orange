""" Specific node class wrappers for all Orange widgets in FastAPI-Red.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from fastapi_red_orangered.base_node import OrangeBaseNode
from fastapi_red_orangered.widgets import (
    or_data,
    or_model,
    or_preprocess,
    or_unsupervised,
    or_evaluate,
    or_scripting,
    bridge,
    sp_image,
    sp_audio,
)

# ----------------------------------------------------------------------
# 1. Data Nodes
# ----------------------------------------------------------------------

class FileLoaderNode(OrangeBaseNode):
    widget_cls = or_data.HLFileLoader
    input_names = []
    output_names = ["Data"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"file_path": config.get("filePath", "iris")}

    async def start(self) -> None:
        """ As a root source node, automatically execute on startup/deploy. """
        asyncio.create_task(self.on_input({}))


class DataSamplerNode(OrangeBaseNode):
    widget_cls = or_data.HLDataSampler
    input_names = ["Data"]
    output_names = ["Data Sample", "Remaining Data"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        st = config.get("sampleType", "Proportion")
        sampling_type = or_data.HLDataSampler.FixedSize if st == "Fixed" else or_data.HLDataSampler.FixedProportion
        pct = float(config.get("sampleProportion", 70))
        fixed_n = int(config.get("fixedSampleSize", 100))
        use_seed = bool(config.get("replicable", True))
        return {
            "sampling_type": sampling_type,
            "sampleSizePercentage": pct,
            "sampleSizeNumber": fixed_n,
            "stratify": bool(config.get("stratified", False)),
            "use_seed": use_seed,
            "replacement": False,
        }


class SelectColumnsNode(OrangeBaseNode):
    widget_cls = or_data.HLSelectColumns
    input_names = ["Data"]
    output_names = ["Features"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "features": config.get("features", []),
            "target": config.get("target"),
            "metas": config.get("metas", []),
        }


class SelectRowsNode(OrangeBaseNode):
    widget_cls = or_data.HLSelectRows
    input_names = ["Data"]
    output_names = ["Matching Data", "Unmatched Data"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "conditions": config.get("conditions", []),
            "mode": config.get("mode", "all"),
        }


class ViewerNode(OrangeBaseNode):
    widget_cls = or_data.HLViewer
    input_names = ["Data"]
    output_names = []


class MergeDataNode(OrangeBaseNode):
    widget_cls = or_data.HLMergeData
    input_names = ["Data", "Extra Data"]
    output_names = ["Data"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "how": config.get("how", "inner"),
            "left_on": config.get("leftOn"),
            "right_on": config.get("rightOn"),
        }


class ConcatenateNode(OrangeBaseNode):
    widget_cls = or_data.HLConcatenate
    input_names = ["Primary Data", "Additional Data"]
    output_names = ["Data"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "axis": config.get("axis", "rows"),
            "ignore_unknown": bool(config.get("ignoreUnknown", True)),
        }


class SaveDataNode(OrangeBaseNode):
    widget_cls = or_data.HLSaveData
    input_names = ["Data"]
    output_names = []

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "file_path": config.get("filePath", ""),
            "format": config.get("format", "tab"),
        }


class EditDomainNode(OrangeBaseNode):
    widget_cls = or_data.HLEditDomain
    input_names = ["Data"]
    output_names = ["Data"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "renames": config.get("renames", {}),
            "role_changes": config.get("roleChanges", {}),
        }


# ----------------------------------------------------------------------
# 2. Transform & Preprocess Nodes
# ----------------------------------------------------------------------

class ImputeNode(OrangeBaseNode):
    widget_cls = or_preprocess.HLImpute
    input_names = ["Data"]
    output_names = ["Data"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "method": config.get("method", "average"),
            "value": config.get("value"),
        }


class NormalizeNode(OrangeBaseNode):
    widget_cls = or_preprocess.HLNormalize
    input_names = ["Data"]
    output_names = ["Data"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "method": config.get("method", "standardize"),
        }


class ContinuizeNode(OrangeBaseNode):
    widget_cls = or_preprocess.HLContinuize
    input_names = ["Data"]
    output_names = ["Data"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "multinomial_treatment": config.get("multinomialTreatment", "indicators"),
        }


class DiscretizeNode(OrangeBaseNode):
    widget_cls = or_preprocess.HLDiscretize
    input_names = ["Data"]
    output_names = ["Data"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "method": config.get("method", "equal_width"),
            "n_bins": int(config.get("nBins", 3)),
        }


class PCANode(OrangeBaseNode):
    widget_cls = or_preprocess.HLPCA
    input_names = ["Data"]
    output_names = ["Transformed Data"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "n_components": int(config.get("nComponents", 2)),
            "normalize": bool(config.get("normalize", True)),
        }


class OutliersNode(OrangeBaseNode):
    widget_cls = or_preprocess.HLOutliers
    input_names = ["Data"]
    output_names = ["Inliers", "Outliers"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "method": config.get("method", "isolation_forest"),
            "contamination": float(config.get("contamination", 0.05)),
        }


class TSNENode(OrangeBaseNode):
    widget_cls = or_preprocess.HLTSNE
    input_names = ["Data"]
    output_names = ["Transformed Data"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "n_components": int(config.get("nComponents", 2)),
            "perplexity": float(config.get("perplexity", 30.0)),
        }


class MDSNode(OrangeBaseNode):
    widget_cls = or_preprocess.HLMDS
    input_names = ["Data"]
    output_names = ["Transformed Data"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "n_components": int(config.get("nComponents", 2)),
        }


class CorrelationsNode(OrangeBaseNode):
    widget_cls = or_preprocess.HLCorrelations
    input_names = ["Data"]
    output_names = ["Data", "Correlations"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "method": config.get("method", "pearson"),
        }


class RankNode(OrangeBaseNode):
    widget_cls = or_preprocess.HLRank
    input_names = ["Data"]
    output_names = ["Reduced Data", "Scores"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "scoring_method": config.get("scoring_method") or config.get("scorer", "auto"),
            "select_mode": config.get("select_mode") or config.get("selectionMode", "top_k"),
            "n_selected": int(config.get("n_selected") or config.get("topK", 5)),
            "threshold": float(config.get("threshold", 0.0)),
        }


# ----------------------------------------------------------------------
# 3. Model Nodes
# ----------------------------------------------------------------------

class LogisticRegressionNode(OrangeBaseNode):
    widget_cls = or_model.HLLogisticRegression
    input_names = ["Data", "Preprocessor"]
    output_names = ["Learner", "Model"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "penalty": config.get("penalty", "l2"),
            "C": float(config.get("C", 1.0)),
        }


class RandomForestNode(OrangeBaseNode):
    widget_cls = or_model.HLRandomForest
    input_names = ["Data", "Preprocessor"]
    output_names = ["Learner", "Model"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "n_estimators": int(config.get("nEstimators", 100)),
            "max_depth": int(config.get("maxDepth")) if config.get("maxDepth") not in ("", None) else None,
            "random_state": int(config.get("randomState")) if config.get("randomState") not in ("", None) else None,
        }


class TreeNode(OrangeBaseNode):
    widget_cls = or_model.HLTree
    input_names = ["Data", "Preprocessor"]
    output_names = ["Learner", "Model"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "max_depth": int(config.get("maxDepth")) if config.get("maxDepth") not in ("", None) else None,
            "min_samples_split": int(config.get("minSamplesSplit", 2)),
        }


class KNNNode(OrangeBaseNode):
    widget_cls = or_model.HLkNN
    input_names = ["Data", "Preprocessor"]
    output_names = ["Learner", "Model"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "n_neighbors": int(config.get("nNeighbors", 5)),
            "metric": config.get("metric", "euclidean"),
            "weights": config.get("weights", "uniform"),
        }


class NaiveBayesNode(OrangeBaseNode):
    widget_cls = or_model.HLNaiveBayes
    input_names = ["Data", "Preprocessor"]
    output_names = ["Learner", "Model"]


class SVMNode(OrangeBaseNode):
    widget_cls = or_model.HLSVM
    input_names = ["Data", "Preprocessor"]
    output_names = ["Learner", "Model"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "C": float(config.get("C", 1.0)),
            "kernel": config.get("kernel", "rbf"),
        }


class NeuralNetworkNode(OrangeBaseNode):
    widget_cls = or_model.HLNeuralNetwork
    input_names = ["Data", "Preprocessor"]
    output_names = ["Learner", "Model"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "hidden_layer_sizes": config.get("hiddenLayerSizes", (100,)),
            "activation": config.get("activation", "relu"),
            "max_iter": int(config.get("maxIter", 200)),
        }


class AdaBoostNode(OrangeBaseNode):
    widget_cls = or_model.HLAdaBoost
    input_names = ["Data", "Preprocessor"]
    output_names = ["Learner", "Model"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "n_estimators": int(config.get("nEstimators", 50)),
            "learning_rate": float(config.get("learningRate", 1.0)),
        }


class SGDNode(OrangeBaseNode):
    widget_cls = or_model.HLSGD
    input_names = ["Data", "Preprocessor"]
    output_names = ["Learner", "Model"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "loss": config.get("loss", "log_loss"),
            "alpha": float(config.get("alpha", 0.0001)),
        }


class ConstantNode(OrangeBaseNode):
    widget_cls = or_model.HLConstant
    input_names = ["Data", "Preprocessor"]
    output_names = ["Learner", "Model"]


class LinearRegressionNode(OrangeBaseNode):
    widget_cls = or_model.HLLinearRegression
    input_names = ["Data", "Preprocessor"]
    output_names = ["Learner", "Model"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "regularization": config.get("regularization", "none"),
            "alpha": float(config.get("alpha", 1.0)),
            "fit_intercept": bool(config.get("fitIntercept", True)),
        }


# ----------------------------------------------------------------------
# 4. Unsupervised Nodes
# ----------------------------------------------------------------------

class KMeansNode(OrangeBaseNode):
    widget_cls = or_unsupervised.HLKMeans
    input_names = ["Data"]
    output_names = ["Annotated Data"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "k": int(config.get("k", 3)),
            "n_init": int(config.get("nInit", 10)),
        }


class DBSCANNode(OrangeBaseNode):
    widget_cls = or_unsupervised.HLDBSCAN
    input_names = ["Data"]
    output_names = ["Annotated Data"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "eps": float(config.get("eps", 0.5)),
            "min_samples": int(config.get("minSamples", 5)),
        }


# ----------------------------------------------------------------------
# 5. Evaluation & Diagnostics Nodes
# ----------------------------------------------------------------------

class TestAndScoreNode(OrangeBaseNode):
    widget_cls = or_evaluate.HLTestAndScore
    input_names = ["Data", "Learner"]
    output_names = ["Evaluation Results", "Predictions"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "n_folds": int(config.get("cvFolds", config.get("nFolds", 5))),
            "resampling": int(config.get("resampling", or_evaluate.HLTestAndScore.KFold)),
            "stratified": bool(config.get("stratified", True)),
        }


class PredictionsNode(OrangeBaseNode):
    widget_cls = or_evaluate.HLPredictions
    input_names = ["Data", "Model"]
    output_names = ["Predictions", "Evaluation Results"]


# ----------------------------------------------------------------------
# 6. Bridge Nodes (Seamless integration with standard Node-RED streams)
# ----------------------------------------------------------------------

class BridgeInNode(OrangeBaseNode):
    widget_cls = bridge.NodeRedIn
    input_names = ["Data"]
    output_names = ["Data"]

    async def on_input(self, msg: Dict[str, Any]) -> None:
        """ Takes an incoming array of dicts / records and converts into an Orange Table. """
        payload = msg.get("payload")
        if not isinstance(payload, list):
            raise ValueError("BridgeIn expects msg.payload to be a list of records/dicts.")
        
        self.widget.inject_payload(payload)
        await asyncio.to_thread(self.widget.handle_new_signals)
        
        out_table = self.pending_outputs.get("Data")
        if out_table is not None:
            await self.send([{"payload": out_table, "_orange_signal": "Data"}])
            await self.status(fill="green", shape="dot", text=f"{len(payload)} rows injected")


class BridgeOutNode(OrangeBaseNode):
    widget_cls = bridge.NodeRedOut
    input_names = ["Data"]
    output_names = []

    async def on_input(self, msg: Dict[str, Any]) -> None:
        """ Takes an Orange Table and emits standard JSON records to msg.payload. """
        val = msg.get("payload")
        self.widget.receive("Data", val)
        await asyncio.to_thread(self.widget.handle_new_signals)
        
        records = self.widget.export_payload()
        await self.send([{"payload": records or []}])
        await self.status(fill="green", shape="dot", text=f"emitted {len(records or [])} rows")


# ----------------------------------------------------------------------
# 7. SciPy N-D Image Nodes
# ----------------------------------------------------------------------

class ImageLoaderNode(OrangeBaseNode):
    widget_cls = sp_image.HLImageLoader
    input_names = []
    output_names = ["Image"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"file_path": config.get("filePath", "")}

    async def start(self) -> None:
        asyncio.create_task(self.on_input({}))


class ImageFilters1DNode(OrangeBaseNode):
    widget_cls = sp_image.HLImageFilters1D
    input_names = ["Image"]
    output_names = ["Image"]


class ImageFilters2DNode(OrangeBaseNode):
    widget_cls = sp_image.HLImageFilters2D
    input_names = ["Image"]
    output_names = ["Image"]


class ImageFourierNode(OrangeBaseNode):
    widget_cls = sp_image.HLImageFourier
    input_names = ["Image"]
    output_names = ["Image"]


class ImageViewerNode(OrangeBaseNode):
    widget_cls = sp_image.HLImageViewer
    input_names = ["Image"]
    output_names = ["Image"]


class ImageSaverNode(OrangeBaseNode):
    widget_cls = sp_image.HLImageSaver
    input_names = ["Image"]
    output_names = []


# ----------------------------------------------------------------------
# 8. Python Scripting Node
# ----------------------------------------------------------------------

class PythonScriptNode(OrangeBaseNode):
    widget_cls = or_scripting.HLPythonScript
    input_names = ["in_data"]
    output_names = ["out_data"]

    def map_config_to_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"script": config.get("script", "")}
