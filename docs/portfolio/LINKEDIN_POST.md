# LinkedIn Post — Governed NL-to-Analytics Agent

**Format:** Short, credible, technical-but-readable.  
**Target length:** ~900–1,300 characters (adjust to taste).  
**CTA:** Watch 60–90s demo + view repo/case study.

## 60–90s Video Hook (record this first)

**Goal:** Show a governed analytics agent answering a natural-language question safely, with evidence of governance — not just a SQL generation trick.

| Time | Visual | Voiceover / on-screen text |
|---|---|---|
| 0:00–0:08 | Terminal/cockpit with repo name + architecture snippet | “Text-to-SQL demos break when business logic, joins, and security matter. I built a governed NL-to-analytics agent to explore that problem.” |
| 0:08–0:22 | User asks: “GMV by customer state for delivered orders” (or similar repo-supported query) | “A natural-language question enters a LangGraph workflow. Certified metrics are compiled from a YAML semantic layer — the LLM doesn’t author certified SQL.” |
| 0:22–0:38 | Show semantic layer excerpt / metric definition (brief flash) + generated SQL | “The metric definition lives in config, so business logic is explicit and reviewable.” |
| 0:38–0:55 | Show SQLGlot AST guardrail/validation step (logs, code path, or diagram) | “Before execution, SQL passes through a SQLGlot AST guardrail: read-only checks, blocked risky functions, join/limit controls.” |
| 0:55–1:10 | Query executes on DuckDB over Olist Parquet dataset; result table/chart appears | “Execution runs against a real e-commerce dataset in DuckDB. The same design targets a poly-warehouse abstraction.” |
| 1:10–1:20 | Show repair/reflexion path OR MCP tool call (optional quick cut) | “If validation/execution fails, the agent can attempt bounded repair. The project also exposes governed tools via MCP.” |
| 1:20–1:30 | End card: repo + case study links | “Repo, architecture notes, and benchmark harness are in the link. Feedback welcome.” `[Demo video URL]` `[GitHub repo URL]` |

**Recording checklist:** use a real query supported by the demo; avoid editing that implies unverifiable speed/accuracy claims; include a visible disclaimer if benchmark numbers appear (“project benchmark harness; see repo for setup”).

## Post Draft (Option A — engineering credibility)

Most NL-to-SQL demos look good until you ask for governed business metrics.

I’ve been building `agentic-bi-warehouse` — a governed NL-to-analytics agent over a real e-commerce dataset (Olist, 550k+ rows / 8 tables) — to explore how to make agentic BI safer and more deterministic.

What’s implemented in the repo:
- **LangGraph workflow** for routing, grounding, SQL generation, validation, execution, and response synthesis
- **YAML semantic layer** as the source of truth for certified metrics (certified SQL is compiled from config, not authored by the LLM)
- **SQLGlot AST guardrail** before execution (read-only/statement controls, blocked risky patterns, limit/join safeguards)
- **DuckDB + Parquet** local execution, with a **poly-warehouse abstraction** design for broader warehouse targets
- **MCP exposure** for governed analytics tools
- **Bounded reflexion/repair** and a **legacy deterministic fallback** mode
- **Sarvam Token Factory (OpenAI-compatible)** integration for selected LLM-assisted steps

I recorded a 60–90s walkthrough showing the governance path end-to-end: [Demo video URL]

Repo + architecture notes: [GitHub repo URL]  
Technical case study: [Case study URL]

If you’re building agentic analytics, data copilots, or governed Text-to-SQL systems, I’d value your feedback on the guardrail design.

#AIEngineering #DataEngineering #TextToSQL #LangGraph #DuckDB #SQL #MCP #LLMOps

## Post Draft (Option B — freelance/client angle)

If you want an AI analytics assistant, the hard part isn’t generating SQL — it’s making the answers governed.

I built `agentic-bi-warehouse`, a governed NL-to-analytics prototype, to demonstrate a safer pattern for agentic BI:

- Certified metrics compiled from a **YAML semantic layer**
- **SQLGlot AST validation** before any query runs
- **LangGraph** orchestration with bounded repair/reflexion
- **DuckDB** local analytics over real e-commerce data (Olist dataset)
- **MCP** tools + poly-warehouse-oriented architecture
- Optional LLM-assisted routing/SQL/narrative via **Sarvam Token Factory (OpenAI-compatible)**

60–90s demo: [Demo video URL]  
GitHub: [GitHub repo URL]

I’m available for freelance projects around governed Text-to-SQL, semantic layers, agentic BI workflows, and DuckDB/MCP integrations. DM me or comment “case study” and I’ll share the technical write-up: [Case study URL]

## Comment/CTA variants

- “I’ll share the architecture diagram + case study outline in the comments.” (then post `[Case study URL]`)
- “Happy to compare notes with anyone implementing AST guardrails for LLM-generated SQL.”
- “If useful, I can also share the benchmark harness approach used in the repo.” `[Benchmark results link]`