'use client';

import { useMemo } from 'react';
import { useProjectStore } from '@/stores/projectStore';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer } from 'recharts';
import { Award } from 'lucide-react';

export default function SupplierComparison() {
  const { suppliers } = useProjectStore();

  const comparison = useMemo(() => {
    if (suppliers.length < 2) return null;
    // Compare first two rotating suppliers as example
    const s1 = suppliers.find((s) => s.id === 'sup-1')!; // MHI
    const s2 = suppliers.find((s) => s.id === 'sup-2')!; // Siemens

    const data = [
      { metric: 'Quality', current: s1.qualityScore, alternative: s2.qualityScore },
      { metric: 'On-Time', current: s1.onTimeDelivery, alternative: s2.onTimeDelivery },
      { metric: 'Capacity', current: s1.capacity, alternative: s2.capacity },
      { metric: 'Risk (inv)', current: 100 - s1.riskScore, alternative: 100 - s2.riskScore },
      { metric: 'Lead Time (inv)', current: Math.max(0, 100 - s1.leadTimeDays / 5), alternative: Math.max(0, 100 - s2.leadTimeDays / 5) },
    ];

    return { current: s1, alternative: s2, data };
  }, [suppliers]);

  if (!comparison) return <div className="text-xs text-slate-500">No data available</div>;

  const metrics = [
    { label: 'Quality', current: comparison.current.qualityScore, alt: comparison.alternative.qualityScore, unit: '%' },
    { label: 'On-Time', current: comparison.current.onTimeDelivery, alt: comparison.alternative.onTimeDelivery, unit: '%' },
    { label: 'Capacity', current: comparison.current.capacity, alt: comparison.alternative.capacity, unit: '%' },
    { label: 'Risk', current: comparison.current.riskScore, alt: comparison.alternative.riskScore, unit: '/100', lowerBetter: true },
    { label: 'Lead Time', current: comparison.current.leadTimeDays, alt: comparison.alternative.leadTimeDays, unit: 'd', lowerBetter: true },
  ];

  return (
    <div className="flex flex-col h-full">
      <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Supplier Comparison</span>

      <div className="flex items-center gap-3 mb-3 text-[10px]">
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
          <span className="text-slate-300">{comparison.current.name}</span>
        </div>
        <span className="text-slate-600">vs</span>
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-orange-400" />
          <span className="text-slate-300">{comparison.alternative.name}</span>
          <Award className="w-3 h-3 text-green-400" />
        </div>
      </div>

      <div className="h-[140px] mb-2">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={comparison.data}>
            <PolarGrid stroke="#1e3a5f" />
            <PolarAngleAxis dataKey="metric" tick={{ fontSize: 8, fill: '#64748b' }} />
            <Radar name="Current" dataKey="current" stroke="#06b6d4" fill="#06b6d4" fillOpacity={0.15} strokeWidth={1.5} />
            <Radar name="Alternative" dataKey="alternative" stroke="#f97316" fill="#f97316" fillOpacity={0.15} strokeWidth={1.5} />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      <div className="space-y-1">
        {metrics.map((m) => {
          const delta = m.alt - m.current;
          const better = m.lowerBetter ? delta < 0 : delta > 0;
          return (
            <div key={m.label} className="flex items-center justify-between text-[9px]">
              <span className="text-slate-500 w-16">{m.label}</span>
              <span className="text-slate-400">{m.current}{m.unit}</span>
              <span className="text-slate-600">vs</span>
              <span className="text-slate-400">{m.alt}{m.unit}</span>
              <span className={`w-14 text-right font-medium ${better ? 'text-green-400' : delta === 0 ? 'text-slate-500' : 'text-red-400'}`}>
                {delta > 0 ? '+' : ''}{delta}{m.unit}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
