# red-orange

What if [Orange Data Mining](https://orangedatamining.com/) had a web interface instead of a desktop one.
Could we have a server and access remotely? 

Orange3 and SciPy Data Mining, Machine Learning, and N-D Image Processing plugin for [**Red-Fastapi**](https://github.com/tasahi/red-fastapi) project, being a port of Node-RED to a Python backend.

## Features
- **40+ Drag-and-Drop Nodes** across 9 palette categories (`OR Data`, `OR Transform`, `OR Unsupervised`, `OR Model`, `OR Evaluate`, `OR Visualize`, `OR Scripting`, `OR Bridge`, `OR SciPy`).
- **Single-Process Python Execution:** Runs natively inside Red-Fastapi's asyncio runtime.
- **Zero-Copy In-Memory Passing:** Orange Tables, Learners, and Models stay directly in Python heap memory without JSON serialization.
- **Interactive Previews:** Tabulator tables, Plotly charts, Decision Tree hierarchies, and ROC curves directly in the Node-RED dialogs.

## Installation
```
# In the Python environment where red-fastapi is installed:
pip install -e .
```
FastAPI-Red will automatically discover and load `red-orange` on startup!

## Technical Documentation

You can find more technical documentation in the [docs](docs/index.md) folder.

## Note:
For this implementation, AI agents were used to plan and create the code, with stage by stage implementation and validation. Since the frontend is still Node-RED, it inherits all the functionalities of the original project.

Please create your examples and please help to test it in order to continue improving in terms of UI.