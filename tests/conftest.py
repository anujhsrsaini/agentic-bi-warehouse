"""Pytest fixtures for Governed DuckDB Analytics Agent."""

import pytest
from src.engine.connectors.duckdb_connector import DuckDBConnector
from src.semantic.loader import SemanticLayerLoader
from src.semantic.resolver import SemanticQueryResolver
from src.security.ast_validator import ASTSecurityValidator
from src.agents.orchestrator import AgenticBIOrchestrator


@pytest.fixture(scope="session")
def duckdb_connector():
    """Session-scoped DuckDB connector with pre-seeded data."""
    conn = DuckDBConnector()
    conn.connect()
    yield conn
    conn.disconnect()


@pytest.fixture
def semantic_config():
    """Loaded semantic layer configuration."""
    return SemanticLayerLoader().load()


@pytest.fixture
def semantic_resolver(semantic_config):
    """Semantic query resolver instance."""
    return SemanticQueryResolver(config=semantic_config)


@pytest.fixture
def ast_validator():
    """SQLGlot AST security validator."""
    return ASTSecurityValidator()


@pytest.fixture
def orchestrator():
    """End-to-end multi-agent orchestrator."""
    return AgenticBIOrchestrator()
