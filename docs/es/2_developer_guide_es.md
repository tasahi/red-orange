# 2. OrangeRed — Guía del Desarrollador

[⬅ Volver al README](README_es.md) | * [English](../2_developer_guide.md) | Español

> **Audiencia:** Desarrolladores de backend y frontend que mantienen, amplían o integran OrangeRed.  
> **Prerrequisito:** Lea primero [1_concepts_and_introduction_es.md](1_concepts_and_introduction_es.md).

---

## 1. Visión General del Sistema y Estructura del Repositorio

OrangeRed se estructura en un backend de cómputo en Python (FastAPI) y un paquete de nodos personalizados para Node-RED:

```text
orangered/
├── docs/                        # Documentación del proyecto (EN y ES)
│   ├── 1_concepts_and_introduction.md
│   ├── 2_developer_guide.md
│   ├── 3_user_guide.md
│   └── es/                      # Documentación en español
├── frontend/                    # Paquete de nodos personalizados de Node-RED
│   ├── nodes/                   # Plantillas UI (.html) y scripts de ejecución (.js)
│   ├── orangered-client.js      # Módulo cliente de comunicación con FastAPI
│   └── package.json             # Definiciones de registro de nodos de Node-RED
├── src/                         # Backend FastAPI
│   ├── main.py                  # Punto de entrada ASGI
│   ├── api.py                   # Endpoints REST y controladores WebSocket
│   ├── orchestrator.py          # Grafo de dependencias DAG, orden topológico y ejecución
│   ├── headless_widget.py       # Clases base abstractas sin dependencias de Qt
│   ├── registry.py              # Catálogo maestro de clases de widgets registradas
│   ├── conversion.py            # Pasarela de datos entre DataFrames de pandas y Tablas de Orange
│   ├── schemas.py               # Modelos y esquemas Pydantic
│   ├── tracker.py               # Registro de experimentos compatible con MLflow
│   └── widgets/                 # Implementaciones por dominio:
│       ├── bridge.py            # Nodos puente (NodeRedIn, NodeRedOut)
│       ├── or_data.py           # Carga, muestreo, selección, fusión y guardado de datos
│       ├── or_model.py          # Clasificadores, regresores, ensambles y modelos base
│       ├── or_preprocess.py     # Imputación, escalado, discretización, PCA y anomalías
│       ├── or_unsupervised.py   # Agrupamiento (k-Means, DBSCAN) y proyecciones (t-SNE, MDS)
│       ├── or_evaluate.py       # Test & Score, Predicciones, Matriz de Confusión y Curvas ROC
│       ├── or_scripting.py      # Ejecutor de scripts Python con persistencia de variables
│       ├── sp_image.py          # Filtros n-dimensionales, morfología y Fourier con SciPy
│       └── sp_audio.py          # Procesamiento de audio y espectrogramas con SciPy
└── tests/                       # Batería de pruebas automatizadas y comprobaciones
```

---

## 2. Contratos de Datos y Serialización

OrangeRed opera a través de fronteras bien delimitadas. Internamente, los algoritmos requieren estructuras en memoria específicas, mientras que las APIs HTTP demandan cargas serializables en JSON.

### 2.1 Datos Tabulares: `Orange.data.Table` y `DomainSchema`
Los algoritmos de Orange requieren una rica semántica de columnas (Variables continuas, discretas con categorías definidas, variables objetivo de clase y atributos de metadatos). Los DataFrames tradicionales de pandas carecen de estas distinciones.

Para conectar ambos mundos sin pérdida de información, `src/conversion.py` y `src/schemas.py` implementan un esquema de contrato dual:
* **`DomainSchema`**: Metadatos complementarios que definen:
  * `attributes`: Lista de variables de características de entrada (`VariableSpec`).
  * `class_vars`: Lista de variables objetivo o etiquetas.
  * `metas`: Columnas complementarias (identificadores, texto explicativo).
* **Ingesta (`dataframe_to_table`)**: Convierte registros JSON en un `Orange.data.Domain` explícito y genera una `Orange.data.Table`.
* **Egreso (`table_to_dataframe`)**: Convierte instancias de `Orange.data.Table` en DataFrames de pandas junto con el `DomainSchema` exportado para su consumo en el frontend.

### 2.2 Matrices N-Dimensionales: `xarray.DataArray`
Los nodos de imagen y audio de SciPy operan con tensores multidimensionales. OrangeRed utiliza `xarray.DataArray` como formato estándar porque envuelve matrices de NumPy con etiquetas dimensionales con nombre (ej. `['height', 'width', 'channel']`). Las imágenes se transmiten al navegador mediante el endpoint `/image_preview` en formato PNG binario.

