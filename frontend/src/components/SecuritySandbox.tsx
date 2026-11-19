import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  ShieldX,
  Play,
  Bug,
  AlertTriangle,
  Zap,
  Flame,
  CheckCircle2,
  HelpCircle,
  TrendingDown,
  Layers,
  ArrowRight,
} from 'lucide-react';
import { SecurityTestResult, ChasmTrapDemo } from '../types';
import { testSecurity, getChasmTrapDemo } from '../lib/api';

const ATTACK_PRESETS = [
  {
    id: 'drop_table',
    title: 'SQL Injection / Table Drop',
    category: 'Mutating DDL',
    sql: 'DROP TABLE orders;',
    expected: "SecurityViolationError: Unauthorized root statement type 'Drop'. Only SELECT queries are permitted.",
  },
  {
    id: 'multi_statement',
    title: 'Stacked Multi-Statement Injection',
    category: 'Stacking Attack',
    sql: 'SELECT 1; DROP TABLE orders;',
    expected: 'Multi-statement queries detected. Only single-statement queries permitted.',
  },
  {
    id: 'path_traversal',
    title: 'Local Path Traversal Read',
    category: 'Arbitrary File Read',
    sql: "SELECT * FROM read_csv('/etc/passwd');",
    expected: "Forbidden function or table generator 'read_csv' detected.",
  },
  {
    id: 's3_exfiltration',
    title: 'Cloud Parquet Exfiltration',
    category: 'Out-of-Bounds Network',
    sql: "SELECT * FROM read_parquet('s3://malicious-bucket/exfiltrate.parquet');",
    expected: "Forbidden function or table generator 'read_parquet' detected.",
  },
  {
    id: 'cartesian_dos',
    title: 'Cartesian Explosion DoS',
    category: 'DoS / Resource Exhaustion',
    sql: 'SELECT * FROM orders CROSS JOIN order_items;',
    expected: 'Unconstrained Cartesian cross join detected.',
  },
  {
    id: 'unregistered_table',
    title: 'Unregistered Table Access',
    category: 'Privilege Escalation',
    sql: 'SELECT * FROM unauthorized_internal_payroll;',
    expected: "Table 'unauthorized_internal_payroll' is not registered in authorized catalog schema.",
  },
  {
    id: 'safe_query',
    title: 'Authorized Governed SELECT',
    category: 'Legitimate Analytical Query',
    sql: 'SELECT customer_state, COUNT(*) as cnt FROM customers GROUP BY 1 ORDER BY cnt DESC LIMIT 10;',
    expected: 'Passes all 7 AST Firewall checks.',
  },
];

