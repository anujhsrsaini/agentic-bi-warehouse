# Agentic BI Warehouse - Architecture

**Status**: Implemented (LangGraph/Sarvam migration)  
**Dataset**: Olist Brazilian E-Commerce (550,761 rows across 8 tables)

## Overview

Governed, multi-agent analytics system for natural-language BI over the Olist warehouse. Queries flow through intent routing, entity grounding, governed SQL generation, SQLGlot AST validation, execution with bounded repair, lineage/attribution, and narrative synthesis.

## Orchestration

- **Primary engine**: LangGraph `StateGraph` workflow (`src/graph/workflow.py`, `src/graph/nodes.py`).
- **Runtime selection**: `AGENTIC_BI_ENGINE=langgraph|legacy` (`legacy` preserves the original deterministic pipeline; `langgraph` is default).
- **Public contract**: `AgenticBIOrchestrator.process_query(question, session_id) -> AgenticBIState` (`src/agents/orchestrator.py`).

## LLM Integration (Sarvam Token Factory)

- **Provider**: Sarvam Token Factory, OpenAI-compatible endpoint: `https://api.sarvam.ai/v2/chat/completions`.
- **Client stack**: `langchain-openai` / LangChain chat models (`src/llm/factory.py`), with structured outputs where used.
- **Model placement** (exact defaults):
  - `sarvam-105b`: **route / grounder / repair** (`AGENTIC_BI_LLM_MODEL_ROUTER`, `AGENTIC_BI_LLM_MODEL_GROUNDER`, `AGENTIC_BI_LLM_MODEL_REPAIR`)
  - `glm5.3-flash`: **exploratory SQL / narrative** (`AGENTIC_BI_LLM_MODEL_SQL`, `AGENTIC_BI_LLM_MODEL_NARRATIVE`)
- **Fallback behavior**: if LLM calls fail/unavailable, graph nodes fall back to deterministic router/SQL/narrative logic for reliability.

## Governance & Safety Rules

1. **Certified metrics are never LLM-authored SQL.** Certified metric queries are always compiled deterministically from `config/semantic_layer.yaml` via the semantic resolver/loader. An LLM may only assist with routing/parameter selection; compilation remains governed.
2. **All SQL is validated by SQLGlot before execution.** The AST security validator enforces single-statement `SELECT/UNION`, blocks DDL/DML/mutating operations, blocks forbidden functions/table generators (e.g., file/system access), rejects Cartesian/unconstrained joins, verifies table/CTE authorization, and clamps `LIMIT` (max 1000).
3. **Repair is bounded.** Validation/execution errors can trigger limited repair attempts; results/errors are surfaced in state.

## Graph Stages (current LangGraph flow)

| Stage | Responsibility | Notes |
|---|---|---|
| Route | Classify intent (certified metric, exploratory SQL, diagnostic why, schema/metadata, clarification) | LLM-assisted when enabled; deterministic fallback |
| Ground | Resolve Brazilian entities/filters (states, payment types, statuses, etc.) | Deterministic grounding; filters appended safely |
| Generate SQL | Certified metrics compiled from `config/semantic_layer.yaml`; exploratory SQL generated only for non-certified paths | **LLM never authors certified SQL** |
| Validate/Execute/Repair | SQLGlot AST validation, execution via warehouse connector, bounded repair loop | **All SQL validated before execution** |
| Lineage | Column-level lineage (Mermaid/ASCII) for executed SQL | Best-effort |
| Attribution | Diagnostic "why" variance/root-cause analysis for `DIAGNOSTIC_WHY` | Deterministic attribution |
| Canvas/Narrative | Result summary/chart narrative; optional LLM narrative refinement | Uses `glm5.3-flash` when enabled |

## Key Components

- **Semantic layer**: `config/semantic_layer.yaml` (source of truth for certified metrics); models/loader/resolver in `src/semantic/`.
- **Security**: `src/security/ast_validator.py` (SQLGlot AST firewall), `src/security/transpiler.py`.
- **Execution/connectors**: `src/engine/` (DuckDB default, pluggable connectors, session/pool/cache/profiler/lineage).
- **MCP**: `src/mcp/server.py` exposes governed analytics tools (`list_governed_metrics`, `get_dataset_schema`, `query_analytics_warehouse`).
- **CLI**: `src/cli.py` / `demo.py`.

## Configuration (`.env` / environment)

Copy `.env.example` to `.env` and set credentials/config as needed:

```bash
cp .env.example .env
# Required for Sarvam-backed LLM tasks (LangGraph engine):
SARVAM_API_KEY=...
```

Relevant settings (see `.env.example` / `src/core/config.py`):
- `AGENTIC_BI_ENGINE=langgraph|legacy`
- `SARVAM_API_KEY` (or `AGENTIC_BI_LLM_API_KEY`)
- `AGENTIC_BI_LLM_BASE_URL=https://api.sarvam.ai/v2`
- `AGENTIC_BI_LLM_MODEL=sarvam-105b`
- `AGENTIC_BI_LLM_MODEL_ROUTER=sarvam-105b`
- `AGENTIC_BI_LLM_MODEL_GROUNDER=sarvam-105b`
- `AGENTIC_BI_LLM_MODEL_SQL=glm5.3-flash`
- `AGENTIC_BI_LLM_MODEL_REPAIR=sarvam-105b`
- `AGENTIC_BI_LLM_MODEL_NARRATIVE=glm5.3-flash`
- LLM controls: temperature/timeout/retries/max tokens/reasoning effort.

## Data & Stack

- **Data**: 8 Olist Parquet tables in `data/` (`orders`, `order_items`, `order_payments`, `order_reviews`, `customers`, `products`, `sellers`, `category_translation`).
- **Core stack**: Python 3.10+, DuckDB, PyArrow, SQLGlot, Pydantic, PyYAML, Rich, MCP/FastMCP, LangGraph, LangChain, `langchain-openai`.
