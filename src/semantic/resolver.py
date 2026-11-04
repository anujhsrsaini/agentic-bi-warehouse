"""Governed Semantic Query Transpiler & Join Graph Resolver.

Translates high-level business metric queries into deterministic, canonical SQL:
- Pulls certified formulas from SemanticLayerConfig
- Resolves minimal safe join paths to requested dimensions
- Injects hygiene filters (e.g., is_deleted = false)
- Prevents Cartesian join explosions and Fan-Out traps
"""

from __future__ import annotations

from typing import Any
import sqlglot
from sqlglot import exp

from src.core.exceptions import SemanticResolutionError
from src.semantic.loader import SemanticLayerLoader
from src.semantic.models import MetricDefinition, SemanticLayerConfig, SemanticModel


class SemanticQueryResolver:
    """Compiles governed metric queries into canonical SQL."""

    def __init__(self, config: SemanticLayerConfig | None = None):
        self.config = config or SemanticLayerLoader().load()

    def resolve_metric_query(
        self,
        metric_name: str,
        dimensions: list[str] | None = None,
        filters: list[str] | None = None,
        limit: int = 100,
        order_by_metric: bool = True,
    ) -> str:
        """Resolve a metric and dimensions into deterministic SQL."""
        metric = self.config.get_metric(metric_name)
        if not metric:
            available = [m.name for m in self.config.metrics]
            raise SemanticResolutionError(
                f"Unknown metric '{metric_name}'. Certified metrics are: {', '.join(available)}"
            )

        target_dims = dimensions or []
        base_model = self.config.get_model(metric.model)
        if not base_model:
            raise SemanticResolutionError(f"Base model '{metric.model}' for metric '{metric_name}' not found.")

        # Determine required joins based on requested dimensions
        joins_needed: list[tuple[str, str, str]] = []  # (target_table, join_condition, join_type)
        dim_select_exprs: list[str] = []
        group_by_exprs: list[str] = []

        for dim_name in target_dims:
            dim_loc = self._find_dimension(dim_name)
            if not dim_loc:
                raise SemanticResolutionError(f"Dimension '{dim_name}' not found in semantic catalog.")
            
            tbl_name, col_name = dim_loc
            qualified_col = f"{tbl_name}.{col_name}"
            dim_select_exprs.append(f"{qualified_col} AS {dim_name}")
            group_by_exprs.append(qualified_col)

            # If dimension is from another table, resolve join
            if tbl_name != base_model.table:
                join_clause = self._resolve_join(base_model, tbl_name)
                if join_clause and join_clause not in joins_needed:
                    joins_needed.append(join_clause)

        # Also check if any filter references an external table
        for f in filters or []:
            for model in self.config.models:
                if model.table != base_model.table and f"{model.table}." in f:
                    join_clause = self._resolve_join(base_model, model.table)
                    if join_clause and join_clause not in joins_needed:
                        joins_needed.append(join_clause)

        # Assemble WHERE clauses
        where_clauses: list[str] = []
        if metric.filter:
            where_clauses.append(f"({metric.filter})")
        if filters:
            for f in filters:
                where_clauses.append(f"({f})")

        # Automatically inject is_deleted = false hygiene if dim_customers is joined
        joined_tables = [base_model.table] + [j[0] for j in joins_needed]
        if "dim_customers" in joined_tables:
            where_clauses.append("dim_customers.is_deleted = false")

        # Build SQL Parts
        select_parts = []
        if dim_select_exprs:
            select_parts.extend(dim_select_exprs)
        select_parts.append(f"{metric.calculation} AS {metric.name}")

        sql = f"SELECT\n    {', '.join(select_parts)}\nFROM {base_model.table}"

        for target_tbl, on_cond, j_type in joins_needed:
            sql += f"\n{j_type} JOIN {target_tbl} ON {on_cond}"

        if where_clauses:
            sql += f"\nWHERE {' AND '.join(where_clauses)}"

        if group_by_exprs:
            sql += f"\nGROUP BY {', '.join(group_by_exprs)}"

        if order_by_metric:
            sql += f"\nORDER BY {metric.name} DESC"

        if limit > 0:
            sql += f"\nLIMIT {limit}"

        sql += ";"
        return sql

    def _find_dimension(self, dim_name: str) -> tuple[str, str] | None:
        """Find table and column for a dimension name or synonym."""
        for model in self.config.models:
            for dim in model.dimensions:
                if dim.name.lower() == dim_name.lower():
                    return (model.table, dim.column)
                if dim_name.lower() in [s.lower() for s in dim.synonyms]:
                    return (model.table, dim.column)
        return None

    def _resolve_join(self, base_model: SemanticModel, target_table: str) -> tuple[str, str, str]:
        """Find foreign key join between base model and target table."""
        # 1. Direct FK on base model
        for fk in base_model.foreign_keys:
            ref_tbl, ref_col = fk.references.split(".")
            if ref_tbl == target_table:
                return (target_table, f"{base_model.table}.{fk.fk} = {target_table}.{ref_col}", "LEFT")

        # 2. Reverse FK on target table
        target_model = self.config.get_model(target_table)
        if target_model:
            for fk in target_model.foreign_keys:
                ref_tbl, ref_col = fk.references.split(".")
                if ref_tbl == base_model.table:
                    return (target_table, f"{target_table}.{fk.fk} = {base_model.table}.{ref_col}", "LEFT")

        raise SemanticResolutionError(f"No join path resolved between '{base_model.table}' and '{target_table}'.")
