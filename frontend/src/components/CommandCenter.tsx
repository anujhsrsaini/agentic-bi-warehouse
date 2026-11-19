import React, { useState, useEffect, useRef } from 'react';
import {
  Search,
  Sparkles,
  CornerDownLeft,
  Loader2,
  RefreshCw,
  AlertCircle,
  ShieldX,
  PlusCircle,
  DollarSign,
  Star,
  Truck,
  CreditCard,
  HelpCircle,
  TrendingDown,
  ArrowRight,
} from 'lucide-react';
import { QueryResponse } from '../types';
import { runQuery } from '../lib/api';

import { InsightCanvas } from './InsightCanvas';
import { GovernanceSheet } from './GovernanceSheet';
import { ProvenanceBar } from './ProvenanceBar';
import { DisambiguationCard } from './DisambiguationCard';

const DEMO_CARDS = [
  {
    icon: DollarSign,
    color: 'emerald',
    title: 'Revenue & Net GMV',
    subtitle: 'Product sales across 27 Brazilian customer states',
    query: 'What is our GMV by customer state?',
  },
  {
    icon: Star,
    color: 'amber',
    title: 'Customer Satisfaction (CSAT)',
    subtitle: 'Average review rating by product category',
    query: 'What is the average review score by product category?',
  },
  {
    icon: Truck,
    color: 'blue',
    title: 'Shipping & Delivery Latency',
    subtitle: 'Which states experience the worst shipping delays?',
    query: 'Which customer states experience the longest shipping delays?',
  },
  {
    icon: CreditCard,
    color: 'purple',
    title: 'Payment Distribution',
    subtitle: 'Credit card vs boleto vs voucher installments',
    query: 'Show distribution of payment methods (credit card vs boleto vs voucher)',
  },
  {
    icon: TrendingDown,
    color: 'rose',
    title: 'Root-Cause Diagnostic',
    subtitle: 'Automated multi-factor attribution on CSAT drop',
    query: 'Why did review scores drop?',
  },
  {
    icon: HelpCircle,
    color: 'cyan',
    title: 'Ambiguity & Triage Test',
    subtitle: 'Zero blind guessing — asks for disambiguation',
    query: 'Show revenue',
  },
];

interface CommandCenterProps {
  initialQuery?: string | null;
  onQueryExecuted?: () => void;
}

