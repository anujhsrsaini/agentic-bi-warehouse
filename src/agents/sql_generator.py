"""SQL Generator & Query Planner Agent — Olist Brazilian E-Commerce Edition.

Dual-Track SQL Generation:
- Track 1 (Certified Metric): Compiles deterministic SQL from YAML semantic model.
- Track 2 (Exploratory SQL): Synthesizes dialect-aware analytical SQL with schema linking.

IMPORTANT: Olist has a Fan-out/Chasm Trap.
  orders → order_items (1:N)
  orders → order_payments (1:N)
  Direct join of both facts on orders WILL duplicate rows.
  Diagnostic SQL must aggregate each fact in its own CTE before joining.
"""

from __future__ import annotations

from src.agents.entity_grounder import CategoricalEntityGrounder
from src.agents.state import AgenticBIState, UserIntent
from src.semantic.resolver import SemanticQueryResolver


class SQLGeneratorAgent:
    """Generates canonical SQL queries according to user intent."""

    def __init__(self):
        self.resolver = SemanticQueryResolver()
        self.grounder = CategoricalEntityGrounder()

    def generate(self, state: AgenticBIState) -> AgenticBIState:
        """Generate canonical SQL and attach to state."""
        # 1. Ground any entities mentioned in the query
        grounded = self.grounder.ground_entities(state.question)
        state.grounded_entities = {f"{g[0]}.{g[1]}": g[2] for g in grounded}

        filter_clauses = list(state.filters)
        for tbl, col, val, conf in grounded:
            filter_clauses.append(f"{tbl}.{col} = '{val}'")

        if state.intent == UserIntent.CERTIFIED_METRIC and state.metric_name:
            # Track 1: Certified Semantic Compilation
            state.raw_sql = self.resolver.resolve_metric_query(
                metric_name=state.metric_name,
                dimensions=state.dimensions,
                filters=filter_clauses,
                limit=state.limit,
                order_ascending=state.order_ascending,
            )
            state.sql_rationale = (
                f"Compiled certified formula for [{state.metric_name}] "
                f"from semantic_layer.yaml with dimensions: {state.dimensions or ['overall']}."
            )
            return state

        elif state.intent == UserIntent.DIAGNOSTIC_WHY:
            # Diagnostic Root-Cause: multi-dimensional cohort breakdown
            # Uses CTEs to avoid chasm-trap between order_items and order_payments
            state.raw_sql = """
WITH items_agg AS (
    -- Aggregate GMV and freight per order to avoid fan-out
    SELECT
        oi.order_id,
        SUM(oi.price)         AS order_gmv,
        SUM(oi.freight_value) AS order_freight
    FROM order_items oi
    GROUP BY oi.order_id
),
review_agg AS (
    SELECT
        r.order_id,
        AVG(r.review_score) AS avg_score
    FROM order_reviews r
    GROUP BY r.order_id
)
SELECT
    c.customer_state,
    COUNT(DISTINCT o.order_id)                                                  AS total_orders,
    ROUND(AVG(rev.avg_score), 3)                                               AS avg_review_score,
    ROUND(SUM(ia.order_gmv), 2)                                                AS total_gmv,
    ROUND(
        SUM(CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date
                 THEN 1.0 ELSE 0.0 END)
        / NULLIF(COUNT(DISTINCT o.order_id), 0) * 100.0,
        2
    )                                                                          AS late_delivery_pct,
    ROUND(AVG(DATE_DIFF('day', o.order_purchase_timestamp, o.order_delivered_customer_date)), 1) AS avg_delivery_days
FROM orders o
JOIN customers c    ON o.customer_id    = c.customer_id
JOIN items_agg ia   ON o.order_id       = ia.order_id
LEFT JOIN review_agg rev ON o.order_id  = rev.order_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
GROUP BY c.customer_state
ORDER BY avg_review_score ASC
LIMIT 50;
            """.strip()
            state.sql_rationale = (
                "Generated multi-dimensional root-cause diagnostic: review score + delivery delay rate "
                "by Brazilian state using CTEs to prevent chasm-trap fan-out."
            )
            return state

        else:
            # Track 2: Exploratory SQL Synthesis — Olist schema
            q_lower = state.question.lower()

            if any(t in q_lower for t in ["new vs repeat", "repeat vs new", "new vs returning", "repeat customer", "new customer", "first time vs returning"]):
                # Determine time grain (daywise, monthly, or overall)
                is_daywise = "order_date" in state.dimensions or any(w in q_lower for w in ["day", "daily", "daywise", "date"])
                is_monthly = "order_month" in state.dimensions or any(w in q_lower for w in ["month", "monthly", "monthwise"])

                date_expr = "CAST(co.order_purchase_timestamp AS DATE)" if is_daywise else "DATE_TRUNC('month', co.order_purchase_timestamp)"
                date_alias = "order_date" if is_daywise else "order_month"

                # Check for time filter
                time_filter_clause = ""
                time_filter_inner = ""
                if state.filters:
                    f_clean = state.filters[0].replace("orders.", "co.")
                    time_filter_clause = f"WHERE {f_clean}"
                    time_filter_inner = f"AND {state.filters[0].replace('orders.', 'o.')}"
                elif "last" in q_lower:
                    time_filter_clause = "WHERE co.order_purchase_timestamp >= (SELECT MAX(order_purchase_timestamp) - INTERVAL 60 DAY FROM orders WHERE order_status != 'canceled')"

                wants_count = ("count" in q_lower or "number of" in q_lower) and not any(
                    w in q_lower for w in ["gmv", "revenue", "sales", "value"]
                )

                if wants_count and (is_daywise or is_monthly):
                    state.raw_sql = f"""
WITH customer_orders AS (
    SELECT
        o.order_id,
        o.order_purchase_timestamp,
        c.customer_unique_id,
        ROW_NUMBER() OVER (
            PARTITION BY c.customer_unique_id
            ORDER BY o.order_purchase_timestamp ASC
        ) AS order_sequence
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status != 'canceled'
)
SELECT
    {date_expr} AS {date_alias},
    COUNT(DISTINCT CASE WHEN co.order_sequence = 1 THEN co.customer_unique_id END) AS new_customers,
    COUNT(DISTINCT CASE WHEN co.order_sequence > 1 THEN co.customer_unique_id END) AS repeat_customers,
    COUNT(DISTINCT co.customer_unique_id) AS total_customers
FROM customer_orders co
{time_filter_clause}
GROUP BY 1
ORDER BY {date_alias} ASC
LIMIT 100;
                    """.strip()
                    state.sql_rationale = (
                        "Generated cohort New vs Repeat distinct customer count split using window "
                        "partition on customer_unique_id."
                    )
                    return state

                if wants_count:
                    state.raw_sql = f"""
WITH customer_orders AS (
    SELECT
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS order_count
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status != 'canceled'
    {time_filter_inner}
    GROUP BY 1
)
SELECT
    CASE WHEN order_count = 1 THEN 'New Customer' ELSE 'Repeat Customer' END AS customer_type,
    COUNT(*) AS total_customers
FROM customer_orders
GROUP BY 1
ORDER BY total_customers DESC;
                    """.strip()
                    state.sql_rationale = (
                        "Generated overall New vs Repeat distinct customer count split."
                    )
                    return state

                if is_daywise or is_monthly:
                    state.raw_sql = f"""
WITH customer_orders AS (
    SELECT
        o.order_id,
        o.order_purchase_timestamp,
        c.customer_unique_id,
        ROW_NUMBER() OVER (
            PARTITION BY c.customer_unique_id
            ORDER BY o.order_purchase_timestamp ASC
        ) AS order_sequence
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status != 'canceled'
),
items_agg AS (
    SELECT
        order_id,
        SUM(price) AS order_gmv
    FROM order_items
    GROUP BY order_id
)
SELECT
    {date_expr} AS {date_alias},
    ROUND(SUM(CASE WHEN co.order_sequence = 1 THEN ia.order_gmv ELSE 0 END), 2) AS new_customer_gmv,
    ROUND(SUM(CASE WHEN co.order_sequence > 1 THEN ia.order_gmv ELSE 0 END), 2) AS repeat_customer_gmv,
    ROUND(SUM(ia.order_gmv), 2) AS total_gmv,
    ROUND(
        SUM(CASE WHEN co.order_sequence > 1 THEN ia.order_gmv ELSE 0 END)
        / NULLIF(SUM(ia.order_gmv), 0) * 100.0,
        1
    ) AS repeat_pct
FROM customer_orders co
JOIN items_agg ia ON co.order_id = ia.order_id
{time_filter_clause}
GROUP BY 1
ORDER BY {date_alias} ASC
LIMIT 100;
                    """.strip()
                    state.sql_rationale = (
                        "Generated cohort New vs Repeat GMV breakdown using window partition on customer_unique_id "
                        "and CTE pre-aggregation to avoid fan-out duplication."
                    )
                else:
                    state.raw_sql = f"""
WITH customer_orders AS (
    SELECT
        o.order_id,
        o.order_purchase_timestamp,
        c.customer_unique_id,
        ROW_NUMBER() OVER (
            PARTITION BY c.customer_unique_id
            ORDER BY o.order_purchase_timestamp ASC
        ) AS order_sequence
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status != 'canceled'
),
items_agg AS (
    SELECT
        order_id,
        SUM(price) AS order_gmv
    FROM order_items
    GROUP BY order_id
)
SELECT
    CASE WHEN co.order_sequence = 1 THEN 'New Customer' ELSE 'Repeat Customer' END AS customer_type,
    COUNT(DISTINCT co.order_id) AS total_orders,
    ROUND(SUM(ia.order_gmv), 2) AS total_gmv,
    ROUND(
        SUM(ia.order_gmv) / SUM(SUM(ia.order_gmv)) OVER () * 100.0,
        1
    ) AS gmv_pct
FROM customer_orders co
JOIN items_agg ia ON co.order_id = ia.order_id
{time_filter_clause}
GROUP BY 1
ORDER BY total_gmv DESC;
                    """.strip()
                    state.sql_rationale = (
                        "Generated executive New vs Repeat customer cohort GMV comparison."
                    )
                return state

            elif "top" in q_lower and ("seller" in q_lower or "sellers" in q_lower):
                state.raw_sql = """
SELECT
    s.seller_id,
    s.seller_city,
    s.seller_state,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    ROUND(SUM(oi.price), 2)     AS total_gmv
FROM sellers s
JOIN order_items oi ON s.seller_id = oi.seller_id
JOIN orders o       ON oi.order_id = o.order_id
WHERE o.order_status != 'canceled'
GROUP BY s.seller_id, s.seller_city, s.seller_state
ORDER BY total_gmv DESC
LIMIT 10;
                """.strip()

            elif ("category" in q_lower or "categories" in q_lower) and ("latency" in q_lower or "delivery" in q_lower or "delay" in q_lower):
                state.raw_sql = """
SELECT
    COALESCE(ct.product_category_name_english, p.product_category_name) AS category,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    ROUND(SUM(oi.price), 2) AS total_gmv,
    ROUND(AVG(DATE_DIFF('day', o.order_purchase_timestamp, o.order_delivered_customer_date)), 1) AS avg_delivery_days
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN products p ON oi.product_id = p.product_id
LEFT JOIN category_translation ct ON p.product_category_name = ct.product_category_name
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
GROUP BY 1
ORDER BY total_gmv DESC
LIMIT 5;
                """.strip()

            elif "category" in q_lower or "categories" in q_lower:
                state.raw_sql = """
SELECT
    COALESCE(ct.product_category_name_english, p.product_category_name) AS category,
    COUNT(DISTINCT oi.order_id)      AS orders,
    ROUND(SUM(oi.price), 2)          AS gmv,
    ROUND(AVG(r.review_score), 3)    AS avg_review_score
FROM order_items oi
JOIN orders o   ON oi.order_id = o.order_id
JOIN products p ON oi.product_id = p.product_id
LEFT JOIN category_translation ct ON p.product_category_name = ct.product_category_name
LEFT JOIN order_reviews r         ON oi.order_id = r.order_id
WHERE o.order_status != 'canceled'
GROUP BY 1
ORDER BY gmv DESC
LIMIT 20;
                """.strip()

            elif "delay" in q_lower or "shipping" in q_lower or "late" in q_lower:
                state.raw_sql = """
SELECT
    c.customer_state,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(
        SUM(CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date
                 THEN 1.0 ELSE 0.0 END)
        / NULLIF(COUNT(DISTINCT o.order_id), 0) * 100.0,
        2
    ) AS late_delivery_pct,
    ROUND(AVG(DATE_DIFF('day', o.order_purchase_timestamp, o.order_delivered_customer_date)), 1) AS avg_delivery_days
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
GROUP BY c.customer_state
ORDER BY late_delivery_pct DESC
LIMIT 15;
                """.strip()

            elif "payment" in q_lower:
                state.raw_sql = """
SELECT
    op.payment_type,
    COUNT(DISTINCT op.order_id)  AS total_orders,
    ROUND(SUM(op.payment_value), 2) AS total_payment_value,
    ROUND(AVG(op.payment_installments), 2) AS avg_installments
FROM order_payments op
JOIN orders o ON op.order_id = o.order_id
WHERE o.order_status != 'canceled'
GROUP BY op.payment_type
ORDER BY total_payment_value DESC;
                """.strip()

            elif "review" in q_lower or "rating" in q_lower or "csat" in q_lower:
                state.raw_sql = """
SELECT
    c.customer_state,
    COUNT(DISTINCT r.review_id)   AS review_count,
    ROUND(AVG(r.review_score), 3) AS avg_review_score
FROM order_reviews r
JOIN orders o   ON r.order_id = o.order_id
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_state
ORDER BY avg_review_score ASC
LIMIT 27;
                """.strip()

            else:
                # Default: GMV by Brazilian state
                state.raw_sql = """
SELECT
    c.customer_state,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(oi.price), 2)   AS gmv
FROM orders o
JOIN customers c    ON o.customer_id = c.customer_id
JOIN order_items oi ON o.order_id    = oi.order_id
WHERE o.order_status != 'canceled'
GROUP BY c.customer_state
ORDER BY gmv DESC
LIMIT 27;
                """.strip()

            state.sql_rationale = (
                "Synthesized exploratory analytical SQL with Olist schema linking "
                "and chasm-trap-safe join paths."
            )
            return state
