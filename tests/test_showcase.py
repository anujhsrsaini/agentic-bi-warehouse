"""Checks for the deliberately small offline showcase question set."""

import socket

import pytest

from src.cli import EXAMPLES, _caveats, _source_tables, execute_and_render
from src.engine.connectors.duckdb_connector import DuckDBConnector
from src.security.ast_validator import ASTSecurityValidator
from src.semantic.resolver import SemanticQueryResolver


# Independent SQL expresses the same business definitions without the resolver.
GOLD_SQL = {
    "gmv": """SELECT c.customer_state, SUM(i.price) AS value
              FROM orders o JOIN order_items i ON o.order_id = i.order_id
              JOIN customers c ON o.customer_id = c.customer_id
              WHERE o.order_status <> 'canceled' GROUP BY c.customer_state""",
    "delivery_delay_rate": """SELECT c.customer_state,
        100.0 * COUNT(*) FILTER (WHERE o.order_delivered_customer_date > o.order_estimated_delivery_date)
        / COUNT(*) AS value FROM orders o JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
        AND o.order_estimated_delivery_date IS NOT NULL GROUP BY c.customer_state""",
    "total_orders": "SELECT COUNT(DISTINCT order_id) AS value FROM orders WHERE order_status = 'delivered'",
    "aov": """SELECT SUM(i.price) / COUNT(DISTINCT i.order_id) AS value
             FROM orders o JOIN order_items i ON o.order_id = i.order_id WHERE o.order_status = 'delivered'""",
    "avg_review_score": """SELECT AVG(r.review_score) AS value FROM orders o
                         JOIN order_reviews r ON o.order_id = r.order_id WHERE o.order_status = 'delivered'""",
}


@pytest.fixture(scope="module")
def connector():
    connection = DuckDBConnector()
    yield connection
    connection.disconnect()


@pytest.mark.parametrize("question,metric,dimensions", EXAMPLES.values())
def test_examples_match_independent_queries(connector, question, metric, dimensions):
    del question
    sql = SemanticQueryResolver().resolve_metric_query(metric, dimensions=dimensions)
    sql, _ = ASTSecurityValidator().validate_and_sanitize(sql)
    actual = connector.execute_query(sql).to_pylist()
    expected = connector.execute_query(GOLD_SQL[metric]).to_pylist()
    if dimensions:
        actual_values = {row[dimensions[0]]: row[metric] for row in actual}
        expected_values = {row[dimensions[0]]: row["value"] for row in expected}
        assert actual_values == pytest.approx(expected_values)
    else:
        assert actual[0][metric] == pytest.approx(expected[0]["value"])


def test_unrecognized_question_does_not_fall_back(capsys):
    execute_and_render("What is the meaning of life?")
    assert "only recognizes the listed example questions" in capsys.readouterr().out


def test_guided_example_needs_no_network_or_key(monkeypatch, capsys):
    def no_network(*args, **kwargs):
        raise AssertionError("The offline demo attempted a network connection")

    monkeypatch.delenv("SARVAM_API_KEY", raising=False)
    monkeypatch.setattr(socket.socket, "connect", no_network)
    execute_and_render(EXAMPLES["1"][0])
    output = capsys.readouterr().out
    assert "Sources in executed SQL" in output
    assert "Unable to run" not in output


def test_caveats_and_sources():
    assert any("NPS" in item for item in _caveats("avg_review_score"))
    assert _source_tables("SELECT o.order_id FROM orders o") == ["orders"]
