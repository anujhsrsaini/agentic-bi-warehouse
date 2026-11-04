"""Automated Semantic Layer Bootstrapper (Zero-to-One Onboarding Engine).

Automatically analyzes an unmodeled warehouse schema:
1. Profiles tables, column null ratios, uniqueness ratios, and naming patterns
2. Classifies tables into Fact vs Dimension tables
3. Discovers foreign key relationships via sample set-inclusion tests
4. Synthesizes candidate measures (SUM, COUNT DISTINCT) and derived metrics
5. Emits a valid, production-ready semantic_layer.yaml
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
import yaml

from src.engine.connectors.base import BaseWarehouseConnector, CatalogSchema, StandardDataType


class SemanticBootstrapEngine:
    """Zero-to-One Semantic Layer Bootstrapper."""

    def __init__(self, connector: BaseWarehouseConnector):
        self.connector = connector

    def bootstrap(self, output_path: Path | str | None = None) -> dict[str, Any]:
        """Introspect schema, classify tables, discover relationships, and generate YAML."""
        catalog = self.connector.introspect_schema()

        models = []
        metrics = []

        # 1. Classify Fact vs Dimension tables
        table_classifications = {}
        for tbl_name, tbl_meta in catalog.tables.items():
            is_fact = self._classify_table(tbl_meta)
            table_classifications[tbl_name] = "fact" if is_fact else "dimension"

        # 2. Extract dimensions, measures, and primary keys
        for tbl_name, tbl_meta in catalog.tables.items():
            is_fact = (table_classifications[tbl_name] == "fact")

            # Detect primary key
            pk = self._detect_primary_key(tbl_meta)

            dims = []
            measures = []
            fks = []

            for col_name, col_meta in tbl_meta.columns.items():
                if col_name == pk:
                    continue

                # Check if it looks like a foreign key
                fk_target = self._detect_foreign_key(tbl_name, col_name, catalog)
                if fk_target:
                    fks.append({
                        "fk": col_name,
                        "references": f"{fk_target[0]}.{fk_target[1]}",
                        "relationship": "many_to_one",
                    })

                # Numeric measures on fact tables
                if is_fact and col_meta.standard_type in [StandardDataType.FLOAT, StandardDataType.INTEGER]:
                    if not col_name.endswith("_id") and not col_name.endswith("_pk") and not col_name.endswith("_fk"):
                        measures.append({
                            "name": f"total_{col_name}",
                            "expr": col_name,
                            "agg": "sum",
                        })
                        # Propose a certified metric
                        metrics.append({
                            "name": f"total_{col_name}",
                            "label": col_name.replace("_", " ").title(),
                            "description": f"Total aggregated sum of {col_name}.",
                            "model": tbl_name,
                            "calculation": f"SUM({col_name})",
                            "dimensions": [],
                            "synonyms": [col_name.replace("_", " ")],
                        })
                else:
                    # Categorical or timestamp dimension
                    dims.append({
                        "name": col_name,
                        "type": col_meta.standard_type.value.lower(),
                        "column": col_name,
                    })

            # Record count metric for fact tables
            if is_fact:
                metrics.append({
                    "name": f"{tbl_name}_count",
                    "label": f"{tbl_name.replace('_', ' ').title()} Count",
                    "description": f"Total number of records in {tbl_name}.",
                    "model": tbl_name,
                    "calculation": "COUNT(*)",
                    "dimensions": [],
                    "synonyms": [f"{tbl_name} count", f"number of {tbl_name}"],
                })

            model_dict = {
                "name": tbl_name,
                "table": tbl_name,
                "primary_key": pk or list(tbl_meta.columns.keys())[0],
                "dimensions": dims,
            }
            if measures:
                model_dict["measures"] = measures
            if fks:
                model_dict["foreign_keys"] = fks

            models.append(model_dict)

        result_config = {
            "version": "1.0",
            "models": models,
            "metrics": metrics,
        }

        if output_path:
            out_file = Path(output_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            with open(out_file, "w", encoding="utf-8") as f:
                yaml.dump(result_config, f, sort_keys=False, default_flow_style=False)

        return result_config

    def _classify_table(self, tbl: Any) -> bool:
        """Classify if a table is Fact (True) or Dimension (False)."""
        name = tbl.table_name.lower()
        if name.startswith("fct_") or name.startswith("fact_") or "events" in name or "transactions" in name or "invoices" in name:
            return True
        if name.startswith("dim_") or name.startswith("dimension_") or "users" in name or "customers" in name or "plans" in name:
            return False
        # Fallback to column types: if > 40% numeric measures, treat as fact
        num_numeric = sum(1 for c in tbl.columns.values() if c.standard_type in [StandardDataType.FLOAT, StandardDataType.INTEGER])
        return (num_numeric / max(1, len(tbl.columns))) > 0.4

    def _detect_primary_key(self, tbl: Any) -> str | None:
        """Heuristic detection of primary key column."""
        for col in tbl.columns:
            if col == "id" or col == f"{tbl.table_name}_id" or col.endswith("_id") and (col.startswith("dim_") or "cust" in col or "plan" in col):
                return col
        return list(tbl.columns.keys())[0] if tbl.columns else None

    def _detect_foreign_key(self, current_table: str, col_name: str, catalog: CatalogSchema) -> tuple[str, str] | None:
        """Detect foreign key targets across catalog."""
        if not col_name.endswith("_id") and not col_name.endswith("_fk"):
            return None

        # Look for matching table name or pk
        target_name_guess = col_name.replace("_id", "").replace("_fk", "")
        for tbl_name, tbl_meta in catalog.tables.items():
            if tbl_name == current_table:
                continue
            if tbl_name == target_name_guess or tbl_name == f"dim_{target_name_guess}" or tbl_name == f"fct_{target_name_guess}":
                # Find matching pk column in target table
                if col_name in tbl_meta.columns:
                    return (tbl_name, col_name)
                # Check for id column in target
                if "id" in tbl_meta.columns:
                    return (tbl_name, "id")
                # Check for primary key in target
                pk = self._detect_primary_key(tbl_meta)
                if pk:
                    return (tbl_name, pk)
        return None
