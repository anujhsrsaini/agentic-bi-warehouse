"""Connection Factory and Session Manager."""

from __future__ import annotations

from src.core.config import settings
from src.core.exceptions import WarehouseConnectionError
from src.engine.cache import ParquetQueryCache
from src.engine.connectors.base import BaseWarehouseConnector
from src.engine.connectors.duckdb_connector import DuckDBConnector
from src.engine.connectors.postgres_connector import PostgresConnector
from src.engine.connectors.snowflake_connector import SnowflakeConnector
from src.engine.connectors.bigquery_connector import BigQueryConnector
from src.engine.connectors.clickhouse_connector import ClickHouseConnector


class WarehouseSession:
    """Manages active warehouse connection and query cache."""

    def __init__(self, connector: BaseWarehouseConnector | None = None, enable_cache: bool = True):
        self.connector = connector or self._create_default_connector()
        self.enable_cache = enable_cache
        self.cache = ParquetQueryCache() if enable_cache else None

    def _create_default_connector(self) -> BaseWarehouseConnector:
        """Create connector based on settings."""
        w_type = settings.warehouse_type.lower()
        if w_type == "duckdb":
            return DuckDBConnector()
        elif w_type == "postgres":
            return PostgresConnector()
        elif w_type == "snowflake":
            return SnowflakeConnector()
        elif w_type == "bigquery":
            return BigQueryConnector()
        elif w_type == "clickhouse":
            return ClickHouseConnector()
        else:
            raise WarehouseConnectionError(f"Unsupported warehouse type: {w_type}")

    def get_connector(self) -> BaseWarehouseConnector:
        return self.connector
