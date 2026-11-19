import React from 'react';
import { HelpCircle, ArrowRight } from 'lucide-react';

interface DisambiguationCardProps {
  promptText: string;
  options: string[];
  onSelectOption: (optionText: string) => void;
}

export const DisambiguationCard: React.FC<DisambiguationCardProps> = ({
  promptText,
  options,
  onSelectOption,
}) => {
  return (
    <div className="w-full bg-amber-50/90 dark:bg-[#1A1813] border border-amber-200 dark:border-amber-600/40 rounded-2xl p-5 shadow-sm dark:shadow-2xl relative overflow-hidden transition-colors">
      <div className="flex items-start space-x-3 mb-4">
        <div className="p-2 rounded-xl bg-amber-100 dark:bg-amber-500/15 border border-amber-200 dark:border-amber-500/30 text-amber-700 dark:text-amber-400 shrink-0 mt-0.5">
          <HelpCircle className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h3 className="text-sm font-semibold text-amber-950 dark:text-amber-200">
              Disambiguation & Triage Required
            </h3>
            <span className="text-[10px] font-mono uppercase bg-amber-100 dark:bg-amber-950/80 text-amber-800 dark:text-amber-400 border border-amber-300 dark:border-amber-700/60 px-1.5 py-0.5 rounded font-medium">
              Zero Guesswork
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-700 dark:text-gray-300 mt-1 leading-relaxed">
            {promptText}
          </p>
        </div>
      </div>

      <div className="space-y-2 mt-4">
        <div className="text-[11px] font-mono uppercase tracking-wider text-slate-500 dark:text-gray-400 mb-2">
          Select certified metric interpretation:
        </div>
        {options.map((opt, i) => {
          const optTitle = opt.split(':')[0] || opt;
          const optDesc = opt.includes(':') ? opt.split(':').slice(1).join(':') : '';

          return (
            <button
              key={i}
              onClick={() => onSelectOption(opt)}
              className="w-full flex items-center justify-between p-3 rounded-xl bg-white dark:bg-[#231E15] hover:bg-amber-100/60 dark:hover:bg-[#2C2417] border border-amber-200 dark:border-amber-900/50 hover:border-amber-400 dark:hover:border-amber-500/60 transition-all duration-200 text-left group shadow-xs"
            >
              <div className="flex items-center space-x-3">
                <span className="flex items-center justify-center w-6 h-6 rounded-lg bg-amber-100 dark:bg-amber-500/20 text-amber-800 dark:text-amber-300 text-xs font-mono font-bold border border-amber-200 dark:border-amber-500/30">
                  {i + 1}
                </span>
                <div>
                  <div className="text-xs font-semibold text-slate-900 dark:text-amber-100 group-hover:text-amber-900 dark:group-hover:text-amber-300 transition-colors">
                    {optTitle}
                  </div>
                  {optDesc && (
                    <div className="text-[11px] text-slate-600 dark:text-gray-400 group-hover:text-slate-800 dark:group-hover:text-gray-300">
                      {optDesc}
                    </div>
                  )}
                </div>
              </div>
              <ArrowRight className="w-4 h-4 text-amber-600 dark:text-amber-500/60 group-hover:text-amber-800 dark:group-hover:text-amber-300 group-hover:translate-x-1 transition-all" />
            </button>
          );
        })}
      </div>
    </div>
  );
};
