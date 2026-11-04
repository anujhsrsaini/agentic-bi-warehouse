# Autonomous Agentic BI & Warehouse System: The 10-Star Innovation Blueprint

> **Author**: Agentic BI Innovation Architect  
> **Status**: Approved Architectural Blueprint  
> **Target System**: Governed Agentic BI & Poly-Warehouse Question-Answering Engine  
> **Target Warehouse Engines**: DuckDB (Embedded OLAP & Vector Store), Snowflake, PostgreSQL, BigQuery, ClickHouse  

---

## Executive Summary & Innovation Paradigm

Traditional Text-to-SQL tools operate as brittle, single-shot translation interfaces: a user submits a question, an LLM outputs raw SQL, and if the syntax executes, a flat tabular grid is returned. In enterprise business intelligence, this paradigm fails across five critical dimensions:

1. **The Setup Friction Barrier**: Data teams must spend weeks hand-authoring semantic definitions, metric expressions, and join graphs before the system answers a single query.
2. **The "Black Box" Trust Barrier**: When an executive asks *"Why is our Net Retention 108%?"*, they are shown a number without mathematical proof, lineage, or CTE audit trails.
3. **The Categorical Value Mismatch**: Real users query colloquial entities (*"Google"*, *"US"*, *"iPhone 15"*), whereas data warehouses store legal entities (*"Alphabet Inc."*, *"USA"*, *"IPHONE-15-PRO-MAX"*), causing silent filter misses and empty results.
4. **The Descriptive Analytics Trap**: Legacy BI only answers *"What happened?"* (e.g., *"Revenue dropped 12%"*), forcing business analysts to spend days manually slicing tables to discover *"Why did it happen?"*.
5. **The Visual Monoculture**: Outputting raw markdown tables forces users to copy-paste numbers into spreadsheets instead of providing interactive, multimodal visual artifacts, KPI scorecards, and guided drill-downs.

This blueprint details the **Five Breakthrough Pillars** that transform our system from a standard text-to-SQL tool into a world-class, 10-star autonomous data analyst.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                          THE 10-STAR AUTONOMOUS DATA ANALYST                                    │
└────────────────────────────────┬────────────────────────────────────────────────────────────────┘
                                 │
         ┌───────────────────────┼────────────────────────┬───────────────────────┐
         ▼                       ▼                        ▼                       ▼
  ┌─────────────┐         ┌─────────────┐          ┌─────────────┐         ┌─────────────┐
  │  Pillar 1   │         │  Pillar 2   │          │  Pillar 3   │         │  Pillar 4   │
  │  Zero-to-One│         │Column-Level │          │Fuzzy Entity │         │ Diagnostic  │
  │  Semantic   │         │Data Lineage │          │Grounding &  │         │    "Why"    │
  │Bootstrapping│         │& Math Proof │          │Categorical  │         │ Analytics   │
  │             │         │ (SQLGlot)   │          │  Indexing   │         │(Attribution)│
  └──────┬──────┘         └──────┬──────┘          └──────┬──────┘         └──────┬──────┘
         │                       │                        │                       │
         └───────────────────────┼────────────────────────┴───────────────────────┘
                                 ▼
                     ┌───────────────────────┐
                     │       Pillar 5        │
                     │ Conversational Canvas │
                     │  & Visual Artifacts   │
                     │(Vega-Lite, Scorecards)│
                     └───────────────────────┘
```

---

## Pillar 1: Automated Semantic Layer Bootstrapping (Zero-to-One Onboarding)

### 1. The Operational Bottleneck
The primary adoption killer for semantic layers (such as dbt Semantic Layer, MetricFlow, or Cube.js) is the "blank canvas" problem. Data engineers must manually specify every dimension, additive measure, expression, grain, primary key, and foreign key relationship across dozens of unmodeled tables.

### 2. Four-Stage Automated Bootstrapping Architecture

```
Raw Warehouse Schema (DuckDB / Snowflake / Postgres)
    │
    ▼
