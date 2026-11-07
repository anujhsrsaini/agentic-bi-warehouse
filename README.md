# Business analytics assistant — local portfolio demo

This project demonstrates how a business could ask questions about its data, see how a metric is defined, and inspect the query behind the answer. It uses a sample e-commerce dataset and runs locally with DuckDB. The guided demo is designed to be repeatable without an AI model, API key, cloud account, or network connection after installation.

**A portfolio demonstration, not a client deployment.** The included Olist Brazilian e-commerce data is historical: its orders span 2016–2018. It does not represent current business performance.

## See it in action

The guided menu includes these examples:

| Business question | What it demonstrates |
| --- | --- |
| What is GMV by customer state? | Compare item sales across states, with a defined GMV calculation. |
| What is the late delivery rate by customer state? | Explore delivery performance with a stated denominator and caveat. |
| How many orders were delivered? | Count delivered orders using a defined filter. |
| What is average order value? | Inspect a defined order-level sales metric. |
| What is the average review score? | Summarize customer ratings, with a reminder that ratings are not NPS. |

The menu also shows why the word “revenue” needs clarification and demonstrates an unsafe `DROP TABLE` statement being rejected before execution. Each supported metric displays its definition, calculation, source tables, caveats and executed SQL.

The local tour recognizes the listed questions and a small clarification example; it is **not** a general-purpose chatbot. Its purpose is to demonstrate a controlled starting point that can be adapted to a client's questions and definitions.

## Run the demo

Prerequisites: Python 3.10 or later, a terminal, and internet access to install Python packages. The repository contains the sample Parquet files under `data/seed/`. Installation may take more than a minute; a cloud database or `.env` file is not required for the guided demo.

### Streamlit interface

From the project directory, install the optional web dependencies and start the local app:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[web]"
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

On macOS/Linux, use `.venv/bin/python` instead. Open the local URL shown in the terminal. The example questions work without an API key; other questions use the configured model when available. Configure `.env` as described below; questions and relevant result data may be sent to the configured provider. The customer-ID switch controls the local query validator and is not a replacement for database permissions. This is a local portfolio demo, not a hosted multi-user service.

### Terminal interface

**Windows PowerShell**

```powershell
git clone https://github.com/anujhsrsaini/agentic-bi-warehouse.git
cd agentic-bi-warehouse
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe demo.py
```

**macOS / Linux**

```bash
git clone https://github.com/anujhsrsaini/agentic-bi-warehouse.git
cd agentic-bi-warehouse
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python demo.py
```

Choose `1` for sales by state, `2` for late deliveries, `6` for the clarification example, `7` for the blocked query, and `0` to exit. The launcher reports missing dependencies or sample files and suggests how to restore them.

## How it works

1. A menu question selects a defined business metric and supported breakdown.
2. The semantic layer in [`config/semantic_layer.yaml`](config/semantic_layer.yaml) supplies the metric's formula and filters.
3. The query is inspected by a SQLGlot-based validator and executed locally with DuckDB.
4. The result is shown with its definition, source tables, caveats, and SQL so the calculation can be reviewed.

The validator rejects several risky query patterns, including mutation statements, most configured sensitive column references, and wildcard projections; `COUNT(*)` remains allowed. Customer-ID protection is optional and off by default. These checks are useful safeguards for a demo, **not a replacement for database-enforced permissions or a guarantee of security**. A client deployment requires its own read-only database access, row and column policies, cost controls, and testing appropriate to its environment.

The repository also contains an MCP server, a configurable agent workflow, and connectors for other warehouses. The guided showcase uses local DuckDB and does not establish full integration parity for those additional paths. Optional LLM-assisted components require separate credentials and configuration; see [`.env.example`](.env.example). The guided demo does not use them.

For the experimental live agent, copy `.env.example` to `.env`, put your key in `SARVAM_API_KEY`, and run `python -m src.agent_cli` using the virtual environment. The live agent accepts free-form questions and may send questions and relevant context to the configured model provider. It can fall back to deterministic behavior if a model call fails, and its results require review; it is not covered by the five-question showcase guarantee. The default router model may need adjustment for your account and its structured-output support.

The live terminal also includes a predefined, independently tested Olist workflow for `Top 10 products and their breakdown of new vs repeat customers purchases/revenue and order splits`. It ranks by item revenue, uses the first observed non-canceled order to identify new customers, and reports units, revenue and order splits. It uses exact supported phrasings and does not silently apply additional filters; other questions follow the experimental agent path.

In the live terminal agent, type `/privacy` to see the customer-ID protection setting, `/privacy on` to block queries referencing `customer_unique_id`, and `/privacy off` to allow them again. The setting is off by default and changes last only for the current process. When off, customer identifiers can appear in query results or model context; other SQL checks and any warehouse permissions still apply. For real client data, configure access according to the client's requirements.

## Verify and explore

After installing the development dependencies above, run the test suite:

```bash
python -m pytest tests/ -q
python eval/showcase_runner.py
```

Use the virtual environment's Python executable if it is not activated (on Windows, `.\.venv\Scripts\python.exe`; on macOS/Linux, `.venv/bin/python`). The showcase runner compares the five guided metric results against separately written reference SQL on the bundled dataset. Tests and evaluation measure only the cases they cover, not correctness for every possible question or production workload. The broader legacy `eval/benchmark_runner.py` is experimental and contains known failing cases; it is not the showcase acceptance gate.

- [Business metric configuration](config/semantic_layer.yaml)
- [Business handbook: sales and orders](docs/knowledge/sales-and-orders.md), [delivery](docs/knowledge/delivery.md), and [reviews](docs/knowledge/reviews.md)
- [SQL validation policy](config/security_policies.yaml)
- [Technical case study](docs/portfolio/TECHNICAL_CASE_STUDY.md)
- [Freelance profile and project description](docs/portfolio/FREELANCE_PROFILE.md)
- [Demo recording script](docs/portfolio/DEMO_RECORDING_SCRIPT.md)
- [Showcase implementation plan](docs/FREELANCE_SHOWCASE_PLAN.md)

## Adapting this for a client

A typical engagement starts with a few important questions and the tables behind them. Together, we define the metrics and permissions, build a scoped prototype on suitable sample data, validate answers with a domain expert, and decide what is needed for the client's database and deployment environment. The definitions, integrations, user interface, and safeguards can then be tailored to the actual business.

This project does not claim a customer deployment, measured customer ROI, or production certification. See [LICENSE](LICENSE) for license terms.
