import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  ComposedChart,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';
import { ChartSpec } from '../types';
import { BarChart3, LineChart as LineIcon, PieChart as PieIcon } from 'lucide-react';

interface ChartRendererProps {
  spec: ChartSpec | null;
  data: Record<string, any>[];
  columns: string[];
}

const COLORS = [
  '#06B6D4', // cyan-500
  '#10B981', // emerald-500
  '#8B5CF6', // violet-500
  '#F59E0B', // amber-500
  '#3B82F6', // blue-500
  '#EC4899', // pink-500
  '#14B8A6', // teal-500
  '#F97316', // orange-500
];

export const ChartRenderer: React.FC<ChartRendererProps> = ({ spec, data, columns }) => {
  if (!data || data.length === 0) return null;

  // If spec is not defined, infer default
  const chartType = spec?.type || (data.length <= 6 ? 'donut' : 'bar');
  const xKey = spec?.xKey || columns[0];
  const numCols = columns.filter((c) => typeof data[0]?.[c] === 'number');
  const yKey = spec?.yKey || numCols[0] || columns[1];

  // Helper formatter for numbers & currencies
  const formatValue = (value: any, keyName = '') => {
    if (typeof value !== 'number') return value;
    const lowerKey = keyName.toLowerCase();
    if (lowerKey.includes('pct') || lowerKey.includes('rate') || lowerKey.includes('ratio')) {
      return `${value.toFixed(2)}%`;
    }
    if (lowerKey.includes('score') || lowerKey.includes('rating') || lowerKey.includes('days') || lowerKey.includes('installment')) {
      return value.toFixed(2);
    }
    if (lowerKey.includes('gmv') || lowerKey.includes('aov') || lowerKey.includes('order_value') || lowerKey.includes('price') || lowerKey.includes('payment') || lowerKey.includes('revenue') || lowerKey.includes('freight') || lowerKey.includes('sales')) {
      return `R$ ${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
    return value.toLocaleString();
  };

  const isDark = typeof document !== 'undefined' && document.documentElement.classList.contains('dark');
  const gridStroke = isDark ? '#1F293D' : '#E2E8F0';
  const axisTickColor = isDark ? '#9CA3AF' : '#64748B';

  // Custom Dual-Theme Tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white/95 dark:bg-[#0F172A]/95 border border-slate-200 dark:border-[#1F293D] p-3 rounded-xl shadow-xl backdrop-blur-md">
          <p className="text-xs font-semibold text-slate-800 dark:text-gray-200 mb-1.5 border-b border-slate-100 dark:border-gray-800 pb-1">
            {label ? String(label).toUpperCase() : ''}
          </p>
          {payload.map((entry: any, index: number) => (
            <div key={`item-${index}`} className="flex items-center justify-between space-x-3 text-xs">
              <span className="flex items-center space-x-1.5 text-slate-500 dark:text-gray-400">
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
                <span>{String(entry.name).replace(/_/g, ' ')}:</span>
              </span>
              <span className="font-mono font-medium text-blue-600 dark:text-cyan-300">
                {formatValue(entry.value, entry.name)}
              </span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full overflow-x-auto">
      <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-100 dark:border-[#1F293D]/60">
        <div className="flex items-center space-x-2">
          {chartType === 'donut' ? (
            <PieIcon className="w-4 h-4 text-blue-500 dark:text-cyan-400" />
          ) : chartType === 'line' ? (
            <LineIcon className="w-4 h-4 text-emerald-500 dark:text-emerald-400" />
          ) : (
            <BarChart3 className="w-4 h-4 text-blue-500 dark:text-cyan-400" />
          )}
          <h3 className="text-sm font-semibold text-slate-800 dark:text-gray-200">
            {spec?.title || `${yKey.replace(/_/g, ' ').toUpperCase()} Distribution`}
          </h3>
        </div>
        <span className="text-xs font-mono text-slate-500 dark:text-gray-400">
          {data.length} datapoints
        </span>
      </div>

      <div className="h-72 w-full min-w-[500px]">
        <ResponsiveContainer width="100%" height="100%">
          {chartType === 'donut' ? (
            <PieChart>
              <Tooltip content={<CustomTooltip />} />
              <Legend
                verticalAlign="bottom"
                height={36}
                formatter={(val) => <span className="text-xs text-slate-600 dark:text-gray-300 capitalize">{String(val).replace(/_/g, ' ')}</span>}
              />
              <Pie
                data={data}
                dataKey={yKey}
                nameKey={xKey}
                cx="50%"
                cy="45%"
                innerRadius={60}
                outerRadius={95}
                paddingAngle={4}
                stroke={isDark ? '#121826' : '#FFFFFF'}
                strokeWidth={2}
              >
                {data.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
            </PieChart>
          ) : chartType === 'line' ? (
            <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} vertical={false} />
              <XAxis
                dataKey={xKey}
                stroke={axisTickColor}
                tick={{ fill: axisTickColor, fontSize: 11 }}
                tickLine={false}
              />
              <YAxis
                stroke={axisTickColor}
                tick={{ fill: axisTickColor, fontSize: 11 }}
                tickLine={false}
                tickFormatter={(v) => (v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v)}
              />
              <Tooltip content={<CustomTooltip />} />
              {spec?.metrics && spec.metrics.length > 1 ? (
                <>
                  <Legend
                    verticalAlign="top"
                    height={30}
                    formatter={(val) => (
                      <span className="text-xs text-slate-700 dark:text-gray-300 font-medium capitalize">
                        {String(val).replace(/_/g, ' ')}
                      </span>
                    )}
                  />
                  {spec.metrics.map((mKey, idx) => (
                    <Line
                      key={mKey}
                      type="monotone"
                      dataKey={mKey}
                      name={mKey.replace(/_/g, ' ').replace(/\bgmv\b/gi, 'GMV')}
                      stroke={COLORS[idx % COLORS.length]}
                      strokeWidth={2}
                      dot={{ r: 2.5, fill: COLORS[idx % COLORS.length] }}
                      activeDot={{ r: 5 }}
                    />
                  ))}
                </>
              ) : (
                <Line
                  type="monotone"
                  dataKey={yKey}
                  stroke="#2563EB"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: '#2563EB' }}
                  activeDot={{ r: 6, fill: '#3B82F6' }}
                />
              )}
            </LineChart>
          ) : chartType === 'combo' ? (
            <ComposedChart data={data.slice(0, 20)} margin={{ top: 10, right: 10, left: 10, bottom: 25 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} vertical={false} />
              <XAxis
                dataKey={xKey}
                stroke={axisTickColor}
                tick={{ fill: axisTickColor, fontSize: 11 }}
                interval={0}
                angle={data.length > 8 ? -35 : 0}
                textAnchor={data.length > 8 ? 'end' : 'middle'}
                tickLine={false}
              />
              <YAxis
                yAxisId="left"
                stroke={axisTickColor}
                tick={{ fill: axisTickColor, fontSize: 11 }}
                tickLine={false}
                tickFormatter={(v) => (v >= 1000000 ? `${(v / 1000000).toFixed(1)}M` : v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v)}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                stroke={axisTickColor}
                tick={{ fill: axisTickColor, fontSize: 11 }}
                tickLine={false}
                tickFormatter={(v) => (v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v)}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                verticalAlign="top"
                height={30}
                formatter={(val) => (
                  <span className="text-xs text-slate-700 dark:text-gray-300 font-medium capitalize">
                    {String(val).replace(/_/g, ' ')}
                  </span>
                )}
              />
              <Bar
                yAxisId="left"
                dataKey={spec?.barKey || yKey}
                name={(spec?.barKey || yKey).replace(/_/g, ' ')}
                fill="#2563EB"
                radius={[6, 6, 0, 0]}
                barSize={28}
              />
              {(spec?.lineKeys || (spec?.metrics || []).filter((m) => m !== (spec?.barKey || yKey))).map((mKey, idx) => (
                <Line
                  yAxisId="right"
                  key={mKey}
                  type="monotone"
                  dataKey={mKey}
                  name={mKey.replace(/_/g, ' ')}
                  stroke={COLORS[(idx + 1) % COLORS.length]}
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: COLORS[(idx + 1) % COLORS.length] }}
                  activeDot={{ r: 6 }}
                />
              ))}
            </ComposedChart>
          ) : (
            <BarChart data={data.slice(0, 20)} margin={{ top: 10, right: 10, left: 10, bottom: 25 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} vertical={false} />
              <XAxis
                dataKey={xKey}
                stroke={axisTickColor}
                tick={{ fill: axisTickColor, fontSize: 11 }}
                interval={0}
                angle={data.length > 8 ? -35 : 0}
                textAnchor={data.length > 8 ? 'end' : 'middle'}
                tickLine={false}
              />
              <YAxis
                stroke={axisTickColor}
                tick={{ fill: axisTickColor, fontSize: 11 }}
                tickLine={false}
                tickFormatter={(v) => (v >= 1000000 ? `${(v / 1000000).toFixed(1)}M` : v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v)}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey={yKey} radius={[6, 6, 0, 0]}>
                {data.slice(0, 20).map((_, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={index === 0 ? '#2563EB' : COLORS[index % COLORS.length]}
                    className="hover:opacity-80 transition-opacity"
                  />
                ))}
              </Bar>
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
};
