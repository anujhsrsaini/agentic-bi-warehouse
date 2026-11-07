"""Hand-calculated regression cases for the fixed product cohort workflow."""

import duckdb
import pytest

from src.agents.product_cohorts import PRODUCT_COHORT_SQL, matches_product_cohort_question
from src.core.config import settings
from src.core.exceptions import SecurityViolationError
from src.security.ast_validator import ASTSecurityValidator


def test_product_cohorts_use_repeat_customer_and_product_order_grain(monkeypatch):
    monkeypatch.setattr(settings, "customer_identifier_protection", False)
    sql, _ = ASTSecurityValidator().validate_and_sanitize(PRODUCT_COHORT_SQL)
    c = duckdb.connect()
    c.execute("CREATE TABLE customers (customer_id VARCHAR, customer_unique_id VARCHAR)")
    c.execute("CREATE TABLE orders (order_id VARCHAR, customer_id VARCHAR, order_status VARCHAR, order_purchase_timestamp TIMESTAMP)")
    c.execute("CREATE TABLE order_items (order_id VARCHAR, product_id VARCHAR, price DOUBLE)")
    c.execute("CREATE TABLE products (product_id VARCHAR, product_category_name VARCHAR)")
    c.execute("CREATE TABLE category_translation (product_category_name VARCHAR, product_category_name_english VARCHAR)")
    c.execute("INSERT INTO customers VALUES ('c1','person1'),('c2','person1'),('c3','person2'),('c4','person2')")
    c.execute("INSERT INTO orders VALUES ('o1','c1','delivered','2018-01-01'),('o2','c2','delivered','2018-01-02'),('o3','c3','delivered','2018-01-03'),('o4','c4','canceled','2018-01-04')")
    c.execute("INSERT INTO order_items VALUES ('o1','p1',10),('o1','p1',20),('o2','p1',30),('o3','p1',20),('o4','p1',500)")
    c.execute("INSERT INTO products VALUES ('p1','category')")
    result = c.execute(sql)
    row = dict(zip([x[0] for x in result.description], result.fetchone()))
    assert row["units"] == 4 and row["revenue"] == 80
    assert row["orders"] == 3 and row["new_orders"] == 2 and row["repeat_orders"] == 1
    assert row["new_units"] == 3 and row["repeat_units"] == 1
    assert row["new_revenue"] == 50 and row["repeat_revenue"] == 30
    assert row["new_order_pct"] == pytest.approx(66.67) and row["repeat_order_pct"] == pytest.approx(33.33)
    c.close()


def test_customer_id_policy_is_respected(monkeypatch):
    monkeypatch.setattr(settings, "customer_identifier_protection", True)
    with pytest.raises(SecurityViolationError):
        ASTSecurityValidator().validate_and_sanitize(PRODUCT_COHORT_SQL)


def test_fixed_workflow_does_not_silently_ignore_filters():
    base = "Top 10 products and thier breakdown of new vs repeat customers purchases/revenue and order splits"
    assert matches_product_cohort_question(base)
    assert not matches_product_cohort_question(base + " in 2018")
