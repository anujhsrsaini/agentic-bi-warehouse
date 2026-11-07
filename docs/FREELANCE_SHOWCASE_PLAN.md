# Freelance analytics showcase: implementation plan

## Goal and scope

Turn the existing project into a credible, easy-to-run portfolio demonstration for prospective freelance clients. It should show that a client can ask a business question, receive a grounded answer, inspect its definition and source, and see basic query safeguards. It should also show how the solution can be adapted to a client's data and business definitions.

The first release uses the existing Rich terminal interface, local DuckDB, and bundled Olist data. It does not require an API key or network access after installation. Olist is historical data from 2016–2018, not a current business dashboard. An LLM-enabled mode can remain optional and must be clearly distinguished from the repeatable demo.

**Out of scope for the showcase:** hosted service, user accounts, enterprise identity, a new web UI, universal natural-language question answering, production security certification, and full integration testing of every cloud warehouse. Treat these as potential client-specific engagements.

## 1. Establish a repeatable demo

**Goal:** A prospective client can follow a short guided walkthrough without configuring an LLM or cloud account.

1. Audit the actual no-key execution paths in `demo.py`, `src/cli.py`, `src/graph/`, and configuration. Explicitly select a deterministic local mode for the showcased questions; verify rather than assume the existing legacy or LangGraph mode provides this behavior.
2. Add an early preflight for required dependencies and bundled Parquet files, with concise instructions to fix missing prerequisites. Clearly separate package installation from running offline.
3. Simplify the menu around a 3–4 minute story: sales by state, late deliveries by state, an ambiguous question that asks for clarification, and a blocked unsafe query. Retain custom questions and access to executed SQL, but label unsupported or exploratory requests accurately.
4. Use historical dates or state the dataset's coverage. Remove unverified latency promises and claims of root-cause analysis; descriptive associations are not proof of cause.
5. Document tested Windows and Linux setup and run commands, including optional LLM configuration. State Python and dependency prerequisites and explain the limits of the offline question set.

**Acceptance:** In a fresh environment, follow the README from installation through launch. With API keys unset and network disabled after installation, all scripted examples run consistently; ambiguity asks for clarification and unsupported requests do not claim a certified answer. Missing data produces an actionable message. Record tested OS, Python version, and exact commands.

## 2. Make a small set of answers demonstrably correct

**Goal:** Demonstrate a defined set of useful calculations rather than promise correct answers to every question.

1. Agree and document a small metric and dimension matrix, initially GMV, order count, average order value, average review score, and late delivery rate. For each, specify its formula, grain, date, status filters, denominator, null handling, and allowed breakdowns. Review `config/semantic_layer.yaml` and actual SQL together; business meaning takes precedence over a convenient implementation.
2. Remove misleading synonyms, including treating review score as NPS or late-delivery rate as on-time delivery rate. Make ambiguous terms such as revenue request clarification where necessary.
3. Add a small independently calculated fixture containing multiple items and payments per order, canceled orders, missing delivery dates, and relevant reviews. Calculate expected values independently of the implementation. Test each showcased metric and supported breakdown against these expectations, including fan-out cases.
4. Guard the tested combinations: when a join or dimension is not known to be safe, explain that the question is unsupported or request clarification. Do not imply that every possible join is fan-out safe.
5. Replace any fixed or inferred lineage statements in `src/engine/lineage.py` with information supported by the executed SQL and available schema. If a trace cannot be established, explicitly mark it unavailable.

**Acceptance:** All five chosen metrics and the guided questions match independent expected results on the fixture and relevant Olist checks. Tests cover the defined edge cases. Unsupported combinations do not receive a certified label, and explanations do not invent filters or sources.

## 3. Show practical security boundaries

**Goal:** Demonstrate that the local assistant applies useful safeguards, while accurately describing their limits.

1. Fix the no-op sensitive-column branch in `src/security/ast_validator.py`. For the showcase, prefer rejecting sensitive projections and unsafe wildcard queries over promising general-purpose masking. Use schema-aware checks where available and fail closed when the system cannot safely determine exposure; ensure permitted aggregate queries still work.
2. Verify the existing read-only, table-allowlist, single-statement, external-file access, and query-limit checks on the actual demo execution path. Make the unsafe-query walkthrough show a clear rejection.
3. Test direct and qualified columns, aliases, expressions, CTEs, wildcards, disallowed tables and commands, alongside ordinary permitted queries. Specify which dialects and configurations the tests cover.
4. Explain in the README that SQL checks are a defense layer for this demonstration. Real client deployments need appropriately scoped database accounts and database-enforced access policies; tailor them to the client.

**Acceptance:** The demonstrated attacks and representative sensitive-column cases are blocked; supported aggregate examples work. Documentation makes no claim that AST validation alone provides enterprise authorization or comprehensive privacy protection.

## 4. Add a lightweight business handbook and answer card

**Goal:** Make answers understandable to nontechnical clients and show how their own definitions can be incorporated.