### 2.3 Cargas de Puente y Scripting: JSON Nativo
Los nodos puente y el nodo de Scripting en Python admiten listas y diccionarios JSON arbitrarios provenientes de Node-RED, facilitando la ingesta de datos no estructurados y la transmisión de diccionarios de estado entre nodos consecutivos.

---

## 3. Arquitectura de Widgets Headless (`src/headless_widget.py`)

OrangeRed elimina completamente cualquier dependencia de PyQt mediante la clase base `HeadlessWidget`:

```python
class HeadlessWidget:
    def __init__(self, node_id: str, orchestrator: Orchestrator, settings: dict):
        self.node_id = node_id
        self._orchestrator = orchestrator
        self._settings = settings
        self._inputs = {}
        self._outputs = {}

    @classmethod
    def get_input_signals(cls) -> list[SignalDesc]:
        """Puertos de entrada declarados y tipos aceptados."""
        return []

    @classmethod
    def get_output_signals(cls) -> list[SignalDesc]:
        """Puertos de salida declarados y tipos emitidos."""
        return []

    def receive(self, input_name: str, value: Any) -> None:
        """Invocado por el orquestador cuando llegan señales de entrada."""
        self._inputs[input_name] = value

    def handle_new_signals(self) -> None:
        """Ejecuta el cómputo y emite resultados mediante self.send()."""
        raise NotImplementedError

    def send(self, output_name: str, value: Any) -> None:
        """Publica el resultado hacia los enlaces downstream conectados."""
        self._outputs[output_name] = value
```

### Arquitectura de Modelos (`_HLBaseLearner`)
Los modelos de machine learning heredan de `_HLBaseLearner`. Esta clase gestiona el entrenamiento al recibir datos, registra los hiperparámetros y guarda automáticamente el historial en el sistema de trazabilidad compatible con MLflow (`src/tracker.py`).

---

## 4. El Motor Orquestador DAG (`src/orchestrator.py`)

El `Orchestrator` controla la ejecución del grafo:
1. **Validación de Grafo**: Registra nodos y enlaces dirigidos comprobando la compatibilidad de tipos entre puertos conectados.
2. **Orden Topológico**: Calcula el orden lineal de ejecución mediante el algoritmo de Kahn, garantizando que los nodos previos se ejecuten antes que los nodos que consumen sus datos.
3. **Propagación de Señales**: Itera por los nodos ordenados:
   - Asigna las entradas en `receive()`.
   - Ejecuta `handle_new_signals()`.
   - Direcciona las salidas emitidas hacia las entradas de los nodos downstream vinculados.
4. **Estados y Notificaciones**: Dispara eventos de cambio de estado (`idle` → `running` → `completed` o `error`) transmitidos por WebSocket.

---

## 5. Referencia Completa de la API REST y WebSockets

El backend expone una completa suite de endpoints REST en `http://127.0.0.1:8000`:

### 5.1 Registro y Ciclo de Vida
* **`GET /api/registry`**: Devuelve los descriptores y puertos de señal de todos los widgets registrados.
* **`POST /api/workflows`**: Crea una nueva sesión de flujo de trabajo aislada.
* **`GET /api/workflows/{wf_id}`**: Obtiene la estructura actual del grafo y el estado de los nodos.
* **`POST /api/workflows/{wf_id}/batch_setup`**: Registra atómicamente todos los nodos y enlaces enviados desde Node-RED en una sola transacción.
* **`POST /api/workflows/{wf_id}/execute`**: Ejecuta asíncronamente el DAG completo de principio a fin.
* **`WS /api/workflows/{wf_id}/ws`**: Conexión WebSocket en tiempo real para eventos de estado de los nodos (`node_id`, `status`, `error`).

### 5.2 Gestión de Nodos y Conexiones
* **`POST /api/workflows/{wf_id}/nodes`**: Añade un nodo individual.
* **`PATCH /api/workflows/{wf_id}/nodes/{node_id}/settings`**: Modifica hiperparámetros o ajustes de un nodo.
* **`DELETE /api/workflows/{wf_id}/nodes/{node_id}`**: Elimina un nodo y sus conexiones asociadas.
* **`POST /api/workflows/{wf_id}/links`**: Conecta un puerto de salida de un nodo con un puerto de entrada de otro.
* **`DELETE /api/workflows/{wf_id}/links/{link_id}`**: Elimina una conexión.

### 5.3 Ingesta y Puentes (Bridge)
* **`POST /api/workflows/{wf_id}/nodes/{node_id}/inject`**: Inyecta un conjunto de datos tabular en formato JSON en un puerto de entrada.
* **`POST /api/workflows/{wf_id}/nodes/{node_id}/bridge_inject`**: Endpoint para el nodo `or-bridge-in`; transforma el mensaje en una Tabla de Orange y dispara la ejecución del flujo.
* **`GET /api/workflows/{wf_id}/nodes/{node_id}/bridge_export`**: Exporta los datos procesados del nodo `or-bridge-out` como registros JSON hacia Node-RED.

