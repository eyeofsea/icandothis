'use client';

import { useState } from 'react';
import { Bell } from 'lucide-react';
import Sidebar, { ViewId } from '@/components/layout/Sidebar';
import NotificationPanel from '@/components/layout/NotificationPanel';
import DashboardView from '@/views/DashboardView';
import RiskMatrixView from '@/views/RiskMatrixView';
import ProjectsView from '@/views/ProjectsView';
import AlertsView from '@/views/AlertsView';
import MapView from '@/views/MapView';
import OntologyView from '@/views/OntologyView';
import ImpactView from '@/views/ImpactView';
import ScenarioView from '@/views/ScenarioView';
import HedgingReportView from '@/views/HedgingReportView';
import ChatPanel from '@/components/chat/ChatPanel';
import ScenarioSelector from '@/components/scenario/ScenarioSelector';
import { useDisruptionStore } from '@/stores/disruptionStore';
import Tooltip from '@/components/ui/Tooltip';

const VIEW_TITLES: Record<ViewId, string> = {
  dashboard: 'Dashboard',
  riskmatrix: 'Risk Matrix',
  projects: 'Projects',
  alerts: 'Alerts',
  map: 'Global Map',
  ontology: 'Knowledge Graph',
  impact: 'Impact Analysis',
  scenario: 'Scenario Simulation',
  hedging: 'Hedging & TCO Report',
};

export default function Home() {
  const [activeView, setActiveView] = useState<ViewId>('dashboard');
  const [notifOpen, setNotifOpen] = useState(false);
  const { activeDisruptions } = useDisruptionStore();

  const renderView = () => {
    switch (activeView) {
      case 'dashboard': return <DashboardView />;
      case 'riskmatrix': return <RiskMatrixView />;
      case 'projects': return <ProjectsView />;
      case 'alerts': return <AlertsView />;
      case 'map': return <MapView />;
      case 'ontology': return <OntologyView />;
      case 'impact': return <ImpactView />;
      case 'scenario': return <ScenarioView />;
      case 'hedging': return <HedgingReportView />;
    }
  };

  return (
    <div className="h-screen w-screen flex overflow-hidden bg-[#0a0e1a]">
      {/* Sidebar */}
      <Sidebar activeView={activeView} onViewChange={setActiveView} alertCount={8} />

      {/* Main area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="h-11 flex-shrink-0 flex items-center justify-between px-4 border-b border-[#1e3a5f]/60 bg-[#0c1220]/90 backdrop-blur-sm z-[100]">
          <div className="flex items-center gap-3">
            <h1 className="text-sm font-bold text-white tracking-tight">
              {VIEW_TITLES[activeView]}
            </h1>
            <div className="hidden md:flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-green-400" />
              <span className="text-[10px] text-slate-500">System Online</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <ScenarioSelector />

            {activeDisruptions.length > 0 && (
              <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-red-500/10 border border-red-500/20 animate-pulse-alert">
                <div className="w-1.5 h-1.5 rounded-full bg-red-400" />
                <span className="text-[10px] text-red-400 font-medium">
                  {activeDisruptions.length} Active Disruption{activeDisruptions.length > 1 ? 's' : ''}
                </span>
              </div>
            )}

            <Tooltip content="Notifications">
              <button
                onClick={() => setNotifOpen(true)}
                className="relative p-1.5 hover:bg-white/5 rounded-md transition-colors"
              >
                <Bell className="w-4 h-4 text-slate-400" />
                <span className="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 bg-red-500 rounded-full text-[8px] text-white flex items-center justify-center font-bold">
                  4
                </span>
              </button>
            </Tooltip>
          </div>
        </header>

        {/* View content - full width */}
        <main className="flex-1 overflow-hidden">
          {renderView()}
        </main>
      </div>

      {/* Notification drawer */}
      <NotificationPanel open={notifOpen} onClose={() => setNotifOpen(false)} />

      {/* Chat panel */}
      <ChatPanel />
    </div>
  );
}
