'use client';

import { useMemo } from 'react';
import { useProjectStore } from '@/stores/projectStore';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell } from 'recharts';
// Route colors used for styling

export default function RouteComparison() {
  const { routes } = useProjectStore();

  const comparison = useMemo(() => {
    // Compare Hormuz route vs alternatives
    const main = routes.find((r) => r.id === 'rt-1');
    const alternatives = [
      { name: 'Cape of Good Hope', transitDays: 37, costPerTon: 62, riskScore: 15 },
      { name: 'Trans-Pacific + Panama', transitDays: 42, costPerTon: 78, riskScore: 12 },
      { name: 'Rail + Short Sea', transitDays: 28, costPerTon: 95, riskScore: 25 },
    ];

    if (!main) return null;

    return {
      current: main,
      alternatives,
      transitData: [
        { name: main.name.split(' ')[0] + '...', days: main.transitDays, fill: '#22c55e' },
        ...alternatives.map((a) => ({ name: a.name.split(' ')[0] + '...', days: a.transitDays, fill: '#3b82f6' })),
      ],
      costData: [
        { name: main.name.split(' ')[0] + '...', cost: main.costPerTon, fill: '#22c55e' },
        ...alternatives.map((a) => ({ name: a.name.split(' ')[0] + '...', cost: a.costPerTon, fill: '#3b82f6' })),
      ],
    };
  }, [routes]);

  if (!comparison) return <div className="text-xs text-slate-500">No route data</div>;

  return (
    <div className="flex flex-col h-full">
      <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Route Alternatives</span>

      <div className="mb-2">
        <div className="text-[9px] text-slate-500 mb-1">Transit Time (days)</div>
        <div className="h-[80px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={comparison.transitData} layout="vertical" margin={{ left: 0, right: 5 }}>
              <XAxis type="number" tick={{ fontSize: 8, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 7, fill: '#94a3b8' }} axisLine={false} tickLine={false} width={55} />
              <Bar dataKey="days" radius={[0, 3, 3, 0]} barSize={12}>
                {comparison.transitData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} fillOpacity={0.7} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="mb-2">
        <div className="text-[9px] text-slate-500 mb-1">Cost per Ton ($)</div>
        <div className="h-[80px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={comparison.costData} layout="vertical" margin={{ left: 0, right: 5 }}>
              <XAxis type="number" tick={{ fontSize: 8, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 7, fill: '#94a3b8' }} axisLine={false} tickLine={false} width={55} />
              <Bar dataKey="cost" radius={[0, 3, 3, 0]} barSize={12}>
                {comparison.costData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} fillOpacity={0.7} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="space-y-1 mt-1">
        {comparison.alternatives.map((alt) => (
          <div key={alt.name} className="flex items-center justify-between text-[9px] px-1.5 py-1 rounded bg-[#1a2236]/50">
            <span className="text-slate-300">{alt.name}</span>
            <div className="flex items-center gap-2">
              <span className="text-slate-400">+{alt.transitDays - comparison.current.transitDays}d</span>
              <span className="text-slate-400">+${alt.costPerTon - comparison.current.costPerTon}/t</span>
              <span className={`font-medium ${alt.riskScore < comparison.current.riskScore ? 'text-green-400' : 'text-red-400'}`}>
                Risk: {alt.riskScore}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
