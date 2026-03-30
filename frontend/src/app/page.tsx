'use client';

import { useState } from 'react';
import { Radar, Bell } from 'lucide-react';
import * as Tabs from '@radix-ui/react-tabs';

import WorldMap from '@/components/map/WorldMap';
import KPICards from '@/components/dashboard/KPICards';
import RiskMatrix from '@/components/dashboard/RiskMatrix';
import ProjectHealth from '@/components/dashboard/ProjectHealth';
import AlertFeed from '@/components/dashboard/AlertFeed';
import Timeline from '@/components/dashboard/Timeline';
import GraphViewer from '@/components/ontology/GraphViewer';
import ImpactFlow from '@/components/impact/ImpactFlow';
import SupplierComparison from '@/components/impact/SupplierComparison';
import RouteComparison from '@/components/impact/RouteComparison';
import CostAnalysis from '@/components/impact/CostAnalysis';
import EventInjector from '@/components/scenario/EventInjector';
import ScenarioSelector from '@/components/scenario/ScenarioSelector';
import ChatPanel from '@/components/chat/ChatPanel';
import { useDisruptionStore } from '@/stores/disruptionStore';

export default function Home() {
  const [notifications] = useState(3);
  const { activeDisruptions } = useDisruptionStore();

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-[#0a0e1a]">
      {/* Top bar */}
      <header className="h-11 flex-shrink-0 flex items-center justify-between px-4 border-b border-[#1e3a5f]/60 bg-[#0c1220]/90 backdrop-blur-sm z-[100]">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Radar className="w-5 h-5 text-cyan-400" />
            <h1 className="text-sm font-bold text-white tracking-tight">
              SCM Risk Intelligence
            </h1>
          </div>
          <div className="hidden md:flex items-center gap-1.5 ml-4">
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

          <button className="relative p-1.5 hover:bg-white/5 rounded-md transition-colors">
            <Bell className="w-4 h-4 text-slate-400" />
            {notifications > 0 && (
              <span className="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 bg-red-500 rounded-full text-[8px] text-white flex items-center justify-center font-bold">
                {notifications}
              </span>
            )}
          </button>
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Map area (70%) */}
        <div className="flex-[7] relative">
          <WorldMap />

          {/* Bottom alert ticker overlay */}
          <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-[#0a0e1a]/90 to-transparent flex items-end z-[100]">
            <div className="w-full overflow-hidden px-4 pb-1.5">
              <div className="ticker-scroll flex items-center gap-6 whitespace-nowrap text-[10px]">
                <span className="text-yellow-400">ADVISORY: Red Sea threat level elevated</span>
                <span className="text-slate-500">|</span>
                <span className="text-cyan-400">Gas Turbine in transit - ETA 15 Aug</span>
                <span className="text-slate-500">|</span>
                <span className="text-red-400">BOG Compressor delayed - risk score 78</span>
                <span className="text-slate-500">|</span>
                <span className="text-green-400">ESD Valve Package cleared customs</span>
                <span className="text-slate-500">|</span>
                <span className="text-yellow-400">Shanghai port congestion level: 55%</span>
                <span className="text-slate-500">|</span>
                <span className="text-yellow-400">ADVISORY: Red Sea threat level elevated</span>
                <span className="text-slate-500">|</span>
                <span className="text-cyan-400">Gas Turbine in transit - ETA 15 Aug</span>
                <span className="text-slate-500">|</span>
                <span className="text-red-400">BOG Compressor delayed - risk score 78</span>
                <span className="text-slate-500">|</span>
                <span className="text-green-400">ESD Valve Package cleared customs</span>
              </div>
            </div>
          </div>
        </div>

        {/* Side panel (30%) */}
        <div className="flex-[3] min-w-[320px] max-w-[420px] border-l border-[#1e3a5f]/60 bg-[#0a0e1a] flex flex-col overflow-hidden">
          <Tabs.Root defaultValue="dashboard" className="flex flex-col h-full">
            <Tabs.List className="flex-shrink-0 flex border-b border-[#1e3a5f]/60">
              {[
                { value: 'dashboard', label: 'Dashboard' },
                { value: 'ontology', label: 'Ontology' },
                { value: 'impact', label: 'Impact' },
                { value: 'scenario', label: 'Scenario' },
              ].map((tab) => (
                <Tabs.Trigger
                  key={tab.value}
                  value={tab.value}
                  className="flex-1 px-2 py-2.5 text-[11px] font-medium text-slate-500 border-b-2 border-transparent transition-colors data-[state=active]:text-cyan-400 data-[state=active]:border-cyan-400 hover:text-slate-300"
                >
                  {tab.label}
                </Tabs.Trigger>
              ))}
            </Tabs.List>

            <div className="flex-1 overflow-y-auto p-3">
              <Tabs.Content value="dashboard" className="h-full flex flex-col gap-3">
                <KPICards />
                <div className="glass-card p-3 flex-1 min-h-[200px]">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">Risk Matrix</span>
                  <RiskMatrix />
                </div>
                <div className="glass-card p-3">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">Projects</span>
                  <ProjectHealth />
                </div>
                <div className="glass-card p-3 h-[180px]">
                  <Timeline />
                </div>
                <div className="glass-card p-3 h-[240px]">
                  <AlertFeed />
                </div>
              </Tabs.Content>

              <Tabs.Content value="ontology" className="h-full">
                <div className="h-full min-h-[500px]">
                  <GraphViewer />
                </div>
              </Tabs.Content>

              <Tabs.Content value="impact" className="h-full flex flex-col gap-3">
                <div className="glass-card p-3">
                  <ImpactFlow />
                </div>
                <div className="glass-card p-3">
                  <SupplierComparison />
                </div>
                <div className="glass-card p-3">
                  <RouteComparison />
                </div>
                <div className="glass-card p-3">
                  <CostAnalysis />
                </div>
              </Tabs.Content>

              <Tabs.Content value="scenario" className="h-full flex flex-col gap-3">
                <div className="glass-card p-3">
                  <EventInjector />
                </div>
              </Tabs.Content>
            </div>
          </Tabs.Root>
        </div>
      </div>

      {/* Chat panel */}
      <ChatPanel />
    </div>
  );
}
