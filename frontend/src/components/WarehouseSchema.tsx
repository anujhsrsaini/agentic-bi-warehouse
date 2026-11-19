import React, { useState, useEffect } from 'react';
import { Database, Table, HardDrive, Cpu, Layers, ExternalLink, CheckCircle } from 'lucide-react';
import { WarehouseStats } from '../types';
import { getStats } from '../lib/api';

export const WarehouseSchema: React.FC = () => {
  const [stats, setStats] = useState<WarehouseStats | null>(null);

  useEffect(() => {
    getStats().then(setStats).catch(console.error);
  }, []);

  const tableSchemas = [
    {
      name: 'orders',
      rows: 99441,
      pk: 'order_id',
      fks: ['customer_id -> customers.customer_id'],
      description: 'Core order transactions, timestamp milestones, and fulfillment status',
      columns: ['order_id (VARCHAR)', 'customer_id (VARCHAR)', 'order_status (VARCHAR)', 'order_purchase_timestamp (TIMESTAMP)', 'order_delivered_customer_date (TIMESTAMP)', 'order_estimated_delivery_date (TIMESTAMP)'],
    },
    {
      name: 'order_items',
      rows: 112650,
      pk: 'order_id + order_item_id',
      fks: ['order_id -> orders.order_id', 'product_id -> products.product_id', 'seller_id -> sellers.seller_id'],
      description: 'Line-item products, item prices (GMV), and freight costs',
      columns: ['order_id (VARCHAR)', 'order_item_id (INT)', 'product_id (VARCHAR)', 'seller_id (VARCHAR)', 'price (DOUBLE)', 'freight_value (DOUBLE)'],
    },
    {
      name: 'order_payments',
      rows: 103886,
      pk: 'order_id + payment_sequential',
      fks: ['order_id -> orders.order_id'],
      description: 'Payment methods (credit card, boleto, voucher, debit) and installment schedules',
      columns: ['order_id (VARCHAR)', 'payment_sequential (INT)', 'payment_type (VARCHAR)', 'payment_installments (INT)', 'payment_value (DOUBLE)'],
    },
    {
      name: 'order_reviews',
      rows: 99224,
      pk: 'review_id',
      fks: ['order_id -> orders.order_id'],
      description: 'Customer CSAT 1-5 star ratings, feedback timestamps, and comments',
      columns: ['review_id (VARCHAR)', 'order_id (VARCHAR)', 'review_score (INT)', 'review_creation_date (TIMESTAMP)', 'review_answer_timestamp (TIMESTAMP)'],
    },
    {
      name: 'customers',
      rows: 99441,
      pk: 'customer_id',
      fks: [],
      description: 'Customer profiles, unique buyer IDs, cities, and 27 Brazilian states (SP, RJ, MG...)',
      columns: ['customer_id (VARCHAR)', 'customer_unique_id (VARCHAR)', 'customer_city (VARCHAR)', 'customer_state (VARCHAR)'],
    },
    {
      name: 'products',
      rows: 32951,
      pk: 'product_id',
      fks: ['product_category_name -> category_translation.product_category_name'],
      description: 'Catalog products, categories, dimensions, and weights',
      columns: ['product_id (VARCHAR)', 'product_category_name (VARCHAR)', 'product_name_length (INT)', 'product_weight_g (DOUBLE)'],
    },
    {
      name: 'sellers',
      rows: 3095,
      pk: 'seller_id',
      fks: [],
      description: 'Merchant profiles, fulfillment origins, cities, and states',
      columns: ['seller_id (VARCHAR)', 'seller_zip_code_prefix (INT)', 'seller_city (VARCHAR)', 'seller_state (VARCHAR)'],
    },
    {
      name: 'category_translation',
      rows: 73,
      pk: 'product_category_name',
      fks: [],
      description: 'Portuguese to English product category semantic dictionary',
      columns: ['product_category_name (VARCHAR)', 'product_category_name_english (VARCHAR)'],
    },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-50 via-white to-slate-50 dark:from-[#121826] dark:via-[#161F30] dark:to-[#121826] border border-slate-200 dark:border-[#1F293D] shadow-sm dark:shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 mb-1">
              <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-emerald-100 text-emerald-800 border border-emerald-300 dark:bg-emerald-950/80 dark:text-emerald-400 dark:border-emerald-800/60 font-semibold">
                In-Process Vectorized Storage
              </span>
              <span className="text-slate-400 dark:text-gray-500">•</span>
              <span className="text-xs text-slate-500 dark:text-gray-400">Apache Arrow Zero-Copy Transport</span>
            </div>
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
              Warehouse Catalog & Schema Introspection
            </h1>
            <p className="text-xs sm:text-sm text-slate-600 dark:text-gray-400 mt-1 max-w-3xl">
              Backed by DuckDB Vectorized Execution over 550,761 real-world e-commerce transactions. Zero network hop latency and sub-15ms analytical aggregations.
            </p>
          </div>

          <div className="flex items-center space-x-3 shrink-0">
            <div className="p-3 rounded-xl bg-white dark:bg-[#0B0F17] border border-slate-200 dark:border-[#1F293D] text-center shadow-sm">
              <div className="text-lg font-bold font-mono text-blue-600 dark:text-cyan-400">
                {stats?.total_rows ? stats.total_rows.toLocaleString() : '550,761'}
              </div>
              <div className="text-[10px] text-slate-500 dark:text-gray-400 uppercase font-mono">Total Rows</div>
            </div>
            <div className="p-3 rounded-xl bg-white dark:bg-[#0B0F17] border border-slate-200 dark:border-[#1F293D] text-center shadow-sm">
              <div className="text-lg font-bold font-mono text-emerald-600 dark:text-emerald-400">8 Tables</div>
              <div className="text-[10px] text-slate-500 dark:text-gray-400 uppercase font-mono">Normalized</div>
            </div>
          </div>
        </div>
      </div>

      {/* Tables Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {tableSchemas.map((tbl) => (
          <div
            key={tbl.name}
            className="p-5 rounded-2xl bg-white dark:bg-[#121826] border border-slate-200 dark:border-[#1F293D] shadow-sm dark:shadow-lg flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <Table className="w-4 h-4 text-blue-500 dark:text-cyan-400" />
                  <span className="text-base font-bold text-slate-900 dark:text-white font-mono">{tbl.name}</span>
                </div>
                <span className="px-2.5 py-0.5 rounded-full bg-blue-50 dark:bg-cyan-950/60 border border-blue-200 dark:border-cyan-800/60 text-xs font-mono text-blue-700 dark:text-cyan-300 font-semibold">
                  {tbl.rows.toLocaleString()} rows
                </span>
              </div>

              <p className="text-xs text-slate-600 dark:text-gray-400 mb-3 leading-relaxed">
                {tbl.description}
              </p>

              <div className="space-y-1.5 mb-3 text-xs font-mono">
                <div className="flex items-center space-x-2 text-slate-700 dark:text-gray-300">
                  <span className="text-slate-400 dark:text-gray-500 uppercase text-[10px]">PK:</span>
                  <span className="text-amber-600 dark:text-amber-400 font-semibold">{tbl.pk}</span>
                </div>
                {tbl.fks.length > 0 && (
                  <div className="flex flex-col space-y-0.5 text-slate-600 dark:text-gray-400 text-[11px]">
                    <span className="text-slate-400 dark:text-gray-500 uppercase text-[10px]">FKs:</span>
                    {tbl.fks.map((fk, idx) => (
                      <span key={idx} className="text-purple-600 dark:text-purple-300 pl-2">
                        ↳ {fk}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div>
              <div className="text-[10px] font-mono uppercase text-slate-500 dark:text-gray-500 mb-1.5">
                Column Signatures:
              </div>
              <div className="flex flex-wrap gap-1">
                {tbl.columns.map((col, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 rounded bg-slate-100 dark:bg-[#0B0F17] border border-slate-200 dark:border-[#1F293D] text-[10px] font-mono text-slate-600 dark:text-gray-400"
                  >
                    {col}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
