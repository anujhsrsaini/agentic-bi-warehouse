import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { CommandCenter } from './components/CommandCenter';
import { SecuritySandbox } from './components/SecuritySandbox';
import { SemanticCatalog } from './components/SemanticCatalog';
import { WarehouseSchema } from './components/WarehouseSchema';
import { getStats } from './lib/api';
import { WarehouseStats } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'command' | 'security' | 'semantic' | 'schema'>('command');
  const [stats, setStats] = useState<WarehouseStats | null>(null);
  const [pendingQuery, setPendingQuery] = useState<string | null>(null);
  
  // Theme state: defaults to 'light' for clean, low cognitive load
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const saved = localStorage.getItem('duckdb_theme');
    return saved === 'dark' ? 'dark' : 'light';
  });

  useEffect(() => {
    getStats().then(setStats).catch(console.error);
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('duckdb_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#0B0F17] text-slate-900 dark:text-[#F3F4F6] flex flex-col selection:bg-cyan-500/20 selection:text-cyan-800 dark:selection:text-cyan-200 transition-colors duration-200">
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        totalRows={stats?.total_rows || 550761}
        engine={stats?.engine || 'DuckDB Vectorized In-Process'}
        theme={theme}
        onToggleTheme={toggleTheme}
      />

      {/* Main Content Area */}
      <main className="flex-1 px-4 sm:px-6 pt-6">
        {activeTab === 'command' && (
          <CommandCenter
            initialQuery={pendingQuery}
            onQueryExecuted={() => setPendingQuery(null)}
          />
        )}
        {activeTab === 'security' && <SecuritySandbox />}
        {activeTab === 'semantic' && (
          <SemanticCatalog
            onSelectMetric={(q) => {
              setPendingQuery(q);
              setActiveTab('command');
            }}
          />
        )}
        {activeTab === 'schema' && <WarehouseSchema />}
      </main>

      {/* Enterprise Footer */}
      <footer className="border-t border-slate-200 dark:border-[#1F293D] bg-white dark:bg-[#0B0F17] px-4 sm:px-6 py-4 text-xs text-slate-500 dark:text-gray-500 mt-12 transition-colors">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center space-x-3">
            <span className="font-semibold text-slate-700 dark:text-gray-400">Governed DuckDB Analytics Agent</span>
            <span>•</span>
            <span>Olist Brazilian E-Commerce (550,761 Rows)</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
