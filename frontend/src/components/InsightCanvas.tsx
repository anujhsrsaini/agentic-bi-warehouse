import React from 'react';
import { BarChart3, Table as TableIcon, ShieldCheck, Sparkles, SlidersHorizontal } from 'lucide-react';
import { QueryResponse } from '../types';
import { ChartRenderer } from './ChartRenderer';
import { DataTable } from './DataTable';

interface InsightCanvasProps {
  result: QueryResponse;
  activeView: 'chart' | 'table';
  onViewChange: (view: 'chart' | 'table') => void;
  onOpenInspector: (tab: 'sql' | 'lineage') => void;
}

export const InsightCanvas: React.FC<InsightCanvasProps> = ({
  result,
  activeView,
  onViewChange,
  onOpenInspector,
}) => {
  // Render markdown bold in narrative cleanly with subtle high-contrast pills
  const renderFormattedNarrative = (text: string) => {
    if (!text) return null;
    return text.split('\n').filter((l) => l.trim().length > 0).map((line, idx) => {
      const isBullet = line.trim().startsWith('-') || line.trim().startsWith('•') || /^\d+\./.test(line.trim());
      const cleanLine = line.replace(/^[-•\d.]\s*/, '');
      const parts = cleanLine.split(/(\*\*.*?\*\*)/g);

      return (
        <div key={idx} className={`flex items-start space-x-2 my-1.5 ${isBullet ? 'pl-1 sm:pl-2' : ''}`}>
          {isBullet && (
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-500 mt-2 shrink-0"></span>
          )}
          <p className="text-xs sm:text-sm text-slate-700 dark:text-gray-300 leading-relaxed">
            {parts.map((p, pIdx) => {
              if (p.startsWith('**') && p.endsWith('**')) {
                return (
                  <strong key={pIdx} className="font-semibold text-slate-900 dark:text-white bg-cyan-50 dark:bg-cyan-500/10 px-1.5 py-0.5 rounded border border-cyan-200 dark:border-cyan-500/20">
                    {p.slice(2, -2)}
                  </strong>
                );
              }
              return <span key={pIdx}>{p}</span>;
            })}
          </p>
        </div>
      );
    });
  };

  return (
    <div className="w-full bg-white dark:bg-[#101726]/90 border border-slate-200 dark:border-[#1F293D] rounded-2xl overflow-hidden shadow-sm dark:shadow-2xl transition-colors">
      {/* 1. Executive Summary Hero Card */}
      <div className="p-4 sm:p-5 border-b border-slate-200 dark:border-[#1F293D] bg-slate-50/70 dark:bg-gradient-to-r dark:from-[#121929] dark:via-[#151E32] dark:to-[#121929] transition-colors">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 mb-2.5">
          <div className="flex items-center space-x-2">
            <div className="p-1.5 rounded-lg bg-cyan-100 dark:bg-cyan-500/15 border border-cyan-200 dark:border-cyan-500/30 text-cyan-700 dark:text-cyan-400">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-900 dark:text-gray-100 tracking-tight">
                Executive Synthesis & Key Takeaways
              </h3>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-[11px] font-mono text-cyan-700 dark:text-cyan-400 bg-cyan-50 dark:bg-cyan-950/60 border border-cyan-200 dark:border-cyan-800/60 px-2.5 py-0.5 rounded-full font-medium">
              DuckDB Vectorized ({result.execution_time_ms.toFixed(2)} ms)
            </span>
            <button
              onClick={() => onOpenInspector('sql')}
              className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/60 hover:bg-emerald-100 dark:hover:bg-emerald-900/60 border border-emerald-200 dark:border-emerald-800/60 text-[11px] font-mono text-emerald-700 dark:text-emerald-400 font-medium transition-colors"
              title="Click to inspect AST Firewall validation"
            >
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>AST Safe ({result.validation_time_us ? result.validation_time_us.toFixed(0) : '<200'} μs)</span>
            </button>
          </div>
        </div>

        <div className="space-y-1">
          {renderFormattedNarrative(result.summary_narrative)}
        </div>
      </div>

      {/* 2. Unified Workspace Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between px-4 sm:px-5 py-2.5 bg-slate-100/60 dark:bg-[#0D1322] border-b border-slate-200 dark:border-[#1F293D] gap-2 transition-colors">
        {/* Left: Viewport Switcher */}
        <div className="flex items-center bg-white dark:bg-[#070B14] p-1 rounded-xl border border-slate-200 dark:border-[#1F293D] space-x-1">
          <button
            onClick={() => onViewChange('chart')}
            className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-medium transition-all ${
              activeView === 'chart'
                ? 'bg-cyan-50 dark:bg-cyan-500/20 text-cyan-700 dark:text-cyan-300 border border-cyan-200 dark:border-cyan-500/40 shadow-sm'
                : 'text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-gray-200 hover:bg-slate-100 dark:hover:bg-[#141C2E]'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            <span>Visualization</span>
          </button>

          <button
            onClick={() => onViewChange('table')}
            className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-medium transition-all ${
              activeView === 'table'
                ? 'bg-cyan-50 dark:bg-cyan-500/20 text-cyan-700 dark:text-cyan-300 border border-cyan-200 dark:border-cyan-500/40 shadow-sm'
                : 'text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-gray-200 hover:bg-slate-100 dark:hover:bg-[#141C2E]'
            }`}
          >
            <TableIcon className="w-3.5 h-3.5" />
            <span>Data Table ({result.rows_returned || result.data?.length || 0})</span>
          </button>
        </div>

        {/* Right: Technical Inspector Trigger */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => onOpenInspector('sql')}
            className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 dark:text-gray-300 hover:text-slate-900 dark:hover:text-white bg-white dark:bg-[#141D2E] hover:bg-slate-100 dark:hover:bg-[#1C263A] rounded-xl border border-slate-200 dark:border-[#1F293D] hover:border-cyan-400 transition-colors shadow-sm"
          >
            <SlidersHorizontal className="w-3.5 h-3.5 text-cyan-600 dark:text-cyan-400" />
            <span>View SQL & Lineage (⌘I)</span>
          </button>
        </div>
      </div>

      {/* 3. Canvas Content Body (Chart or Table) */}
      <div className="p-4 sm:p-5">
        {activeView === 'chart' ? (
          <ChartRenderer
            spec={result.chart_spec}
            data={result.data}
            columns={result.columns}
          />
        ) : (
          <DataTable
            columns={result.columns}
            data={result.data}
            executionTimeMs={result.execution_time_ms}
          />
        )}
      </div>
    </div>
  );
};
