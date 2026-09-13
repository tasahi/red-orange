# 3. OrangeRed — Guía del Usuario

[⬅ Volver al README](README_es.md) | * [English](../3_user_guide.md) | Español

> **Audiencia:** Científicos de datos, analistas, ingenieros y creadores de flujos en OrangeRed.

---

## 1. Construcción de Flujos en el Lienzo

OrangeRed utiliza **Node-RED** como lienzo visual de diseño. Los flujos de trabajo se componen arrastrando nodos analíticos al lienzo, conectándolos mediante cables, configurando sus parámetros y desplegando el grafo.

```
┌──────────────┐       ┌────────────────┐     ┌──────────────┐
│ File Loader  ├──────►│Preprocesamiento├────►│ Dispersión   │
└──────────────┘       └──────┬─────────┘     └──────────────┘
                              │
                              ▼
                       ┌──────────────┐       ┌──────────────┐
                       │Random Forest ├──────►│ Test & Score │
                       └──────────────┘       └──────────────┘
```

### 1.1 Organización de la Paleta
Todos los nodos de OrangeRed se sitúan en la parte superior de la paleta izquierda de Node-RED con el prefijo **`OR`**:
* **`OR Data`**: Carga de archivos, muestreo, edición de dominio, unión y guardado de datos.
* **`OR Transform`**: Imputación, normalización, discretización, PCA y detección de valores atípicos (anomalías).
* **`OR Unsupervised`**: Agrupamiento no supervisado (k-Means, DBSCAN) y proyecciones dimensionales (t-SNE, MDS).
* **`OR Model`**: Algoritmos supervisados de clasificación, regresión, redes neuronales y modelos base.
* **`OR Evaluate`**: Validación cruzada, predicciones sobre datos nuevos, matrices de confusión y curvas ROC.
* **`OR Visualize`**: Gráficos interactivos de dispersión, histogramas, diagramas de cajas y árboles de decisión.
* **`OR Scripting`**: Ejecución de código Python a medida con persistencia de variables de estado.
* **`OR Bridge`**: Puertas de enlace de entrada y salida para integrar Orange con flujos estándar de Node-RED.
* **`OR SciPy`**: Filtros n-dimensionales de imágenes, morfología matemática, transformada de Fourier y audio.

### 1.2 Reglas de Conexión y Puertos
Cada nodo cuenta con puertos direccionales (entradas a la izquierda, salidas a la derecha):
* **Datos Tabulares** (Orange Table): Conecta cargadores de datos, transformadores y sumideros de datos.
* **Algoritmos y Modelos**: Conecta definiciones de aprendices a nodos de entrenamiento y evaluación.
* **Resultados de Evaluación**: Transmite matrices de probabilidad hacia nodos de diagnóstico.
* **Matrices N-D**: Conecta arreglos multidimensionales de imagen o audio entre filtros SciPy.

### 1.3 Despliegue e Indicadores de Estado
A diferencia de las herramientas de escritorio convencionales:
1. Diseñe y conecte sus nodos en el lienzo.
2. Haga clic en el botón rojo **"Deploy"** (arriba a la derecha) para sincronizar el flujo con el motor de Python.
3. Observe los indicadores luminosos de estado bajo cada nodo:
   * 🔵 **Running...** — El nodo se está ejecutando en Python.
   * 🟢 **Completed (ej. "150 rows", "Trained")** — Cálculo analítico completado con éxito.
   * 🔴 **Error** — Error en la ejecución; pase el cursor o consulte el panel de depuración para ver la traza.

---

## 2. Exploración y Visualización de Datos

### 2.1 Vistas Previas Tabulares Integradas
Cada nodo que genera o transforma tablas de datos incluye una pestaña **Preview**:
1. Haga doble clic en el nodo para abrir su panel de propiedades.
2. Seleccione la pestaña **Preview**.
3. Se mostrará una tabla interactiva (gestionada por `Tabulator`) con las primeras 50 filas de datos.
4. Las columnas están clasificadas por colores:
   * **Atributos (Características)**: Estilo estándar.
   * **Objetivo (Variable de Clase)**: Resaltada con un distintivo visual.
   * **Metadatos**: Texto atenuado para identificadores y notas.
5. Los encabezados incluyen resúmenes estadísticos (media, desviación, mínimos, máximos o frecuencias de categorías).

### 2.2 Nodos de Visualización Dedicados
Para análisis visual avanzado, agregue nodos de la categoría `OR Visualize`:

