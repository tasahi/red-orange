---
title: Red-Cyan Semantic Prompt & Agent Pack Integration
document_type: Architecture Specification
project: red-orange
target: Integration of Red-Cyan prompt DAGs and agent nodes into Red-Orange React Flow canvas
status: Implemented (Phase 1 & Phase 2)
date: October 2026
---

# Red-Cyan Semantic Prompt & Agent Pack Integration

## 1. Overview

`red-orange` has expanded its visual dataflow capabilities beyond classical tabular data mining and ML models by integrating **`red-cyan`**'s semantic prompt transformation and agent node pack directly into the shared **React Flow** canvas.

This delivers a unified **Neuro-Symbolic Natural Language Processing Platform**:
- Quantitative nodes (`OR Data`, `OR Transform`, `OR Model`) process numerical datasets and compute statistical distributions, cluster assignments, and predictive scores.
- Semantic nodes (`Cyan Prompt`) consume tabular metrics and feature summaries, executing LLM-driven prompt transformations to generate natural language explanations and hypotheses.

```mermaid
flowchart LR
    subgraph DataMining ["red-orange Tabular Pipeline"]
        N1["or-file-loader<br/>(Iris Data)"] --> N2["or-data-sampler<br/>(70% Sample)"]
        N2 --> N3["or-tree<br/>(Decision Tree)"]
    end

    subgraph SemanticAnalysis ["red-cyan Prompt Pipeline"]
        N3 -->|"Model Metrics / Importances"| C1["cyan-prompt-transform<br/>(Prompt Transform)"]
        C1 --> C2["cyan-synthesis-node<br/>(Synthesis & Insight)"]
    end
```

---

## 2. Integrated Palette & Catalog Specification

The node catalog (`src/flow/catalog.ts`) now includes the official **"Cyan Prompt"** category with accent color `#06B6D4`:

| Node Type | Category | Inputs | Outputs | Description |
| :--- | :--- | :--- | :--- | :--- |
| `cyan-prompt-transform` | Cyan Prompt | Dynamic | 1 | Executes LLM prompt transformations with live token preview. |
| `cyan-tabular-context` | Cyan Prompt | 1 | 1 | Serializes upstream tabular DataFrames into LLM prompt context. |
| `cyan-synthesis-node` | Cyan Prompt | 1 | 0 | Synthesizes multi-node inputs into knowledge base artifacts. |

---

## 3. Dynamic React Flow Node: `CyanPromptNode`

Unlike standard static nodes, `CyanPromptNode` (`src/flow/CyanPromptNode.tsx`) features dynamic reactivity:

1. **Reactive Handle Inferrer (`cyanViewModel.ts`)**:
   - Parses the Jinja2 prompt template in real time for `{{ inputs.<variable> }}`.
   - Automatically computes vertical handle positions and mounts labeled target handles (`in-<variable>`) along the left edge.
2. **In-Canvas Template Editor**:
   - Allows on-the-fly editing of prompt instructions, model parameters (`gpt-4o`, `claude-3-5`), and temperature.
3. **Real-time Output Preview**:
   - Displays streaming output text and markdown summaries directly on the canvas surface.
4. **Static & Dynamic Attribute Chips**:
   - Visual badges for static tags (`#churn`, `#finance`) and dynamic inference properties (`sentiment: negative`).

---

## 4. Drag-and-Drop & Type Contracts

- **Drag & Drop**: `instantiateDroppedNode` in `paletteDnd.ts` checks `category === "Cyan Prompt"` and instantiates a `cyanPromptNode` on drop.
- **Data Contracts**: `types.ts` defines `SemanticPayload` and `NodeAttributeSet`, ensuring cross-node contract fidelity across wires.