┌──────────────────────────────────────────────────────────────────┐
│ Stage 1: Warehouse Statistical & AST Profiler                     │
│ • Cardinality Ratio (Unique / Total)   • Null Ratio              │
│ • Shannon Entropy of String Columns   • Regex Pattern Matching   │
│ • Numeric Value Range & Distribution  • Temporal Density         │
└─────────────────────────────────┬────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│ Stage 2: Star/Snowflake Schema Topology Classifier               │
│ • Fact Table Detector (High rows, dense measures, event timestamps)│
│ • Dimension Table Detector (Natural PKs, low-entropy descriptors)│
│ • Join Graph Engine (Set inclusion testing, Shortest-Path DAG)   │
└─────────────────────────────────┬────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│ Stage 3: Candidate Metric & Dimension Synthesis (Rule + LLM)     │
│ • Additive Measures (SUM, COUNT DISTINCT)                        │
│ • Derived Ratios (Conversion %, Margins, AOV)                    │
│ • Temporal Windows & Cohorts                                     │
└─────────────────────────────────┬────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│ Stage 4: Human-in-the-Loop (HITL) Calibration & YAML Emission    │
│ • Confidence scoring per candidate                               │
│ • Interactive CLI / Web Cockpit review                           │
│ • Output: Validated semantic_layer.yaml                          │
└──────────────────────────────────────────────────────────────────┘
```

### 3. Profiling Heuristics & Detection Algorithms

#### A. Fact Table vs. Dimension Table Classifier
A table $T$ is classified using a composite score $S_{\text{fact}}(T) \in [0, 1]$:

$$S_{\text{fact}}(T) = 0.35 \cdot \text{RowVolumeScore} + 0.30 \cdot \text{NumericMeasureRatio} + 0.20 \cdot \text{TimestampPresence} + 0.15 \cdot \text{ForeignKeyCandidateDensity}$$

* **Row Volume Score**: Log-normalized table row count relative to the largest table in the schema: $\min\left(1.0, \frac{\log_{10}(\text{rows}_T + 1)}{\log_{10}(\max_{t}\text{rows}_t + 1)}\right)$.
* **Numeric Measure Ratio**: Fraction of non-key numeric columns (`INTEGER`, `BIGINT`, `DECIMAL`, `FLOAT`, `DOUBLE`) matching measure patterns (`amount`, `revenue`, `price`, `qty`, `cost`, `duration`, `score`).
* **Timestamp Presence**: Binary indicator (1.0 if column exists matching `created_at`, `order_date`, `timestamp`, `event_time`, `updated_at`).
* **Dimension Table Classification**: If $S_{\text{fact}}(T) < 0.40$ and the table contains a column with Uniqueness Ratio $= 1.0$ and Null Ratio $= 0.0$, the table is classified as a `Dimension`.

#### B. Foreign Key & Join Graph Discovery via Set Inclusion Testing
Foreign key constraints are rarely declared explicitly in modern cloud data warehouses. The agent discovers relationships via a 3-step pipeline:

1. **Name Matching Heuristics**: Column name pattern `^(fk_|)([a-z0-9_]+)_(id|code|key)$` matches table name or singular entity (e.g., `customer_id` in table `orders` matches table `customers` with PK `id`).
2. **Type Compatibility Check**: Both columns must share equivalent physical or logical data types (e.g., `INT` to `INT`, or `UUID` to `VARCHAR(36)`).
3. **Data-Driven Set Inclusion Pushdown Query**:
   The agent runs an ultra-fast pushdown query on sample partitions:
   ```sql
   SELECT 
       COUNT(DISTINCT f.customer_id) AS foreign_distinct,
       COUNT(DISTINCT d.id) AS dimension_distinct,
       COUNT(DISTINCT CASE WHEN d.id IS NULL THEN f.customer_id END) AS orphaned_keys
   FROM (SELECT customer_id FROM orders TABLESAMPLE BERNOULLI (10 PERCENT)) f
   LEFT JOIN customers d ON f.customer_id = d.id;
   ```
   If $\frac{\text{orphaned\_keys}}{\text{foreign\_distinct}} < 0.005$ (< 0.5% orphaned keys), the join edge $\text{orders.customer\_id} \to \text{customers.id}$ is confirmed with high confidence (0.98).

#### C. Chasm Trap & Fan Trap Prevention in the Join Graph
The join paths are structured into a Directed Acyclic Graph (DAG) with edge weights corresponding to relationship cardinality ($1:1$, $1:N$, $N:M$).
* **Fan Trap Prevention**: When querying measures across two fact tables through a dimension (e.g., `customers` joined to `orders` and `support_tickets`), the agent prevents Cartesian explosions by requiring CTE-level pre-aggregation before joining to the dimension.
* **Chasm Trap Prevention**: When two dimension tables join to a single fact table, queries aggregate the fact table directly rather than joining across non-related dimensions.

#### D. Metric Candidate Discovery Rules
1. **Additive Measures**:
   - Monetary/Numeric columns with names containing `amt`, `amount`, `revenue`, `cost`, `tax`, `total`, `sales`, `spend` $\to$ `SUM(column)`
   - Volume/Count columns: `quantity`, `units`, `items` $\to$ `SUM(column)`
2. **Distinct Entity Counts**:
   - Foreign key or entity columns: `user_id`, `customer_id`, `session_id`, `visitor_id`, `account_id` $\to$ `COUNT(DISTINCT column)`
3. **Derived Ratio Metrics**:
   - Automated formula synthesis from additive metrics:
     - $\text{Average Order Value} = \frac{\text{SUM(order\_amount)}}{\text{COUNT(DISTINCT order\_id)}}$
     - $\text{Gross Margin \%} = \frac{\text{SUM(revenue)} - \text{SUM(cogs)}}{\text{SUM(revenue)}} \times 100$
     - $\text{Conversion Rate} = \frac{\text{COUNT(DISTINCT converted\_users)}}{\text{COUNT(DISTINCT total\_visitors)}}$

### 4. Semantic Layer Output Specification (`semantic_layer.yaml`)

```yaml
version: 1.0.0
entities:
  - name: orders
    type: fact
    description: "Core transaction log for customer orders and payments"
    primary_key: order_id
    time_dimension: created_at
    dimensions:
      - name: order_id
        type: string
        description: "Unique order identifier"
      - name: status
        type: categorical
        cardinality: 5
        sample_values: ["completed", "pending", "canceled", "refunded"]
      - name: created_at
        type: timestamp
        grain: ["day", "week", "month", "quarter", "year"]
    measures:
      - name: total_revenue
        description: "Total gross merchandise revenue from completed orders"
        expr: "SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END)"
        data_type: decimal(18,2)
        default_aggregation: sum
      - name: order_count
        description: "Total number of completed purchase transactions"
        expr: "COUNT(DISTINCT CASE WHEN status = 'completed' THEN order_id END)"
        data_type: integer
    joins:
      - target: customers
        relationship: many_to_one
        foreign_key: customer_id
        target_key: id
        join_type: left

  - name: customers
    type: dimension
    description: "Customer account profiles and segmentation attributes"
    primary_key: id
    dimensions:
      - name: id
        type: string
        description: "Unique customer identifier"
      - name: company_name
        type: string
        synonyms: ["client", "organization", "firm"]
      - name: country
        type: categorical
        cardinality: 195
      - name: subscription_tier
        type: categorical
        sample_values: ["free", "pro", "enterprise"]
    measures:
      - name: total_customers
        description: "Distinct count of registered customers"
        expr: "COUNT(DISTINCT id)"
        data_type: integer

metrics:
  - name: average_order_value
    description: "Average revenue generated per completed order"
    type: derived
    expr: "total_revenue / NULLIF(order_count, 0)"
    format: currency_usd
  - name: revenue_per_customer
    description: "Average revenue generated per active registered customer"
    type: derived
    expr: "orders.total_revenue / NULLIF(customers.total_customers, 0)"
    format: currency_usd