* **Gráfico de Dispersión (`or-scatter-plot`)**: Permite seleccionar ejes X e Y, colorear puntos según variables categóricas o continuas, y modificar el tamaño de los puntos de forma interactiva.
* **Histograma (`or-histogram`)**: Muestra la distribución de frecuencias para variables numéricas o categorías discretas.
* **Diagrama de Cajas (`or-box-plot`)**: Visualiza medianas, cuartiles y rangos estadísticos, con opción de agrupar por variables categóricas.
* **Gráfico de Líneas (`or-line-plot`)**: Muestra secuencias temporales o mediciones continuas de sensores.
* **Visor de Árboles (`or-tree-viewer`)**: Se conecta a un nodo de `Decision Tree` para renderizar un diagrama jerárquico interactivo con reglas de división y pureza de nodos.
* **Matriz de Confusión (`or-confusion-matrix`)**: Se conecta a `Test & Score` para desplegar un mapa de calor interactivo con aciertos y errores de clasificación.
* **Curvas ROC (`or-roc-analysis`)**: Visualiza curvas ROC multiclase calculando la tasa de verdaderos positivos frente a falsos positivos.
* **Visor de Imágenes y Audio (`sp-image-viewer`, `sp-audio-loader`)**: Visualiza matrices de imagen y espectrogramas de audio en el propio lienzo.

---

## 3. Catálogo Completo de Nodos

### 3.1 OR Data
* **File Loader (`or-file-loader`)**: Carga datos en formatos CSV, TSV, Parquet, Excel (`.xlsx`) y formato nativo de Orange (`.tab`) con detección automática de delimitadores.
* **Data Table (`or-data-table`)**: Muestra vistas tabulares completas ordenables y con búsqueda interactiva.
* **Data Sampler (`or-data-sampler`)**: Divide conjuntos de datos en subconjuntos de entrenamiento y prueba mediante muestreo aleatorio o estratificado.
* **Select Columns / Edit Domain (`or-edit-domain`)**: Reasigna columnas entre variables de entrada, variable objetivo (clase) y metadatos, o descarta atributos innecesarios.
* **Select Rows**: Filtra observaciones según condiciones lógicas o valores faltantes.
* **Merge Data (`or-merge-data`)**: Realiza uniones de tablas basadas en columnas clave compartidas.
* **Concatenate (`or-concatenate`)**: Apila verticalmente tablas que comparten esquemas compatibles.
* **Save Data (`or-save-data`)**: Guarda tablas procesadas en disco en formatos CSV, Tab o Parquet.

### 3.2 OR Transform
* **Impute (`or-impute`)**: Imputación de valores faltantes por Media, Mediana, Moda o Valor Constante.
* **Normalize (`or-normalize`)**: Escalado de características numéricas con StandardScaler, MinMax Scaler o RobustScaler.
* **Continuize (`or-continuize`)**: Convierte atributos categóricos en variables numéricas (one-hot o codificación ordinal).
* **Discretize (`or-discretize`)**: Convierte variables continuas en intervalos discretos.
* **PCA (`or-pca`)**: Análisis de Componentes Principales para reducción de dimensionalidad según número fijo de componentes o porcentaje de varianza explicada.
* **Outliers (`or-outliers`)**: Detección de valores anómalos mediante Local Outlier Factor (LOF) o Bosques de Aislamiento (Isolation Forest).
* **Correlations (`or-correlations`)**: Calcula coeficientes de correlación de Pearson o Spearman y niveles de significación p entre características continuas. Emite la tabla `Data` original y una tabla `Correlation Table` ordenada. Incluye visor de pares y mapa de calor interactivo con Plotly.
* **Rank (`or-rank`)**: Evalúa y clasifica la importancia de los atributos según Ganancia de Información (InfoGain), Razón de Ganancia, Gini, ANOVA, Chi² o Regresión Lineal Univariada. Emite `Reduced Data` (conservando solo las mejores *k* características o las que superen un umbral) y una tabla `Scores`. Incluye gráfico de barras interactivo con Plotly.

### 3.3 OR Unsupervised
* **k-Means (`or-kmeans`)**: Agrupamiento en *k* conglomerados mediante distancia euclídea; añade la columna `Cluster` resultante.
* **DBSCAN (`or-dbscan`)**: Agrupamiento espacial basado en densidad; identifica automáticamente formas arbitrarias y etiqueta puntos dispersos como Ruido (Noise).
* **t-SNE (`or-tsne`)**: Incrustación estocástica de vecinos para proyectar datos de alta dimensión en 2D o 3D (`t-SNE-x`, `t-SNE-y`).
* **MDS (`or-mds`)**: Escalamiento multidimensional conservando distancias originales.

> [!TIP]
> **Canalización Visual Recomendada:** Conecte la salida de **t-SNE**, **MDS** o **DBSCAN** a un nodo **Scatter Plot**. Seleccione `t-SNE-x` y `t-SNE-y` como ejes y utilice `Cluster` como atributo de color para visualizar sus agrupamientos al instante.

