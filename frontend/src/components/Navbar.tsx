import React from 'react';
import { Terminal, Shield, Layers, Database, Sparkles, Cpu, Sun, Moon, Calendar } from 'lucide-react';

interface NavbarProps {
  activeTab: 'command' | 'security' | 'semantic' | 'schema';
  setActiveTab: (tab: 'command' | 'security' | 'semantic' | 'schema') => void;
  totalRows: number;
  engine: string;
  theme?: 'light' | 'dark';
  onToggleTheme?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  totalRows,
  engine,
  theme = 'light',
  onToggleTheme,
}) => {
  const tabs = [
    { id: 'command', label: 'Demo Chat', icon: Sparkles },
    { id: 'security', label: 'CTO Security Sandbox', icon: Shield },
    { id: 'semantic', label: 'Semantic Catalog', icon: Layers },
    { id: 'schema', label: 'Warehouse Schema', icon: Database },
  ] as const;

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200 dark:border-[#1F293D] bg-white/90 dark:bg-[#0B0F17]/90 backdrop-blur-md px-4 sm:px-6 py-2.5 transition-colors">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Left: Brand Identity */}
        <div className="flex items-center space-x-3">
          <img src="https://www.d2cgrowthos.com/logos/direction_1_mark.png" alt="D2C Growth OS Logo" className="w-8 h-8 object-contain" />
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-semibold text-slate-900 dark:text-white tracking-tight text-sm">
                Governed DuckDB
              </span>
              <span className="px-1.5 py-0.5 text-[10px] font-mono tracking-wider font-semibold rounded bg-cyan-50 dark:bg-cyan-950/80 text-cyan-700 dark:text-cyan-400 border border-cyan-200 dark:border-cyan-800/60 uppercase">
                Demo
              </span>
            </div>
            <div className="flex items-center space-x-2 text-xs text-slate-500 dark:text-gray-400">
              <span>Olist Warehouse</span>
              <span className="text-slate-300 dark:text-gray-600">•</span>
              <span className="font-mono text-cyan-600 dark:text-cyan-300 font-medium">
                {totalRows.toLocaleString()} rows
              </span>
            </div>
          </div>
        </div>

        {/* Center: Navigation Tabs */}
        <nav className="hidden md:flex items-center p-1 bg-slate-100/80 dark:bg-[#121826] border border-slate-200 dark:border-[#1F293D] rounded-xl space-x-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-3.5 py-1.5 text-xs font-medium rounded-lg transition-all duration-150 ${
                  isActive
                    ? 'bg-white dark:bg-cyan-500/15 text-slate-900 dark:text-cyan-300 border border-slate-200/80 dark:border-cyan-500/30 shadow-sm'
                    : 'text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-gray-200 hover:bg-white/60 dark:hover:bg-[#1A2234]'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-cyan-600 dark:text-cyan-400' : 'text-slate-400 dark:text-gray-500'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Right: Theme Toggle & Engine Badge */}
        <div className="flex items-center space-x-2">
          {/* Discovery Call CTA */}
          <a
            href="https://www.d2cgrowthos.com/"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-700 text-white text-xs font-medium transition-colors shadow-sm"
          >
            <Calendar className="w-3.5 h-3.5" />
            <span>Book Call</span>
          </a>

          {/* Light/Dark Toggle */}
          {onToggleTheme && (
            <button
              onClick={onToggleTheme}
              className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-[#141D2E] dark:hover:bg-[#1C263A] border border-slate-200 dark:border-[#1F293D] text-slate-600 dark:text-gray-300 transition-colors"
              title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {theme === 'dark' ? (
                <Sun className="w-4 h-4 text-amber-400" />
              ) : (
                <Moon className="w-4 h-4 text-slate-600" />
              )}
            </button>
          )}

          <div className="hidden lg:flex items-center space-x-2 px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-[#121826] border border-slate-200 dark:border-[#1F293D] text-xs">
            <Cpu className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            <span className="text-slate-500 dark:text-gray-400">Engine:</span>
            <span className="font-mono text-emerald-600 dark:text-emerald-400 font-medium">DuckDB</span>
            <span className="text-slate-300 dark:text-gray-600">|</span>
            <span className="text-emerald-600 dark:text-emerald-400 font-mono">sub-15ms</span>
          </div>

          <div className="flex md:hidden">
            <select
              value={activeTab}
              onChange={(e) => setActiveTab(e.target.value as any)}
              className="bg-slate-100 dark:bg-[#121826] border border-slate-200 dark:border-[#1F293D] text-xs text-slate-800 dark:text-gray-200 rounded-lg px-2.5 py-1.5 focus:outline-none"
            >
              <option value="command">Demo Chat</option>
              <option value="security">CTO Security Sandbox</option>
              <option value="semantic">Semantic Catalog</option>
              <option value="schema">Warehouse Schema</option>
            </select>
          </div>
        </div>
      </div>
    </header>
  );
};
