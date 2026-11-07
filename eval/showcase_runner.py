"""Check the five guided demo metrics against independently written SQL.

This checks exactly the fixed metric/dimension combinations in the local tour,
not free-form question understanding or production data access controls.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from eval.comparator import ResultComparator
from src.cli import EXAMPLES
from src.engine.connectors.duckdb_connector import DuckDBConnector
from src.security.ast_validator import ASTSecurityValidator
from src.semantic.resolver import SemanticQueryResolver

# These references are deliberately separate from the semantic configuration.
GOLD = {
    "gmv": """SELECT c.customer_state, SUM(i.price) FROM order_items i
              JOIN orders o ON i.order_id = o.order_id
              JOIN customers c ON o.customer_id = c.customer_id
              WHERE o.order_status != 'canceled' GROUP BY c.customer_state""",
    "delivery_delay_rate": """SELECT c.customer_state,
              SUM(CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date
                  THEN 1.0 ELSE 0.0 END) / COUNT(DISTINCT o.order_id) * 100.0
              FROM orders o JOIN customers c ON o.customer_id = c.customer_id
              WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
                AND o.order_estimated_delivery_date IS NOT NULL GROUP BY c.customer_state""",
    "total_orders": "SELECT COUNT(DISTINCT order_id) FROM orders WHERE order_status = 'delivered'",
    "aov": """SELECT SUM(i.price) / NULLIF(COUNT(DISTINCT i.order_id), 0)
              FROM order_items i JOIN orders o ON i.order_id = o.order_id
              WHERE o.order_status = 'delivered'""",
    "avg_review_score": """SELECT AVG(r.review_score) FROM order_reviews r
              JOIN orders o ON r.order_id = o.order_id WHERE o.order_status = 'delivered'""",
}


def main():
    connector = DuckDBConnector()
    comparator = ResultComparator()
    resolver = SemanticQueryResolver()
    validator = ASTSecurityValidator()
    passed = 0
    try:
        connector.connect()
        for question, metric, dimensions in EXAMPLES.values():
            try:
                query = resolver.resolve_metric_query(metric, dimensions=dimensions)
                safe_query, _ = validator.validate_and_sanitize(query, dialect="duckdb")
                actual = connector.execute_query(safe_query)
                expected = connector.execute_query(GOLD[metric])
                ok = comparator.compare_tables(actual.data, expected.data)
                print(f"{'PASS' if ok else 'FAIL'} {question}")
                passed += int(ok)
            except Exception as exc:
                print(f"FAIL {question}: {type(exc).__name__}: {exc}")
    finally:
        connector.disconnect()
    total = len(EXAMPLES)
    print(f"Showcase metric comparisons: {passed}/{total}. Results compare against reference SQL on bundled Olist data.")
    return 0 if total == len(GOLD) and passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
