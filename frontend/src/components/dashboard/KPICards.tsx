'use client';

import { useMemo } from 'react';
import { DollarSign, AlertTriangle, Activity, TrendingUp, Shield, Zap } from 'lucide-react';
import { useProjectStore } from '@/stores/projectStore';
import { useDisruptionStore } from '@/stores/disruptionStore';
import { formatCurrency } from '@/lib/utils';

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
      { label: 'Portfolio Value', value: formatCurrency(totalValue), icon: DollarSign, color: 'text-cyan-400', bgColor: 'bg-cyan-500/10', trend: '+2.1%', trendUp: true },
      { label: 'At-Risk Value', value: formatCurrency(atRiskValue), icon: AlertTriangle, color: 'text-red-400', bgColor: 'bg-red-500/10', trend: atRiskValue > 0 ? 'Active' : 'None', trendUp: false },
      { label: 'Active Disruptions', value: String(activeDisruptions.length), icon: Zap, color: 'text-orange-400', bgColor: 'bg-orange-500/10', trend: activeDisruptions.length > 0 ? 'Monitoring' : 'Clear', trendUp: activeDisruptions.length === 0 },
      { label: 'Avg Risk Score', value: `${avgRisk}/100`, icon: Activity, color: 'text-yellow-400', bgColor: 'bg-yellow-500/10', trend: avgRisk < 40 ? 'Low' : avgRisk < 60 ? 'Medium' : 'High', trendUp: avgRisk < 40 },
      { label: 'Critical Items', value: String(criticalCount), icon: Shield, color: 'text-purple-400', bgColor: 'bg-purple-500/10', trend: `of ${equipment.length}`, trendUp: true },
      { label: 'Potential Savings', value: formatCurrency(potentialSavings), icon: TrendingUp, color: 'text-green-400', bgColor: 'bg-green-500/10', trend: potentialSavings > 0 ? 'Available' : '-', trendUp: true },
    ];
  }, [projects, equipment, activeDisruptions, affectedEquipmentIds]);

  return (
    <div className="grid grid-cols-2 gap-2">
      {kpis.map((kpi) => (
        <div key={kpi.label} className="glass-card p-3 hover:bg-white/[0.03] transition-colors">
          <div className="flex items-start justify-between mb-1.5">
            <div className={`p-1.5 rounded-md ${kpi.bgColor}`}>
              <kpi.icon className={`w-3.5 h-3.5 ${kpi.color}`} />
            </div>
            <span className={`text-[10px] font-medium ${kpi.trendUp ? 'text-green-400' : 'text-red-400'}`}>
              {kpi.trend}
            </span>
          </div>
          <div className="text-lg font-bold text-white leading-tight">{kpi.value}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">{kpi.label}</div>
        </div>
      ))}
    </div>
  );
}
