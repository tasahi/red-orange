---
title: Red-Orange Technical Documentation Index
document_type: Documentation Hub / Table of Contents
project: red-orange
target: Orange3 and SciPy Data Mining, Machine Learning, and N-D Image Processing plugin for red-fastapi
status: Operational
date: October 2026
---

# Red-Orange Technical Documentation Index

**Project:** `red-orange`  
**Host Framework:** `red-fastapi`  
**Document Type:** Documentation Hub / Table of Contents  
**Status:** Operational (40+ Nodes across 9 Palette Categories & Dual UI Support)  
**Date:** October 2026  

---

## 1. Overview

Welcome to the documentation repository for **`red-orange`** (OrangeRed). This package brings **Orange3** data mining, machine learning, and **SciPy/xarray** N-dimensional scientific computing natively into **`red-fastapi`** as an in-process Python plugin, supporting both classic **Node-RED** and modern **React Flow** web interfaces.

---

## 2. Documentation Directory

### Architecture & System Design (`docs/architecture/`)

In-depth technical architecture, decoupled kernel designs, and multi-interface specifications.

| Document | Description |
| :--- | :--- |
| **[Concepts & Core Architecture](architecture/concepts_and_architecture.md)** | Core concepts, functional organization, palette breakdown (OR Data, OR Transform, OR Model, etc.), memory management, and decoupled architecture. |
| **[React Flow Interface Architecture](architecture/react_flow_architecture.md)** | Modern React Flow interface design, dual-UI selection strategy, JSON-RPC 2.0 communication, bidirectional flow adapters, and spatial parity with Node-RED. |
| **[Red-Cyan Semantic Prompt & Agent Pack Integration](architecture/cyan_agent_pack_integration.md)** | Integration specification for red-cyan semantic prompt nodes, dynamic Jinja handles, and neuro-symbolic data insight pipelines. |

---

### Guides & Manuals (`docs/guides/`)

Practical references for users, developers, and workflow designers.

| Document | Description |
| :--- | :--- |
| **[User Guide](guides/user_guide.md)** | End-user handbook: step-by-step workflow construction, dataset inspection with Tabulator, model evaluation (ROC, Confusion Matrix), interactive visualizations (Plotly), and image processing pipelines. |
| **[Developer Guide](guides/developer_guide.md)** | Technical specification for plugin developers: node lifecycle, widget porting from Orange3/SciPy, template structure, communication APIs, and testing workflows. |

---

### Evolution & Historical Records (`docs/history/`)

Records of project transitions, historical milestones, and design iterations preserved for future reference and audits.

| Record | Description |
| :--- | :--- |
| **[Legacy Bridge to In-Process Plugin Migration](history/legacy_bridge_to_plugin_migration.md)** | Design document detailing the architectural transition from an external multi-process bridge into an in-process native plugin for `red-fastapi`. |
| **[React Flow Master Roadmap](history/react_flow_master_plan.md)** | Complete blueprint detailing the roadmap for the React Flow web interface, JSON-RPC 2.0 integration, and UI switcher. |
| **[Flow Adapter & Palette Report](history/react_flow_adapter_and_palette_report.md)** | Technical verification report on the JSON-RPC 2.0 client, bidirectional flow translation, and declarative palette system. |
| **[Workspace & Deployment Plan](history/react_flow_workspace_and_deployment_plan.md)** | Specification for multi-tab workspace state management (`WorkspaceStore`), Deploy controller over JSON-RPC, and header navigation. |

---

### Documentación en Español (`docs/es/`)

| Documento | Descripción |
| :--- | :--- |
| **[1. Conceptos y Arquitectura](es/1_concepts_and_introduction_es.md)** | Fundamentos conceptuales, desacoplamiento de Orange3, gestión de memoria e integración con el canvas de Node-RED. |
| **[2. Guía del Desarrollador](es/2_developer_guide_es.md)** | Ciclo de vida de nodos, creación de widgets personalizados, plantillas HTML y pruebas automatizadas. |
| **[3. Guía del Usuario](es/3_user_guide_es.md)** | Construcción de flujos, previsualización de datos interactiva, entrenamiento de modelos y análisis multidimensional. |
| **[Resumen del Proyecto](es/README_es.md)** | Descripción general del proyecto en español. |
