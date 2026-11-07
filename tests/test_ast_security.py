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


@pytest.mark.parametrize("sql", [
    "SELECT customer_unique_id FROM customers",
    "SELECT c.customer_unique_id AS identifier FROM customers AS c",
    "SELECT UPPER(customer_unique_id) AS identifier FROM customers",
    "SELECT customer_id FROM customers WHERE customer_unique_id = 'x'",
    "WITH x AS (SELECT customer_unique_id AS identifier FROM customers) SELECT identifier FROM x",
    'SELECT "CUSTOMER_UNIQUE_ID" FROM customers',
])
def test_rejects_sensitive_column_references(ast_validator, sql, monkeypatch):
    from src.core.config import settings
    monkeypatch.setattr(settings, "customer_identifier_protection", True)
    with pytest.raises(SecurityViolationError) as exc_info:
        ast_validator.validate_and_sanitize(sql)
    assert exc_info.value.violation_type == "SENSITIVE_COLUMN_ACCESS"


@pytest.mark.parametrize("sql", [
    "SELECT * FROM customers",
    "SELECT c.* FROM customers AS c",
    "WITH x AS (SELECT * FROM customers) SELECT customer_id FROM x",
    "WITH x AS (SELECT customer_id FROM customers) SELECT * FROM x",
])
def test_rejects_wildcard_projections(ast_validator, sql):
    with pytest.raises(SecurityViolationError) as exc_info:
        ast_validator.validate_and_sanitize(sql)
    assert exc_info.value.violation_type == "WILDCARD_PROJECTION"


def test_permits_count_star_without_exposing_columns(ast_validator):
    sql, _ = ast_validator.validate_and_sanitize("SELECT COUNT(*) AS n FROM customers")
    assert "COUNT(*)" in sql
    assert "LIMIT 1000" in sql


def test_inner_limit_does_not_replace_outer_limit(ast_validator):
    sql, _ = ast_validator.validate_and_sanitize(
        "WITH x AS (SELECT order_id FROM orders LIMIT 1) SELECT order_id FROM x"
    )
    assert sql.endswith("LIMIT 1000")


@pytest.mark.parametrize("dialect", ["duckdb", "postgres", "snowflake", "bigquery", "clickhouse"])
def test_sensitive_column_policy_applies_across_supported_dialects(ast_validator, dialect, monkeypatch):
    from src.core.config import settings
    monkeypatch.setattr(settings, "customer_identifier_protection", True)
    with pytest.raises(SecurityViolationError) as exc_info:
        ast_validator.validate_and_sanitize("SELECT customer_unique_id FROM customers", dialect=dialect)
    assert exc_info.value.violation_type == "SENSITIVE_COLUMN_ACCESS"
