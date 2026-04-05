'use client';

import { useState } from 'react';
import { Filter, Download, RefreshCw, LayoutGrid, List } from 'lucide-react';
import KPICards from '@/components/dashboard/KPICards';
import RiskMatrix from '@/components/dashboard/RiskMatrix';
import ProjectHealth from '@/components/dashboard/ProjectHealth';
import AlertFeed from '@/components/dashboard/AlertFeed';
import Timeline from '@/components/dashboard/Timeline';
import EquipmentDetailModal from '@/components/detail/EquipmentDetailModal';
import ProjectDetailModal from '@/components/detail/ProjectDetailModal';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';

export default function DashboardView() {
  const [selectedEquipmentId, setSelectedEquipmentId] = useState<string | null>(null);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [viewType, setViewType] = useState<'grid' | 'list'>('grid');

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6">
      {/* Header section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-black text-white tracking-tight uppercase">System Overview</h2>
          <p className="text-[11px] text-slate-500 font-bold uppercase tracking-wider mt-0.5">Real-time portfolio intelligence & risk orchestration</p>
        </div>
        
        <div className="flex items-center gap-2">
          <div className="flex items-center bg-slate-900/50 rounded-lg p-1 border border-slate-800">
            <button 
              onClick={() => setViewType('grid')}
              className={`p-1.5 rounded-md transition-all ${viewType === 'grid' ? 'bg-sky-500 text-white' : 'text-slate-500 hover:text-slate-300'}`}
            >
              <LayoutGrid className="w-3.5 h-3.5" />
            </button>
            <button 
              onClick={() => setViewType('list')}
              className={`p-1.5 rounded-md transition-all ${viewType === 'list' ? 'bg-sky-500 text-white' : 'text-slate-500 hover:text-slate-300'}`}
            >
              <List className="w-3.5 h-3.5" />
            </button>
          </div>
          <Button variant="outline" size="sm" icon={Filter}>Filter</Button>
          <Button variant="outline" size="sm" icon={Download}>Export</Button>
          <Button variant="primary" size="sm" icon={RefreshCw}>Sync</Button>
        </div>
      </div>

      {/* KPI Cards */}
      <KPICards />

      {/* Main Analysis Row */}
      <div className="grid grid-cols-12 gap-6">
        <Card 
          title="Global Risk Matrix" 
          subtitle="Impact vs. Probability"
          className="col-span-12 lg:col-span-7 h-[420px]"
          padding="none"
        >
          <div className="w-full h-full p-6">
            <RiskMatrix />
          </div>
        </Card>
        
        <Card 
          title="Intelligence Feed" 
          subtitle="Live Disruptions"
          className="col-span-12 lg:col-span-5 h-[420px]"
          padding="none"
        >
          <AlertFeed />
        </Card>
      </div>

      {/* Execution Row */}
      <div className="grid grid-cols-12 gap-6">
        <Card 
          title="Portfolio Health" 
          subtitle="Critical Path Monitoring"
          className="col-span-12 lg:col-span-6 min-h-[320px]"
          padding="none"
        >
          <ProjectHealth />
        </Card>
        
        <Card 
          title="Delivery Trajectory" 
          subtitle="Timeline Simulation"
          className="col-span-12 lg:col-span-6 h-[320px]"
          padding="none"
        >
          <div className="w-full h-full p-4">
            <Timeline />
          </div>
        </Card>
      </div>

      <EquipmentDetailModal equipmentId={selectedEquipmentId} onClose={() => setSelectedEquipmentId(null)} />
      <ProjectDetailModal projectId={selectedProjectId} onClose={() => setSelectedProjectId(null)} />
    </div>
  );
}
