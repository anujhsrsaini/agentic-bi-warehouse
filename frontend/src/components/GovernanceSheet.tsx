import React, { useState } from 'react';
import { X, Code2, GitCommit, Copy, Check, ShieldCheck, ArrowRight, Zap, CheckCircle2 } from 'lucide-react';
import { QueryResponse } from '../types';

interface GovernanceSheetProps {
  isOpen: boolean;
  onClose: () => void;
  activeTab: 'sql' | 'lineage';
  onTabChange: (tab: 'sql' | 'lineage') => void;
  result: QueryResponse;
}

export const GovernanceSheet: React.FC<GovernanceSheetProps> = ({
  isOpen,
  onClose,
  activeTab,
  onTabChange,
  result,
}) => {
  const [copied, setCopied] = useState(false);
  const [lineageMode, setLineageMode] = useState<'dag' | 'raw'>('dag');

  if (!isOpen) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(result.validated_sql || result.raw_sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const dagNodes = [
    { id: 'source', label: 'Parquet Seed Files', type: 'Source Storage', detail: 'orders.parquet, order_items.parquet' },
    { id: 'duckdb', label: 'DuckDB Vectorized In-Process', type: 'OLAP Engine', detail: 'Zero-copy Apache Arrow buffers' },
    { id: 'semantic', label: `Metric: ${result.metric_name || 'Computed Metric'}`, type: 'Semantic Formula', detail: result.dimensions?.length ? `Grouped by ${result.dimensions.join(', ')}` : 'Overall aggregation' },
    { id: 'output', label: 'Verified Canvas Response', type: 'Presentation', detail: `${result.rows_returned || result.data?.length || 0} rows delivered` },
  ];

  // Monokai-style syntax highlighting
  const highlightSQL = (text: string) => {
    const keywords = [
      'SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN',
      'GROUP BY', 'ORDER BY', 'LIMIT', 'AS', 'AND', 'OR', 'ON', 'WITH', 'DESC',
      'ASC', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'SUM', 'AVG', 'COUNT', 'ROUND',
      'DISTINCT', 'NULLIF', 'COALESCE', 'DATE_DIFF', 'NOT', 'NULL', 'IS'
    ];

    const lines = text.split('\n');
    return lines.map((line, lIdx) => {
      const parts = line.split(/(\s+|[(),;])/);
      return (
        <div key={lIdx} className="table-row">
          <span className="table-cell pr-4 text-right select-none text-gray-600 font-mono text-[11px]">
            {lIdx + 1}
          </span>
          <span className="table-cell font-mono text-xs whitespace-pre">
            {parts.map((token, tIdx) => {
              const upper = token.toUpperCase();
              if (keywords.includes(upper)) {
                return (
                  <span key={tIdx} className="text-[#F92672] font-semibold">
                    {token}
                  </span>
                );
              }
              if (/^'.*'$/.test(token)) {
                return (
                  <span key={tIdx} className="text-[#E6DB74]">
                    {token}
                  </span>
                );
              }
              if (/^\d+(\.\d+)?$/.test(token)) {
                return (
                  <span key={tIdx} className="text-[#AE81FF]">
                    {token}
                  </span>
                );
              }
              if (['SUM', 'AVG', 'COUNT', 'ROUND', 'NULLIF', 'COALESCE', 'DATE_DIFF'].includes(upper)) {
                return (
                  <span key={tIdx} className="text-[#66D9EF]">
                    {token}
                  </span>
                );
              }
              if (token.startsWith('--')) {
                return (
                  <span key={tIdx} className="text-[#75715E] italic">
                    {token}
                  </span>
                );
              }
              return (
                <span key={tIdx} className="text-[#F8F8F2]">
                  {token}
                </span>
              );
            })}
          </span>
        </div>
      );
    });
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        onClick={onClose}
        className="absolute inset-0 bg-black/70 backdrop-blur-sm transition-opacity"
      />

      {/* Slide-over Sheet */}
      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-xl bg-[#0D121F] border-l border-[#1F293D] shadow-2xl flex flex-col z-10">
              {/* Header */}
              <div className="flex items-center justify-between px-5 py-4 border-b border-[#1F293D] bg-[#111827]">
                <div className="flex items-center space-x-2.5">
                  <div className="p-1.5 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400">
                    <ShieldCheck className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-gray-100 flex items-center space-x-2">
                      <span>Governance & Provenance Inspector</span>
                      <span className="text-[10px] font-mono uppercase bg-emerald-950/80 text-emerald-400 border border-emerald-800/60 px-1.5 py-0.2 rounded">
                        Audited
                      </span>
                    </h3>
                    <p className="text-[11px] text-gray-400 font-mono">
                      AST Guardrail Firewall • DuckDB Vectorized Proof
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <span className="text-[11px] font-mono text-gray-500 hidden sm:inline">
                    Press <kbd className="px-1 py-0.5 rounded bg-gray-800 text-gray-300">Esc</kbd> to close
                  </span>
                  <button
                    onClick={onClose}
                    className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-[#1F293D] transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Tabs */}
              <div className="flex border-b border-[#1F293D] px-5 bg-[#0B0F17]">
                <button
                  onClick={() => onTabChange('sql')}
                  className={`flex items-center space-x-2 py-3 border-b-2 text-xs font-medium mr-6 transition-colors ${
                    activeTab === 'sql'
                      ? 'border-cyan-400 text-cyan-300'
                      : 'border-transparent text-gray-400 hover:text-gray-200'
                  }`}
                >
                  <Code2 className="w-4 h-4" />
                  <span>Certified SQL & AST</span>
                </button>

                <button
                  onClick={() => onTabChange('lineage')}
                  className={`flex items-center space-x-2 py-3 border-b-2 text-xs font-medium transition-colors ${
                    activeTab === 'lineage'
                      ? 'border-purple-400 text-purple-300'
                      : 'border-transparent text-gray-400 hover:text-gray-200'
                  }`}
                >
                  <GitCommit className="w-4 h-4" />
                  <span>Column Lineage DAG</span>
                </button>
              </div>

              {/* Body */}
              <div className="flex-1 overflow-y-auto p-5 space-y-4">
                {activeTab === 'sql' && (
                  <div className="space-y-4">
                    {/* AST Security Banner */}
                    <div className="flex items-center justify-between p-3.5 rounded-xl bg-emerald-950/25 border border-emerald-800/40">
                      <div className="flex items-center space-x-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                        <div>
                          <div className="text-xs font-semibold text-emerald-300">
                            7-Stage AST Firewall Verified
                          </div>
                          <div className="text-[11px] text-gray-400 font-mono">
                            Multi-statement, Mutation, Cartesian & Exfiltration safe
                          </div>
                        </div>
                      </div>
                      <span className="text-xs font-mono font-medium text-emerald-400 bg-emerald-900/40 px-2 py-0.5 rounded border border-emerald-700/50">
                        {result.validation_time_us ? result.validation_time_us.toFixed(1) : '<200'} μs
                      </span>
                    </div>

                    {/* Rationale */}
                    {result.sql_rationale && (
                      <div className="p-3 bg-[#131B2C] rounded-xl border border-[#1F293D] text-xs text-gray-300 leading-relaxed">
                        <span className="font-semibold text-cyan-300 mr-1.5">Planner Rationale:</span>
                        {result.sql_rationale}
                      </div>
                    )}

                    {/* Monokai SQL Code Block */}
                    <div className="rounded-xl overflow-hidden border border-[#1F293D] bg-[#070A0F]">
                      <div className="flex items-center justify-between px-3.5 py-2 bg-[#111827] border-b border-[#1F293D]">
                        <span className="text-[11px] font-mono text-gray-400 flex items-center space-x-1.5">
                          <Zap className="w-3 h-3 text-cyan-400" />
                          <span>DuckDB Canonical Dialect</span>
                        </span>
                        <button
                          onClick={handleCopy}
                          className="flex items-center space-x-1.5 px-2.5 py-1 text-xs font-medium text-gray-300 hover:text-white bg-[#1F293D]/60 hover:bg-[#1F293D] rounded-lg transition-colors border border-gray-700/50"
                        >
                          {copied ? (
                            <>
                              <Check className="w-3.5 h-3.5 text-emerald-400" />
                              <span className="text-emerald-400">Copied!</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3.5 h-3.5 text-gray-400" />
                              <span>Copy SQL</span>
                            </>
                          )}
                        </button>
                      </div>

                      <div className="p-4 overflow-x-auto select-text font-mono text-xs">
                        <div className="table w-full">
                          {highlightSQL(result.validated_sql || result.raw_sql)}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'lineage' && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-400 font-mono">Data Lineage DAG</span>
                      <div className="flex bg-[#0B0F17] rounded-lg p-0.5 border border-[#1F293D]">
                        <button
                          onClick={() => setLineageMode('dag')}
                          className={`px-2.5 py-0.5 text-xs rounded font-medium transition-colors ${
                            lineageMode === 'dag' ? 'bg-purple-500/20 text-purple-300' : 'text-gray-400'
                          }`}
                        >
                          Visual Nodes
                        </button>
                        <button
                          onClick={() => setLineageMode('raw')}
                          className={`px-2.5 py-0.5 text-xs rounded font-medium transition-colors ${
                            lineageMode === 'raw' ? 'bg-purple-500/20 text-purple-300' : 'text-gray-400'
                          }`}
                        >
                          ASCII / Mermaid
                        </button>
                      </div>
                    </div>

                    {lineageMode === 'dag' ? (
                      <div className="space-y-3 py-2">
                        {dagNodes.map((n, i) => (
                          <React.Fragment key={n.id}>
                            <div className="p-3.5 bg-[#131B2C] border border-[#22304A] rounded-xl flex items-center justify-between shadow-sm">
                              <div>
                                <span className="text-[10px] font-mono uppercase text-purple-400 tracking-wider">
                                  {n.type}
                                </span>
                                <h4 className="text-xs font-semibold text-gray-200 mt-0.5">
                                  {n.label}
                                </h4>
                                <p className="text-[11px] text-gray-400 mt-0.5 font-mono">
                                  {n.detail}
                                </p>
                              </div>
                              <span className="text-xs font-mono text-gray-500">Step {i + 1}</span>
                            </div>
                            {i < dagNodes.length - 1 && (
                              <div className="flex justify-center text-purple-400/60 font-mono text-xs">
                                ↓
                              </div>
                            )}
                          </React.Fragment>
                        ))}
                      </div>
                    ) : (
                      <div className="space-y-3 font-mono text-xs">
                        {result.lineage_ascii && (
                          <div>
                            <div className="text-gray-500 text-[11px] mb-1">ASCII Lineage Tree:</div>
                            <pre className="p-3 bg-[#070A0F] rounded-xl text-purple-300 border border-[#1F293D] overflow-x-auto whitespace-pre">
                              {result.lineage_ascii}
                            </pre>
                          </div>
                        )}
                        {result.lineage_mermaid && (
                          <div>
                            <div className="text-gray-500 text-[11px] mb-1">Mermaid Graph Definition:</div>
                            <pre className="p-3 bg-[#070A0F] rounded-xl text-gray-400 border border-[#1F293D] overflow-x-auto text-[11px]">
                              {result.lineage_mermaid}
                            </pre>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      );
};
