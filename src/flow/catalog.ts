/**
 * Catalog of red-orange and standard node definitions
 * Contains categories, colors, default inputs/outputs, and labels
 * to mirror Node-RED's palette and aesthetics in React Flow.
 */

export interface NodeCatalogItem {
  type: string;
  category: string;
  label: string;
  color: string;
  icon?: string;
  inputs: number;
  outputs: number;
  outputLabels?: string[];
  defaultConfig?: Record<string, unknown>;
  description?: string;
}

export const NODE_CATEGORIES = [
  "OR Data",
  "OR Transform",
  "OR Unsupervised",
  "OR Model",
  "OR Evaluate",
  "OR Visualize",
  "OR Scripting",
  "OR Bridge",
  "OR SciPy",
  "Cyan Prompt",
  "common",
] as const;

export const CATEGORY_COLORS: Record<string, string> = {
  "OR Data": "#FFAA00",
  "OR Transform": "#52C41A",
  "OR Unsupervised": "#13C2C2",
  "OR Model": "#1890FF",
  "OR Evaluate": "#722ED1",
  "OR Visualize": "#EB2F96",
  "OR Scripting": "#FA8C16",
  "OR Bridge": "#FAAD14",
  "OR SciPy": "#2F54EB",
  "Cyan Prompt": "#06B6D4",
  common: "#A0A0A0",
};

