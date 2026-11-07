"""Local Streamlit adapter for guided and experimental analytics workflows."""

from threading import RLock

from src.agents.orchestrator import AgenticBIOrchestrator
from src.agents.product_cohorts import matches_product_cohort_question
from src.agents.state import AgenticBIState
from src.cli import EXAMPLES, _caveats, _normalize, _source_tables
from src.core.config import settings
from src.engine.connectors.duckdb_connector import DuckDBConnector
from src.engine.session import WarehouseSession
from src.llm.factory import llm_enabled
from src.security.ast_validator import ASTSecurityValidator
from src.semantic.loader import SemanticLayerLoader
from src.semantic.resolver import SemanticQueryResolver

PRODUCT_QUESTION = "Top 10 products and their breakdown of new vs repeat customers purchases/revenue and order splits"
GUIDED_QUESTIONS = tuple(item[0] for item in EXAMPLES.values()) + (PRODUCT_QUESTION,)
_QUERY_LOCK = RLock()


def execute_question(question: str, mode: str, protect_customer_ids: bool) -> dict:
    """Return display data; serialize temporary process-wide policy changes.

    Streamlit runs sessions in threads. Holding the shared lock until the query
    finishes and restoring the setting prevents one session's choice from being
    used by another Streamlit session. This local demo is not an auth boundary.
    """
    with _QUERY_LOCK:
        previous = settings.customer_identifier_protection
        settings.customer_identifier_protection = protect_customer_ids
        try:
            if mode == "auto":
                known = any(_normalize(item) == _normalize(question) for item in GUIDED_QUESTIONS)
                mode = "guided" if known or matches_product_cohort_question(question) else "ai"
            if mode == "guided":
                return _guided(question)
            if mode != "ai":
                raise ValueError("Unknown analytics mode")
            if not llm_enabled():
                return {"error": "This question needs a Sarvam key in your local .env file or Streamlit secrets and the LangGraph engine. You can still use the example questions."}
            return _from_state(AgenticBIOrchestrator().process_query(question))
        finally:
            settings.customer_identifier_protection = previous


def _guided(question: str) -> dict:
    if matches_product_cohort_question(question):
        return _from_state(AgenticBIOrchestrator().process_query(question), governed=True)
    example = next((item for item in EXAMPLES.values() if _normalize(item[0]) == _normalize(question)), None)
    if example is None:
        return {"error": "Choose one of the listed guided questions, or switch to AI mode for a different question."}
    _, metric_name, dimensions = example
    metric = SemanticLayerLoader().load().get_metric(metric_name)
    if metric is None:
        return {"error": "The metric definition is unavailable."}
    session = WarehouseSession()
    connector = session.get_connector()
    sql = SemanticQueryResolver().resolve_metric_query(metric_name, dimensions=dimensions)
    sql, _ = ASTSecurityValidator().validate_and_sanitize(sql, dialect="duckdb")
    result = connector.execute_query(sql)
    return {
        "summary": _metric_summary(metric_name, result.to_pylist()),
        "method": metric.description,
        "sql": sql,
        "data": result.data,
        "sources": _source_tables(sql),
        "caveats": _caveats(metric_name),
        "label": "Defined metric",
    }


def _metric_summary(metric_name: str, rows: list[dict]) -> str:
    if not rows:
        return "No matching records were found for this question."
    row = rows[0]
    value = row.get(metric_name)
    if not isinstance(value, (int, float)):
        return "The matching results are shown below."
    if metric_name == "gmv" and row.get("customer_state"):
        return f"{row['customer_state']} has the highest recorded item sales, at R$ {value:,.2f}."
    if metric_name == "delivery_delay_rate" and row.get("customer_state"):
        return f"{row['customer_state']} has the highest reported late-delivery rate, at {value:,.2f}%."
    if metric_name == "total_orders":
        return f"The dataset contains {value:,.0f} delivered orders."
    if metric_name == "aov":
        return f"The average item value per delivered order is R$ {value:,.2f}."
    if metric_name == "avg_review_score":
        return f"The average review score is {value:,.2f} out of 5."
    return "The matching results are shown below."


def _from_state(state: AgenticBIState, governed: bool = False) -> dict:
    if state.clarification_prompt:
        return {"clarification": state.clarification_prompt}
    if state.execution_error:
        return {"error": state.execution_error}
    if state.execution_result is None:
        return {"error": "The assistant did not return a result. Try rephrasing your question."}
    summary = state.summary_narrative
    if governed:
        rows = state.execution_result.to_pylist()
        if rows:
            top = rows[0]
            summary = (
                f"The highest-revenue product in this sample generated R$ {top['revenue']:,.2f} "
                f"across {top['orders']:,} orders. Of those orders, {top['new_order_pct']:.2f}% "
                f"were customers' first observed orders and {top['repeat_order_pct']:.2f}% came from returning customers. "
                "The product ID and the full breakdown are shown below."
            )
    return {
        "summary": summary,
        "method": "Products are ranked by item revenue, excluding freight and canceled orders. New means the customer's first observed non-canceled order in the dataset; repeat means a later order. Percentages use orders containing each product. Product names and purchases before the dataset are not available." if governed else "The assistant generated this answer from the SQL and result shown below. Review its interpretation and assumptions.",
        "sql": state.validated_sql,
        "data": state.execution_result.data,
        "sources": _source_tables(state.validated_sql) if state.validated_sql else [],
        "caveats": ["Olist is historical data from 2016–2018; it does not represent current performance."],
        "label": "Defined product analysis" if governed else "Exploratory analysis · review before use",
    }
