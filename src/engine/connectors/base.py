"""Unified Warehouse Abstraction Layer (UWAL) - Base Connector Interface.

Defines the pluggable protocol for all warehouse engines (DuckDB, Postgres,
Snowflake, BigQuery, ClickHouse) with zero-copy Apache Arrow data transport.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import pyarrow as pa


class StandardDataType(str, Enum):
    """Normalized cross-warehouse data types."""
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    STRING = "STRING"
    BOOLEAN = "BOOLEAN"
    TIMESTAMP = "TIMESTAMP"
    DATE = "DATE"
    JSON = "JSON"
    ARRAY = "ARRAY"
    UNKNOWN = "UNKNOWN"


@dataclass
class ColumnMetadata:
    """Metadata description of a warehouse table column."""
    name: str
    standard_type: StandardDataType
    raw_type: str
    nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False
    description: str | None = None
    sample_values: list[Any] = field(default_factory=list)


@dataclass
class TableMetadata:
    """Metadata description of a warehouse table or view."""
    table_name: str
    schema_name: str = "main"
    columns: dict[str, ColumnMetadata] = field(default_factory=dict)
    row_count: int | None = None
    description: str | None = None
    primary_key: list[str] = field(default_factory=list)


@dataclass
class CatalogSchema:
    """Introspected catalog containing all registered tables."""
    tables: dict[str, TableMetadata] = field(default_factory=dict)

    def get_table(self, name: str) -> TableMetadata | None:
        """Retrieve table by case-insensitive name."""
        for tbl_name, tbl_meta in self.tables.items():
            if tbl_name.lower() == name.lower():
                return tbl_meta
        return None

    def get_column_names(self, table_name: str) -> list[str]:
        """Get column names for a table."""
        tbl = self.get_table(table_name)
        return list(tbl.columns.keys()) if tbl else []


@dataclass
class QueryResult:
    """Unified tabular execution result backed by Apache Arrow."""
    data: pa.Table
    execution_time_ms: float
    rows_scanned: int
    rows_returned: int
    bytes_scanned: int | None = None
    dialect: str = "duckdb"
    sql: str = ""

    def to_pylist(self) -> list[dict[str, Any]]:
        """Convert Arrow table to list of dictionaries."""
        return self.data.to_pylist()

    def to_pandas(self):
        """Convert Arrow table to pandas DataFrame."""
        return self.data.to_pandas()

    @property
    def column_names(self) -> list[str]:
        """List of column names in the result."""
        return self.data.column_names


@dataclass
class QueryCostEstimate:
    """Pre-flight query cost and resource scan estimate."""
    estimated_bytes: int
    estimated_cost_usd: float = 0.0
    will_exceed_limit: bool = False
    explanation: str = ""


class BaseWarehouseConnector(ABC):
    """Abstract Base Class for all warehouse backend adapters."""

    @abstractmethod
    def connect(self) -> None:
        """Establish physical connection to the warehouse backend."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close physical connection and release resources."""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Verify network connectivity and authentication."""
        pass

    @abstractmethod
    def introspect_schema(self, schema_name: str | None = None, table_filter: list[str] | None = None) -> CatalogSchema:
        """Introspect and return the normalized catalog schema."""
        pass

    @abstractmethod
    def execute_query(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
        limit: int | None = None,
        timeout_ms: int | None = None,
    ) -> QueryResult:
        """Execute a validated query and return a zero-copy Arrow QueryResult."""
        pass

    @abstractmethod
    def explain(self, sql: str) -> str:
        """Return the physical execution plan for a query."""
        pass

    @abstractmethod
    def get_dialect(self) -> str:
        """Return the SQLGlot dialect identifier (e.g. 'duckdb', 'snowflake', 'postgres')."""
        pass

    def estimate_cost_or_bytes(self, sql: str) -> QueryCostEstimate:
        """Estimate bytes scanned and query cost before execution (default implementation)."""
        return QueryCostEstimate(estimated_bytes=0, estimated_cost_usd=0.0, will_exceed_limit=False)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