export const NODE_CATALOG: Record<string, NodeCatalogItem> = {
  // OR Data
  "or-file-loader": {
    type: "or-file-loader",
    category: "OR Data",
    label: "File",
    color: "#FFAA00",
    inputs: 0,
    outputs: 1,
    outputLabels: ["Data"],
    defaultConfig: { filename: "iris.tab", sheet: "" },
    description: "Read data from file (Orange .tab, CSV, Excel)",
  },
  "or-data-sampler": {
    type: "or-data-sampler",
    category: "OR Data",
    label: "Data Sampler",
    color: "#FFAA00",
    inputs: 1,
    outputs: 2,
    outputLabels: ["Sample", "Remaining"],
    defaultConfig: { sample_type: "percentage", sample_size: 70 },
    description: "Sample a subset of data instances",
  },
  "or-select-columns": {
    type: "or-select-columns",
    category: "OR Data",
    label: "Select Columns",
    color: "#FFAA00",
    inputs: 1,
    outputs: 1,
    outputLabels: ["Transformed Data"],
    defaultConfig: { features: [], target: "" },
    description: "Select features, target variable, and metas",
  },
  "or-select-rows": {
    type: "or-select-rows",
    category: "OR Data",
    label: "Select Rows",
    color: "#FFAA00",
    inputs: 1,
    outputs: 1,
    outputLabels: ["Matching Rows"],
    defaultConfig: { conditions: [] },
    description: "Filter data instances matching conditions",
  },
  "or-data-table": {
    type: "or-data-table",
    category: "OR Data",
    label: "Data Table",
    color: "#FFAA00",
    inputs: 1,
    outputs: 1,
    outputLabels: ["Selected Data"],
    defaultConfig: {},
    description: "View data matrix in Tabulator spreadsheet",
  },
  "or-merge-data": {
    type: "or-merge-data",
    category: "OR Data",
    label: "Merge Data",
    color: "#FFAA00",
    inputs: 2,
    outputs: 1,
    defaultConfig: { join_type: "inner" },
    description: "Join two tables on shared columns",
  },
  "or-concatenate": {
    type: "or-concatenate",
    category: "OR Data",
    label: "Concatenate",
    color: "#FFAA00",
    inputs: 2,
    outputs: 1,
    defaultConfig: {},
    description: "Stack multiple datasets vertically or horizontally",
  },
  "or-save-data": {
    type: "or-save-data",
    category: "OR Data",
    label: "Save Data",
    color: "#FFAA00",
    inputs: 1,
    outputs: 0,
    defaultConfig: { filename: "output.tab" },
    description: "Save table to disk (.tab, .csv, .xlsx)",
  },
  "or-edit-domain": {
    type: "or-edit-domain",
    category: "OR Data",
    label: "Edit Domain",
    color: "#FFAA00",
    inputs: 1,
    outputs: 1,
    defaultConfig: {},
    description: "Rename variables or change column types",
  },

  // OR Transform
  "or-impute": {
    type: "or-impute",
    category: "OR Transform",
    label: "Impute",
    color: "#52C41A",
    inputs: 1,
    outputs: 1,
    defaultConfig: { method: "average" },
    description: "Impute missing values in dataset",
  },
  "or-normalize": {
    type: "or-normalize",
    category: "OR Transform",
    label: "Normalize",
    color: "#52C41A",
    inputs: 1,
    outputs: 1,
    defaultConfig: { method: "standardize" },
    description: "Standardize or scale numeric features",
  },
  "or-continuize": {
    type: "or-continuize",
    category: "OR Transform",
    label: "Continuize",
    color: "#52C41A",
    inputs: 1,
    outputs: 1,
    defaultConfig: {},
    description: "Convert categorical variables to continuous indicators",
  },
  "or-discretize": {
    type: "or-discretize",
    category: "OR Transform",
    label: "Discretize",
    color: "#52C41A",
    inputs: 1,
    outputs: 1,
    defaultConfig: { intervals: 3 },
    description: "Discretize continuous features into bins",
  },
  "or-pca": {
    type: "or-pca",
    category: "OR Transform",
    label: "PCA",
    color: "#52C41A",
    inputs: 1,
    outputs: 1,
    outputLabels: ["Transformed Data"],
    defaultConfig: { n_components: 2 },
    description: "Principal Component Analysis dimension reduction",
  },
  "or-outliers": {
    type: "or-outliers",
    category: "OR Transform",
    label: "Outliers",
    color: "#52C41A",
    inputs: 1,
    outputs: 2,
    outputLabels: ["Inliers", "Outliers"],
    defaultConfig: { contamination: 0.05 },
    description: "Detect anomaly rows with Isolation Forest or Covariance",
  },
  "or-correlations": {
    type: "or-correlations",
    category: "OR Transform",
    label: "Correlations",
    color: "#52C41A",
    inputs: 1,
    outputs: 1,
    defaultConfig: { method: "pearson" },
    description: "Compute pairwise column correlation coefficients",
  },
  "or-rank": {
    type: "or-rank",
    category: "OR Transform",
    label: "Rank",
    color: "#52C41A",
    inputs: 1,
    outputs: 1,
    defaultConfig: { scorer: "info_gain" },
    description: "Score and rank attributes by relevance to target",
  },

  // OR Model
  "or-logistic-regression": {
    type: "or-logistic-regression",
    category: "OR Model",
    label: "Logistic Regression",
    color: "#1890FF",
    inputs: 1,
    outputs: 1,
    outputLabels: ["Learner / Model"],
    defaultConfig: { penalty: "l2", C: 1.0 },
    description: "Linear classification model",
  },
  "or-random-forest": {
    type: "or-random-forest",
    category: "OR Model",
    label: "Random Forest",
    color: "#1890FF",
    inputs: 1,
    outputs: 1,
    outputLabels: ["Learner / Model"],
    defaultConfig: { n_estimators: 100, max_depth: 0 },
    description: "Ensemble of randomized decision trees",
  },
  "or-tree": {
    type: "or-tree",
    category: "OR Model",
    label: "Tree",
    color: "#1890FF",
    inputs: 1,
    outputs: 1,
    outputLabels: ["Learner / Model"],
    defaultConfig: { max_depth: 10, min_samples_split: 5 },
    description: "Decision tree classification or regression model",
  },
  "or-knn": {
    type: "or-knn",
    category: "OR Model",
    label: "k-NN",
    color: "#1890FF",
    inputs: 1,
    outputs: 1,
    outputLabels: ["Learner / Model"],
    defaultConfig: { n_neighbors: 5, metric: "euclidean" },
    description: "k-Nearest Neighbors classifier",
  },
  "or-naive-bayes": {
    type: "or-naive-bayes",
    category: "OR Model",
    label: "Naive Bayes",
    color: "#1890FF",
    inputs: 1,
    outputs: 1,
    outputLabels: ["Learner / Model"],
    defaultConfig: {},
    description: "Probabilistic classifier based on Bayes' theorem",
  },
  "or-svm": {
    type: "or-svm",
    category: "OR Model",
    label: "SVM",
    color: "#1890FF",
    inputs: 1,
    outputs: 1,
    outputLabels: ["Learner / Model"],
    defaultConfig: { kernel: "rbf", C: 1.0 },
    description: "Support Vector Machine classifier/regressor",
  },
  "or-neural-network": {
    type: "or-neural-network",
    category: "OR Model",
    label: "Neural Network",
    color: "#1890FF",
    inputs: 1,
    outputs: 1,
    outputLabels: ["Learner / Model"],
    defaultConfig: { hidden_layers: [100], activation: "relu", max_iter: 200 },
    description: "Multi-layer Perceptron neural network",
  },
  "or-linear-regression": {
    type: "or-linear-regression",
    category: "OR Model",
    label: "Linear Regression",
    color: "#1890FF",
    inputs: 1,
    outputs: 1,
    outputLabels: ["Learner / Model"],
    defaultConfig: { fit_intercept: true },
    description: "Ordinary Least Squares linear regression",
  },

  // OR Unsupervised
  "or-kmeans": {
    type: "or-kmeans",
    category: "OR Unsupervised",
    label: "k-Means",
    color: "#13C2C2",
    inputs: 1,
    outputs: 1,
    defaultConfig: { k: 3 },
    description: "Partition instances into k clusters",
  },
  "or-dbscan": {
    type: "or-dbscan",
    category: "OR Unsupervised",
    label: "DBSCAN",
    color: "#13C2C2",
    inputs: 1,
    outputs: 1,
    defaultConfig: { eps: 0.5, min_samples: 5 },
    description: "Density-based spatial clustering of applications with noise",
  },

  // OR Evaluate
  "or-test-and-score": {
    type: "or-test-and-score",
    category: "OR Evaluate",
    label: "Test & Score",
    color: "#722ED1",
    inputs: 2,
    outputs: 1,
    defaultConfig: { cv_folds: 5 },
    description: "Cross-validation and testing metrics for models",
  },
  "or-predictions": {
    type: "or-predictions",
    category: "OR Evaluate",
    label: "Predictions",
    color: "#722ED1",
    inputs: 2,
    outputs: 1,
    defaultConfig: {},
    description: "Predict target values using trained model on fresh data",
  },
  "or-confusion-matrix": {
    type: "or-confusion-matrix",
    category: "OR Evaluate",
    label: "Confusion Matrix",
    color: "#722ED1",
    inputs: 1,
    outputs: 1,
    defaultConfig: {},
    description: "Proportion of correctly and incorrectly classified instances",
  },
  "or-roc-analysis": {
    type: "or-roc-analysis",
    category: "OR Evaluate",
    label: "ROC Analysis",
    color: "#722ED1",
    inputs: 1,
    outputs: 0,
    defaultConfig: {},
    description: "Receiver Operating Characteristic curve visualization",
  },

  // OR Visualize
  "or-scatter-plot": {
    type: "or-scatter-plot",
    category: "OR Visualize",
    label: "Scatter Plot",
    color: "#EB2F96",
    inputs: 1,
    outputs: 1,
    defaultConfig: { x_axis: "", y_axis: "", color: "" },
    description: "2D scatter plot visualization with Plotly",
  },
  "or-histogram": {
    type: "or-histogram",
    category: "OR Visualize",
    label: "Distributions",
    color: "#EB2F96",
    inputs: 1,
    outputs: 1,
    defaultConfig: {},
    description: "Value distributions and histograms",
  },
  "or-box-plot": {
    type: "or-box-plot",
    category: "OR Visualize",
    label: "Box Plot",
    color: "#EB2F96",
    inputs: 1,
    outputs: 1,
    defaultConfig: {},
    description: "Distribution quartiles and outlier visualizer",
  },
  "or-tree-viewer": {
    type: "or-tree-viewer",
    category: "OR Visualize",
    label: "Tree Viewer",
    color: "#EB2F96",
    inputs: 1,
    outputs: 0,
    defaultConfig: {},
    description: "Interactive visual decision tree graph",
  },

  // Common / Core
  inject: {
    type: "inject",
    category: "common",
    label: "inject",
    color: "#A6BBCF",
    inputs: 0,
    outputs: 1,
    defaultConfig: { payload: "", topic: "", repeat: "" },
    description: "Trigger flow with custom payload or timer",
  },
  debug: {
    type: "debug",
    category: "common",
    label: "debug",
    color: "#87A987",
    inputs: 1,
    outputs: 0,
    defaultConfig: { active: true, complete: "payload" },
    description: "Display message payload in debug panel",
  },
  // Cyan Prompt & Knowledge Base Nodes
  "cyan-prompt-transform": {
    type: "cyan-prompt-transform",
    category: "Cyan Prompt",
    label: "Prompt Transform",
    color: "#06B6D4",
    icon: "sparkles",
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      template: "Analyze incoming data: {{ inputs.in1.text_content }}",
      model: "gpt-4o",
      temperature: 0.7,
      staticAttributes: { domain: "general" },
    },
    description: "Applies an LLM prompt transformation and outputs an enriched SemanticPayload.",
  },
  "cyan-tabular-context": {
    type: "cyan-tabular-context",
    category: "Cyan Prompt",
    label: "Tabular Context",
    color: "#0891B2",
    icon: "table",
    inputs: 1,
    outputs: 1,
    defaultConfig: {
      maxSampleRows: 5,
      includeCorrelations: true,
    },
    description: "Serializes upstream red-orange tabular data into structured semantic prompt context.",
  },
  "cyan-synthesis-node": {
    type: "cyan-synthesis-node",
    category: "Cyan Prompt",
    label: "Synthesis & Insight",
    color: "#0E7490",
    icon: "book-open",
    inputs: 1,
    outputs: 0,
    defaultConfig: {
      extractEntities: true,
      inferSentiment: true,
    },
    description: "Synthesizes multi-node inputs into executive insights and records knowledge base lineage.",
  },
};

/**
 * Get catalog item for a given type with sensible fallback
 */
export function getNodeCatalogItem(type: string): NodeCatalogItem {
  if (NODE_CATALOG[type]) {
    return NODE_CATALOG[type];
  }

  // Derive sensible fallback
  return {
    type,
    category: "common",
    label: type,
    color: "#D0D0D0",
    inputs: 1,
    outputs: 1,
    defaultConfig: {},
    description: `Generic node (${type})`,
  };
}

/**
 * List catalog items grouped by category
 */
export function getCatalogGroupedByCategory(): Record<string, NodeCatalogItem[]> {
  const grouped: Record<string, NodeCatalogItem[]> = {};
  for (const cat of NODE_CATEGORIES) {
    grouped[cat] = [];
  }

  for (const item of Object.values(NODE_CATALOG)) {
    if (!grouped[item.category]) {
      grouped[item.category] = [];
    }
    grouped[item.category].push(item);
  }

  return grouped;
}

