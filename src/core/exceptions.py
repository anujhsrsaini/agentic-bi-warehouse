"""Domain exceptions for agentic-bi-warehouse."""

class AgenticBIError(Exception):
    """Base exception for all agentic BI errors."""
    pass


class WarehouseConnectionError(AgenticBIError):
    """Raised when connecting to a warehouse backend fails."""
    pass


class QueryExecutionError(AgenticBIError):
    """Raised when a warehouse query execution fails at runtime."""
    def __init__(self, message: str, sql: str | None = None, dialect: str | None = None, raw_error: Exception | None = None):
        super().__init__(message)
        self.sql = sql
        self.dialect = dialect
        self.raw_error = raw_error


class SecurityViolationError(AgenticBIError):
    """Raised when an AST security guardrail or policy check is violated."""
    def __init__(self, message: str, violation_type: str, details: dict | None = None):
        super().__init__(f"Security Violation [{violation_type}]: {message}")
        self.violation_type = violation_type
        self.details = details or {}


class SemanticResolutionError(AgenticBIError):
    """Raised when resolving metrics, dimensions, or join paths in the semantic layer fails."""
    pass


class SelfHealingExhaustedError(AgenticBIError):
    """Raised when query self-healing fails after maximum retry attempts."""
    def __init__(self, message: str, attempts: int, last_error: str):
        super().__init__(f"Self-healing exhausted after {attempts} attempts. Last error: {last_error}")
        self.attempts = attempts
        self.last_error = last_error
