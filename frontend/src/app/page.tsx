'use client';

import { useState } from 'react';
import { Bell, Search, User, ChevronDown, Bot } from 'lucide-react';
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
import NewsView from '@/views/NewsView';
import ChatPanel from '@/components/chat/ChatPanel';
import ScenarioSelector from '@/components/scenario/ScenarioSelector';
import { useDisruptionStore } from '@/stores/disruptionStore';
import { useFeedStore } from '@/stores/feedStore';
import Tooltip from '@/components/ui/Tooltip';
import Button from '@/components/ui/Button';

const VIEW_TITLES: Record<ViewId, string> = {
  dashboard: 'Dashboard',
  riskmatrix: 'Risk Matrix',
  projects: 'Projects',
  alerts: 'Alerts',
  news: 'News & Intelligence',
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
  const { agentStatuses } = useFeedStore();
  const activeAgents = agentStatuses.filter((a) => a.status !== 'idle');
  const workingAgent = agentStatuses.find((a) => a.status === 'analyzing');

  const renderView = () => {
    switch (activeView) {
      case 'dashboard': return <DashboardView />;
      case 'riskmatrix': return <RiskMatrixView />;
      case 'projects': return <ProjectsView />;
      case 'alerts': return <AlertsView />;
      case 'news': return <NewsView />;
      case 'map': return <MapView />;
      case 'ontology': return <OntologyView />;
      case 'impact': return <ImpactView />;
      case 'scenario': return <ScenarioView />;
      case 'hedging': return <HedgingReportView />;
    }
  };

  return (
    <div className="h-screen w-screen flex overflow-hidden bg-slate-950 font-[family-name:var(--font-geist-sans)]">
      {/* Sidebar */}
      <Sidebar activeView={activeView} onViewChange={setActiveView} alertCount={8} />

      {/* Main area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="h-14 flex-shrink-0 flex items-center justify-between px-6 border-b border-slate-800/60 bg-slate-900/40 backdrop-blur-md z-[100]">
          <div className="flex items-center gap-6">
            <h1 className="text-sm font-bold text-white tracking-widest uppercase">
              {VIEW_TITLES[activeView]}
            </h1>
            
            <div className="hidden lg:flex items-center h-8 px-3 rounded-full bg-slate-800/50 border border-slate-700/50 group focus-within:border-sky-500/50 transition-all">
              <Search className="w-3.5 h-3.5 text-slate-500 group-focus-within:text-sky-400" />
              <input 
                type="text" 
                placeholder="Search resources..." 
                className="bg-transparent border-none outline-none text-[11px] text-slate-300 ml-2 w-48 placeholder:text-slate-600"
              />
            </div>
          </div>

          <div className="flex items-center gap-4">
            <ScenarioSelector />

            {/* Agent Status */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800/50 border border-slate-700/50">
              <Bot className="w-3.5 h-3.5 text-sky-400" />
              <span className="text-[10px] text-slate-300 font-bold">
                {activeAgents.length}/{agentStatuses.length}
              </span>
              {workingAgent && (
                <span className="text-[10px] text-amber-400 font-medium animate-pulse truncate max-w-[120px]">
                  {workingAgent.name}...
                </span>
              )}
            </div>

            {activeDisruptions.length > 0 && (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-rose-500/10 border border-rose-500/20 group cursor-default">
                <div className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse shadow-glow-red" />
                <span className="text-[10px] text-rose-400 font-bold uppercase tracking-tighter">
                  {activeDisruptions.length} CRITICAL INCIDENT{activeDisruptions.length > 1 ? 'S' : ''}
                </span>
              </div>
            )}

            <div className="h-6 w-[1px] bg-slate-800/60 mx-1" />

            <div className="flex items-center gap-1">
              <Tooltip content="Notifications">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setNotifOpen(true)}
                  className="relative p-2"
                >
                  <Bell className="w-4 h-4 text-slate-400" />
                  <span className="absolute top-1 right-1 w-3.5 h-3.5 bg-rose-500 border-2 border-slate-950 rounded-full text-[7px] text-white flex items-center justify-center font-black">
                    4
                  </span>
                </Button>
              </Tooltip>

              <button className="flex items-center gap-2 pl-2 pr-1 py-1 rounded-full hover:bg-white/5 transition-colors group">
                <div className="w-7 h-7 rounded-full bg-sky-500/10 border border-sky-400/20 flex items-center justify-center">
                  <User className="w-4 h-4 text-sky-400" />
                </div>
                <div className="hidden md:block text-left mr-1">
                  <p className="text-[10px] font-bold text-white leading-none">J. DOE</p>
                  <p className="text-[9px] text-slate-500 leading-none mt-1">Lead Architect</p>
                </div>
                <ChevronDown className="w-3 h-3 text-slate-500 group-hover:text-slate-300 transition-colors" />
              </button>
            </div>
          </div>
        </header>

        {/* View content - full width */}
        <main className="flex-1 overflow-hidden relative">
          {/* Background grid effect */}
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:40px_40px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none" />
          
          <div className="h-full w-full relative z-10">
            {renderView()}
          </div>
        </main>
      </div>

      {/* Notification drawer */}
      <NotificationPanel open={notifOpen} onClose={() => setNotifOpen(false)} />

      {/* Chat panel */}
      <ChatPanel />
    </div>
  );
}
