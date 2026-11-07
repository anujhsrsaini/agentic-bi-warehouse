# Case study: a local business analytics assistant

**Project type:** Personal portfolio demo

**Dataset:** Historical Olist Brazilian e-commerce data, 2016–2018
**Repository:** [agentic-bi-warehouse](https://github.com/anujhsrsaini/agentic-bi-warehouse)

## The problem

Business teams often need quick answers from data but rely on someone else to write the SQL. An analytics assistant can help, but the answer is only useful if people understand what a metric means and can inspect how it was calculated. Terms such as “revenue” can also have more than one definition.

This portfolio project explores a small, reviewable version of that workflow. It does not claim to be deployed for a customer or to have delivered customer time or cost savings.

## The demonstration

A viewer opens the terminal and selects “What is GMV by customer state?” The assistant executes a defined calculation over local sample data and shows the result, metric description, formula, filters, source tables, caveats, and actual SQL. The menu also includes late deliveries, delivered orders, average order value, and review score.

Two additional interactions show the limits of automated answers:

- **Ambiguous question:** “Show revenue” prompts for clarification because item sales and payments can mean different things.
- **Unsafe query:** An attempted `DROP TABLE orders` is rejected by the SQL validator before execution.

The menu supports a deliberately limited set of questions. It does not use an LLM or network connection after installation and does not claim to answer arbitrary business questions.

## What was built

| Component | Role |
| --- | --- |
| DuckDB and bundled Parquet | Run the guided examples against a local multi-table e-commerce dataset. |
| YAML semantic configuration | Define metric names, formulas, filters and available dimensions. |
| SQLGlot validator | Inspect SQL and reject configured risky patterns before the demo executes it. |
| CLI and caveat registry | Present results and attach relevant explanations and limitations. |
| Tests | Exercise project-specific correctness and safeguards for the cases included in the repository. |

The guided path is in [`src/cli.py`](../../src/cli.py), metric definitions are in [`config/semantic_layer.yaml`](../../config/semantic_layer.yaml), and the validator is in [`src/security/ast_validator.py`](../../src/security/ast_validator.py). See the [README](../../README.md) for setup and test commands.

## Evidence and limits

Anyone can run the examples and tests locally using the commands in the README. The dataset is historical, so the results are not current business indicators. The metrics use the definitions in this demonstration; another business may define revenue, orders, or delivery performance differently.

SQL validation is one safety layer, not complete authorization. Client deployments also need suitable database-level permissions, protection for sensitive data, and tests against their actual schema and workloads. The repository includes additional connectors and agent-oriented components, but the guided showcase is local DuckDB; it should not be interpreted as proof of production readiness across other warehouses.

## How this can be adapted

A client engagement could start by identifying a few high-value questions, agreeing on definitions with the relevant business owner, and validating calculations against known results. The prototype could then be adapted to a client-provided sample or read-only data source. Any production integration, identity and permissions, cost controls, and support arrangements would be scoped to the client's environment.
