import React from 'react';
import { GitCommit, Calendar } from 'lucide-react';

interface ProvenanceBarProps {
  onOpenInspector: () => void;
}

export const ProvenanceBar: React.FC<ProvenanceBarProps> = ({ onOpenInspector }) => {
  return (
    <div className="flex items-center space-x-3">
      <button
        onClick={onOpenInspector}
        className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#111827] border border-[#1F293D] hover:border-purple-500/50 text-purple-300 text-xs font-mono transition-colors shadow-sm"
      >
        <GitCommit className="w-3.5 h-3.5" />
        <span>Provenance Verified</span>
      </button>
      <a
        href="https://www.d2cgrowthos.com/"
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-700 text-white text-xs font-medium transition-colors shadow-sm"
      >
        <Calendar className="w-3.5 h-3.5" />
        <span>Book Discovery Call</span>
      </a>
    </div>
  );
};
