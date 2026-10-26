# 3. OrangeRed — User Guide

[⬅ Back to README](../README.md) | * English | [Español](es/3_user_guide_es.md)

> **Audience:** Data scientists, analysts, engineers, and flow builders creating workflows in OrangeRed.

---

## 1. Building Workflows on the Canvas

OrangeRed uses **Node-RED** as its visual design canvas. Workflows are composed by dragging analytical nodes onto the canvas, wiring them together, configuring settings, and executing the graph.

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│ File Loader  ├──────►│ Preprocessing├──────►│ Scatter Plot │
└──────────────┘       └──────┬───────┘       └──────────────┘
                              │
                              ▼
                       ┌──────────────┐       ┌──────────────┐
                       │Random Forest ├──────►│ Test & Score │
                       └──────────────┘       └──────────────┘
```

### 1.1 Navigating the Palette
All OrangeRed nodes are positioned at the top of the left-hand Node-RED palette under the **`OR`** prefix:
* **`OR Data`**: Ingestion, sampling, domain editing, merging, and saving.
* **`OR Transform`**: Imputation, scaling, normalization, PCA, and outlier detection.
* **`OR Unsupervised`**: Clustering (k-Means, DBSCAN) and manifold embeddings (t-SNE, MDS).
* **`OR Model`**: Supervised classifiers, regressors, neural networks, and baseline learners.
* **`OR Evaluate`**: Cross-validation, predictions, confusion matrices, and ROC curves.
* **`OR Visualize`**: Interactive 2D scatter plots, distributions, box plots, and decision trees.
* **`OR Scripting`**: Custom Python scripts with state variable persistence.
* **`OR Bridge`**: Ingress and egress gateways connecting Orange to native Node-RED flows.
* **`OR SciPy`**: N-dimensional image filters, Fourier transforms, morphology, and audio processing.

### 1.2 Wiring Rules & Port Types
Each node has directional ports (inputs on the left, outputs on the right):
* **Tabular Data** (Orange Table): Connects data loaders, transformers, and data sinks.
* **Learners & Models**: Connects algorithm definitions to training nodes and evaluators.
* **Evaluation Results**: Carries cross-validation probability matrices to diagnostic nodes.
* **N-D Arrays**: Carries image and audio matrices across SciPy filters.

### 1.3 Deploying & Status Indicators
Unlike desktop tools where execution occurs synchronously on mouse-click:
1. Make your changes and wire nodes on the canvas.
2. Click the red **Deploy** button in the top-right corner to synchronize the graph with the backend.
3. Observe the live status badges underneath each node:
   * 🔵 **Running...** — Node is currently executing in Python.
   * 🟢 **Completed (e.g., "150 rows", "Trained")** — Computation completed successfully.
   * 🔴 **Error** — Execution failed; hover over the node or inspect the debug panel for the traceback.

---

## 2. Exploring & Visualizing Data

### 2.1 Inline Tabular Previews
Every node that produces or transforms tabular data includes an embedded **Preview** tab:
1. Double-click the node to open its configuration panel.
2. Select the **Preview** tab.
3. An interactive table (powered by `Tabulator`) renders a paginated view of the data.
4. Columns are color-coded by role:
   * **Attributes (Features)**: Standard styling.
   * **Target (Class Variable)**: Highlighted with a distinctive badge.
   * **Metas**: Muted text for non-feature identifiers and annotations.
5. Column headers display summary statistics (mean, min, max, std, or discrete category distributions).

### 2.2 Dedicated Interactive Visualizations
For rich visual analytics, connect specialized visualization nodes:

* **Scatter Plot (`or-scatter-plot`)**:
  * Select arbitrary attributes for X and Y axes.
  * Color points dynamically by categorical class or continuous attributes.
  * Adjust point size, opacity, and zoom/pan interactively.
* **Histogram (`or-histogram`)**:
  * Inspect frequency distributions of numeric attributes or categorical counts.
  * Configure custom bin counts.
* **Box Plot (`or-box-plot`)**:
  * Visualize medians, quartiles, and statistical outliers across continuous features.
  * Group distributions by categorical variables.
* **Line Plot (`or-line-plot`)**:
  * Plot sequential, time-series, or ordered sensor data across multiple series.
* **Tree Viewer (`or-tree-viewer`)**:
  * Connect directly to a `Decision Tree` node.
  * Renders an interactive, collapsible D3.js tree diagram detailing split rules, sample counts, and node purity.
* **Confusion Matrix (`or-confusion-matrix`)**:
  * Connect to `Test & Score`.
  * Displays an interactive true vs. predicted classification heatmap with proportion and count views.
* **ROC Analysis (`or-roc-analysis`)**:
  * Connect to `Test & Score`.
  * Renders multi-class Receiver Operating Characteristic curves plotting True Positive Rate against False Positive Rate.
* **Image & Audio Viewers (`sp-image-viewer`, `sp-audio-loader`)**:
  * Inspect raw and filtered image matrices inline or preview audio spectrograms.

---

## 3. Complete Node Catalog

### 3.1 OR Data
* **File Loader (`or-file-loader`)**: Loads datasets from local or server paths. Supported formats: CSV, TSV, Parquet, Excel (`.xlsx`), and Orange native format (`.tab`). Includes auto-delimiter detection and schema inference.
* **Data Table (`or-data-table`)**: Canvas inspection node providing full-screen searchable and sortable tabular views.
* **Data Sampler (`or-data-sampler`)**: Splits datasets into subsets using random sampling, stratified sampling (preserving class distributions), or fixed percentages (e.g., 80% train / 20% test). Emits `Data` and `Remaining Data` on separate ports.
* **Select Columns / Edit Domain (`or-edit-domain`)**: Reassigns column roles between **Feature Attributes**, **Class Target**, and **Meta Information**. Allows dropping unused variables.
* **Select Rows**: Filters data instances based on conditional threshold rules and missing value criteria.
* **Merge Data (`or-merge-data`)**: Joins two datasets based on common key columns (inner, left, or outer join).
* **Concatenate (`or-concatenate`)**: Vertically stacks multiple datasets sharing compatible schemas.
* **Save Data (`or-save-data`)**: Exports processed tabular data to disk in CSV, Tab-delimited, or Parquet format.

### 3.2 OR Transform
* **Impute (`or-impute`)**: Handles missing values with configurable strategies: Mean, Median, Most Frequent (Mode), or Constant Value.
* **Normalize (`or-normalize`)**: Scales continuous features using StandardScaler (zero mean, unit variance), MinMax Scaler (0 to 1), or RobustScaler (quantile-based).
* **Continuize (`or-continuize`)**: Transforms discrete/categorical attributes into numeric indicators (one-hot encoding or ordinal encoding).
* **Discretize (`or-discretize`)**: Converts continuous variables into categorical bins using equal-width, equal-frequency, or entropy-based splitting.
* **PCA (`or-pca`)**: Principal Component Analysis for dimensionality reduction. Configurable by fixed component count or target explained variance ratio.
* **Outliers (`or-outliers`)**: Detects anomalous samples using Local Outlier Factor (LOF), Isolation Forest, or Covariance estimators. Appends an `Outlier` boolean flag to the dataset.
* **Correlations (`or-correlations`)**: Computes pairwise Pearson or Spearman correlation coefficients and two-tailed p-values between continuous features. Emits pass-through `Data` and a sortable `Correlation Table`. Includes an embedded pairwise data table and interactive Plotly correlation matrix heatmap.
* **Rank (`or-rank`)**: Scores and ranks attributes using Information Gain, Gain Ratio, Gini impurity, ANOVA F-test, Chi-Square, or Univariate Linear Regression. Emits `Reduced Data` (retaining only the top-*k* features or features exceeding a threshold) and a `Scores` table. Includes an embedded Plotly score bar chart.

### 3.3 OR Unsupervised
* **k-Means (`or-kmeans`)**: Groups samples into *k* clusters based on Euclidean distance. Allows setting cluster count *k*, initialization iterations, and appends a `Cluster` column.
* **DBSCAN (`or-dbscan`)**: Density-based spatial clustering. Groups dense neighborhoods together and flags sparse points as `Noise` (outliers) without requiring a pre-specified cluster count.
* **t-SNE (`or-tsne`)**: t-Distributed Stochastic Neighbor Embedding. Projects high-dimensional datasets into 2D or 3D space (`t-SNE-x`, `t-SNE-y`), optimized for cluster separation.
* **MDS (`or-mds`)**: Multidimensional Scaling. Preserves relative pairwise distances in a lower-dimensional coordinate space.

> [!TIP]
> **Visualization Pipeline:** Pipe the output of **t-SNE**, **MDS**, **k-Means**, or **DBSCAN** directly into the **Scatter Plot** node. In the Scatter Plot dialog, select `t-SNE-x` and `t-SNE-y` as your axes, and choose `Cluster` for the Color attribute to inspect your clusters visually!

### 3.4 OR Model
* **Linear Regression (`or-linear-regression`)**: Standard regression learner and model. Supports Ordinary Least Squares (OLS), Ridge (L2 penalty), Lasso (L1 penalty), and Elastic Net (combined L1/L2 penalty). Includes interactive coefficient inspection and MLflow training history tracking.
* **Logistic Regression (`or-logistic-regression`)**: Linear classification model with L1/L2 regularization and multi-class support. Double-click to inspect model coefficients.
* **Random Forest (`or-random-forest`)**: Ensemble of decision trees with configurable tree count, maximum depth, and feature sub-sampling.
* **Decision Tree (`or-tree`)**: Single classification/regression tree. Supports Gini, Entropy, or MSE splitting with pruning options. Pipe into `Tree Viewer` for visual inspection.
* **k-Nearest Neighbors (`or-knn`)**: Instance-based learner classifying samples based on the *k* closest neighbors.
* **Naive Bayes (`or-naive-bayes`)**: Fast probabilistic classifier based on Bayes' theorem with feature independence assumptions.
* **Support Vector Machines (`or-svm`)**: Linear, Polynomial, and RBF kernel SVM for classification and regression.
* **Neural Network (`or-neural-network`)**: Multi-Layer Perceptron (MLP). Configurable hidden layer architectures (e.g., `100,50`), activation functions (`ReLU`, `Tanh`, `Logistic`), and solvers (`Adam`, `SGD`, `L-BFGS`).
* **AdaBoost (`or-adaboost`)**: Adaptive boosting meta-estimator that sequentially fits weak learners on adjusted instance weights.
* **Stochastic Gradient Descent (`or-sgd`)**: Scalable linear classifier/regressor optimized using convex loss functions.
* **Constant Learner (`or-constant`)**: Baseline dummy model predicting majority class or mean target value. Essential for verifying that complex models exceed trivial statistical baselines.

### 3.5 OR Evaluate
* **Test & Score (`or-test-and-score`)**: Connect a dataset to the `Data` port and one or more learners to the `Learners` port. Evaluates models using K-Fold Cross-Validation or Train/Test Split. Computes Classification Accuracy (CA), F1 Score, AUC, Precision, Recall, RMSE, and MAE.
* **Predictions (`or-predictions`)**: Applies trained models to new, unseen test datasets. Appends predicted probabilities and class labels.
* **Confusion Matrix (`or-confusion-matrix`)**: Interactive heatmap visualizing misclassifications across all target categories.
* **ROC Analysis (`or-roc-analysis`)**: Comparative ROC curves displaying model discriminative ability.

### 3.6 OR Scripting
* **Python Script (`or-python-script`)**: An interactive Jupyter-like code execution node.
  * Inputs: Accepts up to two independent datasets (`in_data`, `in_data2`) and incoming state dictionary (`in_state`).
  * Outputs: Emits up to two datasets (`out_data`, `out_data2`) and an output state dictionary (`out_state`).
  * Includes a built-in code editor, syntax highlighting, and an inline console output viewer.

### 3.7 OR Bridge
* **Bridge In (`or-bridge-in`)**: Translates incoming native Node-RED `msg.payload` data (JSON records) into an Orange dataset and initiates execution of the downstream pipeline.
* **Bridge Out (`or-bridge-out`)**: Converts Orange pipeline outputs back into native Node-RED messages, forwarding predictions or processed metrics to standard Node-RED nodes (MQTT, HTTP endpoints, dashboards).

### 3.8 OR SciPy (Image & Audio)
* **Image Loader (`sp-image-loader`)**: Ingests image files into `xarray.DataArray` format.
* **Image Filters 1D & 2D (`sp-image-filters-1d`, `sp-image-filters-2d`)**: Applies Gaussian, Uniform, Median, Sobel, Laplacian, and Prewitt filters.
* **Image Fourier (`sp-image-fourier`)**: Computes 2D Fast Fourier Transforms (FFT) and frequency domain filtering.
* **Image Morphology (`sp-image-morphology`)**: Performs erosion, dilation, morphological opening, and closing operations.
* **Image Interpolation (`sp-image-interpolation`)**: Affine transforms, scaling, rotation, and spline filtering.
* **Image Measurements (`sp-image-measurements`)**: Connected component analysis, center-of-mass, and object bounding boxes.
* **Image Viewer (`sp-image-viewer`)**: Inline visual canvas display for multi-channel image arrays.
* **Image Saver (`sp-image-saver`)**: Exports processed arrays back to image files on disk.
* **Audio Loader & Saver (`sp-audio-loader`, `sp-audio-saver`)**: Ingests and saves audio files (`.wav`), computing waveform matrices and spectrogram representations.

---

## 4. Working with Bridge Nodes: IoT & API Integration

The Bridge nodes allow you to integrate OrangeRed machine learning into live operational environments:

```
[HTTP In / MQTT] ──► [Function (Prep)] ──► [OR Bridge In] ──► [Predict] ──► [OR Bridge Out] ──► [Dashboard / Alert]
```

### Step-by-Step Bridge Recipe
1. Add an **`inject`** or **`mqtt in`** node from the standard Node-RED palette.
2. Provide a JSON array payload in `msg.payload`:
   ```json
   [
     {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2},
     {"sepal_length": 6.7, "sepal_width": 3.1, "petal_length": 4.7, "petal_width": 1.5}
   ]
   ```
3. Wire the incoming message to **`OR Bridge In`**.
4. Connect **`OR Bridge In`** to a trained **`Predictions`** node.
5. Connect the output of **`Predictions`** to **`OR Bridge Out`**.
6. Wire **`OR Bridge Out`** to a standard **`debug`** or **`dashboard-table`** node.
7. Click **Deploy**. When an MQTT message or HTTP request arrives, OrangeRed automatically converts the JSON, runs model inference, and emits the predicted classes downstream as standard `msg.payload`.

---

## 5. Python Scripting Guide

The **Python Script** node allows you to write custom data manipulation code directly within your workflow:

```python
# Available scope variables:
# in_data   : First input Orange.data.Table (or None)
# in_data2  : Second input Orange.data.Table (or None)
# in_state  : Dictionary passed from upstream script nodes
# out_data  : Set to Orange.data.Table or pandas.DataFrame to emit on port 1
# out_data2 : Set to Orange.data.Table or pandas.DataFrame to emit on port 2
# out_state : Dictionary of variables to pass downstream
# pd, np, Orange : Pre-imported utility modules

# Example: Filter rows where sepal_length > 5.0
if in_data is not None:
    df, schema = in_data.to_pandas()
    filtered_df = df[df["sepal_length"] > 5.0]
    
    print(f"Filtered {len(df)} rows down to {len(filtered_df)} rows.")
    
    out_data = filtered_df
    out_state["filter_applied"] = True
    out_state["row_count"] = len(filtered_df)
```

Click **Run** in the dialog to execute the code and view live output in the **Console** tab.

---

## 6. Experiment Tracking (MLflow Compatibility)

Every Machine Learning model node (`Logistic Regression`, `Random Forest`, `Neural Network`, etc.) automatically tracks its training history in an MLflow-compatible format.

### Inspecting History
1. Double-click any trained Model node on the canvas.
2. Switch to the **Training History** tab.
3. The history ledger displays:
   * **Run ID & Timestamp**: Date and time of training.
   * **Hyperparameters**: Tree count, depth, regularization, learning rates, etc.
   * **Metrics**: Recorded validation loss, training duration, and accuracy metrics.
4. Compare different runs directly inside the dialog to identify optimal hyperparameter configurations.
