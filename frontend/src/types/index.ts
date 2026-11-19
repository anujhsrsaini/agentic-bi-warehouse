export interface QueryResponse {
  question: string;
  session_id: string;
  intent: string;
  confidence: number;
  clarification_prompt: string | null;
  clarification_options: string[];
  metric_name: string | null;
  dimensions: string[];
  filters: string[];
  grounded_entities: Record<string, any>;
  validated_sql: string;
  raw_sql: string;
  sql_rationale: string;
  validation_time_us: number;
  security_passed: boolean;
  security_error: string | null;
  execution_error: string | null;
  execution_time_ms: number;
  rows_returned: number;
  rows_scanned: number;
  columns: string[];
  data: Record<string, any>[];
  summary_narrative: string;
  lineage_mermaid: string;
  lineage_ascii: string;
  chart_spec: ChartSpec | null;
}

export interface ChartSpec {
  type: 'bar' | 'line' | 'donut' | 'kpi' | 'combo';
  xKey: string;
  yKey: string;
  metrics: string[];
  title: string;
  barKey?: string;
  lineKeys?: string[];
}

export interface SecurityTestResult {
  blocked: boolean;
  violation: string | null;
  code: string | null;
  sanitized_sql: string | null;
  validation_time_us: number;
  message: string;
}

export interface CertifiedMetric {
  name: string;
  label: string;
  description: string;
  model: string;
  calculation: string;
  filter: string | null;
  dimensions: string[];
  synonyms: string[];
}

export interface TableStat {
  table: string;
  rows: number;
  description: string;
}

export interface WarehouseStats {
  total_rows: number;
  tables: number;
  engine: string;
  version: string;
  speed: string;
  dataset: string;
  table_stats: TableStat[];
}

export interface ChasmTrapDemo {
  naive: {
    sql: string;
    cartesian_rows: number;
    naive_gmv: number;
    execution_time_ms: number;
    explanation: string;
  };
  governed: {
    sql: string;
    total_orders: number;
    governed_gmv: number;
    governed_payment: number;
    execution_time_ms: number;
    explanation: string;
  };
  inflation_amount: number;
  fanout_factor: number;
}