### 3.4 OR Model
* **Linear Regression (`or-linear-regression`)**: Modelo y aprendiz de regresión lineal estándar. Admite Mínimos Cuadrados Ordinarios (OLS), Ridge (penalización L2), Lasso (penalización L1) y Elastic Net (L1 + L2). Incluye inspección interactiva de coeficientes y trazabilidad con MLflow.
* **Logistic Regression (`or-logistic-regression`)**: Clasificación lineal con regularización L1/L2 e inspección de coeficientes.
* **Random Forest (`or-random-forest`)**: Ensamble de árboles de decisión para clasificación y regresión robusta.
* **Decision Tree (`or-tree`)**: Árbol individual de decisión con criterios de división Gini o Entropía.
* **k-Nearest Neighbors (`or-knn`)**: Clasificador basado en instancias y vecindad más cercana.
* **Naive Bayes (`or-naive-bayes`)**: Clasificador probabilístico rápido basado en el teorema de Bayes.
* **Support Vector Machines (`or-svm`)**: Máquinas de vectores de soporte con núcleos lineal, polinómico y RBF.
* **Neural Network (`or-neural-network`)**: Perceptrón Multicapa (MLP) con capas ocultas configurables (`100,50`), activaciones (`ReLU`, `Tanh`) y optimizadores (`Adam`, `SGD`).
* **AdaBoost (`or-adaboost`)**: Meta-estimador de boosting adaptativo sobre estimadores débiles.
* **Stochastic Gradient Descent (`or-sgd`)**: Modelos lineales optimizados mediante descenso de gradiente estocástico.
* **Constant (`or-constant`)**: Modelo base ficticio que predice la clase mayoritaria o la media; fundamental para verificar que los modelos avanzados realmente aportan aprendizaje.

### 3.5 OR Evaluate
* **Test & Score (`or-test-and-score`)**: Evaluación por validación cruzada (K-Fold) o partición entrenamiento/prueba. Calcula exactitud (CA), F1, AUC, precisión, sensibilidad, RMSE y MAE.
* **Predictions (`or-predictions`)**: Aplica modelos entrenados sobre nuevos conjuntos de datos para predecir clases y probabilidades.
* **Confusion Matrix (`or-confusion-matrix`)**: Mapa de calor con la matriz de aciertos y confusiones del clasificador.
* **ROC Analysis (`or-roc-analysis`)**: Gráfico comparativo de curvas ROC multiclase.

### 3.6 OR Scripting
* **Python Script (`or-python-script`)**: Nodo ejecutor de código Python estilo Jupyter:
  * Permite hasta dos tablas de entrada (`in_data`, `in_data2`) y un diccionario de estado (`in_state`).
  * Emite hasta dos tablas (`out_data`, `out_data2`) y un diccionario de estado (`out_state`).
  * Incluye editor de código integrado y pestaña de visualización de consola (stdout/stderr).

### 3.7 OR Bridge
* **Bridge In (`or-bridge-in`)**: Transforma mensajes `msg.payload` de Node-RED (JSON) en tablas de datos de Orange y desencadena la ejecución del flujo.
* **Bridge Out (`or-bridge-out`)**: Convierte los resultados analíticos generados por Orange en mensajes estándar de Node-RED para enviarlos a paneles de control, MQTT o servicios externos.

### 3.8 OR SciPy (Imagen y Audio)
* **Cargador y Visor de Imágenes (`sp-image-loader`, `sp-image-viewer`)**: Ingesta y visualización de imágenes como `xarray.DataArray`.
* **Filtros 1D y 2D (`sp-image-filters-1d`, `sp-image-filters-2d`)**: Filtros Gaussiano, Mediana, Sobel, Laplaciano y Prewitt.
* **Morfología y Fourier (`sp-image-morphology`, `sp-image-fourier`)**: Dilatación, erosión y transformadas de Fourier.
* **Mediciones e Interpolación (`sp-image-measurements`, `sp-image-interpolation`)**: Conteo de objetos, centro de masa y rotaciones afines.
* **Cargador y Guardador de Audio (`sp-audio-loader`, `sp-audio-saver`)**: Carga y guardado de archivos de audio `.wav` y cálculo de espectrogramas.

---

## 4. Integración de Puentes (Bridge): IoT y APIs

Los nodos Bridge permiten insertar inteligencia artificial en arquitecturas Node-RED en tiempo real:

```
[HTTP / MQTT] ──► [Preparación JSON] ──► [OR Bridge In] ──► [Predicción] ──► [OR Bridge Out] ──► [Alerta / Cuadro de Mando]
```

### Ejemplo Práctico:
1. Conecte un nodo **`mqtt in`** o **`inject`** de Node-RED con un array de registros JSON en `msg.payload`.
2. Enlace dicho mensaje a **`OR Bridge In`**.
3. Conecte **`OR Bridge In`** a un nodo **`Predictions`** que tenga conectado un modelo entrenado.
4. Conecte la salida de **`Predictions`** a **`OR Bridge Out`**.
5. Conecte **`OR Bridge Out`** a un nodo **`debug`** o cuadro de mando.
6. Al pulsar **Deploy**, cada nuevo mensaje recibido ejecutará la inferencia en Python y emitirá las predicciones al flujo de Node-RED downstream.

---

## 5. Trazabilidad de Modelos con MLflow

Cada nodo de modelado supervisado registra de forma transparente su historial de entrenamiento:
1. Haga doble clic en un nodo de modelo entrenado (ej. `Random Forest`).
2. Abra la pestaña **Training History**.
3. Consulte el registro detallado con fecha, hiperparámetros empleados y métricas de desempeño.
