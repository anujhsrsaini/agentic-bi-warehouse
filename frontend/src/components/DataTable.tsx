import React, { useState, useMemo } from 'react';
import { Table, Download, ArrowUpDown, ChevronLeft, ChevronRight, Search } from 'lucide-react';

interface DataTableProps {
  columns: string[];
  data: Record<string, any>[];
  executionTimeMs?: number;
}

export const DataTable: React.FC<DataTableProps> = ({ columns, data, executionTimeMs }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortCol, setSortCol] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [page, setPage] = useState(1);
  const pageSize = 10;

  // Sorting and Filtering
  const filteredData = useMemo(() => {
    let result = [...data];
    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      result = result.filter((row) =>
        Object.values(row).some((val) => String(val).toLowerCase().includes(q))
      );
    }
    if (sortCol) {
      result.sort((a, b) => {
        const valA = a[sortCol];
        const valB = b[sortCol];
        if (typeof valA === 'number' && typeof valB === 'number') {
          return sortDir === 'asc' ? valA - valB : valB - valA;
        }
        const strA = String(valA || '');
        const strB = String(valB || '');
        return sortDir === 'asc' ? strA.localeCompare(strB) : strB.localeCompare(strA);
      });
    }
    return result;
  }, [data, searchTerm, sortCol, sortDir]);

  const totalPages = Math.ceil(filteredData.length / pageSize) || 1;
  const paginatedData = filteredData.slice((page - 1) * pageSize, page * pageSize);

  const handleSort = (col: string) => {
    if (sortCol === col) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortCol(col);
      setSortDir('desc');
    }
  };

  // 1-Click CSV Export
  const exportCSV = () => {
    if (!data.length) return;
    const header = columns.join(',');
    const rows = data.map((row) =>
      columns.map((col) => {
        const val = row[col];
        if (typeof val === 'string' && val.includes(',')) return `"${val}"`;
        return val ?? '';
      }).join(',')
    );
    const csvContent = [header, ...rows].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `duckdb_analytics_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Helper formatting for values in cells
  const formatCell = (col: string, val: any) => {
    if (val === null || val === undefined) return <span className="text-slate-400 dark:text-gray-600">-</span>;
    if (typeof val === 'number') {
      const lower = col.toLowerCase();
      if (lower.includes('pct') || lower.includes('rate') || lower.includes('ratio')) {
        return <span className="font-mono text-emerald-600 dark:text-emerald-300 font-medium">{val.toFixed(2)}%</span>;
      }
      if (lower.includes('score') || lower.includes('rating')) {
        return <span className="font-mono text-amber-600 dark:text-amber-300 font-medium">★ {val.toFixed(2)}</span>;
      }
      if (lower.includes('days') || lower.includes('installments')) {
        return <span className="font-mono text-slate-700 dark:text-gray-300">{val.toFixed(1)}</span>;
      }
      if (lower.includes('gmv') || lower.includes('aov') || lower.includes('order_value') || lower.includes('price') || lower.includes('payment') || lower.includes('revenue') || lower.includes('freight') || lower.includes('sales')) {
        return <span className="font-mono text-blue-600 dark:text-cyan-300 font-medium">R$ {val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>;
      }
      return <span className="font-mono text-slate-800 dark:text-gray-200">{val.toLocaleString()}</span>;
    }
    return <span className="text-slate-800 dark:text-gray-200">{String(val)}</span>;
  };

  if (!data || data.length === 0) return null;

  return (
    <div className="w-full overflow-hidden">
      {/* Table Toolbar */}
      <div className="flex flex-col sm:flex-row items-center justify-between pb-3.5 border-b border-slate-200 dark:border-[#1F293D] gap-3">
        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <Table className="w-4 h-4 text-blue-500 dark:text-cyan-400" />
          <h3 className="text-sm font-semibold text-slate-800 dark:text-gray-200">
            Tabular Result
          </h3>
          <span className="text-xs font-mono text-slate-600 dark:text-gray-400 bg-slate-100 dark:bg-gray-800/80 px-2 py-0.5 rounded-md">
            {data.length.toLocaleString()} rows
          </span>
          {executionTimeMs !== undefined && (
            <span className="text-xs font-mono text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/60 px-2 py-0.5 rounded-md border border-emerald-200 dark:border-emerald-900/40">
              ⚡ {executionTimeMs.toFixed(2)} ms
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2.5 w-full sm:w-auto justify-end">
          {/* Search Box */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 dark:text-gray-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Filter results..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(1);
              }}
              className="bg-slate-50 dark:bg-[#0B0F17] border border-slate-200 dark:border-[#1F293D] rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-800 dark:text-gray-200 placeholder-slate-400 dark:placeholder-gray-500 focus:outline-none focus:border-blue-500 dark:focus:border-cyan-500 w-44 sm:w-48 transition-colors"
            />
          </div>

          {/* CSV Export Button */}
          <button
            onClick={exportCSV}
            className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 dark:text-cyan-300 hover:text-slate-900 dark:hover:text-white bg-slate-100 dark:bg-cyan-950/60 hover:bg-slate-200 dark:hover:bg-cyan-900/60 rounded-lg transition-colors border border-slate-200 dark:border-cyan-800/60 shadow-sm"
            title="Download CSV"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Table Body */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 dark:bg-[#161F30] text-slate-600 dark:text-gray-400 uppercase tracking-wider text-[11px] font-mono border-b border-slate-200 dark:border-[#1F293D]">
            <tr>
              <th className="py-2.5 px-4 w-12 text-center text-slate-400 dark:text-gray-500">#</th>
              {columns.map((col) => (
                <th
                  key={col}
                  onClick={() => handleSort(col)}
                  className="py-2.5 px-4 cursor-pointer hover:text-blue-600 dark:hover:text-cyan-400 transition-colors select-none"
                >
                  <div className="flex items-center space-x-1.5">
                    <span>{col.replace(/_/g, ' ')}</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-400 dark:text-gray-600 hover:text-blue-600 dark:hover:text-cyan-400" />
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-[#1F293D]/60">
            {paginatedData.map((row, rIdx) => (
              <tr
                key={rIdx}
                className="hover:bg-slate-50/80 dark:hover:bg-[#161F30]/70 transition-colors duration-100"
              >
                <td className="py-2.5 px-4 text-center font-mono text-[11px] text-slate-400 dark:text-gray-500">
                  {(page - 1) * pageSize + rIdx + 1}
                </td>
                {columns.map((col) => (
                  <td key={col} className="py-2.5 px-4">
                    {formatCell(col, row[col])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination Bar */}
      <div className="flex items-center justify-between px-4 py-3 bg-slate-50 dark:bg-[#161F30] border-t border-slate-200 dark:border-[#1F293D] text-xs text-slate-600 dark:text-gray-400">
        <div>
          Showing <span className="font-mono text-slate-800 dark:text-gray-200">{(page - 1) * pageSize + 1}</span> to{' '}
          <span className="font-mono text-slate-800 dark:text-gray-200">{Math.min(page * pageSize, filteredData.length)}</span> of{' '}
          <span className="font-mono text-slate-800 dark:text-gray-200">{filteredData.length}</span> entries
        </div>

        <div className="flex items-center space-x-1.5">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="p-1 rounded-md bg-white dark:bg-[#1F293D]/60 hover:bg-slate-100 dark:hover:bg-[#1F293D] border border-slate-200 dark:border-transparent text-slate-700 dark:text-gray-300 disabled:opacity-30 disabled:cursor-not-allowed shadow-sm"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="px-2 font-mono text-xs">
            {page} / {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="p-1 rounded-md bg-white dark:bg-[#1F293D]/60 hover:bg-slate-100 dark:hover:bg-[#1F293D] border border-slate-200 dark:border-transparent text-slate-700 dark:text-gray-300 disabled:opacity-30 disabled:cursor-not-allowed shadow-sm"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
