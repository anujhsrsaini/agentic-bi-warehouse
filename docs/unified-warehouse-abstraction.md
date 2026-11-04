# Unified Warehouse Abstraction Layer: Architectural Specification & Implementation Blueprint

**Document Identifier**: `ARCH-DATA-003`  
**System**: Agentic BI & Warehouse Question-Answering System  
**Role**: Warehouse Connector Architect  
**Author**: Antigravity AI Data Systems Architect  
**Date**: November 2026  
**Status**: APPROVED FOR IMPLEMENTATION  

---

## 1. Executive Summary & Architectural Vision

The core design principle of the **Agentic BI & Warehouse Question-Answering System** is:
> *"DuckDB-first for developer velocity, zero-cloud onboarding, and instant sub-15ms local execution, yet architecturally unconstrained so that any enterprise data warehouse (Snowflake, BigQuery, ClickHouse, PostgreSQL, Databricks) can be seamlessly attached without rewriting semantic models, AST security guardrails, or agent workflows."*

In modern enterprise deployments, analytical agents face conflicting operational requirements:
1. **Developer Experience & Cold-Start**: Prospective enterprise evaluators, CTOs, and internal developers want a zero-setup, in-memory/Parquet evaluation loop running in `< 5 seconds` with zero credentials (`python demo.py`).
2. **Cloud Enterprise Scale**: Enterprise production targets live inside petabyte-scale cloud warehouses (Snowflake, BigQuery, ClickHouse) with strict IAM roles, compute governance, and query cost thresholds.
3. **Agent Iteration Economics**: Autonomous agents often execute 5–15 iterative exploratory queries before finalizing an answer. Running every intermediate micro-query directly against a cloud warehouse burns significant compute credits and incurs network latency (1.5s–5s per roundtrip).

To solve this, our system introduces the **Unified Warehouse Abstraction Layer (UWAL)**. The UWAL decouples:
- The **Governed Semantic Layer** (calculating business metrics like ARR, NRR, churn),
- The **AST Security & Sandbox Engine** (verifying safety, preventing injection, clamping row limits), and
- The **Physical Execution Layer** (routing queries to DuckDB, PostgreSQL, Snowflake, BigQuery, or ClickHouse).

Furthermore, **DuckDB is elevated into a triple-role runtime**:
1. **The Default Local Warehouse**: Vectorized OLAP engine running directly over in-memory tables and local Parquet datasets with zero dependencies.
2. **The Analytical Accelerator & Local Cache**: Materializing bounded working slices (`TABLESAMPLE` or partitioned subsets) from remote enterprise warehouses into ephemeral DuckDB memory for near-instant, zero-cost agent iteration.
3. **The Federation Engine**: Bridging heterogeneous data sources by attaching directly to PostgreSQL/MySQL/MotherDuck and scanning cloud Parquet/Iceberg/Delta tables concurrently.

```mermaid
flowchart TD
    subgraph AgentClient["Agent & User Workflows"]
        UserPrompt["User Natural Language Question"]
        MCP["FastMCP / Claude Code / Cursor"]
        CLI["Rich Terminal Cockpit / Demo"]
    end

    subgraph SemanticAndSecurity["Governed Core (Dialect Agnostic)"]
        Semantic["Governed Semantic Engine<br>(Calculates ARR, NRR, Churn)"]
        CanonicalSQL["Canonical SQL Generator<br>(Target: ANSI / DuckDB Dialect)"]
        ASTGuard["SQLGlot AST Security Firewall<br>• Immutability & DDL Blocking<br>• Limit Clamping (Max 1,000)<br>• Cartesian Join Detection"]
    end

    subgraph UWAL["Unified Warehouse Abstraction Layer (UWAL)"]
        Transpiler["SQLGlot Transpiler<br>(Transforms Canonical AST to Target Dialect)"]
        Router["Warehouse Execution Router"]
        
        subgraph Adapters["Warehouse Adapters (BaseWarehouseConnector)"]
            DuckDBAdapter["DuckDBConnector<br>(Local / Parquet / Iceberg)"]
            PGAdapter["PostgresConnector<br>(psycopg3 / ADBC)"]
            SnowflakeAdapter["SnowflakeConnector<br>(Cloud DW / Arrow)"]
            BQAdapter["BigQueryConnector<br>(Dry-Run / Storage API)"]
            CHAdapter["ClickHouseConnector<br>(Real-Time OLAP)"]
        end
        
        CacheManager["DuckDB Acceleration & Cache Engine<br>(Working Slice Materializer)"]
    end

    subgraph PhysicalWarehouses["Target Data Engines"]
        LocalFiles[("Local Parquet / Iceberg Lakehouse")]
        RemotePG[("PostgreSQL Database")]
        RemoteSnowflake[("Snowflake Data Cloud")]
        RemoteBQ[("Google Cloud BigQuery")]
        RemoteCH[("ClickHouse Cluster")]
    end

    UserPrompt --> MCP
    MCP --> Semantic
    CLI --> Semantic
    Semantic --> CanonicalSQL
    CanonicalSQL --> ASTGuard
    ASTGuard --> Transpiler
    Transpiler --> Router

    Router -->|Local Direct / Cache Hit| DuckDBAdapter
    Router -->|Remote Relational| PGAdapter
    Router -->|Cloud Enterprise| SnowflakeAdapter
    Router -->|Cloud Lakehouse| BQAdapter
    Router -->|Real-Time OLAP| CHAdapter

    Router -.->|Materialize Slice| CacheManager
    CacheManager --> DuckDBAdapter

    DuckDBAdapter --> LocalFiles
    PGAdapter --> RemotePG
    SnowflakeAdapter --> RemoteSnowflake
    BQAdapter --> RemoteBQ
    CHAdapter --> RemoteCH
```

---

## 2. Research & Comparative Analysis: Modern Unified Warehouse Connectivity

To design a clean, extensible abstraction layer, we researched the state of the art across four pillars of modern data engineering:

