# 🍊 OrangeRed

* [English](../../README.md) | Español

**OrangeRed** es un conjunto de herramientas híbrido para ciencia de datos visual y aprendizaje automático. Combina los algoritmos analíticos de minería de datos de **Orange3** (librería de ciencia de datos en Python) y el procesamiento de matrices n-dimensionales de **SciPy/xarray**, con el lienzo visual basado en web de **Node-RED**.

OrangeRed le permite construir canales complejos de procesamiento de datos, machine learning y manipulación de imágenes/matrices simplemente arrastrando nodos al lienzo y conectándolos entre sí, sin escribir una sola línea de código.

---

## 🚀 Visión General de la Arquitectura

A diferencia de las herramientas tradicionales que se ejecutan por completo en el escritorio o transmiten conjuntos de datos masivos a través de un servidor web Node.js, OrangeRed opera sobre una arquitectura desacoplada:

* **Frontend (Lienzo Node-RED):** Funciona como interfaz de diseño visual. Orquesta el Grafo Acíclico Dirigido (DAG) y solicita porciones de datos paginadas y ligeras para renderizar visualizaciones interactivas (gráficos de dispersión, histogramas, tablas, árboles y matrices de confusión).
* **Backend (FastAPI, Orange3 y SciPy):** Funciona como motor de ejecución headless. Almacena de forma segura los conjuntos de datos en memoria, entrena modelos de machine learning, aplica filtros matemáticos avanzados (ej. `scipy.ndimage`), registra el historial compatible con MLflow y ejecuta scripts personalizados de Python.
* **Subsistema de Puentes (Bridge):** Conecta bidireccionalmente los flujos analíticos de Orange con las secuencias de eventos nativas de Node-RED, permitiendo que la telemetría IoT, webhooks HTTP y eventos MQTT activen inferencias de modelos en tiempo real y emitan predicciones a nodos downstream.

Al conectar dos nodos en OrangeRed no se transmiten miles de filas de datos por el navegador. Únicamente se transmite un **puntero de referencia ligero**, indicando al backend cómo conectar los algoritmos en memoria.

---

## 📚 Documentación

Para una comprensión completa, consulte las guías oficiales:

1. [**Conceptos y Arquitectura**](1_concepts_and_introduction_es.md) — Fundamentos conceptuales, paso de datos por punteros, concepto de puente y ejecución headless.
2. [**Guía del Desarrollador**](2_developer_guide_es.md) — Información técnica para desarrolladores, funcionamiento del motor DAG, contratos de datos (`Table`, `xarray`, JSON), referencia completa de los 16 endpoints de la API REST/WebSockets y guía paso a paso para crear nuevos nodos.
3. [**Guía del Usuario**](3_user_guide_es.md) — Manual orientado al usuario para construir flujos, explorar visualizaciones interactivas, catálogo completo de más de 40 nodos organizados en las 9 categorías `OR`, scripts en Python y trazabilidad con MLflow.

---

## 📦 Instalación y Configuración

OrangeRed requiere la ejecución simultánea del Backend en Python y del Frontend en Node-RED.

### 1. Configuración del Backend (FastAPI, Orange3, SciPy, xarray)

1. Asegúrese de contar con Python 3.9 o superior.
2. Clone el repositorio y navegue a la raíz del proyecto:
   ```bash
   git clone https://github.com/tasahi/orangered.git
   cd orangered
   ```
3. Cree un entorno virtual e instale las dependencias:
   ```bash
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   # En Linux/macOS:
   source venv/bin/activate

   pip install -r requirements.txt
   ```
4. Inicie el servidor API:
   ```bash
   uvicorn src.main:app --reload
   ```
   El backend se ejecutará en `http://127.0.0.1:8000`.

### 2. Configuración del Frontend (Node-RED)

1. Instale [Node.js y Node-RED](https://nodered.org/docs/getting-started/local).
2. Instale el paquete `node-red-contrib-orangered` copiando la carpeta `frontend/` dentro del directorio `.node-red/node_modules/`:
   ```bash
   # En Windows (PowerShell)
   Copy-Item -Recurse -Force "frontend\*" -Destination "$env:USERPROFILE\.node-red\node_modules\node-red-contrib-orangered\"
   
   # En Linux/macOS
   cp -r frontend/* ~/.node-red/node_modules/node-red-contrib-orangered/
   ```
3. Inicie Node-RED:
   ```bash
   node-red
   ```
4. Abra su navegador en `http://127.0.0.1:1880`. Encontrará las categorías de OrangeRed situadas en la parte superior de la paleta izquierda precedidas por el prefijo **`OR`** (`OR Data`, `OR Transform`, `OR Unsupervised`, `OR Model`, `OR Evaluate`, `OR Visualize`, `OR Scripting`, `OR Bridge`, `OR SciPy`).
