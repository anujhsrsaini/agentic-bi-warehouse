"""A fixed, inspectable Olist product-cohort analysis for the local demo."""

import re

from src.agents.state import AgenticBIState, UserIntent
from src.engine.session import WarehouseSession
from src.security.ast_validator import ASTSecurityValidator


# Fixed SQL: no question text is interpolated. One row per product/order avoids
# counting a single order twice when it contains multiple units of a product.
PRODUCT_COHORT_SQL = """
WITH ordered AS (
  SELECT o.order_id,
    ROW_NUMBER() OVER (PARTITION BY c.customer_unique_id
      ORDER BY o.order_purchase_timestamp, o.order_id) AS purchase_number
  FROM orders o JOIN customers c ON o.customer_id = c.customer_id
  WHERE o.order_status <> 'canceled' AND o.order_purchase_timestamp IS NOT NULL
    AND c.customer_unique_id IS NOT NULL
), item_orders AS (
  SELECT product_id, order_id, COUNT(*) AS units, SUM(price) AS revenue
  FROM order_items GROUP BY product_id, order_id
), totals AS (
  SELECT i.product_id, SUM(i.units) AS units, SUM(i.revenue) AS revenue,
    COUNT(*) AS orders,
    SUM(CASE WHEN o.purchase_number = 1 THEN 1 ELSE 0 END) AS new_orders,
    SUM(CASE WHEN o.purchase_number > 1 THEN 1 ELSE 0 END) AS repeat_orders,
    SUM(CASE WHEN o.purchase_number = 1 THEN i.units ELSE 0 END) AS new_units,
    SUM(CASE WHEN o.purchase_number > 1 THEN i.units ELSE 0 END) AS repeat_units,
    SUM(CASE WHEN o.purchase_number = 1 THEN i.revenue ELSE 0 END) AS new_revenue,
    SUM(CASE WHEN o.purchase_number > 1 THEN i.revenue ELSE 0 END) AS repeat_revenue
  FROM item_orders i JOIN ordered o ON i.order_id = o.order_id
  GROUP BY i.product_id
)
SELECT t.product_id, COALESCE(ct.product_category_name_english, p.product_category_name, 'unknown') AS category,
  t.units, ROUND(t.revenue, 2) AS revenue, t.orders, t.new_orders, t.repeat_orders,
  t.new_units, t.repeat_units, ROUND(t.new_revenue, 2) AS new_revenue,
  ROUND(t.repeat_revenue, 2) AS repeat_revenue,
  ROUND(100.0 * t.new_orders / NULLIF(t.orders, 0), 2) AS new_order_pct,
  ROUND(100.0 * t.repeat_orders / NULLIF(t.orders, 0), 2) AS repeat_order_pct
FROM totals t LEFT JOIN products p ON t.product_id = p.product_id
LEFT JOIN category_translation ct ON p.product_category_name = ct.product_category_name
ORDER BY t.revenue DESC, t.product_id LIMIT 10
"""


CATEGORY_COHORT_SQL = """
WITH customer_orders AS (
  SELECT o.order_id, c.customer_unique_id, o.order_purchase_timestamp,
    ROW_NUMBER() OVER (PARTITION BY c.customer_unique_id ORDER BY o.order_purchase_timestamp, o.order_id) AS purchase_seq
  FROM orders o JOIN customers c ON o.customer_id = c.customer_id
  WHERE o.order_status <> 'canceled' AND o.order_purchase_timestamp IS NOT NULL
    AND c.customer_unique_id IS NOT NULL
),
cat_item_orders AS (
  SELECT COALESCE(ct.product_category_name_english, p.product_category_name, 'unknown') AS category,
    oi.order_id, oi.price
  FROM order_items oi
  JOIN products p ON oi.product_id = p.product_id
  LEFT JOIN category_translation ct ON p.product_category_name = ct.product_category_name
),
cat_cohorts AS (
  SELECT cio.category,
    SUM(cio.price) AS revenue,
    SUM(CASE WHEN co.purchase_seq = 1 THEN cio.price ELSE 0 END) AS new_revenue,
    SUM(CASE WHEN co.purchase_seq > 1 THEN cio.price ELSE 0 END) AS repeat_revenue
  FROM cat_item_orders cio
  JOIN customer_orders co ON cio.order_id = co.order_id
  GROUP BY cio.category
)
SELECT category,
  ROUND(revenue, 2) AS revenue,
  ROUND(100.0 * revenue / SUM(revenue) OVER (), 2) AS category_pct_of_total_revenue,
  ROUND(new_revenue, 2) AS new_revenue,
  ROUND(repeat_revenue, 2) AS repeat_revenue,
  ROUND(100.0 * new_revenue / NULLIF(revenue, 0), 2) AS new_revenue_pct,
  ROUND(100.0 * repeat_revenue / NULLIF(revenue, 0), 2) AS repeat_revenue_pct
FROM cat_cohorts
ORDER BY revenue DESC
LIMIT 10;
"""


def matches_product_cohort_question(question: str) -> bool:
    """Handle explicit, unfiltered top-10 product and category cohort showcase questions."""
    normalized = re.sub(r"[^a-z0-9]+", " ", question.casefold()).strip()
    words = set(normalized.split())
    if any(y in words for y in ["2016", "2017", "2018", "sp", "rj", "mg"]):
        return False
    if normalized in {
        "top 10 products and thier breakdown of new vs repeat customers purchases revenue and order splits",
        "top 10 products and their breakdown of new vs repeat customers purchases revenue and order splits",
        "top 10 products by revenue and their new vs repeat customer order splits",
    }:
        return True
    if "top 10" in normalized and ("new vs repeat" in normalized or "repeat" in normalized) and ("category" in normalized or "categories" in normalized):
        return True
    return False


def run_product_cohort_analysis(question: str, session_id: str) -> AgenticBIState:
    state = AgenticBIState(question=question, session_id=session_id, intent=UserIntent.EXPLORATORY_SQL)
    is_category = "categor" in question.casefold()
    target_sql = CATEGORY_COHORT_SQL if is_category else PRODUCT_COHORT_SQL
    state.raw_sql = target_sql
    try:
        connector = WarehouseSession().get_connector()
        if connector.get_dialect() != "duckdb":
            state.execution_error = "This predefined product analysis currently supports the local DuckDB sample only."
            return state
        state.validated_sql, state.validation_time_us = ASTSecurityValidator().validate_and_sanitize(target_sql)
        state.security_passed = True
        state.execution_result = connector.execute_query(state.validated_sql)
        if is_category:
            state.summary_narrative = (
                "Top 10 product categories ranked by revenue (BRL, excluding freight and canceled orders). "
                "Calculates category share of total revenue alongside new versus repeat customer revenue splits. "
                "New indicates the customer's first observed non-canceled order; repeat indicates a subsequent order. "
                "Historical sample covering 2016–2018."
            )
        else:
            state.summary_narrative = (
                "Top 10 individual products ranked by item revenue (BRL, excluding freight and canceled orders). "
                "New means the customer's first observed non-canceled order in this dataset; repeat means a later order. "
                "Order percentages use orders containing each product; units and revenue are also split. "
                "Olist covers 2016–2018 and does not provide product names, only IDs and categories. "
                "Earlier purchases outside this dataset are unknown."
            )
    except Exception as exc:
        state.execution_error = str(exc)
    return state
