---
title: Red-Orange Technical Documentation Index
document_type: Documentation Hub / Table of Contents
project: red-orange
target: Orange3 and SciPy Data Mining, Machine Learning, and N-D Image Processing plugin for red-fastapi
status: Operational
date: September 2026
---

# Red-Orange Technical Documentation Index

**Project:** `red-orange`  
**Document Type:** Documentation Hub / Table of Contents  
**Status:** Operational (40+ Nodes across 9 Palette Categories)  
**Host Framework:** `red-fastapi`  
**Date:** September 2026  

---

## Overview

Welcome to the technical documentation repository for **`red-orange`** (OrangeRed). This package brings **Orange3** data mining, machine learning, and **SciPy/xarray** N-dimensional scientific computing natively into **`red-fastapi`** as an in-process Python plugin.

---

## Documentation Directory

### English Documentation

| Document | Description | Type |
| :--- | :--- | :--- |
| **[1. Concepts & Architecture](1_concepts_and_introduction.md)** | Core concepts, functional organization, palette breakdown (OR Data, OR Transform, OR Model, etc.), memory management, and decoupled architecture. | Architecture & Concepts |
| **[2. Developer Guide](2_developer_guide.md)** | Technical specification for plugin developers: node life-cycle, widget porting from Orange3/SciPy, template structure, communication APIs, and testing workflows. | Developer Manual |
| **[3. User Guide](3_user_guide.md)** | End-user handbook: step-by-step workflow construction, dataset inspection with Tabulator, model evaluation (ROC, Confusion Matrix), interactive visualizations (Plotly), and image processing pipelines. | User Handbook |
| **[Plugin Architecture & Migration Plan](plugin_orangered_plan.md)** | Architectural design document detailing the migration of RedOrange from a multi-process bridge into an in-process native plugin for `red-fastapi`. | Migration Specification |

---

### Documentación en Español

| Documento | Descripción | Tipo |
| :--- | :--- | :--- |
| **[1. Conceptos y Arquitectura](es/1_concepts_and_introduction_es.md)** | Fundamentos conceptuales, desacoplamiento de Orange3, gestión de memoria e integración con el canvas de Node-RED. | Arquitectura y Conceptos |
| **[2. Guía del Desarrollador](es/2_developer_guide_es.md)** | Ciclo de vida de nodos, creación de widgets personalizados, plantillas HTML y pruebas automatizadas. | Manual de Desarrollo |
| **[3. Guía del Usuario](es/3_user_guide_es.md)** | Construcción de flujos, previsualización de datos interactiva, entrenamiento de modelos y análisis multidimensional. | Manual de Usuario |
| **[Resumen del Proyecto](es/README_es.md)** | Descripción general del proyecto en español. | Resumen General |

---

## Quick Links

- **Main Repository Overview:** [README.md](../README.md)
- **License:** [Apache 2.0 License](../LICENSE)
- **Host Project (`red-fastapi`):** [Red-Fastapi on GitHub](https://github.com/tasahi/red-fastapi)

