"""Comprehensive tests for SQLGlot AST Security Firewall — Olist Edition."""

import pytest
from src.core.exceptions import SecurityViolationError
from src.security.ast_validator import ASTSecurityValidator


def test_valid_select_query_appends_limit(ast_validator):
    sql = "SELECT order_id, order_status FROM orders WHERE order_status = 'delivered';"
    clean_sql, val_time = ast_validator.validate_and_sanitize(sql)
    assert "LIMIT 1000" in clean_sql
    assert val_time > 0.0


def test_clamps_excessive_limit(ast_validator):
    sql = "SELECT order_id FROM orders LIMIT 50000;"
    clean_sql, _ = ast_validator.validate_and_sanitize(sql)
    assert "LIMIT 1000" in clean_sql
    assert "50000" not in clean_sql


def test_rejects_multi_statement_queries(ast_validator):
    sql = "SELECT 1; DROP TABLE orders;"
    with pytest.raises(SecurityViolationError) as exc_info:
        ast_validator.validate_and_sanitize(sql)
    assert exc_info.value.violation_type == "MULTI_STATEMENT_INJECTION"


@pytest.mark.parametrize("ddl", [
    "DROP TABLE orders;",
    "ALTER TABLE orders ADD COLUMN hacked TEXT;",
    "TRUNCATE TABLE order_items;",
    "DELETE FROM orders WHERE 1=1;",
    "UPDATE orders SET order_status = 'hacked';",
    "INSERT INTO orders VALUES ('fake-id', 'fake-cust', 'delivered', now(), now(), now(), now(), now());",
])
def test_rejects_mutating_ddl_and_dml(ast_validator, ddl):
    with pytest.raises(SecurityViolationError):
        ast_validator.validate_and_sanitize(ddl)


@pytest.mark.parametrize("attack", [
    "SELECT * FROM read_csv('/etc/passwd');",
    "SELECT * FROM read_parquet('s3://exfiltrate/data.parquet');",
    "SELECT * FROM read_json('/root/.aws/credentials');",
    "COPY orders TO '/tmp/leak.csv';",
    "INSTALL httpfs; LOAD httpfs;",
])
def test_rejects_path_traversal_and_extensions(ast_validator, attack):
    with pytest.raises(SecurityViolationError):
        ast_validator.validate_and_sanitize(attack)


def test_rejects_unconstrained_cartesian_join(ast_validator):
    sql = "SELECT * FROM orders CROSS JOIN order_items;"
    with pytest.raises(SecurityViolationError) as exc_info:
        ast_validator.validate_and_sanitize(sql)
    assert exc_info.value.violation_type == "CARTESIAN_JOIN_VIOLATION"


def test_rejects_unregistered_tables(ast_validator):
    sql = "SELECT * FROM super_secret_salaries;"
    with pytest.raises(SecurityViolationError) as exc_info:
        ast_validator.validate_and_sanitize(sql)
    assert exc_info.value.violation_type == "UNAUTHORIZED_TABLE_ACCESS"


def test_permits_ctes_in_select(ast_validator):
    sql = """
    WITH items_agg AS (
        SELECT order_id, SUM(price) AS total_price FROM order_items GROUP BY order_id
    )
    SELECT o.order_id, ia.total_price
    FROM orders o
    JOIN items_agg ia ON o.order_id = ia.order_id
    WHERE o.order_status = 'delivered';
    """
    clean_sql, _ = ast_validator.validate_and_sanitize(sql)
    assert "LIMIT 1000" in clean_sql
