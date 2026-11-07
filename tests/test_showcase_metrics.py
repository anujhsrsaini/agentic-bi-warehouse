"""Independent small-data checks of the showcased semantic metrics."""

import duckdb
import pytest

from src.core.exceptions import SemanticResolutionError
from src.agents.orchestrator import AgenticBIOrchestrator
from src.semantic.resolver import SemanticQueryResolver


@pytest.fixture
def warehouse():
    conn = duckdb.connect(":memory:")
    conn.execute("CREATE TABLE orders (order_id VARCHAR, customer_id VARCHAR, order_status VARCHAR, order_delivered_customer_date DATE, order_estimated_delivery_date DATE)")
    conn.execute("CREATE TABLE customers (customer_id VARCHAR, customer_state VARCHAR)")
    conn.execute("CREATE TABLE order_items (order_id VARCHAR, price DOUBLE)")
    conn.execute("CREATE TABLE order_payments (order_id VARCHAR, payment_type VARCHAR, payment_value DOUBLE)")
    conn.execute("CREATE TABLE order_reviews (order_id VARCHAR, review_score DOUBLE)")
    conn.execute("INSERT INTO customers VALUES ('c1', 'SP'), ('c2', 'RJ'), ('c3', 'SP'), ('c4', 'RJ')")
    conn.execute("""INSERT INTO orders VALUES
        ('o1','c1','delivered','2018-01-03','2018-01-02'),
        ('o2','c2','delivered','2018-01-01','2018-01-02'),
        ('o3','c3','delivered','2018-01-03',NULL),
        ('o4','c4','canceled',NULL,NULL)""")
    conn.execute("INSERT INTO order_items VALUES ('o1',100),('o1',50),('o2',200),('o3',30),('o4',1000)")
    conn.execute("INSERT INTO order_payments VALUES ('o1','credit_card',100),('o1','voucher',50),('o2','credit_card',200)")
    conn.execute("INSERT INTO order_reviews VALUES ('o1',5),('o2',3),('o3',4),('o4',1)")
    yield conn
    conn.close()


@pytest.mark.parametrize(
    ("metric", "expected"),
    [("gmv", 380), ("total_orders", 3), ("aov", 380 / 3),
     ("avg_review_score", 4), ("delivery_delay_rate", 50)],
)
def test_showcase_metrics_match_hand_calculated_results(warehouse, metric, expected):
    sql = SemanticQueryResolver().resolve_metric_query(metric)
    assert warehouse.execute(sql).fetchone()[0] == pytest.approx(expected)


def test_sales_by_state_does_not_multiply_item_rows(warehouse):
    sql = SemanticQueryResolver().resolve_metric_query("gmv", ["customer_state"])
    assert dict(warehouse.execute(sql).fetchall()) == {"SP": 180, "RJ": 200}


def test_unsafe_reverse_join_is_rejected():
    with pytest.raises(SemanticResolutionError):
        SemanticQueryResolver().resolve_metric_query("gmv", ["payment_type"])


def test_misleading_synonyms_are_not_mapped():
    config = SemanticQueryResolver().config
    assert config.get_metric("nps proxy") is None
    assert config.get_metric("on time delivery") is None


def test_unsupported_combination_returns_a_useful_error(monkeypatch):
    from src.graph import workflow

    def fail_resolution(*args, **kwargs):
        raise SemanticResolutionError("unsafe join")

    monkeypatch.setattr(workflow, "run_agentic_bi", fail_resolution)
    state = AgenticBIOrchestrator().process_query("example")
    assert "not supported safely" in state.execution_error
