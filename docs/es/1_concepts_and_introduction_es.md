# 1. OrangeRed — Conceptos y Arquitectura

[⬅ Volver al README](README_es.md) | * [English](../1_concepts_and_introduction.md) | Español

> **Propósito de este documento:** Establecer los fundamentos conceptuales, principios arquitectónicos y la organización funcional de OrangeRed. Lea este documento antes de consultar la [Guía del Desarrollador](2_developer_guide_es.md) o la [Guía del Usuario](3_user_guide_es.md).

---

## 1. ¿Qué es OrangeRed?

**OrangeRed** es un conjunto de herramientas visual e interactivo para minería de datos, aprendizaje automático (machine learning) y computación científica. Combina los algoritmos de minería de datos de **Orange3** (librería de ciencia de datos en Python) y el procesamiento de matrices n-dimensionales de **SciPy/xarray**, con la orquestación de flujos visuales basada en navegador de **Node-RED**.

OrangeRed permite a científicos de datos, ingenieros y analistas construir canales complejos de procesamiento de datos, entrenar modelos de aprendizaje automático, inspeccionar gráficos interactivos y aplicar manipulaciones matriciales científicas conectando nodos en un lienzo web, sin necesidad obligatoria de escribir código.

```
┌────────────────────────────────────────────────────────┐
│               Frontend: Lienzo Node-RED                │
│   • Composición visual de DAG y paleta (categorías OR) │
│   • Vistas previas Tabulator y gráficos interactivos   │
│   • Punteros de referencia ligeros entre cables        │
└───────────────────────────┬────────────────────────────┘
                            │ REST / WebSockets / JSON
┌───────────────────────────▼────────────────────────────┐
│            Backend: Motor FastAPI + Python             │
│   • Orquestador de DAG sin interfaz (orden topológico) │
│   • Motor de datos Orange3 (Table, DomainSchema, etc.) │
│   • Procesamiento N-D de imágenes y audio con SciPy    │
│   • Seguimiento de experimentos compatible con MLflow  │
└────────────────────────────────────────────────────────┘
```

### El Desafío
**Orange Data Mining** es tradicionalmente una aplicación exclusiva de escritorio. Su motor de ejecución está fuertemente acoplado al framework de interfaz gráfica PyQt/Qt, lo que impide ejecutarlo nativamente en entornos en la nube sin interfaz (headless), contenedores o aplicaciones web. Además, las herramientas de flujo visual comunes carecen de semántica nativa para ciencia de datos o sufren al gestionar matrices de alta dimensionalidad.

### La Solución
OrangeRed resuelve esto desacoplando por completo el **Lienzo Visual** del **Motor de Ejecución**:
- **Frontend (Node-RED):** Funciona como lienzo de diseño y orquestación visual. Es responsable del diseño de nodos, diálogos de configuración, inspección de parámetros y renderizado de visualizaciones (gráficos de dispersión, distribuciones, árboles de decisión, matrices de confusión e imágenes).
- **Backend (FastAPI):** Funciona como motor de cómputo headless. Recibe la especificación del Grafo Acíclico Dirigido (DAG), realiza el ordenamiento topológico y ejecuta la canalización analítica en Python, gestiona los conjuntos de datos en memoria y registra el historial de entrenamiento de los modelos.

---

## 2. Arquitectura Central: Paso de Punteros, No de Datos

Un principio arquitectónico fundamental en OrangeRed es la forma en que los datos fluyen entre nodos conectados.

En los flujos estándar de Node-RED, los mensajes que contienen cargas útiles completas (`msg.payload`) circulan a través de los cables entre nodos. En el caso de grandes conjuntos de datos de machine learning (decenas o cientos de miles de filas) o modelos serializados pesados, pasar datos sin procesar por el bucle de eventos de Node.js y conexiones WebSocket causaría cuellos de botella críticos, saturación de memoria y caídas del navegador.

En OrangeRed, **los conjuntos de datos y modelos pesados nunca atraviesan los cables de Node-RED**.

En su lugar, OrangeRed pasa **Punteros de Referencia Ligeros**:

1. **Almacenamiento en el Backend:** Cuando un nodo upstream finaliza su cálculo, su salida (por ejemplo, una `Orange.data.Table` o un `xarray.DataArray`) se conserva en la memoria del orquestador en el backend.
2. **Señales de Cable:** El cable de Node-RED transmite únicamente un paquete de referencia ligero que contiene el `ID de Flujo`, el `ID de Nodo` y el identificador del puerto de salida.
3. **Ejecución Downstream:** El nodo downstream envía este puntero al backend, indicándole al motor de ejecución que recupere la estructura de datos mapeada en memoria para la siguiente etapa analítica.