export const SecuritySandbox: React.FC = () => {
  const [customSQL, setCustomSQL] = useState(ATTACK_PRESETS[0].sql);
  const [selectedPreset, setSelectedPreset] = useState<string>(ATTACK_PRESETS[0].id);
  const [testResult, setTestResult] = useState<SecurityTestResult | null>(null);
  const [testing, setTesting] = useState(false);

  // Chasm Trap State
  const [chasmDemo, setChasmDemo] = useState<ChasmTrapDemo | null>(null);
  const [loadingChasm, setLoadingChasm] = useState(false);

  useEffect(() => {
    handleRunSecurityTest(ATTACK_PRESETS[0].sql);
    handleLoadChasmDemo();
  }, []);

  const handleRunSecurityTest = async (sqlToTest: string) => {
    setTesting(true);
    try {
      const res = await testSecurity(sqlToTest);
      setTestResult(res);
    } catch (err: any) {
      setTestResult({
        blocked: true,
        violation: err.message,
        code: 'NETWORK_ERROR',
        sanitized_sql: null,
        validation_time_us: 0,
        message: err.message,
      });
    } finally {
      setTesting(false);
    }
  };

  const handleLoadChasmDemo = async () => {
    setLoadingChasm(true);
    try {
      const res = await getChasmTrapDemo();
      setChasmDemo(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingChasm(false);
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Header Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-50 via-white to-slate-50 dark:from-[#121826] dark:via-[#161F30] dark:to-[#121826] border border-slate-200 dark:border-[#1F293D] shadow-sm dark:shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 mb-1">
              <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-rose-100 text-rose-700 border border-rose-200 dark:bg-rose-950/80 dark:text-rose-400 dark:border-rose-800/60 font-semibold">
                CTO & SecOps Testbed
              </span>
              <span className="text-slate-400 dark:text-gray-500">•</span>
              <span className="text-xs text-slate-500 dark:text-gray-400">Spider 2.0 Reality Cliff Defense</span>
            </div>
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
              Adversarial Security & AST Guardrail Sandbox
            </h1>
            <p className="text-xs sm:text-sm text-slate-600 dark:text-gray-400 mt-1 max-w-3xl">
              Standard LLM Text-to-SQL agents fail catastrophically in enterprise deployments: they drop tables, exfiltrate files via DuckDB functions, and crash databases with Cartesian cross-joins. Our 7-stage SQLGlot AST Firewall guarantees zero-trust query execution in &lt;200 microseconds.
            </p>
          </div>

          <div className="flex items-center space-x-3 shrink-0">
            <div className="p-3 rounded-xl bg-white dark:bg-[#0B0F17] border border-slate-200 dark:border-[#1F293D] text-center shadow-sm">
              <div className="text-lg font-bold font-mono text-blue-600 dark:text-cyan-400">7 Stages</div>
              <div className="text-[10px] text-slate-500 dark:text-gray-400 uppercase font-mono">AST Inspection</div>
            </div>
            <div className="p-3 rounded-xl bg-white dark:bg-[#0B0F17] border border-slate-200 dark:border-[#1F293D] text-center shadow-sm">
              <div className="text-lg font-bold font-mono text-emerald-600 dark:text-emerald-400">&lt; 250 μs</div>
              <div className="text-[10px] text-slate-500 dark:text-gray-400 uppercase font-mono">Audit Latency</div>
            </div>
          </div>
        </div>
      </div>

      {/* Grid: Attack Presets & Live Firewall Test */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Attack Presets (5 cols) */}
        <div className="lg:col-span-5 space-y-3">
          <h2 className="text-xs font-mono uppercase tracking-wider text-slate-500 dark:text-gray-400 px-1 flex items-center space-x-1.5">
            <Bug className="w-3.5 h-3.5 text-rose-500 dark:text-rose-400" />
            <span>Adversarial Attack Scenarios (1-Click)</span>
          </h2>

          <div className="space-y-2">
            {ATTACK_PRESETS.map((preset) => {
              const isSelected = selectedPreset === preset.id;
              const isSafe = preset.id === 'safe_query';
              return (
                <button
                  key={preset.id}
                  onClick={() => {
                    setSelectedPreset(preset.id);
                    setCustomSQL(preset.sql);
                    handleRunSecurityTest(preset.sql);
                  }}
                  className={`w-full text-left p-3.5 rounded-xl border transition-all duration-150 ${
                    isSelected
                      ? isSafe
                        ? 'bg-emerald-50 dark:bg-emerald-950/30 border-emerald-500/60 shadow-sm'
                        : 'bg-rose-50 dark:bg-rose-950/30 border-rose-500/60 shadow-sm'
                      : 'bg-white dark:bg-[#121826] border-slate-200 dark:border-[#1F293D] hover:bg-slate-50 dark:hover:bg-[#161F30]'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-semibold text-slate-900 dark:text-gray-200">
                      {preset.title}
                    </span>
                    <span
                      className={`text-[10px] font-mono uppercase px-1.5 py-0.5 rounded border ${
                        isSafe
                          ? 'bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-950/80 dark:text-emerald-400 dark:border-emerald-800/60'
                          : 'bg-rose-100 text-rose-800 border-rose-300 dark:bg-rose-950/80 dark:text-rose-400 dark:border-rose-800/60'
                      }`}
                    >
                      {preset.category}
                    </span>
                  </div>
                  <div className="font-mono text-[11px] text-slate-500 dark:text-gray-400 truncate">
                    {preset.sql}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Column: Custom SQL Editor & Live AST Verdict (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="bg-white dark:bg-[#121826] border border-slate-200 dark:border-[#1F293D] rounded-2xl p-4 sm:p-5 shadow-sm dark:shadow-lg">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-mono font-medium text-slate-700 dark:text-gray-300 uppercase tracking-wider flex items-center space-x-1.5">
                <Zap className="w-3.5 h-3.5 text-blue-500 dark:text-cyan-400" />
                <span>Live AST Firewall Inspector</span>
              </span>
              <button
                onClick={() => handleRunSecurityTest(customSQL)}
                disabled={testing || !customSQL.trim()}
                className="flex items-center space-x-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 dark:bg-cyan-600 dark:hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg transition-colors shadow-sm"
              >
                <Play className="w-3 h-3 fill-current" />
                <span>Test AST Firewall</span>
              </button>
            </div>

            {/* SQL Input Area */}
            <div className="relative mb-4">
              <textarea
                value={customSQL}
                onChange={(e) => {
                  setCustomSQL(e.target.value);
                  setSelectedPreset('');
                }}
                rows={4}
                placeholder="Type or paste any arbitrary SQL query to test against the security guardrails..."
                className="w-full bg-slate-50 dark:bg-[#0B0F17] border border-slate-200 dark:border-[#1F293D] rounded-xl p-3 font-mono text-xs text-slate-800 dark:text-gray-200 focus:outline-none focus:border-blue-500 dark:focus:border-cyan-500 transition-colors"
              />
            </div>

            {/* Verdict Card */}
            {testResult && (
              <div
                className={`p-4 rounded-xl border transition-all duration-300 ${
                  testResult.blocked
                    ? 'bg-rose-50 dark:bg-rose-950/40 border-rose-300 dark:border-rose-700/60 text-rose-900 dark:text-rose-200'
                    : 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-300 dark:border-emerald-700/60 text-emerald-900 dark:text-emerald-200'
                }`}
              >
                <div className="flex items-start space-x-3">
                  <div className="p-2 rounded-xl shrink-0">
                    {testResult.blocked ? (
                      <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-rose-100 dark:bg-rose-500/20 border border-rose-300 dark:border-rose-500/40 text-rose-600 dark:text-rose-400 animate-pulse">
                        <ShieldX className="w-6 h-6" />
                      </div>
                    ) : (
                      <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-500/20 border border-emerald-300 dark:border-emerald-500/40 text-emerald-600 dark:text-emerald-400">
                        <ShieldCheck className="w-6 h-6" />
                      </div>
                    )}
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-sm tracking-tight">
                          {testResult.blocked ? 'QUERY BLOCKED' : 'QUERY APPROVED'}
                        </span>
                        <span
                          className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
                            testResult.blocked
                              ? 'bg-rose-100 text-rose-800 border-rose-300 dark:bg-rose-900/60 dark:text-rose-300 dark:border-rose-700'
                              : 'bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-900/60 dark:text-emerald-300 dark:border-emerald-700'
                          }`}
                        >
                          {testResult.code || 'AUDIT_CODE'}
                        </span>
                      </div>
                      <span className="text-xs font-mono text-slate-500 dark:text-gray-400">
                        ⚡ {testResult.validation_time_us ? testResult.validation_time_us.toFixed(1) : '<200'} μs
                      </span>
                    </div>

                    <p className="text-xs mt-2 font-mono leading-relaxed text-slate-700 dark:text-gray-300">
                      {testResult.violation || testResult.message}
                    </p>

                    {testResult.sanitized_sql && (
                      <div className="mt-3 pt-3 border-t border-emerald-200 dark:border-emerald-800/40">
                        <span className="text-[10px] font-mono text-emerald-700 dark:text-emerald-400 uppercase">
                          Sanitized / Clamped AST:
                        </span>
                        <pre className="mt-1 p-2 bg-slate-900 rounded-lg text-emerald-300 font-mono text-xs overflow-x-auto">
                          {testResult.sanitized_sql}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* The Chasm Trap Interactive Benchmark */}
      <div className="bg-white dark:bg-[#121826] border border-slate-200 dark:border-[#1F293D] rounded-2xl p-6 shadow-sm dark:shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-200 dark:border-[#1F293D]">
          <div>
            <div className="flex items-center space-x-2 mb-1">
              <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-amber-100 text-amber-800 border border-amber-300 dark:bg-amber-950/80 dark:text-amber-400 dark:border-amber-800/60 font-semibold">
                Fan-Out / Chasm Trap Defense
              </span>
              <span className="text-slate-400 dark:text-gray-500">•</span>
              <span className="text-xs text-slate-500 dark:text-gray-400">Mathematical Integrity Guarantee</span>
            </div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white tracking-tight">
              The Chasm Trap: Why Naive LLM Text-to-SQL Hallucinates Revenue
            </h2>
            <p className="text-xs text-slate-600 dark:text-gray-400 mt-1 max-w-3xl">
              When an enterprise table links 1:N to multiple facts (e.g., <code className="text-blue-600 dark:text-cyan-400 font-mono">orders → order_items</code> and <code className="text-blue-600 dark:text-cyan-400 font-mono">orders → order_payments</code>), naive SQL generates Cartesian row multiplication. Standard LLMs compute inflated figures ($42M+) that mislead executive leadership. Governed DuckDB enforces pre-aggregation in CTEs to preserve exact mathematical truth.
            </p>
          </div>

          <button
            onClick={handleLoadChasmDemo}
            disabled={loadingChasm}
            className="flex items-center space-x-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-[#161F30] dark:hover:bg-[#1A2438] text-slate-700 dark:text-cyan-300 border border-slate-200 dark:border-cyan-500/30 rounded-xl text-xs font-semibold transition-colors shrink-0 shadow-sm"
          >
            <span>{loadingChasm ? 'Running OLAP Engine...' : 'Re-Run Live Benchmark'}</span>
          </button>
        </div>

        {chasmDemo && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Left: Naive Multi-Join (The Trap) */}
            <div className="p-5 rounded-xl bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-800/50 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <span className="p-1 rounded bg-rose-100 dark:bg-rose-500/20 text-rose-600 dark:text-rose-400 font-bold text-xs">
                      ❌
                    </span>
                    <span className="text-sm font-semibold text-rose-900 dark:text-rose-200">
                      Naive Multi-Join (Fan-Out Hallucination)
                    </span>
                  </div>
                  <span className="text-xs font-mono text-rose-600 dark:text-rose-400">
                    {chasmDemo.naive.execution_time_ms} ms
                  </span>
                </div>

                <div className="space-y-3 mb-4">
                  <div className="flex justify-between items-baseline p-3 bg-white dark:bg-[#0B0F17]/80 rounded-lg border border-rose-200 dark:border-rose-900/40">
                    <span className="text-xs text-slate-600 dark:text-gray-400">Cartesian Exploded Rows:</span>
                    <span className="text-lg font-bold font-mono text-rose-600 dark:text-rose-400">
                      {chasmDemo.naive.cartesian_rows.toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between items-baseline p-3 bg-white dark:bg-[#0B0F17]/80 rounded-lg border border-rose-200 dark:border-rose-900/40">
                    <span className="text-xs text-slate-600 dark:text-gray-400">Falsely Computed GMV:</span>
                    <span className="text-lg font-bold font-mono text-rose-600 dark:text-rose-400">
                      R$ {chasmDemo.naive.naive_gmv.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-rose-800 dark:text-rose-300/90 leading-relaxed mb-4">
                  {chasmDemo.naive.explanation}
                </p>
              </div>

              <div>
                <div className="text-[10px] font-mono uppercase text-slate-500 dark:text-gray-500 mb-1">
                  Naive Flawed Query:
                </div>
                <pre className="p-3 bg-slate-900 rounded-lg text-rose-300 text-[11px] font-mono overflow-x-auto whitespace-pre">
                  {chasmDemo.naive.sql}
                </pre>
              </div>
            </div>

            {/* Right: Governed Pre-Aggregated CTE (The Solution) */}
            <div className="p-5 rounded-xl bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800/50 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <span className="p-1 rounded bg-emerald-100 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 font-bold text-xs">
                      ✓
                    </span>
                    <span className="text-sm font-semibold text-emerald-900 dark:text-emerald-200">
                      Governed Semantic Layer (CTE Pre-Aggregation)
                    </span>
                  </div>
                  <span className="text-xs font-mono text-emerald-600 dark:text-emerald-400">
                    {chasmDemo.governed.execution_time_ms} ms
                  </span>
                </div>

                <div className="space-y-3 mb-4">
                  <div className="flex justify-between items-baseline p-3 bg-white dark:bg-[#0B0F17]/80 rounded-lg border border-emerald-200 dark:border-emerald-900/40">
                    <span className="text-xs text-slate-600 dark:text-gray-400">True Distinct Orders:</span>
                    <span className="text-lg font-bold font-mono text-emerald-600 dark:text-emerald-400">
                      {chasmDemo.governed.total_orders.toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between items-baseline p-3 bg-white dark:bg-[#0B0F17]/80 rounded-lg border border-emerald-200 dark:border-emerald-900/40">
                    <span className="text-xs text-slate-600 dark:text-gray-400">Certified Net GMV:</span>
                    <span className="text-lg font-bold font-mono text-emerald-600 dark:text-emerald-400">
                      R$ {chasmDemo.governed.governed_gmv.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-emerald-800 dark:text-emerald-300/90 leading-relaxed mb-4">
                  {chasmDemo.governed.explanation}
                </p>
              </div>

              <div>
                <div className="text-[10px] font-mono uppercase text-slate-500 dark:text-gray-500 mb-1">
                  Governed Canonical CTE Query:
                </div>
                <pre className="p-3 bg-slate-900 rounded-lg text-emerald-300 text-[11px] font-mono overflow-x-auto whitespace-pre">
                  {chasmDemo.governed.sql}
                </pre>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
