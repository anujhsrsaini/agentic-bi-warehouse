"""Application configuration and settings."""

from __future__ import annotations

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Global configuration settings for Agentic BI Warehouse."""

    model_config = SettingsConfigDict(env_prefix="AGENTIC_BI_", case_sensitive=False)

    # Project paths
    project_root: Path = PROJECT_ROOT
    data_dir: Path = PROJECT_ROOT / "data" / "seed"
    cache_dir: Path = PROJECT_ROOT / ".cache"
    config_dir: Path = PROJECT_ROOT / "config"

    # Default Warehouse Connector
    warehouse_type: str = Field(default="duckdb", description="Target warehouse: duckdb, postgres, snowflake, bigquery, clickhouse")
    
    # DuckDB Engine Settings
    duckdb_path: str = ":memory:"
    duckdb_sandbox_enabled: bool = True
    duckdb_memory_limit: str = "2GB"
    duckdb_threads: int = 4
    duckdb_max_connections: int = 5

    # Security & Guardrail Limits
    max_query_limit: int = 1000
    query_timeout_ms: int = 30000
    allow_cartesian_joins: bool = False
    redact_pii: bool = True

    # Cloud Warehouse Credentials (optional)
    postgres_uri: str | None = None
    snowflake_account: str | None = None
    snowflake_user: str | None = None
    snowflake_password: str | None = None
    snowflake_warehouse: str | None = None
    snowflake_database: str | None = None
    snowflake_schema: str | None = None

    bigquery_project_id: str | None = None
    bigquery_dataset_id: str | None = None
    bigquery_max_bytes_billed: int = 10 * 1024 * 1024 * 1024  # 10 GB limit

    clickhouse_host: str = "localhost"
    clickhouse_port: int = 8123
    clickhouse_user: str = "default"
    clickhouse_password: str = ""
    clickhouse_database: str = "default"


settings = Settings()
