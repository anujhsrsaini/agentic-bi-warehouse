"""Column-Level Data Lineage & Mathematical Explainability Engine.

Uses sqlglot.lineage to construct a Directed Acyclic Graph (DAG) tracing
calculated metrics across CTEs, arithmetic operations, and joins back to
raw source tables.

Outputs:
1. Mermaid Flowchart (flowchart LR)
2. Rich ASCII Hierarchy Tree
3. Mathematical Audit Trail Narrative
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import sqlglot
from sqlglot.lineage import lineage


@dataclass
class LineageNode:
    """Node in the column lineage graph."""
    name: str
    source_table: str | None = None
    expression: str | None = None
    children: list[LineageNode] = field(default_factory=list)
    available: bool = True


class ColumnLineageTracer:
    """Traces and renders column-level data lineage."""

    def __init__(self, schema: dict[str, Any] | None = None):
        self.schema = schema or {}

    def trace(self, column: str, sql: str, dialect: str = "duckdb") -> LineageNode:
        """Trace lineage of a column in SQL query."""
        try:
            node = lineage(column, sql, schema=self.schema, dialect=dialect)
            return self._build_node(node)
        except Exception:
            return LineageNode(name=column, available=False)

    def _build_node(self, node: Any) -> LineageNode:
        source_tbl = str(node.source.name) if hasattr(node, "source") and hasattr(node.source, "name") else None
        expr_str = str(node.expression) if hasattr(node, "expression") else None
        
        children = []
        if hasattr(node, "downstream"):
            for child in node.downstream:
                children.append(self._build_node(child))

        return LineageNode(
            name=str(node.name) if hasattr(node, "name") else "unknown",
            source_table=source_tbl,
            expression=expr_str,
            children=children,
        )

    def to_mermaid(self, column: str, sql: str) -> str:
        """Generate Mermaid flowchart diagram."""
        root = self.trace(column, sql)
        if not root.available:
            return f'flowchart LR\n    unavailable["Lineage unavailable for {column}"]'
        lines = ["flowchart LR"]
        visited = set()

        def _traverse(curr: LineageNode, parent_id: str | None = None):
            node_id = f"node_{abs(hash(curr.name + str(curr.source_table)))}"
            label = f"{curr.source_table}.{curr.name}" if curr.source_table else curr.name
            
            if node_id not in visited:
                lines.append(f'    {node_id}["{label}"]')
                visited.add(node_id)

            if parent_id:
                lines.append(f"    {node_id} --> {parent_id}")

            for ch in curr.children:
                _traverse(ch, node_id)

        _traverse(root)
        return "\n".join(lines)

    def to_ascii_tree(self, column: str, sql: str) -> str:
        """Generate ASCII hierarchy tree string."""
        root = self.trace(column, sql)
        if not root.available:
            return f"Lineage unavailable for {column}"
        output_lines = [f"Lineage: {column}"]

        def _render(node: LineageNode, prefix: str = "", is_last: bool = True):
            connector = "└── " if is_last else "├── "
            label = f"{node.source_table}.{node.name}" if node.source_table else node.name
            output_lines.append(f"{prefix}{connector}{label}")
            new_prefix = prefix + ("    " if is_last else "│   ")
            for i, child in enumerate(node.children):
                _render(child, new_prefix, i == len(node.children) - 1)

        for i, ch in enumerate(root.children):
            _render(ch, "", i == len(root.children) - 1)

        return "\n".join(output_lines)

    def generate_audit_narrative(self, column: str, sql: str) -> str:
        """Generate executive plain-English mathematical audit narrative."""
        node = self.trace(column, sql)
        if not node.available:
            return f"Mathematical Lineage Audit for [{column}]: lineage unavailable."
        return f"Mathematical Lineage Audit for [{column}]:\nExpression: {node.expression}"
