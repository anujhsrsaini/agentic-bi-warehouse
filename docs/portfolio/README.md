# Portfolio Content Plan — Governed NL-to-Analytics Agent

**Project:** `agentic-bi-warehouse` (governed NL-to-analytics agent / poly-warehouse BI engine)  
**Audience:** Hiring managers, founders, data/platform teams, and freelance clients evaluating AI data engineering work  
**Goal:** Showcase credible, repo-backed engineering for governed Text-to-SQL/analytics agents — not generic AI demos.

## Deliverables (repo-local drafts)

| File | Purpose | Status |
|---|---|---|
| [`LINKEDIN_POST.md`](./LINKEDIN_POST.md) | Short LinkedIn post + 60–90s video hook/script beats | Draft |
| [`FREELANCE_PROFILE.md`](./FREELANCE_PROFILE.md) | Upwork/Contra/freelance project bullets, service offerings, profile copy | Draft |
| [`TECHNICAL_CASE_STUDY.md`](./TECHNICAL_CASE_STUDY.md) | 1–2 page technical case study outline/content draft | Draft |

## Positioning (use consistently)

- **Category:** Governed NL-to-analytics / agentic BI engineering.
- **Core claim (verifiable in repo):** Natural-language analytics with deterministic governance — certified metrics compile from YAML, SQL is AST-validated before execution, and the system supports local DuckDB plus a poly-warehouse abstraction design.
- **Differentiators:** YAML semantic layer, SQLGlot AST guardrail, LangGraph orchestration, Sarvam Token Factory (OpenAI-compatible) integration, reflexion/bounded repair, legacy deterministic fallback, MCP exposure.
- **Proof points to reference:** Olist Brazilian E-Commerce dataset (550k+ rows, 8 tables) as a real-world demo dataset; benchmark harness/results documented in repo (link to exact section when publishing); CLI/MCP/demo entry points.

## Claims & evidence guardrails

- **Do not claim:** production deployments, customer ROI, time/cost savings, accuracy/latency improvements beyond what is reproducibly documented in the repo, or endorsements.
- **When citing metrics:** use “project benchmark harness results (see [benchmark link/section])” and include the commit/date/environment if published.
- **Use placeholders:** `[Demo video URL]`, `[GitHub repo URL]`, `[Case study URL]`, `[MCP demo URL]`, `[Benchmark results link]`, `[Live demo URL if any]`.

## Suggested publish sequence

1. Finalize README/demo GIF or 60–90s screen recording.
2. Publish LinkedIn post with video hook and repo link.
3. Add project to Upwork/Contra with 2–3 outcome-focused bullets grounded in repo capabilities.
4. Publish technical case study (GitHub Pages, Notion, or repo `docs/`) and link from profiles.

## Suggested GitHub topics/tags

Use a focused set (GitHub recommends relevant topics; avoid over-tagging):

```text
agentic-ai
text-to-sql
nl-to-sql
analytics-engineering
business-intelligence
semantic-layer
sqlglot
langgraph
duckdb
mcp
model-context-protocol
data-governance
llm-security
fastmcp
data-warehouse
python
```

**Optional (if accurate for the published state):** `sarvam-ai`, `openai-compatible`, `olap`, `parquet`, `postgresql`, `snowflake`, `bigquery`, `clickhouse` (use warehouse tags only where connector support is implemented/documented clearly).