---

## 3. El Concepto de Puente (Bridge): Fusión de Flujos por Eventos y Procesamiento Analítico

Node-RED tradicional está orientado fundamentalmente a **eventos** (gestión de señales de sensores, webhooks o paquetes MQTT a medida que llegan), mientras que Orange Data Mining está orientado a **procesamiento por lotes/analítico** (procesamiento de tablas de datos, entrenamiento de modelos y cálculo de matrices estadísticas).

OrangeRed conecta ambos paradigmas mediante los **Nodos Puente (Bridge)**:

* **`OR Bridge In` (`or-bridge-in`):** Recibe datos orientados a eventos (`msg.payload` estándar en JSON, resultados de consultas de bases de datos, peticiones REST) de nodos nativos de Node-RED, los convierte en tablas analíticas en el backend y activa la ejecución del flujo.
* **`OR Bridge Out` (`or-bridge-out`):** Extrae predicciones, subconjuntos filtrados o métricas de evaluación del flujo analítico y los emite como objetos `msg.payload` estándar de Node-RED (por ejemplo, para activar alertas MQTT, actualizar cuadros de mando o guardar en bases de datos externas).

---

## 4. Estrategia de Visualización Multicapa

Dado que el backend almacena los datos en memoria, OrangeRed emplea un modelo de visualización en dos niveles:

1. **Vistas Previas Tabulares Integradas:** Cada nodo que produce datos tabulares incorpora una pestaña de **Vista Previa (Preview)**. Al abrirse, el frontend consulta un endpoint paginado para obtener una pequeña porción (por ejemplo, las primeras 50 filas) junto con los roles de las variables (continuas, discretas, metadatos, objetivos), renderizada con el motor `Tabulator`.
2. **Visualizaciones Interactivas Dedicadas:**
   * **Gráficos Plotly.js:** Nodos como `Scatter Plot`, `Histogram`, `Box Plot` y `Line Plot` solicitan dinámicamente muestras de datos y generan gráficos responsivos con zoom, desplazamiento y leyendas dinámicas.
   * **Árboles Jerárquicos D3.js:** El nodo `Tree Viewer` extrae la estructura anidada de los árboles de decisión entrenados y genera diagramas jerárquicos interactivos y colapsables.
   * **Mapas de Calor y Curvas de Diagnóstico:** Los nodos `Confusion Matrix` y `ROC Analysis` obtienen matrices de probabilidad para renderizar mapas de calor interactivos y curvas ROC multiclase.
   * **Inspección de Imágenes y Audio:** Visores especializados muestran matrices de imágenes multicanal y espectrogramas de audio en el lienzo.

---

## 5. Almacenamiento, Estado y Modos de Ejecución

### Persistencia del Flujo
* **Diseño (Node-RED):** La definición canónica del flujo, las posiciones de los nodos, los hiperparámetros y las conexiones se guardan en el archivo estándar de Node-RED (`flows.json` en el directorio de usuario, habitualmente `~/.node-red/` o `%USERPROFILE%\.node-red\`).
* **Estado en Tiempo de Ejecución (Backend FastAPI):** Cuando el usuario pulsa "Deploy", la topología y configuraciones se sincronizan con el backend de Python a través de endpoints de configuración atómica por lotes. Los flujos se ejecutan como sesiones activas en memoria.

### Ejecución Headless y Programática
OrangeRed no requiere mantener un navegador web abierto para ejecutar los flujos:

1. **Vía API REST:** Dispare ejecuciones, inyecte datos y extraiga resultados programáticamente mediante endpoints HTTP estándar (ej. `POST /api/workflows/{id}/execute`).
2. **Integración en Python Puro:** Importe la clase `Orchestrator` (`src/orchestrator.py`) directamente en scripts automatizados de Python sin necesidad de arrancar el servidor web.
3. **Node-RED Headless:** Ejecute Node-RED como servicio demonio en servidores o dispositivos IoT para procesar eventos en segundo plano.

---

## 6. Siguientes Pasos

* Para conocer los detalles de implementación, el funcionamiento interno del motor DAG y cómo crear nodos personalizados o consumir las APIs, consulte la [Guía del Desarrollador](2_developer_guide_es.md).
* Para aprender a construir flujos, configurar modelos y explorar el catálogo completo de más de 40 nodos, consulte la [Guía del Usuario](3_user_guide_es.md).
