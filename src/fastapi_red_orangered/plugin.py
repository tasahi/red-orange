""" OrangeRed Plugin for FastAPI-Red.
"""

from pathlib import Path
from typing import List
from fastapi import APIRouter

from fastapi_red.plugins.base import BasePlugin
from fastapi_red_orangered.api import router as orangered_router
from fastapi_red_orangered import nodes as or_nodes

MODULE_NAME = "node-red-contrib-orangered"
TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"


class OrangeRedPlugin(BasePlugin):
    """ First-class OrangeRed Data Science and Machine Learning Plugin.
    """

    @property
    def name(self) -> str:
        return "orangered"

    @property
    def version(self) -> str:
        return "0.1.0"

    def register_nodes(self, registry) -> None:
        """ Registers all 40+ HTML node templates into the Node-RED registry.
        """
        nodes_dir = TEMPLATES_DIR / "nodes"
        icons_dir = TEMPLATES_DIR / "icons"

        if hasattr(registry, "register_icons") and icons_dir.is_dir():
            registry.register_icons(MODULE_NAME, icons_dir)

        # Mapping of node template file -> registered types
        templates = {
            # Data
            "or-file-loader.html": ["or-file-loader"],
            "or-data-sampler.html": ["or-data-sampler"],
            "or-select-columns.html": ["or-select-columns"],
            "or-select-rows.html": ["or-select-rows"],
            "or-data-table.html": ["or-data-table"],
            "or-merge-data.html": ["or-merge-data"],
            "or-concatenate.html": ["or-concatenate"],
            "or-save-data.html": ["or-save-data"],
            "or-edit-domain.html": ["or-edit-domain"],
            # Transform
            "or-impute.html": ["or-impute"],
            "or-normalize.html": ["or-normalize"],
            "or-continuize.html": ["or-continuize"],
            "or-discretize.html": ["or-discretize"],
            "or-pca.html": ["or-pca"],
            "or-outliers.html": ["or-outliers"],
            "or-tsne.html": ["or-tsne"],
            "or-mds.html": ["or-mds"],
            "or-correlations.html": ["or-correlations"],
            "or-rank.html": ["or-rank"],
            # Model
            "or-logistic-regression.html": ["or-logistic-regression"],
            "or-random-forest.html": ["or-random-forest"],
            "or-tree.html": ["or-tree"],
            "or-knn.html": ["or-knn"],
            "or-naive-bayes.html": ["or-naive-bayes"],
            "or-svm.html": ["or-svm"],
            "or-neural-network.html": ["or-neural-network"],
            "or-adaboost.html": ["or-adaboost"],
            "or-sgd.html": ["or-sgd"],
            "or-constant.html": ["or-constant"],
            "or-linear-regression.html": ["or-linear-regression"],
            # Unsupervised
            "or-kmeans.html": ["or-kmeans"],
            "or-dbscan.html": ["or-dbscan"],
            # Evaluate
            "or-test-and-score.html": ["or-test-and-score"],
            "or-predictions.html": ["or-predictions"],
            "or-confusion-matrix.html": ["or-confusion-matrix"],
            "or-roc-analysis.html": ["or-roc-analysis"],
            # Visualize
            "or-scatter-plot.html": ["or-scatter-plot"],
            "or-histogram.html": ["or-histogram"],
            "or-box-plot.html": ["or-box-plot"],
            "or-line-plot.html": ["or-line-plot"],
            "or-tree-viewer.html": ["or-tree-viewer"],
            # Scripting
            "or-python-script.html": ["or-python-script"],
            # Bridge
            "or-bridge-in.html": ["or-bridge-in"],
            "or-bridge-out.html": ["or-bridge-out"],
            # SciPy
            "sp-image-loader.html": ["sp-image-loader"],
            "sp-image-filters-1d.html": ["sp-image-filters-1d"],
            "sp-image-filters-2d.html": ["sp-image-filters-2d"],
            "sp-image-fourier.html": ["sp-image-fourier"],
            "sp-image-viewer.html": ["sp-image-viewer"],
            "sp-image-saver.html": ["sp-image-saver"],
        }

        for tmpl_file, types in templates.items():
            path = nodes_dir / tmpl_file
            if path.is_file():
                set_name = types[0]
                registry.register_node_set(MODULE_NAME, set_name, types, path)

    def register_engine_types(self, engine) -> None:
        """ Registers executable Node constructor classes into FlowEngine.
        """
        type_mapping = {
            # Data
            "or-file-loader": or_nodes.FileLoaderNode,
            "or-data-sampler": or_nodes.DataSamplerNode,
            "or-select-columns": or_nodes.SelectColumnsNode,
            "or-select-rows": or_nodes.SelectRowsNode,
            "or-data-table": or_nodes.ViewerNode,
            "or-merge-data": or_nodes.MergeDataNode,
            "or-concatenate": or_nodes.ConcatenateNode,
            "or-save-data": or_nodes.SaveDataNode,
            "or-edit-domain": or_nodes.EditDomainNode,
            # Transform
            "or-impute": or_nodes.ImputeNode,
            "or-normalize": or_nodes.NormalizeNode,
            "or-continuize": or_nodes.ContinuizeNode,
            "or-discretize": or_nodes.DiscretizeNode,
            "or-pca": or_nodes.PCANode,
            "or-outliers": or_nodes.OutliersNode,
            "or-tsne": or_nodes.TSNENode,
            "or-mds": or_nodes.MDSNode,
            "or-correlations": or_nodes.CorrelationsNode,
            "or-rank": or_nodes.RankNode,
            # Model
            "or-logistic-regression": or_nodes.LogisticRegressionNode,
            "or-random-forest": or_nodes.RandomForestNode,
            "or-tree": or_nodes.TreeNode,
            "or-knn": or_nodes.KNNNode,
            "or-naive-bayes": or_nodes.NaiveBayesNode,
            "or-svm": or_nodes.SVMNode,
            "or-neural-network": or_nodes.NeuralNetworkNode,
            "or-adaboost": or_nodes.AdaBoostNode,
            "or-sgd": or_nodes.SGDNode,
            "or-constant": or_nodes.ConstantNode,
            "or-linear-regression": or_nodes.LinearRegressionNode,
            # Unsupervised
            "or-kmeans": or_nodes.KMeansNode,
            "or-dbscan": or_nodes.DBSCANNode,
            # Evaluate
            "or-test-and-score": or_nodes.TestAndScoreNode,
            "or-predictions": or_nodes.PredictionsNode,
            "or-confusion-matrix": or_nodes.ViewerNode,
            "or-roc-analysis": or_nodes.ViewerNode,
            # Visualize
            "or-scatter-plot": or_nodes.ViewerNode,
            "or-histogram": or_nodes.ViewerNode,
            "or-box-plot": or_nodes.ViewerNode,
            "or-line-plot": or_nodes.ViewerNode,
            "or-tree-viewer": or_nodes.ViewerNode,
            # Scripting
            "or-python-script": or_nodes.PythonScriptNode,
            # Bridge
            "or-bridge-in": or_nodes.BridgeInNode,
            "or-bridge-out": or_nodes.BridgeOutNode,
            # SciPy
            "sp-image-loader": or_nodes.ImageLoaderNode,
            "sp-image-filters-1d": or_nodes.ImageFilters1DNode,
            "sp-image-filters-2d": or_nodes.ImageFilters2DNode,
            "sp-image-fourier": or_nodes.ImageFourierNode,
            "sp-image-viewer": or_nodes.ImageViewerNode,
            "sp-image-saver": or_nodes.ImageSaverNode,
        }

        for node_type, constructor in type_mapping.items():
            engine.register_type(node_type, constructor)

    def get_routers(self) -> List[APIRouter]:
        return [orangered_router]
