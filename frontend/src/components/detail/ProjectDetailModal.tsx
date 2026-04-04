'use client';

import Modal from '@/components/ui/Modal';
import Badge from '@/components/ui/Badge';
import RiskBar from '@/components/ui/RiskBar';
import StatRow from '@/components/ui/StatRow';
import { useProjectStore } from '@/stores/projectStore';
import { formatCurrency } from '@/lib/utils';
import { MapPin, Calendar, DollarSign, Package, AlertTriangle, TrendingUp } from 'lucide-react';

interface ProjectDetailModalProps {
  projectId: string | null;
  onClose: () => void;
}

const statusVariant = (s: string) => {
  switch (s) {
    case 'on-track': return 'success' as const;
    case 'at-risk': return 'medium' as const;
    case 'delayed': return 'high' as const;
    case 'critical': return 'critical' as const;
    default: return 'default' as const;
  }
};

export default function ProjectDetailModal({ projectId, onClose }: ProjectDetailModalProps) {
  const { projects, equipment } = useProjectStore();
  const project = projects.find((p) => p.id === projectId);

  if (!project) return null;

  const projEquip = equipment.filter((e) => e.projectId === project.id);
  const atRiskCount = projEquip.filter((e) => e.riskScore >= 60).length;
  const avgRisk = projEquip.length > 0
    ? Math.round(projEquip.reduce((s, e) => s + e.riskScore, 0) / projEquip.length)
    : 0;
  const totalEquipValue = projEquip.reduce((s, e) => s + e.value, 0);

  return (
    <Modal open={!!projectId} onClose={onClose} title={project.name} width="max-w-2xl">
      <div className="space-y-5">
        <div className="flex items-center gap-2">
          <Badge intent={statusVariant(project.status)}>{project.status}</Badge>
          <span className="text-xs text-slate-400">{project.client}</span>
        </div>

        {/* Progress */}
        <div>
          <div className="flex justify-between text-xs text-slate-400 mb-1">
            <span>Project Progress</span>
            <span className="font-semibold text-white">{project.completionPercent}%</span>
          </div>
          <div className="w-full h-3 rounded-full bg-slate-700/50 overflow-hidden">
            <div
              className="h-full rounded-full transition-all bg-cyan-500"
              style={{ width: `${project.completionPercent}%` }}
            />
          </div>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-3 gap-3">
          <div className="glass-card p-3 rounded-lg text-center">
            <DollarSign className="w-4 h-4 text-green-400 mx-auto mb-1" />
            <div className="text-lg font-bold text-white">{formatCurrency(project.value)}</div>
            <div className="text-[10px] text-slate-500">Project Value</div>
          </div>
          <div className="glass-card p-3 rounded-lg text-center">
            <Package className="w-4 h-4 text-cyan-400 mx-auto mb-1" />
            <div className="text-lg font-bold text-white">{projEquip.length}</div>
            <div className="text-[10px] text-slate-500">Equipment Items</div>
          </div>
          <div className="glass-card p-3 rounded-lg text-center">
            <AlertTriangle className="w-4 h-4 text-red-400 mx-auto mb-1" />
            <div className="text-lg font-bold text-white">{atRiskCount}</div>
            <div className="text-[10px] text-slate-500">At Risk</div>
          </div>
        </div>

        {/* Stats */}
        <div className="glass-card p-3 rounded-lg">
          <StatRow icon={MapPin} label="Location" value={`${project.country}`} color="text-purple-400" />
          <StatRow icon={Calendar} label="Start Date" value={project.startDate} />
          <StatRow icon={Calendar} label="End Date" value={project.endDate} color="text-orange-400" />
          <StatRow icon={TrendingUp} label="Avg Risk Score" value={`${avgRisk}/100`} color="text-yellow-400" />
          <StatRow icon={DollarSign} label="Equipment Value" value={formatCurrency(totalEquipValue)} color="text-green-400" />
        </div>

        {/* Equipment List */}
        <div>
          <span className="text-[10px] uppercase text-slate-500 font-semibold tracking-wider">Equipment</span>
          <div className="mt-2 space-y-1.5">
            {projEquip.map((eq) => (
              <div key={eq.id} className="flex items-center justify-between py-2 px-3 glass-card rounded-lg">
                <div>
                  <div className="text-xs font-medium text-white">{eq.name}</div>
                  <div className="text-[10px] text-slate-500">{formatCurrency(eq.value)}</div>
                </div>
                <div className="flex items-center gap-2">
                  <RiskBar score={eq.riskScore} className="w-20" />
                  <Badge intent={eq.status === 'delayed' ? 'critical' : eq.status === 'in-transit' ? 'info' : 'default'}>
                    {eq.status}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Modal>
  );
}
