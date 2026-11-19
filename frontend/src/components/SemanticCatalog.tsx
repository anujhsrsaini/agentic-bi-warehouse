import React, { useState, useEffect } from 'react';
import { Layers, Search, Filter, Code2, ArrowUpRight, CheckCircle2 } from 'lucide-react';
import { CertifiedMetric } from '../types';
import { getMetrics } from '../lib/api';

interface SemanticCatalogProps {
  onSelectMetric?: (metricName: string) => void;
}

export const SemanticCatalog: React.FC<SemanticCatalogProps> = ({ onSelectMetric }) => {
  const [metrics, setMetrics] = useState<CertifiedMetric[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedModel, setSelectedModel] = useState<string>('all');

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = async () => {
    try {
      const data = await getMetrics();
      setMetrics(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const models = ['all', ...Array.from(new Set(metrics.map((m) => m.model)))];

  const filteredMetrics = metrics.filter((m) => {
    const matchesSearch =
      m.name.toLowerCase().includes(search.toLowerCase()) ||
      m.label.toLowerCase().includes(search.toLowerCase()) ||
      m.description.toLowerCase().includes(search.toLowerCase()) ||
      m.dimensions.some((d) => d.toLowerCase().includes(search.toLowerCase()));
    const matchesModel = selectedModel === 'all' || m.model === selectedModel;
    return matchesSearch && matchesModel;
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-50 via-white to-slate-50 dark:from-[#121826] dark:via-[#161F30] dark:to-[#121826] border border-slate-200 dark:border-[#1F293D] shadow-sm dark:shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 mb-1">
              <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-blue-100 text-blue-700 border border-blue-200 dark:bg-cyan-950/80 dark:text-cyan-400 dark:border-cyan-800/60 font-semibold">
                Single Source of Truth
              </span>
              <span className="text-slate-400 dark:text-gray-500">•</span>
              <span className="text-xs text-slate-500 dark:text-gray-400">config/semantic_layer.yaml</span>
            </div>
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
              Governed Semantic Metric Catalog
            </h1>
            <p className="text-xs sm:text-sm text-slate-600 dark:text-gray-400 mt-1 max-w-3xl">
              All executive metrics are certified, version-controlled, and mathematically defined with certified table dependencies and conformed dimensions. The AI agent never invents formulas on the fly.
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <span className="px-3 py-1.5 rounded-xl bg-white dark:bg-[#0B0F17] border border-slate-200 dark:border-[#1F293D] text-xs font-mono text-blue-600 dark:text-cyan-400 shadow-sm">
              {metrics.length} Certified Metrics
            </span>
          </div>
        </div>
      </div>

      {/* Toolbar: Search & Filters */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 dark:text-gray-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search metric, dimension, or synonym..."
            className="w-full bg-white dark:bg-[#121826] border border-slate-200 dark:border-[#1F293D] rounded-xl pl-9 pr-4 py-2 text-xs text-slate-800 dark:text-gray-200 placeholder-slate-400 dark:placeholder-gray-500 focus:outline-none focus:border-blue-500 dark:focus:border-cyan-500 transition-colors shadow-sm"
          />
        </div>

        <div className="flex items-center space-x-1.5 overflow-x-auto w-full sm:w-auto pb-1">
          <Filter className="w-3.5 h-3.5 text-slate-400 dark:text-gray-500 shrink-0 mr-1" />
          {models.map((mod) => (
            <button
              key={mod}
              onClick={() => setSelectedModel(mod)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium font-mono capitalize transition-colors shrink-0 ${
                selectedModel === mod
                  ? 'bg-blue-50 dark:bg-cyan-500/20 text-blue-600 dark:text-cyan-300 border border-blue-200 dark:border-cyan-500/40'
                  : 'bg-white dark:bg-[#121826] text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-gray-200 border border-slate-200 dark:border-[#1F293D]'
              }`}
            >
              {mod}
            </button>
          ))}
        </div>
      </div>

      {/* Metrics Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredMetrics.map((metric) => (
          <div
            key={metric.name}
            className="flex flex-col justify-between p-5 rounded-2xl bg-white dark:bg-[#121826] border border-slate-200 dark:border-[#1F293D] hover:border-blue-400 dark:hover:border-cyan-500/40 transition-all duration-200 shadow-sm dark:shadow-lg group"
          >
            <div>
              <div className="flex items-start justify-between mb-3">
                <div>
                  <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-slate-100 dark:bg-gray-800 text-blue-600 dark:text-cyan-400 border border-slate-200 dark:border-gray-700 font-semibold">
                    Model: {metric.model}
                  </span>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white mt-1.5 group-hover:text-blue-600 dark:group-hover:text-cyan-300 transition-colors">
                    {metric.label}
                  </h3>
                  <div className="text-xs font-mono text-slate-500 dark:text-gray-400 mt-0.5">
                    [{metric.name}]
                  </div>
                </div>

                <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-sm"></div>
              </div>

              <p className="text-xs text-slate-600 dark:text-gray-400 leading-relaxed mb-4">
                {metric.description}
              </p>

              {/* Mathematical SQL Calculation */}
              <div className="mb-3">
                <div className="text-[10px] font-mono uppercase text-slate-500 mb-1 flex items-center space-x-1">
                  <Code2 className="w-3 h-3 text-blue-500 dark:text-cyan-400" />
                  <span>Certified Calculation:</span>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-[#0B0F17] border border-slate-200 dark:border-[#1F293D] font-mono text-[11px] text-blue-700 dark:text-cyan-300 overflow-x-auto">
                  {metric.calculation}
                </div>
              </div>

              {/* Hygiene Filter if present */}
              {metric.filter && (
                <div className="mb-3">
                  <div className="text-[10px] font-mono uppercase text-slate-500 mb-1">
                    Hygiene Filter:
                  </div>
                  <div className="p-2 rounded-lg bg-emerald-50 dark:bg-[#0B0F17] border border-emerald-200 dark:border-[#1F293D] font-mono text-[10px] text-emerald-700 dark:text-emerald-400 overflow-x-auto">
                    {metric.filter}
                  </div>
                </div>
              )}

              {/* Conformed Dimensions */}
              <div className="mb-4">
                <div className="text-[10px] font-mono uppercase text-slate-500 mb-1.5">
                  Conformed Dimensions:
                </div>
                <div className="flex flex-wrap gap-1">
                  {metric.dimensions.map((dim) => (
                    <span
                      key={dim}
                      className="px-2 py-0.5 rounded bg-slate-100 dark:bg-[#161F30] border border-slate-200 dark:border-[#22304A] text-[10px] font-mono text-slate-600 dark:text-gray-300"
                    >
                      {dim}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {onSelectMetric && (
              <button
                onClick={() => onSelectMetric(`What is our ${metric.name}?`)}
                className="w-full flex items-center justify-center space-x-2 py-2 px-3 rounded-xl bg-slate-50 hover:bg-blue-50 dark:bg-[#161F30] dark:hover:bg-cyan-500/20 text-xs font-semibold text-slate-700 hover:text-blue-600 dark:text-gray-200 dark:hover:text-cyan-300 border border-slate-200 hover:border-blue-300 dark:border-[#1F293D] dark:hover:border-cyan-500/40 transition-colors shadow-sm"
              >
                <span>Query in Command Center</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
