'use client';

import EventInjector from '@/components/scenario/EventInjector';
import ScenarioSelector from '@/components/scenario/ScenarioSelector';
import { useDisruptionStore } from '@/stores/disruptionStore';
import Badge from '@/components/ui/Badge';

export default function ScenarioView() {
  const { activeDisruptions } = useDisruptionStore();

  return (
    <div className="h-full overflow-y-auto p-5">
      <div className="mb-5">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-bold text-white">Scenario Simulation</h2>
          {activeDisruptions.length > 0 && (
            <Badge variant="critical">{activeDisruptions.length} active</Badge>
          )}
        </div>
        <p className="text-xs text-slate-500 mt-0.5">Simulate disruption events and analyze their impact</p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="glass-card p-5 rounded-lg">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-3">Scenario Library</span>
          <ScenarioSelector />
        </div>
        <div className="glass-card p-5 rounded-lg">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-3">Event Injector</span>
          <EventInjector />
        </div>
      </div>

      {activeDisruptions.length > 0 && (
        <div className="mt-5 glass-card p-5 rounded-lg">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-3">Active Disruptions</span>
          <div className="space-y-2">
            {activeDisruptions.map((d) => (
              <div key={d.id} className="flex items-center justify-between p-3 rounded-lg bg-red-500/5 border border-red-500/20">
                <div>
                  <div className="text-sm font-medium text-white">{d.name}</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">{d.description}</div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="critical">Severity {d.severity}/5</Badge>
                  <Badge variant="info">{d.type}</Badge>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
