# Freelance Profile & Project Content — Governed NL-to-Analytics Agent

**Use for:** Upwork, Contra, Topmate/service pages, portfolio sites, LinkedIn Featured/Projects.  
**Tone:** Professional, specific, no unverifiable client claims.

## Profile Headline Options

1. **AI/Data Engineer | Governed Text-to-SQL & Agentic BI (LangGraph, SQLGlot, DuckDB, MCP)**
2. **Freelance Data/AI Engineer | Semantic Layers, Safe NL-to-Analytics, DuckDB & Warehouse Integrations**
3. **Agentic Analytics Engineer | Governed NL-to-SQL, AST Guardrails, Semantic Metrics, MCP Tools**

## Profile Summary (short)

I build governed NL-to-analytics systems that turn natural-language questions into safe, reviewable data workflows. My work focuses on semantic layers, SQL AST guardrails, agent orchestration, and practical analytics execution (DuckDB/local-first with warehouse-oriented abstractions). I prioritize deterministic business logic, security checks before execution, and clear technical documentation.

## Profile Summary (detailed)

I’m a freelance AI/data engineer specializing in governed agentic BI and Text-to-SQL systems. I help teams move beyond demo-only SQL generation by adding the controls needed for trustworthy analytics: YAML/semantic metric definitions, SQLGlot AST validation, read-only/query safeguards, bounded repair loops, and transparent execution paths.

In `agentic-bi-warehouse`, I implemented a governed NL-to-analytics prototype using LangGraph, a YAML semantic layer for certified metrics, SQLGlot AST guardrails, DuckDB/Parquet execution over the Olist e-commerce dataset, MCP tool exposure, reflexion-style bounded repair, and a legacy deterministic fallback. The project also includes Sarvam Token Factory (OpenAI-compatible) integration for selected LLM-assisted steps, while keeping certified metric SQL compiled from configuration.

**Best fit projects:** governed Text-to-SQL copilots, semantic metric layers, agentic analytics workflows, DuckDB-based analytics prototypes, MCP data tools, and architecture/design reviews for LLM data access.

*Links:* `[GitHub repo URL]` · `[Technical case study URL]` · `[Demo video URL]` · `[Calendar/booking URL]`

## Portfolio Project Entry (Upwork/Contra “Project”)

**Project title:** Governed NL-to-Analytics Agent — LangGraph + YAML Semantic Layer + SQLGlot Guardrails + DuckDB/MCP

**One-line description:** Built a governed natural-language analytics prototype that compiles certified metrics from YAML, validates SQL with SQLGlot AST checks before execution, and runs on DuckDB with MCP tool exposure.

**Project description (paste-ready):**
Designed and implemented a repo-local governed NL-to-analytics/agentic BI system to address common Text-to-SQL failure modes: ambiguous business logic, unsafe SQL generation, and join/filter mistakes.

Key implementation details (verifiable in the repository):
- **LangGraph orchestration:** multi-stage workflow for intent routing, entity grounding, SQL generation/planning, validation, execution, lineage/attribution, and narrative synthesis.
- **YAML semantic layer:** certified business metrics are defined in configuration and compiled deterministically; LLM-assisted steps do not author certified metric SQL.
- **SQLGlot AST security/firewall:** SQL is parsed and validated before execution (read-only/query shape controls, blocked risky functions/patterns, and safeguard constraints such as limits/join checks as implemented).
- **DuckDB + Parquet execution:** local analytics over the Olist Brazilian E-Commerce dataset (550k+ rows across 8 tables) for reproducible demos.
- **Poly-warehouse abstraction design:** architecture supports extending beyond local DuckDB to warehouse connectors (see repo docs/implementation status).
- **MCP integration:** exposes governed analytics capabilities as MCP tools for agent/client integrations.
- **Reliability patterns:** bounded reflexion/repair loop for validation/runtime issues and a legacy deterministic fallback mode.
- **LLM integration:** Sarvam Token Factory via OpenAI-compatible endpoint for selected routing/SQL/narrative tasks (configurable), with deterministic governance preserved.

**Tech stack:** Python, LangGraph, LangChain/OpenAI-compatible client, Sarvam Token Factory, SQLGlot, DuckDB, PyArrow/Parquet, YAML semantic modeling, Pydantic, FastMCP/MCP, Rich CLI.

**Links/placeholders:** `[GitHub repo URL]` · `[Demo video URL]` · `[Technical case study URL]` · `[Benchmark results link]`

## Project Bullets (choose 3–5 per platform)

