# fastapi-red-orangered

Orange3 and SciPy Data Mining, Machine Learning, and N-D Image Processing plugin for **FastAPI-Red**.

## Features
- **40+ Drag-and-Drop Nodes** across 9 palette categories (`OR Data`, `OR Transform`, `OR Unsupervised`, `OR Model`, `OR Evaluate`, `OR Visualize`, `OR Scripting`, `OR Bridge`, `OR SciPy`).
- **Single-Process Python Execution:** Runs natively inside FastAPI-Red's asyncio runtime.
- **Zero-Copy In-Memory Passing:** Orange Tables, Learners, and Models stay directly in Python heap memory without JSON serialization.
- **Interactive Previews:** Tabulator tables, Plotly charts, Decision Tree hierarchies, and ROC curves directly in the Node-RED dialogs.

## Installation
```bash
# In the Python environment where fastapi-red is installed:
pip install -e .
```
FastAPI-Red will automatically discover and load `fastapi-red-orangered` on startup!
