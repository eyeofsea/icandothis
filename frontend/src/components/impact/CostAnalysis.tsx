'use client';

import { useMemo } from 'react';
import { useDisruptionStore } from '@/stores/disruptionStore';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';
import { formatCurrency } from '@/lib/utils';
import { TrendingDown, TrendingUp, DollarSign } from 'lucide-react';

export default function CostAnalysis() {
  const { activeDisruptions } = useDisruptionStore();
  const hasDisruptions = activeDisruptions.length > 0;

  const data = useMemo(() => {
    if (!hasDisruptions) {
      return {
        noActionCost: 0,
        scenarios: [
          { name: 'Rerouting', cost: 4200000, savings: 68000000, riskReduction: 60, days: 5 },
          { name: 'Alt. Supplier', cost: 8500000, savings: 45000000, riskReduction: 75, days: 45 },
          { name: 'Air Freight', cost: 12000000, savings: 82000000, riskReduction: 90, days: 2 },
          { name: 'Hybrid', cost: 6800000, savings: 78000000, riskReduction: 85, days: 8 },
        ],
        pieData: [
          { name: 'Equipment Value', value: 45, fill: '#3b82f6' },
          { name: 'Shipping Cost', value: 15, fill: '#06b6d4' },
          { name: 'Delay Penalties', value: 25, fill: '#ef4444' },
          { name: 'Opportunity Cost', value: 15, fill: '#f97316' },
        ],
      };
    }

    return {
      noActionCost: 104500000,
      scenarios: [
        { name: 'Rerouting', cost: 4200000, savings: 68000000, riskReduction: 60, days: 5 },
        { name: 'Alt. Supplier', cost: 8500000, savings: 45000000, riskReduction: 75, days: 45 },
        { name: 'Air Freight', cost: 12000000, savings: 82000000, riskReduction: 90, days: 2 },
        { name: 'Hybrid', cost: 6800000, savings: 78000000, riskReduction: 85, days: 8 },
      ],
      pieData: [
        { name: 'Equipment Value', value: 45, fill: '#3b82f6' },
        { name: 'Shipping Cost', value: 15, fill: '#06b6d4' },
        { name: 'Delay Penalties', value: 25, fill: '#ef4444' },
        { name: 'Opportunity Cost', value: 15, fill: '#f97316' },
      ],
    };
  }, [hasDisruptions]);

  const barData = data.scenarios.map((s) => ({
    name: s.name,
    cost: s.cost / 1000000,
    savings: s.savings / 1000000,
  }));

  return (
    <div className="flex flex-col h-full">
      <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Cost Analysis</span>

      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="glass-card p-2">
          <div className="flex items-center gap-1 mb-1">
            <TrendingDown className="w-3 h-3 text-red-400" />
            <span className="text-[9px] text-slate-500">No Action Cost</span>
          </div>
          <div className="text-sm font-bold text-red-400">
            {hasDisruptions ? formatCurrency(data.noActionCost) : '--'}
          </div>
        </div>
        <div className="glass-card p-2">
          <div className="flex items-center gap-1 mb-1">
            <TrendingUp className="w-3 h-3 text-green-400" />
            <span className="text-[9px] text-slate-500">Best Savings</span>
          </div>
          <div className="text-sm font-bold text-green-400">
            {hasDisruptions ? formatCurrency(Math.max(...data.scenarios.map((s) => s.savings))) : '--'}
          </div>
        </div>
      </div>

      {/* Cost breakdown pie */}
      <div className="text-[9px] text-slate-500 mb-1">Cost Breakdown</div>
      <div className="h-[100px] flex items-center">
        <div className="w-[100px] h-[100px]">
          <ResponsiveContainer>
            <PieChart>
              <Pie
                data={data.pieData}
                cx="50%"
                cy="50%"
                innerRadius={25}
                outerRadius={42}
                dataKey="value"
                strokeWidth={1}
                stroke="#0a0e1a"
              >
                {data.pieData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} fillOpacity={0.8} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="flex-1 space-y-1 ml-2">
          {data.pieData.map((item) => (
            <div key={item.name} className="flex items-center gap-1.5 text-[9px]">
              <div className="w-2 h-2 rounded-sm" style={{ background: item.fill }} />
              <span className="text-slate-400">{item.name}</span>
              <span className="ml-auto text-slate-300">{item.value}%</span>
            </div>
          ))}
        </div>
      </div>

      {/* Scenarios bar chart */}
      <div className="text-[9px] text-slate-500 mt-2 mb-1">Mitigation Scenarios ($M)</div>
      <div className="h-[90px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={barData} margin={{ left: -10, right: 5 }}>
            <XAxis dataKey="name" tick={{ fontSize: 7, fill: '#64748b' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 7, fill: '#64748b' }} axisLine={false} tickLine={false} />
            <Bar dataKey="cost" fill="#ef4444" fillOpacity={0.6} radius={[2, 2, 0, 0]} barSize={14} name="Cost" />
            <Bar dataKey="savings" fill="#22c55e" fillOpacity={0.6} radius={[2, 2, 0, 0]} barSize={14} name="Savings" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* ROI table */}
      <div className="mt-2 space-y-1">
        {data.scenarios.map((s) => {
          const roi = ((s.savings - s.cost) / s.cost * 100).toFixed(0);
          return (
            <div key={s.name} className="flex items-center justify-between text-[9px] px-1.5 py-1 rounded bg-[#1a2236]/50">
              <span className="text-slate-300">{s.name}</span>
              <div className="flex items-center gap-3">
                <span className="text-slate-500">{s.days}d</span>
                <span className="text-green-400 font-medium">{roi}% ROI</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