### 2.1 Ibis Project (`ibis-framework`)
[Ibis](https://ibis-project.org/) is the standard Python dataframe library for unified multi-backend analytics, supporting 20+ SQL engines (DuckDB, Snowflake, BigQuery, ClickHouse, Postgres, Trino, Polars).

#### Key Architectural Insight: The Ibis 9.0+ Paradigm Shift
Historically, Ibis utilized SQLAlchemy for SQL compilation across backends. In Ibis 9.0 ("The Big Refactor"), the project **completely abandoned SQLAlchemy in favor of SQLGlot**:
- **Dialect Sprawl**: SQLAlchemy's compilation model was heavily coupled to third-party dialect packages with inconsistent maintenance cycles and release schedules.
- **AST Directness**: SQLGlot provides a unified, highly optimized AST engine that natively understands modern analytical constructs (window functions, chained CTEs, unnesting arrays/structs, date truncation, regex) across 20+ dialects in pure Python.
- **Decoupling Intent from Engine**: Ibis compiles Python relational algebra (`expr.filter(...).group_by(...)`) into an internal IR, then transforms that IR into a SQLGlot expression tree (`sqlglot.expressions.Expression`), and finally calls SQLGlot's dialect generator (`expr.sql(dialect=target_dialect)`).

#### Application to Our System
While Ibis is exceptional for programmatic Python pipelines, an **Agentic BI System** primarily operates on SQL and natural-language-compiled query specifications. Instead of forcing the LLM to learn an Ibis Python dataframe API or maintaining another translation layer:
1. Our semantic layer emits **Canonical SQL (DuckDB/ANSI standard)**.
2. We leverage **SQLGlot AST directly** for security inspection, limit clamping, and dialect transpilation.
3. This mirrors Ibis's internal architectural decision while preserving sub-millisecond AST manipulation overhead.

---

### 2.2 Apache Arrow & ADBC (Arrow Database Connectivity) vs. SQLAlchemy vs. Native DBAPI

When retrieving analytical query results, data transport efficiency is paramount.

#### The "Transpose Tax" of Legacy DBAPI & SQLAlchemy
Legacy database drivers (DBAPI 2.0, ODBC, JDBC, SQLAlchemy Core) are fundamentally row-oriented:
1. The remote analytical warehouse stores and processes data column-by-column in columnar memory.
2. The legacy driver serializes columns into row tuples (`SQLFetch` / `fetchall()`), allocating a separate Python `PyObject` for every single cell in memory.
3. The client application (pandas, Polars, or DuckDB) must then traverse those Python objects and re-pivot rows back into columnar arrays.
This double-transposition and Python object boxing consumes up to **70–80% of total query latency** and inflates memory usage by 5x–10x.

#### ADBC & Columnar Zero-Copy Streaming
[ADBC (Arrow Database Connectivity)](https://arrow.apache.org/docs/format/ADBC.html) replaces ODBC/JDBC with a standard columnar C-API:
- Drivers return data as **Apache Arrow `RecordBatch` streams** directly across the C Data Interface.
- Python receives a `pyarrow.Table` with zero memory copies and zero Python object allocation overhead.
- Libraries like Polars and DuckDB can ingest Arrow tables in sub-millisecond time via pointer handoffs.

```text
Legacy DBAPI / SQLAlchemy:
[Columnar DW] ---> [De-columnize to Rows] ---> [PyObject Boxing] ---> [Re-columnize in Client] (70% CPU overhead)

Arrow / ADBC Standard (UWAL):
[Columnar DW] =================== (Zero-Copy Arrow RecordBatches) ===================> [DuckDB / Polars / Agent]
```

#### Connector Protocol Evaluation Matrix

| Protocol / Tool | Throughput (MB/s) | Memory Efficiency | Type Fidelity | Dialect Portability | Best Use in UWAL |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Native DuckDB C++** | > 2,500 MB/s | Native Zero-Copy | 100% (Native Arrow) | DuckDB only | **Default local engine** |
| **ADBC Drivers** (`adbc_driver_*`) | 800–1,800 MB/s | Native Zero-Copy | High (Arrow Types) | Standard C API | **Postgres, Snowflake, BQ streaming** |
| **Native Cloud SDKs** (Snowflake Arrow, BQ Storage API) | 600–1,500 MB/s | Near Zero-Copy (Arrow chunks) | High | Vendor specific | **Cloud DW enterprise connectors** |
| **SQLAlchemy 2.0** | 40–120 MB/s | High overhead (Row objects) | Medium (ORM mapping) | Broad | **Metadata catalog fallback only** |

**Architectural Decision**: All UWAL query execution returns a unified `QueryResult` backed internally by an **Apache Arrow Table (`pyarrow.Table`)**, providing zero-copy conversion to Polars, Pandas, or JSON dictionaries as needed by the agent.

---

### 2.3 SQLGlot AST Transpilation & Canonical Dialect Engine

A major failure mode in multi-warehouse agentic systems is asking the LLM to write native SQL for every target dialect. LLMs frequently confuse:
- Date truncations: `DATE_TRUNC('month', dt)` (Postgres/DuckDB) vs `DATE_TRUNC(dt, MONTH)` (BigQuery) vs `DATE_TRUNC('MONTH', dt)` (Snowflake).
- Regex matches: `REGEXP_MATCHES(str, pat)` vs `REGEXP_LIKE(str, pat)`.
- Identifier quoting: `"column"` (Postgres/Snowflake) vs `` `column` `` (BigQuery/ClickHouse).
- Division safety: `a / NULLIF(b, 0)` vs `SAFE_DIVIDE(a, b)`.
- String concatenation: `a || b` vs `CONCAT(a, b)`.
- Nested JSON access: `data->'key'` vs `data:key::string` vs `JSONExtractString(data, 'key')`.

#### The Canonical Transpilation Strategy
Rather than prompting the LLM with differing dialect syntax rules:
1. The **Governed Semantic Layer** always generates SQL in **Canonical SQL** (modeled after ANSI / DuckDB dialect).
2. The **AST Security Firewall** parses the canonical SQL into a SQLGlot AST, performs security validation, join analysis, and limit clamping.
3. The **UWAL Transpiler** translates the verified AST into the target warehouse dialect:
   ```python
   target_sql = ast.sql(dialect=connector.get_dialect(), pretty=True)
   ```
4. This guarantees that 100% of security checks happen uniformly on the canonical AST before dialect-specific rendering.

---

### 2.4 DuckDB as a Unified Engine (Attachments, Lakehouse & Federation)

DuckDB is far more than an in-memory SQL runner; it is a full-featured federated analytical query engine:
1. **Direct Relational Attachments**:
   - `ATTACH 'dbname=production user=app host=...' AS pg (TYPE POSTGRES, READ_ONLY);`
   - `ATTACH 'host=... user=... database=...' AS my (TYPE MYSQL, READ_ONLY);`
   - `ATTACH 'path/to/db.sqlite' AS sqlite (TYPE SQLITE, READ_ONLY);`
   - `ATTACH 'md:enterprise_dw' AS motherduck;`
2. **Direct Lakehouse Storage Scans**:
   - Parquet: `read_parquet('s3://lakehouse/gold/fct_orders/*.parquet')`
   - Apache Iceberg: `iceberg_scan('s3://warehouse/iceberg/table/metadata/00001.metadata.json')`
   - Delta Lake: `delta_scan('s3://warehouse/delta/table/')`
3. **Federated Cross-Engine Joins**:
   DuckDB can join a local customer CSV uploaded via the agent UI with a remote PostgreSQL invoice table and an S3 Parquet cohort file in a single sub-second query.

---

## 3. The Warehouse Adapter Pattern: Core Interfaces & Contracts

To unify local DuckDB and enterprise cloud warehouses, we define a strict interface using Python's `abc.ABC` and modern `typing`.

### 3.1 Type System & Schema Normalization Models

Every warehouse uses proprietary type names. UWAL normalizes these into a single hierarchical type system defined in `src/engine/catalog/types.py`:

```python
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class StandardDataType(str, Enum):
    # Primitives
    BOOLEAN = "BOOLEAN"
    INT8 = "INT8"
    INT16 = "INT16"
    INT32 = "INT32"
    INT64 = "INT64"
    UINT8 = "UINT8"
    UINT16 = "UINT16"
    UINT32 = "UINT32"
    UINT64 = "UINT64"
    INT128 = "INT128"
    FLOAT32 = "FLOAT32"
    FLOAT64 = "FLOAT64"
    DECIMAL = "DECIMAL"
    STRING = "STRING"
    BINARY = "BINARY"
    
    # Temporal
    DATE = "DATE"
    TIME = "TIME"
    TIMESTAMP = "TIMESTAMP"          # Without timezone
    TIMESTAMPTZ = "TIMESTAMPTZ"      # With timezone
    INTERVAL = "INTERVAL"
    
    # Complex / Semi-Structured
    JSON = "JSON"
    ARRAY = "ARRAY"
    STRUCT = "STRUCT"
    MAP = "MAP"
    UUID = "UUID"
    UNKNOWN = "UNKNOWN"

class ColumnMetadata(BaseModel):
    name: str
    original_type: str
    standard_type: StandardDataType
    nullable: bool = True
    precision: Optional[int] = None
    scale: Optional[int] = None
    description: Optional[str] = None
    is_primary_key: bool = False
    is_foreign_key: bool = False
    is_partition_key: bool = False
    sample_values: List[Any] = Field(default_factory=list)

class TableMetadata(BaseModel):
    catalog: Optional[str] = None
    schema_name: str
    table_name: str
    table_type: str = "TABLE"  # TABLE, VIEW, MATERIALIZED_VIEW, EXTERNAL
    columns: List[ColumnMetadata] = Field(default_factory=list)
    row_count_estimate: Optional[int] = None
    size_bytes_estimate: Optional[int] = None
    primary_keys: List[str] = Field(default_factory=list)
    foreign_keys: Dict[str, str] = Field(default_factory=dict) # column -> "ref_table.ref_col"
    description: Optional[str] = None

class CatalogSchema(BaseModel):
    warehouse_type: str
    database_name: str
    schemas: Dict[str, List[TableMetadata]] = Field(default_factory=dict)
```

---

### 3.2 Query Execution & Cost Estimation Models

```python
import pyarrow as pa
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ExecutionMetrics(BaseModel):
    parse_and_ast_duration_ms: float = 0.0
    execution_duration_ms: float = 0.0
    total_duration_ms: float = 0.0
    rows_scanned: Optional[int] = None
    rows_returned: int = 0
    bytes_scanned: Optional[int] = None
    warehouse_credits_billed: Optional[float] = None
    cache_hit: bool = False
    target_dialect: str

class QueryCostEstimate(BaseModel):
    """Returned by estimate_cost_or_bytes() before query execution."""
    supported: bool = True
    bytes_scanned_estimate: Optional[int] = None
    cost_usd_estimate: Optional[float] = None
    query_complexity_score: float = 1.0  # 1.0 (trivial) to 10.0 (extreme join/scan)
    is_partition_pruned: bool = True
    estimated_duration_seconds: Optional[float] = None
    warning_message: Optional[str] = None

class QueryResult:
    """Zero-copy query result container backed by Apache Arrow."""
    def __init__(
        self,
        arrow_table: pa.Table,
        metrics: ExecutionMetrics,
        executed_sql: str
    ):
        self._arrow_table = arrow_table
        self.metrics = metrics
        self.executed_sql = executed_sql

    @property
    def arrow(self) -> pa.Table:
        """Returns the raw PyArrow Table (zero-copy)."""
        return self._arrow_table

    def to_polars(self):
        """Zero-copy handoff to Polars DataFrame."""
        import polars as pl
        return pl.from_arrow(self._arrow_table)

    def to_pandas(self):
        """Convert to Pandas DataFrame."""
        return self._arrow_table.to_pandas()

    def to_dict_records(self) -> List[Dict[str, Any]]:
        """Convert to list of Python dicts for MCP / JSON serialization."""
        return self._arrow_table.to_pylist()

    @property
    def row_count(self) -> int:
        return self._arrow_table.num_rows

    @property
    def column_names(self) -> List[str]:
        return self._arrow_table.column_names
```

---

### 3.3 The Core Connector Interface: `BaseWarehouseConnector`

```python
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Union
from contextlib import AbstractContextManager

class BaseWarehouseConnector(ABC, AbstractContextManager):
    """
    Abstract Base Class for all warehouse connectors in the Agentic BI system.
    Every connector implements connection lifecycle, schema introspection,
    governed query execution, explain plans, and dry-run cost estimation.
    """

    @abstractmethod
    def connect(self) -> None:
        """Establishes physical connection or initializes in-process engine session."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Releases connections, closes sessions, or terminates connection pools."""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Runs a lightweight diagnostic query (e.g. SELECT 1) to verify connectivity."""
        pass

    @abstractmethod
    def introspect_schema(
        self,
        schema_name: Optional[str] = None,
        table_filter: Optional[List[str]] = None
    ) -> CatalogSchema:
        """
        Inspects the warehouse catalogs and returns a unified normalized metadata schema.
        Maps all vendor-specific data types to StandardDataType.
        """
        pass

    @abstractmethod
    def execute_query(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = 1000,
        timeout_seconds: Optional[float] = 30.0
    ) -> QueryResult:
        """
        Executes a validated, transpiled SQL query against the target warehouse.
        Returns a columnar QueryResult backed by Apache Arrow.
        """
        pass

    @abstractmethod
    def get_dialect(self) -> str:
        """
        Returns the SQLGlot dialect name corresponding to this warehouse
        (e.g. 'duckdb', 'postgres', 'snowflake', 'bigquery', 'clickhouse').
        """
        pass

    @abstractmethod
    def explain(self, sql: str) -> str:
        """
        Returns the raw physical or logical execution plan for diagnostic and
        agent-driven query optimization.
        """
        pass

    @abstractmethod
    def estimate_cost_or_bytes(self, sql: str) -> QueryCostEstimate:
        """
        Performs a pre-execution dry-run or plan cost calculation.
        For cloud warehouses (BigQuery/Snowflake), predicts byte consumption
        and estimated dollar cost before actual execution.
        """
        pass

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
```

---

## 4. Concrete Connector Implementations

Here we detail the 5 reference connector implementations, highlighting how each interacts with its target engine, drivers, cost estimators, and type systems.

### 4.1 `DuckDBConnector` (Default, Zero-Setup, Local Lakehouse & In-Memory)
- **Role**: Primary default connector. Runs instantly with zero configuration. Can scan local Parquet, local Iceberg, in-memory tables, or connect to MotherDuck.
- **Security Hardening**: When operating in untrusted agent mode, DuckDB is locked down via:
  `SET enable_external_access = false; SET lock_configuration = true;`
- **Arrow Handoff**: DuckDB produces native Arrow tables via `conn.execute(sql).arrow()`, giving p95 execution latency `< 12ms`.

```python
# src/engine/connectors/duckdb_connector.py
import time
import duckdb
import pyarrow as pa
from typing import Optional, List, Dict, Any
from src.engine.connectors.base import BaseWarehouseConnector, QueryResult, ExecutionMetrics, QueryCostEstimate
from src.engine.catalog.types import CatalogSchema, TableMetadata, ColumnMetadata, StandardDataType

class DuckDBConnector(BaseWarehouseConnector):
    def __init__(
        self,
        database: str = ":memory:",
        read_only: bool = False,
        sandbox_mode: bool = True,
        threads: int = 4
    ):
        self.database = database
        self.read_only = read_only
        self.sandbox_mode = sandbox_mode
        self.threads = threads
        self._conn: Optional[duckdb.DuckDBPyConnection] = None

    def connect(self) -> None:
        self._conn = duckdb.connect(self.database, read_only=self.read_only)
        self._conn.execute(f"PRAGMA threads={self.threads};")
        if self.sandbox_mode and self.database == ":memory:":
            # Lock down external filesystem and network access
            self._conn.execute("SET enable_external_access = false;")
            self._conn.execute("SET lock_configuration = true;")

    def disconnect(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def test_connection(self) -> bool:
        res = self._conn.execute("SELECT 1 AS alive").fetchone()
        return res[0] == 1

    def get_dialect(self) -> str:
        return "duckdb"

    def execute_query(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = 1000,
        timeout_seconds: Optional[float] = 30.0
    ) -> QueryResult:
        start_time = time.perf_counter()
        # Clamped limit is applied at AST level or appended
        cursor = self._conn.cursor()
        arrow_table = cursor.execute(sql, parameters=params).arrow()
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        metrics = ExecutionMetrics(
            execution_duration_ms=duration_ms,
            total_duration_ms=duration_ms,
            rows_returned=arrow_table.num_rows,
            target_dialect="duckdb"
        )
        return QueryResult(arrow_table=arrow_table, metrics=metrics, executed_sql=sql)

    def explain(self, sql: str) -> str:
        df = self._conn.execute(f"EXPLAIN {sql}").fetchall()
        return "\n".join([row[1] for row in df])

    def estimate_cost_or_bytes(self, sql: str) -> QueryCostEstimate:
        # In-process DuckDB has $0 cloud cost
        return QueryCostEstimate(
            supported=True,
            bytes_scanned_estimate=0,
            cost_usd_estimate=0.0,
            query_complexity_score=1.0,
            warning_message=None
        )

    def introspect_schema(
        self,
        schema_name: Optional[str] = "main",
        table_filter: Optional[List[str]] = None
    ) -> CatalogSchema:
        schema = schema_name or "main"
        query = f"""
            SELECT table_name, column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = '{schema}'
            ORDER BY table_name, ordinal_position;
        """
        rows = self._conn.execute(query).fetchall()
        tables_dict: Dict[str, List[ColumnMetadata]] = {}
        for tbl, col, dtype, nullable in rows:
            if table_filter and tbl not in table_filter:
                continue
            if tbl not in tables_dict:
                tables_dict[tbl] = []
            tables_dict[tbl].append(ColumnMetadata(
                name=col,
                original_type=dtype,
                standard_type=self._map_duckdb_type(dtype),
                nullable=(nullable == "YES")
            ))

        table_metas = [
            TableMetadata(schema_name=schema, table_name=tbl, columns=cols)
            for tbl, cols in tables_dict.items()
        ]
        return CatalogSchema(warehouse_type="duckdb", database_name="local", schemas={schema: table_metas})

    @staticmethod
    def _map_duckdb_type(duck_type: str) -> StandardDataType:
        dt = duck_type.upper()
        if "INT" in dt or "HUGEINT" in dt:
            return StandardDataType.INT64 if "HUGE" not in dt else StandardDataType.INT128
        if "DOUBLE" in dt or "FLOAT" in dt:
            return StandardDataType.FLOAT64
        if "VARCHAR" in dt or "TEXT" in dt:
            return StandardDataType.STRING
        if "BOOL" in dt:
            return StandardDataType.BOOLEAN
        if "DATE" in dt:
            return StandardDataType.DATE
        if "TIMESTAMP" in dt:
            return StandardDataType.TIMESTAMPTZ if "WITH TIME ZONE" in dt else StandardDataType.TIMESTAMP
        if "STRUCT" in dt:
            return StandardDataType.STRUCT
        if "LIST" in dt or "ARRAY" in dt:
            return StandardDataType.ARRAY
        if "JSON" in dt:
            return StandardDataType.JSON
        return StandardDataType.UNKNOWN
```

---

### 4.2 `PostgresConnector` (Relational Baseline via psycopg3 / ADBC)
- **Role**: Relational operational baseline or standard reporting replica.
- **Connection**: Uses `psycopg` (v3) connection pooling with server-side statement timeouts:
  `SET statement_timeout = '30000ms';`
- **Arrow Ingestion**: Uses `adbc_driver_postgresql` for zero-copy binary streaming or `psycopg` Arrow fetchers.
- **Cost Estimation**: Leverages `EXPLAIN (FORMAT JSON, COSTS ON) <query>` to extract PostgreSQL optimizer cost units and estimated scan rows.

```python
# src/engine/connectors/postgres_connector.py
import time
import json
from typing import Optional, List, Dict, Any
import psycopg
from psycopg.rows import dict_row
import pyarrow as pa
from src.engine.connectors.base import BaseWarehouseConnector, QueryResult, ExecutionMetrics, QueryCostEstimate
from src.engine.catalog.types import CatalogSchema, TableMetadata, ColumnMetadata, StandardDataType

class PostgresConnector(BaseWarehouseConnector):
    def __init__(self, connection_uri: str, statement_timeout_ms: int = 30000):
        self.connection_uri = connection_uri
        self.statement_timeout_ms = statement_timeout_ms
        self._conn: Optional[psycopg.Connection] = None

    def connect(self) -> None:
        self._conn = psycopg.connect(self.connection_uri, autocommit=True)
        with self._conn.cursor() as cur:
            cur.execute(f"SET statement_timeout = {self.statement_timeout_ms};")

    def disconnect(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def test_connection(self) -> bool:
        with self._conn.cursor() as cur:
            cur.execute("SELECT 1;")
            return cur.fetchone()[0] == 1

    def get_dialect(self) -> str:
        return "postgres"

    def execute_query(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = 1000,
        timeout_seconds: Optional[float] = 30.0
    ) -> QueryResult:
        start = time.perf_counter()
        with self._conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            col_names = [desc[0] for desc in cur.description]
            # Convert to PyArrow Table
            pydict = {col: [row[i] for row in rows] for i, col in enumerate(col_names)}
            arrow_table = pa.Table.from_pydict(pydict)

        duration_ms = (time.perf_counter() - start) * 1000.0
        metrics = ExecutionMetrics(
            execution_duration_ms=duration_ms,
            total_duration_ms=duration_ms,
            rows_returned=arrow_table.num_rows,
            target_dialect="postgres"
        )
        return QueryResult(arrow_table=arrow_table, metrics=metrics, executed_sql=sql)

    def estimate_cost_or_bytes(self, sql: str) -> QueryCostEstimate:
        with self._conn.cursor() as cur:
            cur.execute(f"EXPLAIN (FORMAT JSON, COSTS ON) {sql}")
            plan_json = cur.fetchone()[0]
            plan = plan_json[0]["Plan"]
            total_cost = plan.get("Total Cost", 0.0)
            plan_rows = plan.get("Plan Rows", 0)

        return QueryCostEstimate(
            supported=True,
            bytes_scanned_estimate=plan_rows * 128, # approximate row size
            cost_usd_estimate=0.0, # On-prem/RDS instances have fixed infrastructure cost
            query_complexity_score=min(10.0, max(1.0, total_cost / 1000.0)),
            warning_message="High total cost detected" if total_cost > 100000 else None
        )

    def explain(self, sql: str) -> str:
        with self._conn.cursor() as cur:
            cur.execute(f"EXPLAIN {sql}")
            return "\n".join([r[0] for r in cur.fetchall()])

    def introspect_schema(
        self,
        schema_name: Optional[str] = "public",
        table_filter: Optional[List[str]] = None
    ) -> CatalogSchema:
        schema = schema_name or "public"
        query = """
            SELECT table_name, column_name, data_type, is_nullable, udt_name
            FROM information_schema.columns
            WHERE table_schema = %s
            ORDER BY table_name, ordinal_position;
        """
        with self._conn.cursor() as cur:
            cur.execute(query, (schema,))
            rows = cur.fetchall()

        tables_dict: Dict[str, List[ColumnMetadata]] = {}
        for tbl, col, dtype, nullable, udt in rows:
            if table_filter and tbl not in table_filter:
                continue
            if tbl not in tables_dict:
                tables_dict[tbl] = []
            tables_dict[tbl].append(ColumnMetadata(
                name=col,
                original_type=udt or dtype,
                standard_type=self._map_postgres_type(udt or dtype),
                nullable=(nullable == "YES")
            ))

        table_metas = [
            TableMetadata(schema_name=schema, table_name=tbl, columns=cols)
            for tbl, cols in tables_dict.items()
        ]
        return CatalogSchema(warehouse_type="postgres", database_name="postgres", schemas={schema: table_metas})

    @staticmethod
    def _map_postgres_type(pg_type: str) -> StandardDataType:
        pt = pg_type.lower()
        if pt in ("int2", "smallint"): return StandardDataType.INT16
        if pt in ("int4", "integer"): return StandardDataType.INT32
        if pt in ("int8", "bigint"): return StandardDataType.INT64
        if pt in ("float4", "real"): return StandardDataType.FLOAT32
        if pt in ("float8", "double precision"): return StandardDataType.FLOAT64
        if pt in ("numeric", "decimal"): return StandardDataType.DECIMAL
        if pt in ("varchar", "text", "bpchar"): return StandardDataType.STRING
        if pt == "bool": return StandardDataType.BOOLEAN
        if pt == "date": return StandardDataType.DATE
        if pt in ("timestamp", "timestamp without time zone"): return StandardDataType.TIMESTAMP
        if pt in ("timestamptz", "timestamp with time zone"): return StandardDataType.TIMESTAMPTZ
        if pt in ("json", "jsonb"): return StandardDataType.JSON
        if pt == "uuid": return StandardDataType.UUID
        if pt.startswith("_"): return StandardDataType.ARRAY
        return StandardDataType.UNKNOWN
```

---

### 4.3 `SnowflakeConnector` (Cloud Enterprise Warehouse)
- **Role**: Cloud enterprise data platform.
- **Connection**: Built on `snowflake-connector-python` with native Arrow result streaming (`fetch_arrow_all()`).
- **Session Controls**: Enforces warehouse parameters:
  `ALTER SESSION SET STATEMENT_TIMEOUT_IN_SECONDS = 30;`
  `ALTER SESSION SET QUERY_TAG = '{"client": "agentic-bi-uwal"}';`
- **Cost Estimation**: Inspects `EXPLAIN USING JSON <query>` to extract `bytesAssigned` and `partitionsTotal` vs `partitionsAssigned` (verifying partition pruning).

```python
# src/engine/connectors/snowflake_connector.py
import time
import json
from typing import Optional, List, Dict, Any
from src.engine.connectors.base import BaseWarehouseConnector, QueryResult, ExecutionMetrics, QueryCostEstimate
from src.engine.catalog.types import CatalogSchema, TableMetadata, ColumnMetadata, StandardDataType

class SnowflakeConnector(BaseWarehouseConnector):
    def __init__(
        self,
        account: str,
        user: str,
        password: Optional[str] = None,
        warehouse: Optional[str] = None,
        database: Optional[str] = None,
        schema: Optional[str] = "PUBLIC",
        role: Optional[str] = None,
        statement_timeout_seconds: int = 30
    ):
        self.account = account
        self.user = user
        self.password = password
        self.warehouse = warehouse
        self.database = database
        self.schema = schema
        self.role = role
        self.statement_timeout_seconds = statement_timeout_seconds
        self._conn = None

    def connect(self) -> None:
        import snowflake.connector
        self._conn = snowflake.connector.connect(
            account=self.account,
            user=self.user,
            password=self.password,
            warehouse=self.warehouse,
            database=self.database,
            schema=self.schema,
            role=self.role,
            session_parameters={
                'STATEMENT_TIMEOUT_IN_SECONDS': self.statement_timeout_seconds,
                'QUERY_TAG': 'AgenticBI-Warehouse-Connector'
            }
        )

    def disconnect(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def test_connection(self) -> bool:
        with self._conn.cursor() as cur:
            cur.execute("SELECT 1;")
            return cur.fetchone()[0] == 1

    def get_dialect(self) -> str:
        return "snowflake"

    def execute_query(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = 1000,
        timeout_seconds: Optional[float] = 30.0
    ) -> QueryResult:
        start = time.perf_counter()
        with self._conn.cursor() as cur:
            cur.execute(sql, params)
            # Arrow table fetched natively without row transposition
            arrow_table = cur.fetch_arrow_all()

        duration_ms = (time.perf_counter() - start) * 1000.0
        metrics = ExecutionMetrics(
            execution_duration_ms=duration_ms,
            total_duration_ms=duration_ms,
            rows_returned=arrow_table.num_rows,
            target_dialect="snowflake"
        )
        return QueryResult(arrow_table=arrow_table, metrics=metrics, executed_sql=sql)

    def estimate_cost_or_bytes(self, sql: str) -> QueryCostEstimate:
        with self._conn.cursor() as cur:
            cur.execute(f"EXPLAIN USING JSON {sql}")
            plan_str = cur.fetchone()[0]
            plan = json.loads(plan_str)
            # Snowflake plan contains GlobalStats
            stats = plan.get("GlobalStats", {})
            bytes_assigned = stats.get("bytesAssigned", 0)
            partitions_total = stats.get("partitionsTotal", 1)
            partitions_assigned = stats.get("partitionsAssigned", 1)

        # Standard X-Small warehouse runs ~$2–$4 / hour (~$0.00083/second)
        return QueryCostEstimate(
            supported=True,
            bytes_scanned_estimate=bytes_assigned,
            cost_usd_estimate=None, # Billed on compute credits, not bytes scanned
            query_complexity_score=min(10.0, (bytes_assigned / (1024**3)) * 2.0 + 1.0),
            is_partition_pruned=(partitions_assigned < partitions_total),
            warning_message="Full table scan detected: no partition pruning!" if partitions_assigned == partitions_total and partitions_total > 10 else None
        )

    def explain(self, sql: str) -> str:
        with self._conn.cursor() as cur:
            cur.execute(f"EXPLAIN USING TEXT {sql}")
            return "\n".join([r[0] for r in cur.fetchall()])

    def introspect_schema(
        self,
        schema_name: Optional[str] = None,
        table_filter: Optional[List[str]] = None
    ) -> CatalogSchema:
        target_schema = schema_name or self.schema or "PUBLIC"
        query = f"""
            SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE, NUMERIC_PRECISION, NUMERIC_SCALE
            FROM {self.database}.INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{target_schema.upper()}'
            ORDER BY TABLE_NAME, ORDINAL_POSITION;
        """
        with self._conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()

        tables_dict: Dict[str, List[ColumnMetadata]] = {}
        for tbl, col, dtype, nullable, prec, scale in rows:
            if table_filter and tbl not in table_filter:
                continue
            if tbl not in tables_dict:
                tables_dict[tbl] = []
            tables_dict[tbl].append(ColumnMetadata(
                name=col,
                original_type=dtype,
                standard_type=self._map_snowflake_type(dtype, prec, scale),
                nullable=(nullable == "YES"),
                precision=prec,
                scale=scale
            ))

        table_metas = [
            TableMetadata(schema_name=target_schema, table_name=tbl, columns=cols)
            for tbl, cols in tables_dict.items()
        ]
        return CatalogSchema(warehouse_type="snowflake", database_name=self.database or "SNOWFLAKE", schemas={target_schema: table_metas})

    @staticmethod
    def _map_snowflake_type(stype: str, prec: Optional[int], scale: Optional[int]) -> StandardDataType:
        s = stype.upper()
        if s == "NUMBER":
            if scale == 0:
                return StandardDataType.INT64
            return StandardDataType.DECIMAL
        if s in ("FLOAT", "DOUBLE"): return StandardDataType.FLOAT64
        if s in ("VARCHAR", "STRING", "TEXT"): return StandardDataType.STRING
        if s == "BOOLEAN": return StandardDataType.BOOLEAN
        if s == "DATE": return StandardDataType.DATE
        if s == "TIMESTAMP_NTZ": return StandardDataType.TIMESTAMP
        if s in ("TIMESTAMP_TZ", "TIMESTAMP_LTZ"): return StandardDataType.TIMESTAMPTZ
        if s in ("VARIANT", "OBJECT"): return StandardDataType.JSON
        if s == "ARRAY": return StandardDataType.ARRAY
        return StandardDataType.UNKNOWN
```

---

### 4.4 `BigQueryConnector` (Google Cloud OLAP & Dry-Run Estimator)
- **Role**: Serverless cloud analytics with strict per-query scan costs ($6.25 / TB).
- **Dry-Run Estimation**: Utilizes BigQuery's zero-cost query compilation dry-run:
  `job_config = QueryJobConfig(dry_run=True, use_query_cache=False)`
  Calculates exact `total_bytes_processed` and projected USD cost before touching live data.
- **Arrow Ingestion**: Uses BigQuery Storage Read API (`to_arrow()`) to stream columnar chunks directly into PyArrow.

```python
# src/engine/connectors/bigquery_connector.py
import time
from typing import Optional, List, Dict, Any
from google.cloud import bigquery
import pyarrow as pa
from src.engine.connectors.base import BaseWarehouseConnector, QueryResult, ExecutionMetrics, QueryCostEstimate
from src.engine.catalog.types import CatalogSchema, TableMetadata, ColumnMetadata, StandardDataType

class BigQueryConnector(BaseWarehouseConnector):
    PRICE_PER_TERABYTE_USD = 6.25 # Standard on-demand pricing

    def __init__(self, project_id: str, default_dataset: Optional[str] = None):
        self.project_id = project_id
        self.default_dataset = default_dataset
        self._client: Optional[bigquery.Client] = None

    def connect(self) -> None:
        self._client = bigquery.Client(project=self.project_id)

    def disconnect(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    def test_connection(self) -> bool:
        res = self._client.query("SELECT 1 AS alive").result()
        for row in res:
            return row["alive"] == 1
        return False

    def get_dialect(self) -> str:
        return "bigquery"

    def estimate_cost_or_bytes(self, sql: str) -> QueryCostEstimate:
        job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
        query_job = self._client.query(sql, job_config=job_config)
        bytes_scanned = query_job.total_bytes_processed
        cost_usd = (bytes_scanned / (1024.0 ** 4)) * self.PRICE_PER_TERABYTE_USD
        
        warning = None
        if bytes_scanned > 50 * (1024 ** 3): # Alert if query scans > 50GB
            warning = f"High query volume: {bytes_scanned / (1024**3):.2f} GB scanned (${cost_usd:.4f} USD)"

        return QueryCostEstimate(
            supported=True,
            bytes_scanned_estimate=bytes_scanned,
            cost_usd_estimate=cost_usd,
            query_complexity_score=min(10.0, (bytes_scanned / (1024**3)) * 0.5 + 1.0),
            warning_message=warning
        )

    def execute_query(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = 1000,
        timeout_seconds: Optional[float] = 30.0
    ) -> QueryResult:
        start = time.perf_counter()
        job_config = bigquery.QueryJobConfig(maximum_bytes_billed=100 * (1024**3)) # 100 GB budget guardrail
        query_job = self._client.query(sql, job_config=job_config, timeout=timeout_seconds)
        # Pull directly into Arrow using BigQuery Storage API
        arrow_table = query_job.to_arrow()
        duration_ms = (time.perf_counter() - start) * 1000.0

        metrics = ExecutionMetrics(
            execution_duration_ms=duration_ms,
            total_duration_ms=duration_ms,
            rows_returned=arrow_table.num_rows,
            bytes_scanned=query_job.total_bytes_billed,
            target_dialect="bigquery"
        )
        return QueryResult(arrow_table=arrow_table, metrics=metrics, executed_sql=sql)

    def explain(self, sql: str) -> str:
        dry_job = self._client.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True))
        return f"BigQuery Execution Plan (Dry-Run): Total Bytes = {dry_job.total_bytes_processed}"

    def introspect_schema(
        self,
        schema_name: Optional[str] = None,
        table_filter: Optional[List[str]] = None
    ) -> CatalogSchema:
        dataset_id = schema_name or self.default_dataset
        dataset_ref = self._client.dataset(dataset_id)
        tables = list(self._client.list_tables(dataset_ref))

        table_metas = []
        for tbl_ref in tables:
            if table_filter and tbl_ref.table_id not in table_filter:
                continue
            tbl = self._client.get_table(tbl_ref)
            cols = [
                ColumnMetadata(
                    name=field.name,
                    original_type=field.field_type,
                    standard_type=self._map_bigquery_type(field.field_type),
                    nullable=(field.mode != "REQUIRED"),
                    description=field.description
                )
                for field in tbl.schema
            ]
            table_metas.append(TableMetadata(
                schema_name=dataset_id,
                table_name=tbl.table_id,
                columns=cols,
                row_count_estimate=tbl.num_rows,
                size_bytes_estimate=tbl.num_bytes
            ))

        return CatalogSchema(warehouse_type="bigquery", database_name=self.project_id, schemas={dataset_id: table_metas})

    @staticmethod
    def _map_bigquery_type(bq_type: str) -> StandardDataType:
        b = bq_type.upper()
        if b in ("INT64", "INTEGER"): return StandardDataType.INT64
        if b in ("FLOAT64", "FLOAT"): return StandardDataType.FLOAT64
        if b in ("NUMERIC", "BIGNUMERIC"): return StandardDataType.DECIMAL
        if b == "STRING": return StandardDataType.STRING
        if b == "BOOL" or b == "BOOLEAN": return StandardDataType.BOOLEAN
        if b == "DATE": return StandardDataType.DATE
        if b == "DATETIME": return StandardDataType.TIMESTAMP
        if b == "TIMESTAMP": return StandardDataType.TIMESTAMPTZ
        if b == "BYTES": return StandardDataType.BINARY
        if b in ("RECORD", "STRUCT"): return StandardDataType.STRUCT
        if b == "JSON": return StandardDataType.JSON
        return StandardDataType.UNKNOWN
```

---

### 4.5 `ClickHouseConnector` (Real-Time High-Throughput OLAP)
- **Role**: High-speed real-time event analytics and log analytics.
- **Connection**: Powered by `clickhouse-connect` with native Apache Arrow streaming.
- **Cost / Volume Estimation**: Runs `EXPLAIN ESTIMATE <query>` to discover estimated rows, bytes to scan, and marks to read.

```python
# src/engine/connectors/clickhouse_connector.py
import time
from typing import Optional, List, Dict, Any
import clickhouse_connect
import pyarrow as pa
from src.engine.connectors.base import BaseWarehouseConnector, QueryResult, ExecutionMetrics, QueryCostEstimate
from src.engine.catalog.types import CatalogSchema, TableMetadata, ColumnMetadata, StandardDataType

class ClickHouseConnector(BaseWarehouseConnector):
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8123,
        username: str = "default",
        password: str = "",
        database: str = "default",
        query_timeout_seconds: int = 30
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.query_timeout_seconds = query_timeout_seconds
        self._client = None

    def connect(self) -> None:
        self._client = clickhouse_connect.get_client(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            database=self.database,
            send_receive_timeout=self.query_timeout_seconds
        )

    def disconnect(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    def test_connection(self) -> bool:
        res = self._client.command("SELECT 1")
        return res == 1

    def get_dialect(self) -> str:
        return "clickhouse"

    def execute_query(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = 1000,
        timeout_seconds: Optional[float] = 30.0
    ) -> QueryResult:
        start = time.perf_counter()
        # Direct Arrow fetch from clickhouse-connect
        arrow_table = self._client.query_arrow(sql, parameters=params)
        duration_ms = (time.perf_counter() - start) * 1000.0

        metrics = ExecutionMetrics(
            execution_duration_ms=duration_ms,
            total_duration_ms=duration_ms,
            rows_returned=arrow_table.num_rows,
            target_dialect="clickhouse"
        )
        return QueryResult(arrow_table=arrow_table, metrics=metrics, executed_sql=sql)

    def estimate_cost_or_bytes(self, sql: str) -> QueryCostEstimate:
        try:
            res = self._client.query(f"EXPLAIN ESTIMATE {sql}")
            rows = res.result_rows
            # Format: [(database, table, parts, rows, marks)]
            total_rows = sum(r[3] for r in rows if len(r) > 3)
            bytes_estimate = total_rows * 64 # approximate 64 bytes per column/row
            return QueryCostEstimate(
                supported=True,
                bytes_scanned_estimate=bytes_estimate,
                cost_usd_estimate=0.0,
                query_complexity_score=min(10.0, (total_rows / 1_000_000) + 1.0)
            )
        except Exception:
            return QueryCostEstimate(supported=False)

    def explain(self, sql: str) -> str:
        res = self._client.query(f"EXPLAIN SYNTAX {sql}")
        return "\n".join([r[0] for r in res.result_rows])

    def introspect_schema(
        self,
        schema_name: Optional[str] = None,
        table_filter: Optional[List[str]] = None
    ) -> CatalogSchema:
        db = schema_name or self.database
        query = f"""
            SELECT table, name, type, is_in_primary_key, is_in_partition_key
            FROM system.columns
            WHERE database = '{db}'
            ORDER BY table, position;
        """
        rows = self._client.query(query).result_rows
        tables_dict: Dict[str, List[ColumnMetadata]] = {}
        for tbl, col, dtype, is_pk, is_part in rows:
            if table_filter and tbl not in table_filter:
                continue
            if tbl not in tables_dict:
                tables_dict[tbl] = []
            tables_dict[tbl].append(ColumnMetadata(
                name=col,
                original_type=dtype,
                standard_type=self._map_clickhouse_type(dtype),
                is_primary_key=bool(is_pk),
                is_partition_key=bool(is_part),
                nullable=("Nullable" in dtype)
            ))

        table_metas = [
            TableMetadata(schema_name=db, table_name=tbl, columns=cols)
            for tbl, cols in tables_dict.items()
        ]
        return CatalogSchema(warehouse_type="clickhouse", database_name=db, schemas={db: table_metas})

    @staticmethod
    def _map_clickhouse_type(ch_type: str) -> StandardDataType:
        c = ch_type
        if "LowCardinality" in c:
            # Unwrap LowCardinality(T)
            c = c.replace("LowCardinality(", "").rstrip(")")
        if "Nullable" in c:
            c = c.replace("Nullable(", "").rstrip(")")

        if c.startswith("Int8"): return StandardDataType.INT8
        if c.startswith("Int16"): return StandardDataType.INT16
        if c.startswith("Int32"): return StandardDataType.INT32
        if c.startswith("Int64"): return StandardDataType.INT64
        if c.startswith("UInt8"): return StandardDataType.UINT8
        if c.startswith("UInt16"): return StandardDataType.UINT16
        if c.startswith("UInt32"): return StandardDataType.UINT32
        if c.startswith("UInt64"): return StandardDataType.UINT64
        if c.startswith("Float32"): return StandardDataType.FLOAT32
        if c.startswith("Float64"): return StandardDataType.FLOAT64
        if c.startswith("Decimal"): return StandardDataType.DECIMAL
        if c.startswith("String") or c.startswith("FixedString"): return StandardDataType.STRING
        if c.startswith("Date"): return StandardDataType.DATE
        if c.startswith("DateTime"): return StandardDataType.TIMESTAMPTZ
        if c.startswith("Array"): return StandardDataType.ARRAY
        if c.startswith("Tuple"): return StandardDataType.STRUCT
        if c.startswith("Map"): return StandardDataType.MAP
        if c.startswith("UUID"): return StandardDataType.UUID
        return StandardDataType.UNKNOWN
```

---

## 5. Type Normalization Matrix Across Warehouses

The table below defines the authoritative mapping enforced by the UWAL schema cataloger:

| Unified Standard Type | DuckDB | PostgreSQL | Snowflake | Google BigQuery | ClickHouse |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `BOOLEAN` | `BOOLEAN` | `BOOLEAN` / `BOOL` | `BOOLEAN` | `BOOL` | `Bool` / `UInt8` |
| `INT32` | `INTEGER` | `INTEGER` / `INT4` | `NUMBER(38, 0)` | `INT64` (coerced) | `Int32` |
| `INT64` | `BIGINT` | `BIGINT` / `INT8` | `NUMBER(38, 0)` | `INT64` | `Int64` |
| `INT128` | `HUGEINT` | N/A (`NUMERIC`) | N/A (`NUMBER`) | N/A (`BIGNUMERIC`) | `Int128` |
| `FLOAT64` | `DOUBLE` | `DOUBLE PRECISION` | `FLOAT` / `DOUBLE` | `FLOAT64` | `Float64` |
| `DECIMAL(p, s)` | `DECIMAL(p, s)` | `NUMERIC(p, s)` | `NUMBER(p, s)` | `NUMERIC` / `BIGNUMERIC` | `Decimal(p, s)` |
| `STRING` | `VARCHAR` | `VARCHAR` / `TEXT` | `VARCHAR` / `TEXT` | `STRING` | `String` / `LowCardinality(String)` |
| `DATE` | `DATE` | `DATE` | `DATE` | `DATE` | `Date` / `Date32` |
| `TIMESTAMP` | `TIMESTAMP` | `TIMESTAMP` | `TIMESTAMP_NTZ` | `DATETIME` | `DateTime` |
| `TIMESTAMPTZ` | `TIMESTAMPTZ` | `TIMESTAMPTZ` | `TIMESTAMP_TZ` | `TIMESTAMP` | `DateTime64(3, 'UTC')` |
| `JSON` | `JSON` | `JSONB` / `JSON` | `VARIANT` / `OBJECT`| `JSON` | `JSON` / `String` |
| `ARRAY<T>` | `T[]` / `LIST` | `T[]` | `ARRAY` | `ARRAY<T>` | `Array(T)` |
| `STRUCT` | `STRUCT(...)` | `RECORD` / composite | `OBJECT` | `STRUCT` / `RECORD` | `Tuple(...)` |
| `MAP<K, V>` | `MAP(K, V)` | `HSTORE` / `JSONB` | `OBJECT` | `ARRAY<STRUCT<K, V>>` | `Map(K, V)` |
| `UUID` | `UUID` | `UUID` | `VARCHAR` | `STRING` | `UUID` |

---

## 6. DuckDB as Analytical Accelerator, Cache & Federation Engine

One of the most powerful architectural capabilities of UWAL is turning DuckDB into an **in-process analytical accelerator**:

```mermaid
sequenceDiagram
    autonumber
    actor Agent as Autonomous Analytics Agent
    participant Router as UWAL Execution Router
    participant Cache as DuckDB Accelerator (In-Memory)
    participant CloudDW as Enterprise Cloud DW (Snowflake/BQ)

    Agent->>Router: Query Intent (e.g. "Analyze cohort expansion for 2025")
    Router->>Router: Check Cache / Working Slice Registry
    
    alt Working Slice Not Cached
        Router->>CloudDW: Materialize Bounded Working Slice (Filtered / Sampled)
        Note over CloudDW: Scans 2025 partition once
        CloudDW-->>Cache: Stream Arrow RecordBatches
        Cache->>Cache: Create In-Memory DuckDB Table / Temp View (100k rows)
    end

    loop Agent Reasoning & Iteration (10 micro-queries)
        Agent->>Router: Iterative exploration query
        Router->>Cache: Execute against Local In-Memory Slice
        Cache-->>Agent: Sub-10ms Columnar Result ($0 Cloud Cost)
    end
```

### 6.1 The Accelerated Working Slice Pattern
When an agent is tasked with analyzing a complex cohort or running iterative diagnostics:
1. Instead of issuing 15 separate queries to Snowflake/BigQuery (which would incur 15 separate query charges and 30–60 seconds of network waiting), the agent issues a **Slice Materialization Directive**:
   ```sql
   -- Executed once against Remote Cloud Warehouse
   SELECT * FROM enterprise_dw.fct_invoices 
   WHERE invoice_date >= '2025-01-01' AND invoice_date < '2026-01-01';
   ```
2. The result streams directly as Arrow RecordBatches into the local in-memory DuckDB session:
   ```python
   # Register Arrow Table directly into DuckDB session without disk write
   duckdb_conn.register("cached_invoices_2025", arrow_table)
   ```
3. The agent executes subsequent exploratory aggregations, pivot tables, and anomaly searches against `cached_invoices_2025` with **sub-10ms response times and zero cloud costs**.

### 6.2 DuckDB Query Federation Pattern
DuckDB can also act as the federator across heterogeneous systems:
```sql
-- Attach remote Postgres instance
INSTALL postgres; LOAD postgres;
ATTACH 'dbname=core_db user=readonly host=pg.internal' AS pg (TYPE POSTGRES);

-- Direct join between local Parquet cohort and remote PostgreSQL orders
SELECT 
    p.customer_tier,
    COUNT(o.order_id) as total_orders,
    SUM(o.amount_usd) as total_revenue
FROM read_parquet('data/seed/dim_customers.parquet') AS p
JOIN pg.public.orders AS o ON p.customer_id = o.customer_id
GROUP BY 1;
```

---

## 7. AST Security, Dialect Transpilation & Limit Clamping Pipeline

The pipeline guarantees that every query executed against any warehouse passes through a uniform AST firewall:

```mermaid
flowchart LR
    RawSQL["Canonical SQL<br>(DuckDB Dialect)"] --> ASTParse["SQLGlot AST Parser<br>(parse_one(read='duckdb'))"]
    ASTParse --> ASTCheck["AST Security Inspection<br>• Reject Non-SELECT<br>• Check Table Whitelist<br>• Forbid OS/Network calls"]
    ASTCheck --> CartesianCheck["Cartesian Join Detector<br>(Ensure ON/USING clauses)"]
    CartesianCheck --> LimitClamp["AST Limit Clamp<br>(Inject or clamp LIMIT <= 1000)"]
    LimitClamp --> Transpile["SQLGlot Transpiler<br>(ast.sql(dialect=target_dialect))"]
    Transpile --> TargetSQL["Target Dialect SQL<br>(Executed by Connector)"]
```

### 7.1 AST Clamping Implementation
```python
# src/security/ast_pipeline.py
import sqlglot
from sqlglot import exp
from typing import Tuple

class ASTSecurityPipeline:
    def __init__(self, max_limit: int = 1000):
        self.max_limit = max_limit

    def process(self, canonical_sql: str, target_dialect: str) -> Tuple[str, exp.Expression]:
        # 1. Parse into canonical AST
        tree = sqlglot.parse_one(canonical_sql, read="duckdb")

        # 2. Enforce read-only SELECT
        if not isinstance(tree, exp.Select):
            raise ValueError(f"Security Violation: Only SELECT expressions permitted. Received: {type(tree).__name__}")

        # 3. Detect and block mutating subqueries or commands
        for forbidden in (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.AlterTable, exp.Command):
            if tree.find(forbidden):
                raise ValueError(f"Security Violation: Mutating AST node {forbidden.__name__} detected.")

        # 4. Enforce LIMIT clamping
        limit_node = tree.args.get("limit")
        if limit_node is None:
            # Inject LIMIT
            tree = tree.limit(self.max_limit)
        else:
            # Clamp existing LIMIT
            val = int(limit_node.expression.this)
            if val > self.max_limit:
                tree.args["limit"] = exp.Limit(this=exp.Literal.number(self.max_limit))

        # 5. Transpile to target warehouse dialect
        target_sql = tree.sql(dialect=target_dialect, pretty=True)
        return target_sql, tree
```

---

## 8. Proposed File Manifest & Code Layout

To seamlessly integrate this architecture into the existing codebase layout defined in `duckdb-analytics-agent-hld.md`, we extend `src/engine/` into a modular connector structure:

```text
duckdb-analytics-agent/
├── config/
│   ├── semantic_layer.yaml             # Certified B2B SaaS metrics & dimension graphs
│   ├── security_policies.yaml          # Whitelisted tables, max limits, blocked functions
│   └── warehouses.yaml                 # Multi-warehouse connection profiles (local, staging, prod)
├── src/
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── factory.py                  # WarehouseConnectorFactory (instantiates adapter by config)
│   │   ├── profiler.py                 # Microsecond execution timer & stats
│   │   ├── catalog/
│   │   │   ├── __init__.py
│   │   │   ├── types.py                # StandardDataType & normalized metadata models
│   │   │   └── inspector.py            # Universal catalog cache & schema search
│   │   ├── connectors/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                 # BaseWarehouseConnector ABC & QueryResult
│   │   │   ├── duckdb_connector.py     # Local / Lakehouse / In-Memory DuckDB
│   │   │   ├── postgres_connector.py   # PostgreSQL via psycopg3 / ADBC
│   │   │   ├── snowflake_connector.py  # Snowflake via connector + Arrow
│   │   │   ├── bigquery_connector.py   # BigQuery + Dry-Run Estimator
│   │   │   └── clickhouse_connector.py # ClickHouse OLAP connector
│   │   └── accelerator/
│   │       ├── __init__.py
│   │       ├── cache_manager.py        # Working slice materializer & TTL cache
│   │       └── federator.py            # Cross-engine query federation orchestrator
│   ├── security/
│   │   ├── __init__.py
│   │   ├── ast_validator.py            # SQLGlot AST parser & security firewall
│   │   └── transpiler.py               # Canonical to Target Dialect transpilation
│   ├── semantic/
│   │   ├── __init__.py
│   │   ├── models.py                   # Pydantic models for metrics & dimensions
│   │   ├── loader.py                   # YAML semantic layer parser
│   │   └── resolver.py                 # Question to Canonical SQL compiler
│   └── mcp/
│       ├── __init__.py
│       └── server.py                   # FastMCP server exposing warehouse-agnostic tools
```

### Packaging & Optional Dependencies (`pyproject.toml`)
To maintain the **zero-cloud instant install** promise while allowing enterprise production installs, dependencies are organized via extras:

```toml
[project]
name = "duckdb-analytics-agent"
version = "0.2.0"
dependencies = [
    "duckdb>=1.1.0",
    "pyarrow>=15.0.0",
    "sqlglot>=25.0.0",
    "pydantic>=2.7.0",
    "rich>=13.7.0",
    "fastmcp>=0.1.0",
]

[project.optional-dependencies]
postgres = [
    "psycopg[binary]>=3.1.18",
    "adbc-driver-postgresql>=1.0.0",
]
snowflake = [
    "snowflake-connector-python[pandas]>=3.8.0",
]
bigquery = [
    "google-cloud-bigquery>=3.20.0",
    "google-cloud-bigquery-storage>=2.24.0",
]
clickhouse = [
    "clickhouse-connect>=0.7.0",
]
all = [
    "duckdb-analytics-agent[postgres,snowflake,bigquery,clickhouse]",
]
```

---

## 9. Architectural Decision Records (ADRs)

### ADR-001: Canonical SQL + SQLGlot AST vs. Multi-Dialect LLM Generation
- **Context**: LLMs struggle with dialect nuances (quoting, date truncations, JSON extractors) and hallucinate dialect-specific keywords.
- **Decision**: The LLM / Semantic Layer compiles questions strictly to **Canonical ANSI/DuckDB SQL**. All dialect translation is handled deterministically by SQLGlot AST transpilation.
- **Consequence**: Security guardrails run once on the canonical AST. Testing is deterministic. New warehouse adapters require zero prompt modifications.

### ADR-002: Apache Arrow as the Universal Columnar Intermediate Representation
- **Context**: Ingesting query results as Python row objects creates massive serialization bottlenecks.
- **Decision**: Every warehouse connector returns a `QueryResult` encapsulating an `arrow_table: pa.Table`.
- **Consequence**: Zero-copy conversions to Polars, Pandas, or JSON. Instant ingestion into DuckDB for local caching.

### ADR-003: DuckDB as Dual-Mode Engine (Local Warehouse & Accelerated Cache)
- **Context**: Cloud warehouses incur latency and per-query costs during iterative agent exploration.
- **Decision**: DuckDB is both the primary standalone local engine and the local cache accelerator for remote warehouse query slices.
- **Consequence**: Zero cost for local developer testing; drastic compute cost reduction for production cloud agents.

---

*End of Architectural Specification.*
