'use client';

import { useState } from 'react';
import KPICards from '@/components/dashboard/KPICards';
import RiskMatrix from '@/components/dashboard/RiskMatrix';
import ProjectHealth from '@/components/dashboard/ProjectHealth';
import AlertFeed from '@/components/dashboard/AlertFeed';
import Timeline from '@/components/dashboard/Timeline';
import EquipmentDetailModal from '@/components/detail/EquipmentDetailModal';
import ProjectDetailModal from '@/components/detail/ProjectDetailModal';

export default function DashboardView() {
  const [selectedEquipmentId, setSelectedEquipmentId] = useState<string | null>(null);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);

  return (
    <div className="h-full overflow-y-auto p-5">
      <div className="mb-5">
        <h2 className="text-lg font-bold text-white">Dashboard</h2>
        <p className="text-xs text-slate-500 mt-0.5">Real-time portfolio overview and risk monitoring</p>
      </div>

      {/* KPI Row - 3 column grid */}
      <div className="mb-5">
        <KPICards />
      </div>

      {/* Main content: Risk Matrix 60% + Alerts 40% */}
      <div className="grid grid-cols-10 gap-4 mb-5">
        <div className="col-span-6 glass-card p-4 min-h-[360px]">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-3">Risk Matrix</span>
          <RiskMatrix />
        </div>
        <div className="col-span-4 glass-card p-4 min-h-[360px]">
          <AlertFeed />
        </div>
      </div>

      {/* Bottom: Projects + Timeline */}
      <div className="grid grid-cols-10 gap-4">
        <div className="col-span-5 glass-card p-4">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-3">Project Portfolio</span>
          <ProjectHealth />
        </div>
        <div className="col-span-5 glass-card p-4 h-[280px]">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-3">Delivery Timeline</span>
          <Timeline />
        </div>
      </div>

      <EquipmentDetailModal equipmentId={selectedEquipmentId} onClose={() => setSelectedEquipmentId(null)} />
      <ProjectDetailModal projectId={selectedProjectId} onClose={() => setSelectedProjectId(null)} />
    </div>
  );
}
