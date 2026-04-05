'use client';

import { useMemo } from 'react';
import { DollarSign, AlertTriangle, Activity, TrendingUp, Shield, Zap, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { useProjectStore } from '@/stores/projectStore';
import { useDisruptionStore } from '@/stores/disruptionStore';
import { formatCurrency, cn } from '@/lib/utils';
import Card from '@/components/ui/Card';

export default function KPICards() {
  const { projects, equipment } = useProjectStore();
  const { activeDisruptions, affectedEquipmentIds } = useDisruptionStore();

  const kpis = useMemo(() => {
    const totalValue = projects.reduce((sum, p) => sum + p.value, 0);
    const atRiskEquip = equipment.filter((e) => affectedEquipmentIds.includes(e.id));
    const atRiskValue = atRiskEquip.reduce((sum, e) => sum + e.value, 0);
    const avgRisk = equipment.length > 0 ? Math.round(equipment.reduce((sum, e) => sum + e.riskScore, 0) / equipment.length) : 0;
    const criticalCount = equipment.filter((e) => e.criticality === 'Critical' || e.riskScore >= 70).length;
    const potentialSavings = atRiskValue * 0.35;

    return [
      { label: 'Portfolio Value', value: formatCurrency(totalValue), icon: DollarSign, color: 'text-sky-400', bgColor: 'bg-sky-500/10', trend: '+2.1%', trendUp: true, detail: 'Across all active projects' },
      { label: 'At-Risk Assets', value: formatCurrency(atRiskValue), icon: AlertTriangle, color: 'text-rose-400', bgColor: 'bg-rose-500/10', trend: atRiskValue > 0 ? 'Urgent' : 'Clear', trendUp: false, detail: `${affectedEquipmentIds.length} items impacted` },
      { label: 'Active Incidents', value: String(activeDisruptions.length), icon: Zap, color: 'text-amber-400', bgColor: 'bg-amber-500/10', trend: activeDisruptions.length > 0 ? 'Live' : 'Zero', trendUp: activeDisruptions.length === 0, detail: 'Currently monitoring' },
      { label: 'Network Risk', value: `${avgRisk}/100`, icon: Activity, color: 'text-orange-400', bgColor: 'bg-orange-500/10', trend: avgRisk < 50 ? 'Stable' : 'Volatile', trendUp: avgRisk < 50, detail: 'Global average score' },
      { label: 'Criticality Delta', value: String(criticalCount), icon: Shield, color: 'text-indigo-400', bgColor: 'bg-indigo-500/10', trend: `of ${equipment.length}`, trendUp: true, detail: 'High-priority items' },
      { label: 'Optimization Cap', value: formatCurrency(potentialSavings), icon: TrendingUp, color: 'text-emerald-400', bgColor: 'bg-emerald-500/10', trend: potentialSavings > 0 ? 'Ready' : 'Zero', trendUp: true, detail: 'Mitigation savings' },
    ];
  }, [projects, equipment, activeDisruptions, affectedEquipmentIds]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {kpis.map((kpi) => (
        <Card key={kpi.label} variant="glass" padding="none" className="group hover:scale-[1.02] transition-transform duration-300">
          <div className="p-5">
            <div className="flex items-start justify-between mb-4">
              <div className={cn("p-2.5 rounded-xl border border-white/5", kpi.bgColor)}>
                <kpi.icon className={cn("w-5 h-5", kpi.color)} />
              </div>
              <div className={cn(
                "flex items-center gap-1 px-2 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest",
                kpi.trendUp ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"
              )}>
                {kpi.trendUp ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                {kpi.trend}
              </div>
            </div>
            
            <div className="space-y-1">
              <div className="text-2xl font-black text-white tracking-tight leading-none tabular-nums">
                {kpi.value}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{kpi.label}</span>
                <span className="text-[9px] text-slate-600 font-medium">{kpi.detail}</span>
              </div>
            </div>
          </div>
          
          {/* Visual decoration */}
          <div className={cn("h-1 w-full opacity-50", kpi.trendUp ? "bg-emerald-500/30" : "bg-rose-500/30")} />
        </Card>
      ))}
    </div>
  );
}