```

### 5. Concrete Python Profiling & Generator Implementation

```python
"""
agentic_bi/bootstrap/semantic_profiler.py
Automated Warehouse Introspection & Semantic Layer YAML Bootstrapper
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import duckdb
import yaml
import math
import re

@dataclass
class ColumnProfile:
    name: str
    data_type: str
    total_count: int
    null_count: int
    distinct_count: int
    sample_values: List[str] = field(default_factory=list)
    entropy: float = 0.0

    @property
    def uniqueness_ratio(self) -> float:
        return self.distinct_count / max(1, self.total_count)

    @property
    def null_ratio(self) -> float:
        return self.null_count / max(1, self.total_count)

class SemanticBootstrapEngine:
    def __init__(self, connection: duckdb.DuckDBPyConnection):
        self.con = connection

    def profile_table(self, table_name: str) -> Dict[str, ColumnProfile]:
        total_rows = self.con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        schema_info = self.con.execute(f"DESCRIBE {table_name}").fetchall()
        
        profiles = {}
        for col_name, col_type, null_allowed, _, _, _ in schema_info:
            stats = self.con.execute(f"""
                SELECT 
                    COUNT(*) - COUNT("{col_name}") AS null_cnt,
                    COUNT(DISTINCT "{col_name}") AS dist_cnt
                FROM {table_name}
            """).fetchone()

            samples = [
                str(row[0]) for row in self.con.execute(f"""
                    SELECT DISTINCT "{col_name}" 
                    FROM {table_name} 
                    WHERE "{col_name}" IS NOT NULL 
                    LIMIT 5
                """).fetchall()
            ]

            profiles[col_name] = ColumnProfile(
                name=col_name,
                data_type=col_type.upper(),
                total_count=total_rows,
                null_count=stats[0],
                distinct_count=stats[1],
                sample_values=samples
            )
        return profiles

    def classify_table(self, table_name: str, profiles: Dict[str, ColumnProfile], max_rows: int) -> str:
        row_count = next(iter(profiles.values())).total_count if profiles else 0
        volume_score = min(1.0, math.log10(row_count + 1) / math.log10(max(max_rows, 10) + 1))
        
        measure_keywords = {"amt", "amount", "revenue", "price", "cost", "total", "qty", "quantity", "val", "value"}
        numeric_measures = 0
        has_timestamp = False

        for col in profiles.values():
            if any(t in col.data_type for t in ["INT", "DOUBLE", "FLOAT", "DECIMAL"]):
                if any(kw in col.name.lower() for kw in measure_keywords):
                    numeric_measures += 1
            if any(t in col.data_type for t in ["TIMESTAMP", "DATE"]):
                has_timestamp = True

        score = (
            0.40 * volume_score +
            0.35 * (min(1.0, numeric_measures / 2.0)) +
            0.25 * (1.0 if has_timestamp else 0.0)
        )
        return "fact" if score >= 0.45 else "dimension"

    def auto_generate_yaml(self) -> str:
        tables = [r[0] for r in self.con.execute("SHOW TABLES").fetchall()]
        max_rows = max([self.con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables] or [1])
        
        entities = []
        for t in tables:
            profiles = self.profile_table(t)
            table_type = self.classify_table(t, profiles, max_rows)
            
            dimensions = []
            measures = []
            pk = None

            for col in profiles.values():
                if col.uniqueness_ratio == 1.0 and col.null_ratio == 0.0 and pk is None:
                    pk = col.name

                if any(t_type in col.data_type for t in ["INT", "DOUBLE", "FLOAT", "DECIMAL"]):
                    if table_type == "fact" and any(k in col.name.lower() for k in ["amount", "revenue", "cost", "price", "total"]):
                        measures.append({
                            "name": f"total_{col.name}",
                            "description": f"Sum of {col.name}",
                            "expr": f"SUM({col.name})",
                            "data_type": "decimal(18,2)"
                        })
                    else:
                        dimensions.append({"name": col.name, "type": "numeric"})
                elif any(t_type in col.data_type for t in ["TIMESTAMP", "DATE"]):
                    dimensions.append({"name": col.name, "type": "timestamp", "grain": ["day", "month", "year"]})
                else:
                    dimensions.append({
                        "name": col.name,
                        "type": "categorical",
                        "cardinality": col.distinct_count,
                        "sample_values": col.sample_values[:4]
                    })

            entities.append({
                "name": t,
                "type": table_type,
                "primary_key": pk or "id",
                "dimensions": dimensions,
                "measures": measures
            })

        return yaml.dump({"version": "1.0.0", "entities": entities}, sort_keys=False)
```

---

## Pillar 2: Column-Level Data Lineage & Explainability (using SQLGlot)

### 1. The Executive Trust Dilemma
When an executive asks *"Why is gross margin 28.4%?"*, an AI assistant cannot simply respond *"Because the SQL query returned 28.4"*. The executive requires an indisputable, mathematical chain of custody:
1. What exact tables and raw columns were read?
2. What rows were filtered out, and why?
3. What mathematical expressions and CTE transformations occurred at each hop?

### 2. SQLGlot Lineage Architecture & Traversal

`sqlglot.lineage.lineage` inspects the query's Abstract Syntax Tree (AST), performs dialect-aware semantic scope resolution, builds an internal dependency graph, and provides a root `Node` that points upstream through all CTEs and subqueries.

```
                  ┌──────────────────────────────────────────────┐
                  │ Target KPI Output: `total_revenue`           │
                  │ Expression: `SUM(customer_revenue)`          │
                  └──────────────────────┬───────────────────────┘
                                         │ depends on
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │ CTE `customer_summary`: `customer_revenue`   │
                  │ Expression: `SUM(ro.net_amount)`             │
                  └──────────────────────┬───────────────────────┘
                                         │ depends on
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │ CTE `regional_orders`: `net_amount`          │
                  │ Expression: `amount * (1.0 - discount)`      │
                  └──────────────┬───────────────────────────────┘
                                 │ depends on
                     ┌───────────┴───────────┐
                     ▼                       ▼
      ┌─────────────────────────┐ ┌─────────────────────────┐
      │ Raw Table: `raw_orders` │ │ Raw Table: `raw_orders` │
      │ Column: `amount`        │ │ Column: `discount`      │
      └─────────────────────────┘ └─────────────────────────┘
```

### 3. Dual Visual Rendering Engine

Our architecture transforms the `sqlglot.lineage.Node` graph into two presentation formats:
1. **Mermaid Flowchart (`flowchart LR`)**: Clean, interactive diagram rendered in web frontends or markdown artifacts.
2. **Rich ASCII Tree**: High-contrast, zero-dependency unicode tree for CLI Cockpit and terminal environments.

### 4. Plain-English Mathematical Audit Trail
In addition to visual diagrams, the system synthesizes a **Mathematical Audit Trail** by traversing the lineage AST and decoding arithmetic nodes (`Mul`, `Div`, `Add`, `Sub`, `Case`, `Sum`, `Avg`):

> **Mathematical Proof for `total_revenue` ($1,420,500.00)**:
> 1. **Data Source**: Read base transactions from table `raw_orders` where `status = 'completed'` (18,402 rows).
> 2. **Row-Level Net Calculation**: In CTE `regional_orders`, calculated `net_amount` as `amount * (1.0 - discount)`.
> 3. **Intermediate Aggregation**: In CTE `customer_summary`, aggregated `customer_revenue` via `SUM(net_amount)` grouped by `region` and `customer_id`.
> 4. **Final Metric Consolidation**: Summed all `customer_revenue` across targeted regions to produce final metric `$1,420,500.00`.

### 5. Concrete Python Implementation: `ColumnLineageTracer`

```python
"""
agentic_bi/lineage/column_tracer.py
Column-Level Lineage & Explainability Engine using SQLGlot AST
"""

from typing import Dict, List, Set, Tuple
import sqlglot
from sqlglot.lineage import lineage, Node
from rich.tree import Tree

class ColumnLineageTracer:
    def __init__(self, sql: str, schema: Optional[Dict] = None, dialect: str = "duckdb"):
        self.sql = sql
        self.schema = schema or {}
        self.dialect = dialect

    def trace_column(self, column_name: str) -> Node:
        """Traces the origin of a target column using SQLGlot AST scope resolution."""
        return lineage(
            column=column_name,
            sql=self.sql,
            schema=self.schema,
            dialect=self.dialect
        )

    def to_mermaid(self, root_node: Node) -> str:
        """Converts the lineage DAG into a clean Mermaid flowchart."""
        lines = [
            "flowchart LR",
            "    classDef source fill:#0284c7,stroke:#0369a1,stroke-width:2px,color:#fff;",
            "    classDef transform fill:#f59e0b,stroke:#d97706,stroke-width:2px,color:#fff;",
            "    classDef metric fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff;"
        ]
        
        visited: Set[Tuple[str, str]] = set()
        node_ids: Dict[int, str] = {}
        counter = [0]

        def get_node_id(node: Node) -> str:
            if id(node) not in node_ids:
                counter[0] += 1
                node_ids[id(node)] = f"N{counter[0]}"
            return node_ids[id(node)]

        def traverse(curr: Node):
            curr_id = get_node_id(curr)
            expr_str = str(curr.expression).replace('"', "'").replace("\n", " ")
            if len(expr_str) > 42:
                expr_str = expr_str[:39] + "..."

            label = f'"{curr.name}<br/><small style=\'opacity:0.8\'>{expr_str}</small>"'
            node_class = "metric" if curr == root_node else ("source" if not curr.downstream else "transform")
            lines.append(f"    {curr_id}[{label}]:::{node_class}")

            for parent in curr.downstream:
                parent_id = get_node_id(parent)
                edge = (parent_id, curr_id)
                if edge not in visited:
                    visited.add(edge)
                    traverse(parent)
                    lines.append(f"    {parent_id} --> {curr_id}")

        traverse(root_node)
        return "\n".join(lines)

    def to_ascii_tree(self, root_node: Node) -> str:
        """Renders an ASCII/Unicode hierarchy tree for CLI Cockpit display."""
        root_tree = Tree(f"[bold green]{root_node.name}[/bold green] (Final Output Metric)")

        def build_branch(node: Node, parent_branch: Tree):
            for child in node.downstream:
                expr_summary = str(child.expression).replace("\n", " ")
                if len(expr_summary) > 50:
                    expr_summary = expr_summary[:47] + "..."
                
                label = f"[bold cyan]{child.name}[/bold cyan] [dim]({expr_summary})[/dim]"
                branch = parent_branch.add(label)
                build_branch(child, branch)

        build_branch(root_node, root_tree)
        from rich.console import Console
        console = Console(record=True, width=100)
        console.print(root_tree)
        return console.export_text()
```

---

## Pillar 3: Fuzzy Entity Grounding & Categorical Value Indexing

### 1. The Value Hallucination Failure Mode
In benchmark evaluations (such as BIRD and Spider 2.0), over 35% of failed SQL generation stems from **value grounding failures** rather than syntax errors:
* User Query: *"Show ARR for Google in US"*
* Database: `company_name = 'Alphabet Inc.'` and `country_code = 'USA'`
* LLM SQL: `WHERE company_name = 'Google' AND country = 'US'` $\to$ **Zero rows returned**.

### 2. Tri-Tier Categorical Indexing Architecture

To solve this at warehouse scale without running millions of expensive LLM embedding calls during query execution, the system employs a **Tri-Tier Value Index**:

```
                               User Query: "Show revenue for Google in US"
                                                   │
                                                   ▼
                               ┌──────────────────────────────────────┐
                               │ 1. Entity Mention Extractor (Fast NER│
                               │    Mentions: ["Google", "US"]        │
                               └───────────────────┬──────────────────┘
                                                   │
                ┌──────────────────────────────────┼──────────────────────────────────┐
                ▼                                  ▼                                  ▼
   ┌───────────────────────────┐      ┌───────────────────────────┐      ┌───────────────────────────┐
   │ Tier 1: Lexical Index     │      │ Tier 2: Sub-linear Fuzzy  │      │ Tier 3: Semantic Vector   │
   │ DuckDB Full-Text (FTS)    │      │ MinHash LSH & Trigram     │      │ FastEmbed / Chroma Store  │
   │ Exact token hits, BM25    │      │ Levenshtein & Typo Guard  │      │ Synonyms & Aliases        │
   │ "Google" -> []            │      │ "US" -> "USA" (JW: 0.95)  │      │ "Google" <-> "Alphabet"   │
   └────────────┬──────────────┘      └────────────┬──────────────┘      └────────────┬──────────────┘
                │                                  │                                  │
                └──────────────────────────────────┼──────────────────────────────────┘
                                                   ▼
                               ┌──────────────────────────────────────┐
                               │ 2. Grounded Entity Candidates Matrix │
                               │ • "Google" -> companies.legal_name = │
                               │   'Alphabet Inc.' (score: 0.96)      │
                               │ • "US" -> customers.country_code =   │
                               │   'USA' (score: 0.99)                │
                               └───────────────────┬──────────────────┘
                                                   │
                                                   ▼
                               ┌──────────────────────────────────────┐
                               │ 3. Schema Context Injection & AST Rewriter
                               │ Prompt: Explicitly bound values      │
                               │ AST Firewall: Rewrites literal 'US'  │
                               └──────────────────────────────────────┘
```

### 3. Ingestion & Indexing Protocol
During the bootstrapping phase, the agent inventories all low-to-medium cardinality categorical columns (columns with $N_{\text{distinct}} \le 50,000$ and data type `VARCHAR`/`TEXT`):
1. **DuckDB FTS BM25 Index**: Builds inverted index over text tokens.
2. **MinHash / Trigram Signature Table**: Computes 3-gram character shingles for fast Jaccard/Levenshtein matching.
3. **Dense Vector Embeddings**: Embeds unique categorical strings using a local, sub-100MB ONNX embedding model (`all-MiniLM-L6-v2` via FastEmbed).

### 4. Concrete Python Implementation: `CategoricalEntityGrounder`

```python
"""
agentic_bi/grounding/entity_grounder.py
Tri-Tier Categorical Value Grounding Engine
"""

from typing import Dict, List, Optional, Tuple
import duckdb

class CategoricalEntityGrounder:
    def __init__(self, con: duckdb.DuckDBPyConnection):
        self.con = con
        self._init_fts()

    def _init_fts(self):
        self.con.execute("INSTALL fts; LOAD fts;")
        self.con.execute("""
            CREATE TABLE IF NOT EXISTS entity_value_catalog (
                table_name VARCHAR,
                column_name VARCHAR,
                raw_value VARCHAR,
                normalized_value VARCHAR,
                synonyms VARCHAR[]
            );
        """)

    def register_values(self, table: str, column: str, values: List[str], synonyms_map: Optional[Dict[str, List[str]]] = None):
        synonyms_map = synonyms_map or {}
        records = []
        for val in values:
            syns = synonyms_map.get(val, [])
            records.append((table, column, val, val.lower().strip(), syns))
        
        self.con.executemany("""
            INSERT INTO entity_value_catalog VALUES (?, ?, ?, ?, ?)
        """, records)

    def ground_entity(self, query_token: str, threshold: float = 0.75) -> List[Dict]:
        """
        Executes a combined Jaro-Winkler similarity and synonym search across indexed values.
        """
        token_clean = query_token.lower().strip()
        
        # 1. Check exact match or synonym containment
        exact_matches = self.con.execute("""
            SELECT table_name, column_name, raw_value, 1.0 AS score, 'exact' as method
            FROM entity_value_catalog
            WHERE normalized_value = ? OR list_contains(synonyms, ?)
        """, [token_clean, token_clean]).fetchall()

        if exact_matches:
            return [{
                "table": r[0], "column": r[1], "exact_value": r[2], 
                "confidence": r[3], "match_type": r[4]
            } for r in exact_matches]

        # 2. Fuzzy Jaro-Winkler / Levenshtein search
        fuzzy_matches = self.con.execute("""
            SELECT 
                table_name, 
                column_name, 
                raw_value, 
                jaro_winkler_similarity(normalized_value, ?) AS score,
                'fuzzy' as method
            FROM entity_value_catalog
            WHERE score >= ?
            ORDER BY score DESC
            LIMIT 3
        """, [token_clean, threshold]).fetchall()

        return [{
            "table": r[0], "column": r[1], "exact_value": r[2], 
            "confidence": round(r[3], 3), "match_type": r[4]
        } for r in fuzzy_matches]
```

---

## Pillar 4: Diagnostic "Why" Analytics (Automated Anomaly Attribution)

### 1. Moving from Descriptive ("What") to Diagnostic ("Why")
Traditional BI stops when it reports: *"Churn rose from 4.2% in July to 8.9% in August."*  
The executive immediately responds: *"Why did it spike?"*  
An autonomous data analyst must decompose this variance down to its root drivers across multiple dimensions (Region, Segment, Plan Type, Acquisition Channel, OS Version).

### 2. Mathematical Attribution Frameworks

```
                                  Total Metric Delta: ΔM = M(t1) - M(t0)
                                                    │
                 ┌──────────────────────────────────┴──────────────────────────────────┐
                 ▼                                                                     ▼
   ┌──────────────────────────────┐                                      ┌──────────────────────────────┐
   │ Additive Metrics (Revenue)   │                                      │ Ratio Metrics (Conversion %) │
   │ Variance Decomposition       │                                      │ Kitagawa Decomposition       │
   │ ΔM = ∑ (m_i,t1 - m_i,t0)     │                                      │ ΔR = Mix Effect + Rate Effect│
   └──────────────┬───────────────┘                                      └──────────────┬───────────────┘
                  │                                                                     │
                  ▼                                                                     ▼
   ┌────────────────────────────────────────────────────────────────────────────────────────────────────┐
   │ Automated Dimensional Slice-and-Dice via SQL CUBE / GROUPING SETS                                  │
   │ • Evaluates dimension contributions: Region, Plan Tier, Customer Segment, Operating System         │
   │ • Identifies top positive & negative driver slices accounting for >= 80% of total variance         │
   └────────────────────────────────────────────────┬───────────────────────────────────────────────────┘
                                                    │
                                                    ▼
   ┌────────────────────────────────────────────────────────────────────────────────────────────────────┐
   │ Deterministic Waterfall Bridge & LLM Executive Summary                                             │
   │ • Base Period -> Isolated Dimensional Impacts -> Target Period                                     │
   │ • Plain-English RCA Narrative: "78% of August churn was driven by EU Enterprise accounts on Plan B"│
   └────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Framework A: Additive Metric Variance Decomposition
For additive measures (such as Total Sales or Total Churn Count):

$$\Delta M = M_{t_1} - M_{t_0}$$

Given a dimension $D$ with categorical values $d_k \in D$:

$$\Delta M = \sum_{k=1}^{K} \left( m_{d_k, t_1} - m_{d_k, t_0} \right)$$

The **Dimension Contribution Index (DCI)** for slice $d_k$ is:

$$\text{DCI}(d_k) = \frac{m_{d_k, t_1} - m_{d_k, t_0}}{M_{t_1} - M_{t_0}} \times 100\%$$

Every dollar or unit of variance is accounted for: $\sum \text{DCI}(d_k) = 100.0\%$.

#### Framework B: Ratio/Rate Decomposition (Kitagawa Method)
When analyzing rates (e.g., Conversion Rate, Churn Rate, Average Order Value $R = \frac{Y}{X}$), naive comparisons suffer from **Simpson's Paradox**. A rate can drop overall even if it increased in every individual segment due to population shifts (mix shifts).

The Kitagawa decomposition separates the delta into two mutually exclusive, mathematically closed terms:

$$\Delta R = R_{t_1} - R_{t_0} = \underbrace{\sum_{i} \bar{R}_i \cdot \Delta w_i}_{\text{Mix Effect (Population Shift)}} + \underbrace{\sum_{i} \bar{w}_i \cdot \Delta R_i}_{\text{Rate Effect (Performance Shift)}}$$

Where:
* $w_{i, t} = \frac{X_{i, t}}{\sum_j X_{j, t}}$ is the weight (population share) of segment $i$ at time $t$.
* $\bar{w}_i = \frac{w_{i, t_0} + w_{i, t_1}}{2}$ is the average weight across both periods.
* $\bar{R}_i = \frac{R_{i, t_0} + R_{i, t_1}}{2}$ is the average rate across both periods.
* $\Delta w_i = w_{i, t_1} - w_{i, t_0}$ and $\Delta R_i = R_{i, t_1} - R_{i, t_0}$.

### 3. High-Dimensional Pushdown Query Generation
Rather than running 20 individual queries, the agent dispatches a single SQL query using `GROUPING SETS` to calculate baseline and target values across all candidate dimensions simultaneously:

```sql
WITH period_data AS (
    SELECT 
        CASE 
            WHEN created_at BETWEEN '2026-07-01' AND '2026-07-31' THEN 'baseline'
            WHEN created_at BETWEEN '2026-08-01' AND '2026-08-31' THEN 'target'
        END AS period,
        region,
        plan_tier,
        churned_flag,
        user_id
    FROM user_subscriptions
    WHERE created_at BETWEEN '2026-07-01' AND '2026-08-31'
)
SELECT 
    period,
    region,
    plan_tier,
    COUNT(DISTINCT user_id) AS total_users,
    COUNT(DISTINCT CASE WHEN churned_flag = 1 THEN user_id END) AS churned_users,
    CAST(COUNT(DISTINCT CASE WHEN churned_flag = 1 THEN user_id END) AS FLOAT) / 
        NULLIF(COUNT(DISTINCT user_id), 0) AS churn_rate
FROM period_data
GROUP BY GROUPING SETS (
    (period),
    (period, region),
    (period, plan_tier),
    (period, region, plan_tier)
);
```

### 4. Concrete Python Implementation: `MetricAttributionEngine`

```python
"""
agentic_bi/attribution/diagnostic_engine.py
Automated Root-Cause & Variance Decomposition Engine
"""

from typing import Dict, List, Tuple
import pandas as pd

class MetricAttributionEngine:
    @staticmethod
    def decompose_additive(
        df_base: pd.DataFrame, 
        df_target: pd.DataFrame, 
        dimension_col: str, 
        metric_col: str
    ) -> List[Dict]:
        """
        Decomposes additive metric delta across dimension categories.
        """
        base_agg = df_base.groupby(dimension_col)[metric_col].sum()
        target_agg = df_target.groupby(dimension_col)[metric_col].sum()

        combined = pd.DataFrame({"base": base_agg, "target": target_agg}).fillna(0)
        combined["delta"] = combined["target"] - combined["base"]
        
        total_delta = combined["delta"].sum()
        if total_delta == 0:
            return []

        combined["contribution_pct"] = (combined["delta"] / total_delta) * 100.0
        combined = combined.sort_values(by="delta", key=abs, ascending=False)

        results = []
        for dim_val, row in combined.iterrows():
            results.append({
                "dimension": dimension_col,
                "slice": str(dim_val),
                "base_value": float(row["base"]),
                "target_value": float(row["target"]),
                "delta": float(row["delta"]),
                "contribution_pct": round(float(row["contribution_pct"]), 2)
            })
        return results

    @staticmethod
    def kitagawa_ratio_decomposition(
        df_base: pd.DataFrame, 
        df_target: pd.DataFrame, 
        dimension_col: str, 
        numerator_col: str, 
        denominator_col: str
    ) -> Dict:
        """
        Decomposes ratio metric changes into Mix Effect vs. Rate Effect.
        """
        agg_b = df_base.groupby(dimension_col)[[numerator_col, denominator_col]].sum()
        agg_t = df_target.groupby(dimension_col)[[numerator_col, denominator_col]].sum()

        b_denom_total = agg_b[denominator_col].sum()
        t_denom_total = agg_t[denominator_col].sum()

        agg_b["weight"] = agg_b[denominator_col] / b_denom_total
        agg_b["rate"] = agg_b[numerator_col] / agg_b[denominator_col]

        agg_t["weight"] = agg_t[denominator_col] / t_denom_total
        agg_t["rate"] = agg_t[numerator_col] / agg_t[denominator_col]

        all_dims = sorted(list(set(agg_b.index).union(set(agg_t.index))))
        mix_effect = 0.0
        rate_effect = 0.0
        slice_breakdown = []

        for d in all_dims:
            w0 = agg_b.loc[d, "weight"] if d in agg_b.index else 0.0
            r0 = agg_b.loc[d, "rate"] if d in agg_b.index else 0.0
            w1 = agg_t.loc[d, "weight"] if d in agg_t.index else 0.0
            r1 = agg_t.loc[d, "rate"] if d in agg_t.index else 0.0

            w_bar = (w0 + w1) / 2.0
            r_bar = (r0 + r1) / 2.0
            delta_w = w1 - w0
            delta_r = r1 - r0

            d_mix = delta_w * r_bar
            d_rate = delta_r * w_bar

            mix_effect += d_mix
            rate_effect += d_rate

            slice_breakdown.append({
                "slice": str(d),
                "mix_effect": round(d_mix, 4),
                "rate_effect": round(d_rate, 4),
                "total_slice_effect": round(d_mix + d_rate, 4)
            })

        return {
            "total_rate_delta": round(mix_effect + rate_effect, 4),
            "mix_effect_total": round(mix_effect, 4),
            "rate_effect_total": round(rate_effect, 4),
            "slice_breakdown": slice_breakdown
        }
```

---

## Pillar 5: Conversational Canvas & Visual Artifacts

### 1. Eliminating the Flat Markdown Output
Executive users do not engage with raw tabular blocks of 500 rows. A 10-star system delivers a **Conversational Canvas**: an interactive, multi-modal payload containing:
1. **Executive KPI Scorecard**: High-impact metrics with period-over-period delta badges and sparklines.
2. **Grammar-of-Graphics Chart (Vega-Lite v5 / Plotly JSON)**: Rendered dynamically based on data cardinality and intent.
3. **Structured Data Table**: Searchable, paginated markdown table with column-level totals.
4. **Interactive Action Chips**: Contextual drill-down recommendations.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 EXECUTIVE SCORECARD                                    │
│ ┌───────────────────────────┐ ┌───────────────────────────┐ ┌────────────────────────┐ │
│ │ Monthly Recurring Revenue │ │ Active Subscriptions      │ │ Churn Rate             │ │
│ │ $1,420,500.00             │ │ 12,480                    │ │ 4.12%                  │ │
│ │ ▲ +12.4% vs last month    │ │ ▲ +8.1% vs last month     │ │ ▼ -0.8% vs last month  │ │
│ └───────────────────────────┘ └───────────────────────────┘ └────────────────────────┘ │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                           DYNAMIC VEGA-LITE VISUALIZATION                              │
│  Revenue ($k)                                                                          │
│  1500 ┤                                      ╭────* (August: $1,420k)                  │
│  1000 ┤                       ╭──────────────╯                                         │
│   500 ┤          ╭────────────╯                                                        │
│     0 ┼──────────┴────────────┴──────────────┴────────────                             │
│       Jan       Apr          Jul            Aug                                        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                          INTERACTIVE DRILL-DOWN ACTION CHIPS                           │
│  [🔍 Why did August surge?]   [📊 Breakdown by Region]   [📥 Export Full Cohort CSV]   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2. Leland Wilkinson Chart Selection Decision Matrix
The chart generator employs a deterministic rule engine based on the data signature of the query result:

| Dimension Signature | Metric Signature | Primary Chart Type | Encoding Specification |
| :--- | :--- | :--- | :--- |
| 1 Temporal Column (`DATE`, `TIMESTAMP`) | 1 Continuous Metric | **Temporal Line / Area Chart** | X: Temporal (UTC), Y: Quantitative, Tooltip: Date + Val |
| 1 Low-Cardinality Categorical ($N \le 7$) | 1 Continuous Metric | **Vertical Column Bar Chart** | X: Nominal, Y: Quantitative, Sort: -Y |
| 1 High-Cardinality Categorical ($7 < N \le 25$)| 1 Continuous Metric | **Horizontal Bar Chart** | Y: Nominal (sorted descending), X: Quantitative |
| None (Single row scalar) | 1-3 Continuous Metrics | **Executive KPI Scorecards** | Scorecard Card: Value, Delta %, Sparkline |
| 2 Categorical Dimensions | 1 Continuous Metric | **Grouped / Stacked Bar or Heatmap** | X: Dim 1, Color: Dim 2, Y: Quantitative |
| 0 Categorical Dimensions | 2 Continuous Metrics | **Scatter / Correlation Plot** | X: Metric 1, Y: Metric 2, Trendline: OLS |

### 3. Conversational Canvas Response Schema (Pydantic)

```python
"""
agentic_bi/canvas/canvas_models.py
Standardized Conversational Canvas Multi-Modal Response Specification
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class KPIScorecard(BaseModel):
    title: str
    current_value: str
    previous_value: Optional[str] = None
    delta_percentage: Optional[float] = None
    is_positive_sentiment: bool = True
    sparkline_points: Optional[List[float]] = None

