'use client';

import { useDisruptionStore } from '@/stores/disruptionStore';
import { useProjectStore } from '@/stores/projectStore';
import { useMemo } from 'react';
import { Zap, Globe, Navigation, Package, Building2, ChevronRight } from 'lucide-react';

export default function ImpactFlow() {
  const { activeDisruptions, affectedEquipmentIds, affectedRouteIds } = useDisruptionStore();
  const { equipment, projects, zones } = useProjectStore();

  const cascade = useMemo(() => {
    const affectedProjects = new Set<string>();
    const affectedZones = new Set<string>();

    activeDisruptions.forEach((d) => {
      d.affectedZoneIds.forEach((z) => affectedZones.add(z));
      d.affectedProjectIds.forEach((p) => affectedProjects.add(p));
    });

    equipment
      .filter((e) => affectedEquipmentIds.includes(e.id))
      .forEach((e) => affectedProjects.add(e.projectId));

    return [
      { label: 'Events', count: activeDisruptions.length, icon: Zap, color: '#ef4444', items: activeDisruptions.map((d) => d.name) },
      { label: 'Zones', count: affectedZones.size, icon: Globe, color: '#f97316', items: zones.filter((z) => affectedZones.has(z.id)).map((z) => z.name) },
      { label: 'Routes', count: affectedRouteIds.length, icon: Navigation, color: '#eab308', items: [] as string[] },
      { label: 'Equipment', count: affectedEquipmentIds.length, icon: Package, color: '#3b82f6', items: equipment.filter((e) => affectedEquipmentIds.includes(e.id)).map((e) => e.name) },
      { label: 'Projects', count: affectedProjects.size, icon: Building2, color: '#a855f7', items: projects.filter((p) => affectedProjects.has(p.id)).map((p) => p.name) },
    ];
  }, [activeDisruptions, affectedEquipmentIds, affectedRouteIds, equipment, projects, zones]);

  const hasDisruption = activeDisruptions.length > 0;

  return (
    <div className="flex flex-col h-full">
      <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Disruption Cascade</span>

      {!hasDisruption ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Zap className="w-8 h-8 text-slate-600 mx-auto mb-2" />
            <p className="text-xs text-slate-500">No active disruptions</p>
            <p className="text-[10px] text-slate-600 mt-1">Inject a scenario to see impact cascade</p>
          </div>
        </div>
      ) : (
        <div className="flex items-center gap-1 overflow-x-auto pb-2">
          {cascade.map((step, i) => (
            <div key={step.label} className="flex items-center">
              <div className="flex flex-col items-center min-w-[70px]">
                <div
                  className="w-10 h-10 rounded-full flex items-center justify-center mb-1"
                  style={{ background: `${step.color}20`, border: `1px solid ${step.color}40` }}
                >
                  <step.icon className="w-4 h-4" style={{ color: step.color }} />
                </div>
                <span className="text-lg font-bold text-white">{step.count}</span>
                <span className="text-[9px] text-slate-500">{step.label}</span>
                {step.items.length > 0 && (
                  <div className="mt-1 space-y-0.5">
                    {step.items.slice(0, 3).map((item, j) => (
                      <div key={j} className="text-[8px] text-slate-500 truncate max-w-[70px]">{item}</div>
                    ))}
                    {step.items.length > 3 && (
                      <div className="text-[8px] text-slate-600">+{step.items.length - 3} more</div>
                    )}
                  </div>
                )}
              </div>
              {i < cascade.length - 1 && (
                <ChevronRight className="w-4 h-4 text-slate-600 flex-shrink-0 mx-0.5" />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