1. Add three short guides under a `docs/` knowledge directory: sales and orders, delivery, and reviews. Include metric meaning, formula and filters, supported breakdowns, a sample question, and known limitations. Link each guide to the actual semantic configuration.
2. Add a small local structured caveat file keyed to metrics or specific demo conditions. The application attaches applicable entries deterministically; it does not depend on an LLM remembering to mention them. For example, display that Olist covers historical years and that review ratings are not NPS.
3. Display a concise answer card in the CLI: result, metric definition, covered period where known, relevant caveat, and source tables. Offer the actual executed SQL as details. Use explicit unknown/unavailable fields when provenance cannot be established.
4. Label a result as governed only when it actually used a supported deterministic metric path. Clearly distinguish optional exploratory answers. Apply the same truthful labeling to MCP responses if that path is shown in the portfolio.

**Acceptance:** Every guided metric has a matching guide, the shown definition matches the executed calculation, applicable caveats appear, and a reviewer can follow a result to its real source and SQL. No invented owner, validation, or lineage claims appear.

## 5. Make evaluation and CI credible

**Goal:** Make the reported evidence reproducible and useful to a prospective client.

1. Audit `eval/golden_dataset.yaml` and `eval/benchmark_runner.py`: remove hard-coded semantic precision, correctly evaluate cases that specify SQL expectations, and grade diagnostic cases explicitly rather than merely checking that text exists.
2. Report actual numerator and denominator, selected mode, dataset, environment, and reproducible command. Separate correctness, security checks, and any timing measurements. Do not present the small project dataset as an official Spider benchmark.
3. Return a nonzero process exit when a required check fails; verify this with a deliberate failing fixture or equivalent test. Ensure CI runs the same documented demo mode and meaningful tests.
4. Remove or qualify unsupported 100%, throughput, and latency claims in the README, CLI and portfolio materials. Publish measurements only when reproduced with recorded conditions and sample sizes.

**Acceptance:** A fresh run computes all displayed scores from cases, a deliberate required failure fails the command and CI, and the portfolio references the command and its scope. Independent fixture tests remain separate from the showcase narrative.

## 6. Package the work for Upwork

**Goal:** Help a client quickly understand the business problem, see the working demo, and understand how to engage you.

1. Rewrite the README opening in buyer language: problem, example question, what the demo returns, who it helps, setup, and limitations. Keep detailed architecture available further down or linked separately.
2. Update `docs/portfolio/FREELANCE_PROFILE.md` with a copy-ready project description: business problem, what you built, demonstrated outcomes, tools, and how it can be tailored. Label it as a portfolio demo; do not invent a client, deployment, ROI, or endorsement.
3. Update `docs/portfolio/TECHNICAL_CASE_STUDY.md` with situation, demonstration, implementation, reproducible evidence, limitations, and a client adaptation example. Explain a query-guardrail failure and the response in plain language.
4. Prepare a 2–3 minute recording script using only tested demo prompts: business problem, one answer and definition, a clarification, a blocked query, and the customization offer. Capture the video and screenshots after the implementation works; use placeholders until real links exist.
5. Describe an engagement path: discover the client's data and KPI definitions, build a scoped proof of concept, validate with the client's domain expert, then tailor deployment and access controls. Avoid invented prices and delivery guarantees.

**Acceptance:** A nontechnical buyer can explain the problem solved within a minute; every feature and numerical claim is supported by the repo or a reproducible run. Published copy contains no fake customer story or unmarked placeholder.

## Delivery order and checkpoints

| Stage | Work | Completion checkpoint | Rough effort |
|---|---|---|---|
| 1 | Baseline, offline launch, choose metric matrix | Clean install and guided workflow work without an API key | 0.5–1.5 days |
| 2 | Metric correctness, join boundaries, truthful lineage | Five metrics checked on independent edge-case fixtures | 1.5–3 days |
| 3 | Security safeguards and tests | Demonstrated unsafe and sensitive queries rejected | 1–2 days |
| 4 | Guides, caveats, answer card | Guided answers include correct definitions and sources | 1–2 days |
| 5 | Evaluation, CI, documentation and portfolio drafts | Reproducible evidence and client-ready written story | 1–2 days |
| 6 | Record and review demo | Tested script, recording and screenshots ready to link | 0.5–1 day |

These are rough engineering estimates, not client delivery promises. They assume the existing architecture can support the selected flows without major repair; the baseline may change the scope. Stages 2 and 3 can be worked in parallel after stage 1, while portfolio copy can be drafted early and finalized only after verification.

## Final review checklist

- Fresh setup and guided flow work without credentials or a network after installation.
- The selected metrics match independently checked results; ambiguous and unsupported cases are handled honestly.
- Sensitive access and representative unsafe SQL are rejected in the tested local configuration.
- Result definitions, caveats, sources, SQL, and lineage status reflect the actual execution.
- Automated tests and benchmark gates report real results and fail appropriately.
- README, case study, profile copy, and recording make only verified claims and identify the dataset as historical.
- Client-specific production deployment, permissions, and integrations are identified as future tailored work.
