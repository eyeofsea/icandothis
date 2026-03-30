'use client';

import { useProjectStore } from '@/stores/projectStore';
import { useMapStore } from '@/stores/mapStore';
import { formatCurrency } from '@/lib/utils';
import { STATUS_COLORS } from '@/lib/constants';
import { Building2, Package, AlertTriangle } from 'lucide-react';

export default function ProjectHealth() {
  const { projects, equipment } = useProjectStore();
  const { selectedProjectId, setSelectedProject, setMapCenter, setMapZoom } = useMapStore();

  return (
    <div className="space-y-2">
      {projects.map((proj) => {
        const projEquip = equipment.filter((e) => e.projectId === proj.id);
        const atRiskCount = projEquip.filter((e) => e.riskScore >= 60).length;
        const statusColor = STATUS_COLORS[proj.status] || '#22c55e';
        const isSelected = selectedProjectId === proj.id;

        return (
          <button
            key={proj.id}
            onClick={() => {
              setSelectedProject(isSelected ? null : proj.id);
              if (!isSelected) {
                setMapCenter([proj.location.lat, proj.location.lng]);
                setMapZoom(6);
              }
            }}
            className={`w-full text-left glass-card p-3 transition-all hover:bg-white/[0.04] ${
              isSelected ? 'ring-1 ring-blue-500/50 bg-blue-500/5' : ''
            }`}
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <div
                    className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                    style={{ background: statusColor, boxShadow: `0 0 6px ${statusColor}60` }}
                  />
                  <span className="text-sm font-semibold text-white truncate">{proj.name}</span>
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5 ml-4.5">{proj.client}</div>
              </div>
              <span className="text-xs font-bold text-slate-300">{formatCurrency(proj.value)}</span>
            </div>

            <div className="flex items-center gap-3 mt-2">
              {/* Progress bar */}
              <div className="flex-1">
                <div className="flex justify-between text-[9px] text-slate-500 mb-0.5">
                  <span>Progress</span>
                  <span>{proj.completionPercent}%</span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-slate-700/50">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{ width: `${proj.completionPercent}%`, background: statusColor }}
                  />
                </div>
              </div>

              {/* Stats */}
              <div className="flex items-center gap-2 text-[9px]">
                <div className="flex items-center gap-0.5 text-slate-400">
                  <Package className="w-3 h-3" />
                  <span>{projEquip.length}</span>
                </div>
                {atRiskCount > 0 && (
                  <div className="flex items-center gap-0.5 text-red-400">
                    <AlertTriangle className="w-3 h-3" />
                    <span>{atRiskCount}</span>
                  </div>
                )}
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
