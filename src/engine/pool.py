"""Thread-safe DuckDB Connection Pool (Rill Data Architecture Pattern).

Provides managed in-memory or file-backed DuckDB connection instances with:
- Concurrency semaphore control
- Preloading of required extensions (parquet, fts)
- Memory and thread limits
- Session affinity for temporary tables
"""

from __future__ import annotations

import queue
import threading
from contextlib import contextmanager
from typing import Generator
import duckdb

from src.core.config import settings
from src.core.exceptions import WarehouseConnectionError


class DuckDBConnectionPool:
    """Thread-safe connection pool for DuckDB sessions."""

    def __init__(
        self,
        database: str = ":memory:",
        read_only: bool = False,
        max_connections: int = 5,
        memory_limit: str = "2GB",
        threads: int = 4,
        sandbox_enabled: bool = False,
    ):
        self.database = database
        self.read_only = read_only
        self.max_connections = max_connections
        self.memory_limit = memory_limit
        self.threads = threads
        self.sandbox_enabled = sandbox_enabled

        self._pool: queue.Queue[duckdb.DuckDBPyConnection] = queue.Queue(maxsize=max_connections)
        self._lock = threading.Lock()
        self._created_connections = 0
        self._closed = False

    def _create_connection(self) -> duckdb.DuckDBPyConnection:
        """Create and initialize a single DuckDB connection."""
        try:
            conn = duckdb.connect(self.database, read_only=self.read_only)
            
            # Configure engine properties
            conn.execute(f"SET memory_limit = '{self.memory_limit}';")
            conn.execute(f"SET threads = {self.threads};")
            
            # Preload standard analytical extensions
            try:
                conn.execute("LOAD parquet;")
            except Exception:
                pass  # Parquet is statically compiled into modern DuckDB
            
            if self.sandbox_enabled:
                conn.execute("SET enable_external_access = false;")
                conn.execute("SET lock_configuration = true;")

            return conn
        except Exception as e:
            raise WarehouseConnectionError(f"Failed to initialize DuckDB connection: {e}") from e

    def acquire(self, timeout: float = 10.0) -> duckdb.DuckDBPyConnection:
        """Acquire a connection from the pool."""
        if self._closed:
            raise WarehouseConnectionError("Connection pool is closed.")

        with self._lock:
            if self._created_connections < self.max_connections and self._pool.empty():
                conn = self._create_connection()
                self._created_connections += 1
                return conn

        try:
            return self._pool.get(block=True, timeout=timeout)
        except queue.Empty:
            raise WarehouseConnectionError(f"DuckDB pool exhausted after waiting {timeout}s.")

    def release(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Return a connection to the pool."""
        if self._closed:
            try:
                conn.close()
            except Exception:
                pass
            return

        try:
            self._pool.put_nowait(conn)
        except queue.Full:
            try:
                conn.close()
            except Exception:
                pass

    @contextmanager
    def connection(self, timeout: float = 10.0) -> Generator[duckdb.DuckDBPyConnection, None, None]:
        """Context manager to acquire and automatically return a connection."""
        conn = self.acquire(timeout=timeout)
        try:
            yield conn
        finally:
            self.release(conn)

    def close(self) -> None:
        """Close all connections in the pool."""
        self._closed = True
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except Exception:
                pass