- Built a **governed NL-to-analytics agent** using **LangGraph** that routes natural-language questions through grounding, SQL generation, AST validation, execution, and response synthesis.
- Implemented a **YAML semantic layer** for certified metrics so business logic is explicit and **certified SQL is compiled deterministically from config** rather than authored by an LLM.
- Added a **SQLGlot AST guardrail** to validate queries before execution, enforcing read-only/safety constraints and reducing risky SQL patterns in an agentic workflow.
- Delivered a reproducible **DuckDB + Parquet** analytics demo over the **Olist e-commerce dataset (550k+ rows, 8 tables)**, with architecture/docs for a **poly-warehouse** abstraction.
- Exposed governed analytics capabilities via **MCP tools** and integrated **Sarvam Token Factory (OpenAI-compatible)** for selected LLM-assisted steps with **bounded reflexion/repair** and deterministic fallbacks.

## Service Offerings (packages)

### 1) Governed Text-to-SQL / Agentic BI Prototype
**For:** Teams exploring an internal data copilot or NL analytics assistant.  
**Includes:**
- Discovery of key metrics, tables, and safety requirements
- Semantic metric definitions (YAML/model) for priority KPIs
- NL-to-SQL/analytics workflow design (LangGraph or equivalent)
- SQL validation/guardrail layer (AST checks, read-only constraints, limits)
- Local demo (DuckDB/Parquet or client-provided sample data)
- Handoff docs and extension plan

**Typical deliverables:** working prototype repo/module, metric config, guardrail rules, demo script, architecture notes.  
**Placeholder:** `[Timeline]`, `[Starting price / hourly rate]`

### 2) Semantic Layer + Metric Governance Setup
**For:** Teams with inconsistent KPI logic across dashboards, notebooks, and ad hoc SQL.  
**Includes:**
- KPI inventory and definitions (formulas, filters, grain, caveats)
- Semantic layer structure (YAML/config or client stack equivalent)
- Synonyms/dimensions/join guidance for NL querying
- Validation examples and documentation for analysts/engineers

**Typical deliverables:** semantic config, metric catalog, test queries/examples, governance checklist.  
**Placeholder:** `[Timeline]`, `[Starting price / hourly rate]`

### 3) SQL Safety & AST Guardrail Review
**For:** Teams already generating SQL with LLMs and needing stronger controls.  
**Includes:**
- Review of current prompt/agent SQL generation flow
- Threat/failure-mode analysis (mutation, unsafe functions, unbounded scans, join issues)
- SQLGlot-based validation design or implementation recommendations
- Policy rules, test cases, and observability/logging recommendations

**Typical deliverables:** guardrail design, policy spec, sample validator code/tests, prioritized remediation plan.  
**Placeholder:** `[Timeline]`, `[Starting price / hourly rate]`

### 4) MCP / Agent Tooling for Analytics
**For:** Teams connecting Claude/Cursor/agent clients to governed data workflows.  
**Includes:**
- MCP tool schema design for safe analytics actions
- Integration with existing query/semantic/validation layers
- Tool descriptions, permissions/safety boundaries, and demo client setup
- Documentation for extension and maintenance

**Typical deliverables:** MCP server/tools, config, demo instructions, integration notes.  
**Placeholder:** `[Timeline]`, `[Starting price / hourly rate]`

## Proposal Snippet (customize per job)

Hi `[Client name]` — I can help you build a **governed NL-to-analytics workflow** rather than a plain Text-to-SQL demo.

My approach is to define certified metrics in a semantic layer, generate/route queries through an agent workflow, and run **SQL AST validation before execution** (SQLGlot) so unsafe or malformed queries are caught early. I’ve implemented this pattern in a public-style project using LangGraph, YAML metric definitions, DuckDB, MCP tools, and bounded repair/fallback logic.

For your use case, I’d start by confirming: the target warehouse/tables, priority KPIs, user permissions, and what “safe” means in your environment (read-only, row limits, approved tables/functions, PII constraints). Then I can propose a phased prototype.

Relevant work: `[GitHub repo URL]` · `[Case study URL]`

## Screening Questions to Ask Clients

- Which warehouse/data source will the agent query first, and can you provide a read-only sample/schema?
- Which 3–10 metrics/questions must be correct on day one?
- What governance constraints apply (approved tables, PII, row limits, cost controls, user roles)?
- Should answers use certified metrics only, or also allow exploratory SQL with stricter guardrails?
- How will success be evaluated (benchmark set, SME review, latency/cost targets, safety tests)?