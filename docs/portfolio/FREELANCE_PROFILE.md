# Freelance profile and project description

These drafts describe a personal portfolio project. Adjust the profile to reflect your own experience and services before publishing.

## Suggested headline

AI and Data Engineer | Business Analytics Assistants and SQL

## Profile summary

I build practical analytics tools that help teams ask questions about their data and understand how the answers were calculated. I can help define key business metrics, build a scoped data assistant, and add safeguards suited to the database and users involved.

My portfolio project uses historical e-commerce data to demonstrate a local analytics assistant. It shows sales, order, delivery, and review metrics alongside their definitions, data sources, caveats, and SQL. It also illustrates how to clarify an ambiguous business term and reject an unsafe query.

For a client project, I would start with the questions that matter, the available data, and the people who understand the business. From there I can build and validate a tailored prototype and plan the appropriate integration and access controls.

## Portfolio project entry

**Title:** Business Analytics Assistant for E-commerce Data

**Project type:** Personal portfolio demonstration

**Description:**

I built a local analytics demo that turns a small set of business questions into defined calculations over a real historical e-commerce dataset. A viewer can compare sales or late deliveries by state, inspect an average order value or review score, and see the definition, source tables, caveats, and SQL behind the answer.

The demo also asks for clarification when “revenue” could mean different things and blocks an example of an unsafe SQL command. It uses Python, DuckDB, Parquet, a YAML semantic layer, and SQLGlot query checks. The guided examples run locally without an AI model or cloud credentials after installation.

**Client relevance:** The same approach can be tailored to a company's approved metrics and data, with its own access rules and a validated set of questions. Database permissions and deployment safeguards must be designed for the client's environment.

**Project link:** https://github.com/anujhsrsaini/agentic-bi-warehouse

**Case study:** [Technical case study](TECHNICAL_CASE_STUDY.md)

## Services this work can support

- Define business metrics and document how they are calculated.
- Build a local proof of concept for a small set of analytics questions.
- Review SQL generation and add tested query validation rules.
- Integrate an assistant with a client's approved data source and permissions as a separately scoped engagement.

## Questions for a first client conversation

1. What decisions or recurring questions are taking the most time to answer?
2. Which three to five metrics must be correct, and who can validate their definitions?
3. Where is the data, and can a safe sample or read-only test environment be provided?
4. Who needs access, and which data must remain restricted?
5. How will the team review the prototype's answers and decide whether to expand it?

## Suggested engagement sequence

Start with a discovery session, agree on a small set of questions and definitions, build a scoped prototype, and review results with a business owner. If it is useful, agree separately on integration, security, deployment, maintenance, and any broader analytics coverage.