export const CommandCenter: React.FC<CommandCenterProps> = ({ initialQuery, onQueryExecuted }) => {
  const [question, setQuestion] = useState(initialQuery || '');

  useEffect(() => {
    if (initialQuery) {
      handleRunQuery(initialQuery);
      if (onQueryExecuted) {
        onQueryExecuted();
      }
    }
  }, [initialQuery]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<'chart' | 'table'>('chart');
  const [isInspectorOpen, setIsInspectorOpen] = useState(false);
  const [inspectorTab, setInspectorTab] = useState<'sql' | 'lineage'>('sql');
  const inputRef = useRef<HTMLInputElement>(null);

  // Global keyboard shortcuts: '/' to focus, 'Cmd+I' to inspect, 'Esc' to close inspector
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === '/' && document.activeElement !== inputRef.current) {
        e.preventDefault();
        inputRef.current?.focus();
      }
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'i') {
        e.preventDefault();
        setIsInspectorOpen((prev) => !prev);
      }
      if (e.key === 'Escape' && isInspectorOpen) {
        setIsInspectorOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isInspectorOpen]);

  const handleRunQuery = async (queryText: string) => {
    if (!queryText.trim() || loading) return;
    setLoading(true);
    setError(null);
    try {
      const res = await runQuery(queryText);
      setResult(res);
      setQuestion(queryText);
      if (res.chart_spec && res.chart_spec.type !== 'kpi') {
        setActiveView('chart');
      } else if (res.data && res.data.length > 1) {
        setActiveView('chart');
      } else {
        setActiveView('table');
      }
    } catch (err: any) {
      setError(err.message || 'Execution error');
    } finally {
      setLoading(false);
    }
  };

  const handleResetToHero = () => {
    setResult(null);
    setQuestion('');
    setError(null);
    setTimeout(() => inputRef.current?.focus(), 100);
  };

  const handleDisambiguationChoice = (opt: string) => {
    if (opt.includes('GMV by State')) {
      handleRunQuery('What is our GMV by customer state?');
    } else if (opt.includes('Total Payment Value')) {
      handleRunQuery('What is our total payment value?');
    } else {
      handleRunQuery('What is our total Net GMV?');
    }
  };

  const openInspector = (tab: 'sql' | 'lineage' = 'sql') => {
    setInspectorTab(tab);
    setIsInspectorOpen(true);
  };

  return (
    <div className="max-w-5xl mx-auto pb-16">
      {/* ─────────────────────────────────────────────────────────────────── */}
      {/* 1. HERO VIEW (Centered Chat in the Middle for Easy Demo)            */}
      {/* ─────────────────────────────────────────────────────────────────── */}
      {!result && !loading && (
        <div className="flex flex-col items-center justify-center min-h-[75vh] text-center px-4">
          {/* Badge */}
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-cyan-50 dark:bg-cyan-950/60 border border-cyan-200 dark:border-cyan-800/60 text-xs font-mono text-cyan-700 dark:text-cyan-300 mb-4 shadow-sm">
            <span className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse"></span>
            <span>DuckDB Vectorized OLAP • 550,761 Rows</span>
          </div>

          {/* Big Centered Headline */}
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight max-w-3xl leading-tight">
            Ask me Anything about the <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-600 to-blue-600 dark:from-cyan-400 dark:to-blue-400">Olist Demo Warehouse</span>
          </h1>

          {/* Subtitle */}
          <p className="mt-3 text-sm sm:text-base text-slate-600 dark:text-gray-400 max-w-2xl leading-relaxed">
            Instant natural language analytics on real e-commerce data with certified metric governance, 7-stage AST security, and sub-15ms vectorized execution.
          </p>

          {/* Large Centered Chat Box */}
          <div className="w-full max-w-2xl mt-8">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleRunQuery(question);
              }}
              className="relative flex items-center bg-white dark:bg-[#101726] border border-slate-300 dark:border-[#1F293D] rounded-2xl p-2 shadow-xl focus-within:border-cyan-500 focus-within:ring-2 focus-within:ring-cyan-500/20 transition-all duration-200"
            >
              <div className="p-2.5 text-cyan-600 dark:text-cyan-400">
                <Search className="w-5 h-5" />
              </div>

              <input
                ref={inputRef}
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask any business question (or pick a suggested card below)..."
                className="flex-1 bg-transparent px-2 py-2 text-sm sm:text-base text-slate-900 dark:text-gray-100 placeholder-slate-400 dark:placeholder-gray-500 focus:outline-none"
                disabled={loading}
                autoFocus
              />

              <button
                type="submit"
                disabled={loading || !question.trim()}
                className="flex items-center space-x-1.5 px-4 py-2.5 bg-cyan-600 hover:bg-cyan-500 dark:bg-gradient-to-r dark:from-cyan-500 dark:to-blue-600 text-white text-xs font-semibold rounded-xl transition-all shadow-md active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <span>Ask Agent</span>
                <CornerDownLeft className="w-3.5 h-3.5" />
              </button>
            </form>
          </div>

          {/* 6 Clickable Demo Suggestion Cards */}
          <div className="w-full max-w-3xl mt-8">
            <div className="text-xs font-mono uppercase tracking-wider text-slate-400 dark:text-gray-500 mb-3 text-left pl-1">
              Popular 1-Click Demo Questions:
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 text-left">
              {DEMO_CARDS.map((card, idx) => {
                const Icon = card.icon;
                return (
                  <button
                    key={idx}
                    onClick={() => handleRunQuery(card.query)}
                    className="p-3.5 rounded-xl bg-white dark:bg-[#121929] border border-slate-200 dark:border-[#1F293D] hover:border-cyan-500/60 dark:hover:border-cyan-500/50 hover:shadow-md transition-all duration-150 group flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center space-x-2 mb-1.5">
                        <div className="p-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-cyan-600 dark:text-cyan-400 group-hover:bg-cyan-50 dark:group-hover:bg-cyan-950/60 transition-colors">
                          <Icon className="w-3.5 h-3.5" />
                        </div>
                        <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 group-hover:text-cyan-600 dark:group-hover:text-cyan-400 transition-colors">
                          {card.title}
                        </h4>
                      </div>
                      <p className="text-[11px] text-slate-500 dark:text-gray-400 leading-snug line-clamp-2">
                        "{card.query}"
                      </p>
                    </div>

                    <div className="flex items-center text-[10px] font-mono text-cyan-600 dark:text-cyan-400 mt-2 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                      <span>Click to run</span>
                      <ArrowRight className="w-3 h-3 ml-1" />
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* ─────────────────────────────────────────────────────────────────── */}
      {/* 2. LOADING STATE                                                    */}
      {/* ─────────────────────────────────────────────────────────────────── */}
      {loading && (
        <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-4">
          <div className="relative flex items-center justify-center w-12 h-12 rounded-2xl bg-cyan-50 dark:bg-cyan-950/60 border border-cyan-200 dark:border-cyan-800 text-cyan-600 dark:text-cyan-400 shadow-md">
            <Loader2 className="w-6 h-6 animate-spin" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-slate-900 dark:text-white">
              Running Multi-Agent Cognitive Loop...
            </h3>
            <p className="text-xs text-slate-500 dark:text-gray-400 mt-1 font-mono">
              Router → Semantic Linker → SQLGlot AST Firewall → DuckDB Vectorized OLAP
            </p>
          </div>
          <div className="max-w-md w-full px-4">
            <div className="p-3 bg-white dark:bg-[#121929] border border-slate-200 dark:border-[#1F293D] rounded-xl text-xs font-mono text-slate-600 dark:text-gray-400">
              "{question}"
            </div>
          </div>
        </div>
      )}

      {/* ─────────────────────────────────────────────────────────────────── */}
      {/* 3. ANSWER VIEW (When Result is Available)                           */}
      {/* ─────────────────────────────────────────────────────────────────── */}
      {result && !loading && (
        <div className="space-y-4 pt-2">
          {/* Top Bar: Input + Reset Button */}
          <div className="flex items-center space-x-2">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleRunQuery(question);
              }}
              className="flex-1 relative flex items-center bg-white dark:bg-[#101726] border border-slate-200 dark:border-[#1F293D] rounded-xl px-2 py-1 shadow-sm focus-within:border-cyan-500 transition-all"
            >
              <Search className="w-4 h-4 text-cyan-600 dark:text-cyan-400 ml-1.5 shrink-0" />
              <input
                ref={inputRef}
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask another question about Olist e-commerce..."
                className="flex-1 bg-transparent px-2.5 py-1.5 text-xs sm:text-sm text-slate-900 dark:text-gray-100 placeholder-slate-400 dark:placeholder-gray-500 focus:outline-none"
              />
              <button
                type="submit"
                disabled={!question.trim()}
                className="px-3 py-1 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold rounded-lg transition-colors shadow-sm disabled:opacity-40"
              >
                Run
              </button>
            </form>

            <button
              onClick={handleResetToHero}
              className="flex items-center space-x-1.5 px-3 py-2 bg-white dark:bg-[#131B2C] border border-slate-200 dark:border-[#1F293D] hover:bg-slate-100 dark:hover:bg-[#1C263A] rounded-xl text-xs font-medium text-slate-700 dark:text-gray-300 transition-colors shadow-sm shrink-0"
              title="Return to centered demo prompt screen"
            >
              <PlusCircle className="w-3.5 h-3.5 text-cyan-600 dark:text-cyan-400" />
              <span className="hidden sm:inline">New Question</span>
            </button>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="flex items-center space-x-3 p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800/60 rounded-xl text-rose-800 dark:text-rose-300 text-xs shadow-sm">
              <AlertCircle className="w-4 h-4 text-rose-600 dark:text-rose-400 shrink-0" />
              <div className="flex-1 font-mono text-[11px]">{error}</div>
              <button
                onClick={() => handleRunQuery(question)}
                className="flex items-center space-x-1 px-2.5 py-1 bg-rose-100 dark:bg-rose-900/60 hover:bg-rose-200 rounded-md text-rose-800 dark:text-rose-200 text-xs"
              >
                <RefreshCw className="w-3 h-3" />
                <span>Retry</span>
              </button>
            </div>
          )}

          {/* Crimson AST Security Shield — raw SQL blocked in chat */}
          {result.security_passed === false && !!result.security_error && (
            <div className="flex items-start space-x-3 p-4 bg-rose-50 dark:bg-rose-950/40 border-2 border-rose-300 dark:border-rose-700/70 rounded-xl text-rose-900 dark:text-rose-200 shadow-sm">
              <div className="p-2 rounded-lg bg-rose-100 dark:bg-rose-900/60 text-rose-600 dark:text-rose-300 shrink-0">
                <ShieldX className="w-5 h-5" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <h4 className="text-sm font-semibold tracking-tight">Query Blocked by AST Firewall</h4>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-rose-100 dark:bg-rose-900/60 border border-rose-200 dark:border-rose-800/60">
                    {result.validation_time_us ? `${result.validation_time_us.toFixed(0)} μs` : '<250 μs'}
                  </span>
                </div>
                <p className="mt-1 text-xs font-mono break-words">
                  {result.security_error || 'Unauthorized statement blocked by the 7-stage AST firewall.'}
                </p>
              </div>
            </div>
          )}


          {/* Disambiguation Card (If Ambiguity Detected) */}
          {result.clarification_prompt && (
            <DisambiguationCard
              promptText={result.clarification_prompt}
              options={result.clarification_options}
              onSelectOption={handleDisambiguationChoice}
            />
          )}

          {/* Unified Insight Canvas (Hero Narrative + Segmented Visualization/Table Viewport) */}
          {!result.clarification_prompt && result.security_passed !== false && (
            <div className="space-y-4">
              <div className="flex justify-end">
                <ProvenanceBar onOpenInspector={() => openInspector('lineage')} />
              </div>
              <InsightCanvas
                result={result}
                activeView={activeView}
                onViewChange={setActiveView}
                onOpenInspector={openInspector}
              />
            </div>
          )}

          {/* Slide-Over Governance & SQL Inspector Sheet */}
          <GovernanceSheet
            isOpen={isInspectorOpen}
            onClose={() => setIsInspectorOpen(false)}
            activeTab={inspectorTab}
            onTabChange={setInspectorTab}
            result={result}
          />
        </div>
      )}
    </div>
  );
};
