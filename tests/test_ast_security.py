"""Comprehensive tests for SQLGlot AST Security Firewall."""

import pytest
from src.core.exceptions import SecurityViolationError
from src.security.ast_validator import ASTSecurityValidator


def test_valid_select_query_appends_limit(ast_validator):
    sql = "SELECT customer_id, industry FROM dim_customers WHERE country = 'USA';"
    clean_sql, val_time = ast_validator.validate_and_sanitize(sql)
    assert "LIMIT 1000" in clean_sql
    assert val_time > 0.0


def test_clamps_excessive_limit(ast_validator):
    sql = "SELECT customer_id FROM dim_customers LIMIT 50000;"
    clean_sql, _ = ast_validator.validate_and_sanitize(sql)
    assert "LIMIT 1000" in clean_sql
    assert "50000" not in clean_sql


def test_rejects_multi_statement_queries(ast_validator):
    sql = "SELECT 1; DROP TABLE dim_customers;"
    with pytest.raises(SecurityViolationError) as exc_info:
        ast_validator.validate_and_sanitize(sql)
    assert exc_info.value.violation_type == "MULTI_STATEMENT_INJECTION"


@pytest.mark.parametrize("ddl", [
    "DROP TABLE dim_customers;",
    "ALTER TABLE dim_customers ADD COLUMN hacked TEXT;",
    "TRUNCATE TABLE fct_subscriptions;",
    "DELETE FROM dim_customers WHERE 1=1;",
    "UPDATE dim_customers SET company_name = 'hacked';",
    "INSERT INTO dim_customers VALUES ('CUST-999', 'Evil', 'Fintech', 'Startup', 'USA', now(), false);",
])
def test_rejects_mutating_ddl_and_dml(ast_validator, ddl):
    with pytest.raises(SecurityViolationError):
        ast_validator.validate_and_sanitize(ddl)


@pytest.mark.parametrize("attack", [
    "SELECT * FROM read_csv('/etc/passwd');",
    "SELECT * FROM read_parquet('s3://leak/bucket.parquet');",
    "SELECT * FROM read_json('/root/.aws/credentials');",
    "COPY dim_customers TO '/tmp/leak.csv';",
    "INSTALL httpfs; LOAD httpfs;",
])
def test_rejects_path_traversal_and_extensions(ast_validator, attack):
    with pytest.raises(SecurityViolationError):
        ast_validator.validate_and_sanitize(attack)


def test_rejects_unconstrained_cartesian_join(ast_validator):
    sql = "SELECT * FROM dim_customers CROSS JOIN fct_subscriptions;"
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
    WITH cohort AS (
        SELECT customer_id FROM dim_customers WHERE country = 'USA'
    )
    SELECT * FROM cohort JOIN fct_subscriptions ON cohort.customer_id = fct_subscriptions.customer_id;
    """
    clean_sql, _ = ast_validator.validate_and_sanitize(sql)
    assert "LIMIT 1000" in clean_sql