class ActionChip(BaseModel):
    label: str
    action_type: str = Field(description="'drill_down', 'attribution', 'export', or 'filter'")
    prompt_payload: str

class CanvasArtifactResponse(BaseModel):
    executive_narrative: str
    scorecards: List[KPIScorecard] = Field(default_factory=list)
    chart_spec: Optional[Dict[str, Any]] = None  # Vega-Lite v5 JSON
    data_table_markdown: str
    action_chips: List[ActionChip] = Field(default_factory=list)
```

### 4. Dynamic Vega-Lite Synthesizer & Terminal Fallback

```python
"""
agentic_bi/canvas/chart_synthesizer.py
Adaptive Chart Generation with Terminal ASCII Fallback
"""

from typing import Any, Dict, List
import pandas as pd

class ConversationalCanvasSynthesizer:
    @staticmethod
    def generate_vega_spec(df: pd.DataFrame, title: str) -> Dict[str, Any]:
        """
        Synthesizes a hardened Vega-Lite v5 spec based on dataframe columns and cardinality.
        """
        cols = df.columns.tolist()
        has_time = any("date" in c.lower() or "time" in c.lower() or "month" in c.lower() for c in cols)
        
        if has_time and len(cols) >= 2:
            time_col = next(c for c in cols if "date" in c.lower() or "time" in c.lower() or "month" in c.lower())
            metric_col = next(c for c in cols if c != time_col)
            return {
                "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                "title": title,
                "width": "container",
                "height": 320,
                "data": {"values": df.to_dict(orient="records")},
                "mark": {"type": "line", "point": True, "interpolate": "monotone"},
                "encoding": {
                    "x": {"field": time_col, "type": "temporal", "axis": {"grid": False}},
                    "y": {"field": metric_col, "type": "quantitative", "axis": {"grid": True}}
                }
            }

        # Categorical Bar default
        cat_col = cols[0]
        metric_col = cols[1] if len(cols) > 1 else cols[0]
        return {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "title": title,
            "width": "container",
            "height": 300,
            "data": {"values": df.to_dict(orient="records")},
            "mark": "bar",
            "encoding": {
                "x": {"field": cat_col, "type": "nominal", "sort": "-y", "axis": {"labelAngle": 0}},
                "y": {"field": metric_col, "type": "quantitative"},
                "color": {"value": "#0284c7"}
            }
        }

    @staticmethod
    def render_cli_sparkline(numbers: List[float]) -> str:
        """Renders unicode sparkline ticks for headless CLI cockpits."""
        ticks = [" ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
        if not numbers:
            return ""
        min_v, max_v = min(numbers), max(numbers)
        span = max_v - min_v if max_v != min_v else 1.0
        return "".join([ticks[min(7, int(((val - min_v) / span) * 7))] for val in numbers])
```

---

## Pillar 6: End-to-End Integrated Architecture & Query Lifecycle

### 1. Integration with Existing Multi-Agent StateGraph
The 5 innovation pillars integrate directly into our LangGraph Cognitive Architecture, UWAL (Unified Warehouse Abstraction Layer), and SQLGlot AST Firewall:

```
                  User Query: "Why did our US enterprise churn spike to 14% in August?"
                                                    │
                                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. Entity Grounding Agent (Pillar 3)                                                   │
│ • "US" -> Grounded to `customers.country_code = 'USA'` (Conf: 0.99)                   │
│ • "enterprise" -> Grounded to `customers.subscription_tier = 'enterprise'` (Conf: 0.98)│
│ • Output: Grounded Entity Mapping Context                                             │
└───────────────────────────────────┬────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 2. Intent Classifier & Semantic Resolver (Pillars 1 & 4)                               │
│ • Detects DIAGNOSTIC_WHY intent (User asking "Why did churn spike")                    │
│ • Resolves metric `churn_rate` from `semantic_layer.yaml`                              │
│ • Identifies baseline (July 2026) vs. target (August 2026)                             │
└───────────────────────────────────┬────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 3. Pushdown SQL Synthesizer & Execution Engine (UWAL)                                  │
│ • Synthesizes dialect-specific GROUPING SETS query across Region, Plan, OS             │
│ • Executes on DuckDB / Snowflake / Postgres via UWAL adapter                           │
└───────────────────────────────────┬────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 4. SQLGlot Lineage & Audit Agent (Pillar 2)                                            │
│ • Runs `sqlglot.lineage` on `churn_rate` column across CTEs                            │
│ • Generates Mermaid Flowchart & Step-by-Step Mathematical Lineage Proof                │
└───────────────────────────────────┬────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 5. Diagnostic Attribution Engine (Pillar 4)                                            │
│ • Computes Kitagawa Rate/Mix decomposition across segments                             │
│ • Isolates top driver: "Plan B EU Enterprise churn accounted for 78% of the spike"     │
└───────────────────────────────────┬────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 6. Conversational Canvas Synthesizer (Pillar 5)                                        │
│ • Emits `CanvasArtifactResponse` with Waterfall chart spec, KPI cards, and Action Chips│
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Roadmap & Benchmark Success Metrics

| Milestone | Deliverable | Key Validation Metric |
| :--- | :--- | :--- |
| **M1: Semantic Bootstrapper** | `SemanticBootstrapEngine` + CLI tool `agy semantic bootstrap` | Auto-detects > 90% of valid Star Schema PK/FK edges and metrics on Spider 2.0 schemas |
| **M2: SQLGlot Lineage Engine** | `ColumnLineageTracer` + Mermaid & ASCII formatters | Resolves 100% of column lineages on multi-CTE queries without runtime AST exceptions |
| **M3: Value Grounding Index** | Tri-Tier DuckDB FTS + LSH Grounder | Eliminates > 90% of empty-result-set literal hallucination errors on BIRD benchmark |
| **M4: Diagnostic Engine** | Kitagawa & Additive Metric Attribution Modules | Explains 100% of metric variance in closed-form math with zero unallocated residual |
| **M5: Conversational Canvas** | Dynamic Vega-Lite Synthesizer + CLI Cockpit renderer | Renders responsive visualizations and action chips across Web and Terminal UIs |

---

## Conclusion

By unifying **Automated Semantic Layer Bootstrapping**, **Column-Level AST Lineage**, **Tri-Tier Entity Grounding**, **Diagnostic Anomaly Attribution**, and **Multimodal Conversational Canvases**, our Agentic BI & Warehouse Question-Answering System evolves from a naive text-to-SQL translation utility into an autonomous, trustworthy, 10-star data partner for modern enterprises.