### 5.4 Inspección y Visualización de Salidas
* **`GET /api/workflows/{wf_id}/nodes/{node_id}/status`**: Estado del nodo (`idle`, `running`, `completed`, `error`).
* **`GET /api/workflows/{wf_id}/nodes/{node_id}/output/{output_name}`**: Salida completa de la tabla o resumen del objeto.
* **`GET /api/workflows/{wf_id}/nodes/{node_id}/preview/{output_name}?rows=50&offset=0`**: Vista previa paginada con estadísticas de columna (mínimo, máximo, media, desviación típica, distribución y nulos).
* **`GET /api/workflows/{wf_id}/nodes/{node_id}/metrics`**: Métricas de evaluación (CA, F1, AUC, Precision, Recall, RMSE, MAE, R²) y matrices de confusión generadas por `Test & Score`.
* **`GET /api/workflows/{wf_id}/nodes/{node_id}/coefficients`**: Coeficientes e intercepciones de modelos de Regresión Logística o Regresión Lineal.
* **`GET /api/workflows/{wf_id}/nodes/{node_id}/correlations`**: Matriz de correlación, valores p y lista de pares ordenados de un nodo Correlations.
* **`GET /api/workflows/{wf_id}/nodes/{node_id}/rank_scores`**: Puntuaciones de importancia de atributos y metadatos de selección de un nodo Rank.
* **`GET /api/workflows/{wf_id}/nodes/{node_id}/roc`**: Coordenadas de curvas ROC multiclase (FPR frente a TPR).
* **`GET /api/workflows/{wf_id}/nodes/{node_id}/tree_structure`**: Jerarquía JSON de reglas de división para el visor de árboles en D3.js.
* **`GET /api/workflows/{wf_id}/nodes/{node_id}/console`**: Salidas de texto estándar (stdout/stderr) capturadas por el nodo Python Script.
* **`GET /api/workflows/{wf_id}/nodes/{node_id}/image_preview/{output_name}`**: Flujo de imagen PNG generado a partir de un `xarray.DataArray`.

### 5.5 Trazabilidad y Experimentos (MLflow)
* **`GET /api/tracker/runs?node_id={node_id}`**: Lista de entrenamientos históricos, filtrable opcionalmente por nodo.
* **`GET /api/tracker/runs/{run_id}`**: Detalles completos de hiperparámetros, métricas y artefactos de una ejecución específica.

---

## 6. Creación de un Nuevo Nodo Personalizado (Paso a Paso)

### Paso 1: Implementar el Widget Headless
Cree o amplíe un módulo en `src/widgets/`:

```python
from ..headless_widget import HeadlessWidget
from ..schemas import SignalDesc

class HLEjemploFiltro(HeadlessWidget):
    @classmethod
    def get_input_signals(cls) -> list[SignalDesc]:
        return [SignalDesc(name="Data", type="Orange.data.Table")]

    @classmethod
    def get_output_signals(cls) -> list[SignalDesc]:
        return [SignalDesc(name="Filtered Data", type="Orange.data.Table")]

    def handle_new_signals(self) -> None:
        data = self._inputs.get("Data")
        if data is None:
            return
        
        # Realizar cálculo analítico
        resultado = data.copy()
        self.send("Filtered Data", resultado)
```

### Paso 2: Registrar en `src/registry.py`
Añada la clase al diccionario `_WIDGETS`:

```python
_WIDGETS["transform.EjemploFiltro"] = (HLEjemploFiltro, "Ejemplo Filtro", "Transform")
```

### Paso 3: Crear los Archivos de Frontend
Cree `frontend/nodes/or-ejemplo-filtro.js` y `frontend/nodes/or-ejemplo-filtro.html`:

```javascript
// frontend/nodes/or-ejemplo-filtro.js
module.exports = function(RED) {
    const orangeredClient = require('../orangered-client');
    function EjemploFiltroNode(config) {
        RED.nodes.createNode(this, config);
        orangeredClient.registerNode(this, config, 'transform.EjemploFiltro');
    }
    RED.nodes.registerType('or-ejemplo-filtro', EjemploFiltroNode);
};
```

### Paso 4: Añadir a `frontend/package.json`
Registre el script en la clave `"node-red"` -> `"nodes"` de `frontend/package.json`.

---

## 7. Pruebas y Control de Calidad

Ejecute la suite de pruebas automatizadas con Python:

```powershell
# Ejecutar todas las pruebas
& 'C:\Programs\Python3\python.exe' -m pytest tests/ -v

# Ejecutar pruebas específicas de integración de DAG
& 'C:\Programs\Python3\python.exe' -m pytest tests/test_e2e_dag.py -v
```
