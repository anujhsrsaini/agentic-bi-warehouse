"""SQLGlot AST Security Firewall & Sandbox Guardrail.

Implements a 7-stage deterministic AST inspection pipeline:
1. Multi-Statement Lexical Gate (blocks stacked SQL injection)
2. Root Statement Enforcement (SELECT and UNION only)
3. Mutation & DDL Prevention (blocks DROP, ALTER, UPDATE, DELETE, INSERT)
4. Forbidden Function & Table-Generator Blocker (blocks read_csv, read_parquet, copy, install)
5. Table Whitelist Verification (against registered catalog/views & CTEs)
6. Cartesian Join Detection (rejects unconstrained CROSS JOINs)
7. Sensitive-column and wildcard rejection, and outer LIMIT clamping
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any
import sqlglot
from sqlglot import exp
import yaml

from src.core.config import settings
from src.core.exceptions import SecurityViolationError


class ASTSecurityValidator:
    """7-Stage SQLGlot AST Security Firewall."""

    def __init__(self, policy_path: Path | str | None = None):
        self.policy_path = Path(policy_path or (settings.config_dir / "security_policies.yaml"))
        self.policy = self._load_policy()

    def _load_policy(self) -> dict[str, Any]:
        if self.policy_path.exists():
            with open(self.policy_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {
            "max_limit": 1000,
            "whitelisted_tables": [
                "orders", "order_items", "customers", "order_payments", "order_reviews",
                "products", "sellers", "category_translation"
            ],
            "forbidden_functions": [
                "read_parquet", "read_csv", "read_json", "read_blob", "glob", "httpfs",
                "copy", "install", "load", "shell", "exec", "pg_sleep", "system$wait"
            ],
            "sensitive_columns": ["ssn", "credit_card", "password", "secret"],
        }

    def validate_and_sanitize(self, sql: str, dialect: str = "duckdb") -> tuple[str, float]:
        """Validate SQL through the 7-stage AST inspection pipeline.
        
        Returns:
            tuple of (sanitized_sql, validation_time_us)
        """
        start_time = time.perf_counter()

        # Stage 1: Multi-Statement Lexical Gate
        try:
            statements = sqlglot.parse(sql, read=dialect)
        except Exception as e:
            raise SecurityViolationError(f"SQL parsing failed: {e}", "SYNTAX_PARSE_ERROR") from e

        if not statements:
            raise SecurityViolationError("Empty SQL statement provided.", "EMPTY_STATEMENT")

        if len(statements) > 1:
            raise SecurityViolationError(
                f"Multi-statement queries detected ({len(statements)} statements). Only single-statement queries permitted.",
                "MULTI_STATEMENT_INJECTION"
            )

        root = statements[0]
        if root is None:
            raise SecurityViolationError("Unable to construct valid AST from SQL.", "NULL_AST")

        # Stage 2: Root Statement Type Enforcement
        if not isinstance(root, (exp.Select, exp.Union)):
            raise SecurityViolationError(
                f"Unauthorized root statement type '{type(root).__name__}'. Only SELECT queries are permitted.",
                "UNAUTHORIZED_STATEMENT_TYPE"
            )

        # Stage 3: Mutation & DDL Blocker
        mutating_types = (
            exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Alter,
            exp.Create, exp.Command, exp.Pragma
        )
        for node in root.walk():
            if isinstance(node, mutating_types):
                raise SecurityViolationError(
                    f"Mutating expression '{type(node).__name__}' is forbidden in analytical queries.",
                    "MUTATION_ATTEMPT"
                )

        # Stage 4: Forbidden Functions & Table-Generators Blocker
        forbidden_funcs = {
            "read_parquet", "read_csv", "read_json", "read_blob", "glob", "httpfs",
            "copy", "install", "load", "shell", "exec", "pg_sleep", "system$wait",
            "readcsv", "readparquet", "readjson", "readblob"
        }
        forbidden_funcs.update(str(name).lower() for name in self.policy.get("forbidden_functions", []))
        for node in root.walk():
            node_key = getattr(node, "key", "").lower()
            node_name = getattr(node, "name", "").lower()
            node_type = type(node).__name__.lower()
            if node_key in forbidden_funcs or node_name in forbidden_funcs or node_type in forbidden_funcs:
                raise SecurityViolationError(
                    f"Forbidden function or generator '{node_name or node_key or node_type}' detected.",
                    "FORBIDDEN_FUNCTION"
                )

        # Collect CTE aliases so they are not rejected as unregistered tables
        cte_aliases = set()
        for with_clause in root.find_all(exp.With):
            for cte in with_clause.expressions:
                if cte.alias:
                    cte_aliases.add(cte.alias.lower())

        # Stage 5: Table Whitelist Verification
        whitelisted = {t.lower() for t in self.policy.get("whitelisted_tables", [])}
        for tbl in root.find_all(exp.Table):
            if isinstance(tbl.this, (exp.Func, exp.Anonymous)):
                raise SecurityViolationError(
                    f"Dynamic table generator '{tbl.this}' is not permitted.",
                    "FORBIDDEN_TABLE_GENERATOR"
                )
            table_name = tbl.name.lower()
            if table_name and table_name not in whitelisted and table_name not in cte_aliases:
                raise SecurityViolationError(
                    f"Table '{tbl.name}' is not in the authorized warehouse whitelist.",
                    "UNAUTHORIZED_TABLE_ACCESS",
                    {"table": tbl.name, "authorized": list(whitelisted)}
                )

        # Stage 6: Cartesian Join Detection
        for join in root.find_all(exp.Join):
            # Check for CROSS JOIN
            if join.kind and "CROSS" in join.kind.upper():
                raise SecurityViolationError(
                    "Unconstrained CROSS JOIN detected. Queries must specify explicit join conditions.",
                    "CARTESIAN_JOIN_VIOLATION"
                )
            # Check for comma-joins without ON or USING predicates
            if not join.args.get("on") and not join.args.get("using"):
                raise SecurityViolationError(
                    "Join missing ON or USING predicate. Unconstrained joins are forbidden.",
                    "CARTESIAN_JOIN_VIOLATION"
                )

        # Stage 7: Reject sensitive references in any expression (including
        # filters, joins, and nested queries). Blocking only output projections
        # would still allow an attacker to infer values through predicates.
        sensitive_cols = {str(name).casefold() for name in self.policy.get("sensitive_columns", [])}
        if not settings.customer_identifier_protection:
            sensitive_cols.discard("customer_unique_id")
        for col in root.find_all(exp.Column):
            if col.name.casefold() in sensitive_cols:
                raise SecurityViolationError(
                    f"Access to sensitive column '{col.name}' is not permitted.",
                    "SENSITIVE_COLUMN_ACCESS",
                )

        # The validator has no trusted schema with which to expand a wildcard.
        # Reject it even in CTEs or expressions; COUNT(*) only counts rows and
        # does not project a column, so it remains useful for analytics.
        for star in root.find_all(exp.Star):
            if isinstance(star.parent, exp.Count) and star.parent.this is star:
                continue
            raise SecurityViolationError(
                "Wildcard projections are not permitted; select approved columns explicitly.",
                "WILDCARD_PROJECTION",
            )

        # Apply the limit to the outer query. A limit inside a CTE or subquery
        # does not bound the final result, and must not satisfy this check.
        max_limit = self.policy.get("max_limit", 1000)
        limit_node = root.args.get("limit")

        if limit_node is None:
            # Inject LIMIT 1000
            root = root.limit(max_limit)
        else:
            # Clamp existing LIMIT if it exceeds max_limit
            try:
                curr_limit = int(limit_node.expression.this)
                if curr_limit > max_limit or curr_limit < 0:
                    limit_node.set("expression", exp.Literal.number(max_limit))
            except Exception:
                limit_node.set("expression", exp.Literal.number(max_limit))

        sanitized_sql = root.sql(dialect=dialect)
        validation_time_us = (time.perf_counter() - start_time) * 1_000_000.0

        return sanitized_sql, validation_time_us
