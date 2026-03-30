'use client';

import { useState } from 'react';
import { useDisruptionStore } from '@/stores/disruptionStore';
import { useMapStore } from '@/stores/mapStore';
import { DisruptionEvent } from '@/lib/types';
import { Zap, ChevronDown, Play } from 'lucide-react';

const SCENARIOS: { label: string; description: string; event: DisruptionEvent }[] = [
  {
    label: 'Hormuz Blockade',
    description: 'Strait of Hormuz closed to commercial shipping',
    event: {
      id: 'dis-hormuz', type: 'geopolitical', name: 'Strait of Hormuz Blockade',
      description: 'Full closure of Strait of Hormuz due to military escalation. All maritime traffic halted.',
      severity: 5, startDate: new Date().toISOString(), affectedZoneIds: ['zone-1'],
      affectedRouteIds: ['rt-1', 'rt-3', 'rt-5', 'rt-8'],
      affectedEquipmentIds: ['eq-1', 'eq-5', 'eq-7', 'eq-8', 'eq-12', 'eq-13', 'eq-14'],
      affectedProjectIds: ['proj-1', 'proj-2', 'proj-3', 'proj-4', 'proj-5'],
      location: { lat: 26.5, lng: 56.5 }, radius: 150, status: 'active',
    },
  },
  {
    label: 'Suez Obstruction',
    description: 'Suez Canal blocked by grounded vessel',
    event: {
      id: 'dis-suez', type: 'infrastructure', name: 'Suez Canal Obstruction',
      description: 'Large container vessel grounded in Suez Canal. Expected 7-14 day clearance.',
      severity: 4, startDate: new Date().toISOString(), affectedZoneIds: ['zone-2'],
      affectedRouteIds: ['rt-2', 'rt-6'],
      affectedEquipmentIds: ['eq-2', 'eq-9', 'eq-10', 'eq-15'],
      affectedProjectIds: ['proj-1', 'proj-3', 'proj-5'],
      location: { lat: 30.5, lng: 32.3 }, radius: 50, status: 'active',
    },
  },
  {
    label: 'Japan Earthquake',
    description: 'Major seismic event disrupting Japanese suppliers',
    event: {
      id: 'dis-japan', type: 'natural', name: 'Japan Earthquake M7.5',
      description: 'Magnitude 7.5 earthquake in Kansai region. Supplier facilities damaged.',
      severity: 4, startDate: new Date().toISOString(), affectedZoneIds: [],
      affectedRouteIds: ['rt-1', 'rt-4', 'rt-5'],
      affectedEquipmentIds: ['eq-1', 'eq-4', 'eq-5', 'eq-6', 'eq-7', 'eq-12'],
      affectedProjectIds: ['proj-1', 'proj-2', 'proj-4'],
      location: { lat: 34.7, lng: 135.5 }, radius: 200, status: 'active',
    },
  },
  {
    label: 'China Tariff',
    description: '45% tariff on Chinese manufacturing exports',
    event: {
      id: 'dis-tariff', type: 'economic', name: 'China Export Tariff Escalation',
      description: 'New 45% tariff imposed on Chinese industrial equipment exports. Immediate cost impact.',
      severity: 3, startDate: new Date().toISOString(), affectedZoneIds: ['zone-4'],
      affectedRouteIds: ['rt-8'],
      affectedEquipmentIds: ['eq-14'],
      affectedProjectIds: ['proj-5'],
      location: { lat: 31.2, lng: 121.5 }, radius: 300, status: 'active',
    },
  },
  {
    label: 'Red Sea Attacks',
    description: 'Houthi attacks on commercial shipping escalate',
    event: {
      id: 'dis-redsea', type: 'geopolitical', name: 'Red Sea Shipping Attacks',
      description: 'Escalated Houthi drone and missile attacks on commercial vessels in Red Sea.',
      severity: 4, startDate: new Date().toISOString(), affectedZoneIds: ['zone-2', 'zone-3'],
      affectedRouteIds: ['rt-2', 'rt-6'],
      affectedEquipmentIds: ['eq-2', 'eq-9', 'eq-10', 'eq-15'],
      affectedProjectIds: ['proj-1', 'proj-3', 'proj-5'],
      location: { lat: 13.5, lng: 43.0 }, radius: 200, status: 'active',
    },
  },
];

export default function ScenarioSelector() {
  const [isOpen, setIsOpen] = useState(false);
  const [selected, setSelected] = useState<number | null>(null);
  const { addDisruption, clearDisruptions } = useDisruptionStore();
  const { setMapCenter, setMapZoom } = useMapStore();

  const inject = (idx: number) => {
    clearDisruptions();
    const scenario = SCENARIOS[idx];
    addDisruption(scenario.event);
    setSelected(idx);
    setIsOpen(false);
    setMapCenter([scenario.event.location.lat, scenario.event.location.lng]);
    setMapZoom(5);
  };

  const clear = () => {
    clearDisruptions();
    setSelected(null);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#1a2236] border border-[#1e3a5f] hover:border-[#2d4a7a] text-xs text-slate-300 transition-colors"
      >
        <Zap className="w-3.5 h-3.5 text-orange-400" />
        {selected !== null ? SCENARIOS[selected].label : 'Scenarios'}
        <ChevronDown className={`w-3 h-3 text-slate-500 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full mt-1 right-0 w-72 glass-card p-2 z-[3000] shadow-xl shadow-black/40">
          <div className="text-[10px] text-slate-500 px-2 py-1 mb-1">Select a disruption scenario</div>
          {SCENARIOS.map((scenario, idx) => (
            <button
              key={scenario.label}
              onClick={() => inject(idx)}
              className={`w-full flex items-start gap-2 px-2 py-2 rounded-md text-left hover:bg-white/[0.04] transition-colors ${
                selected === idx ? 'bg-orange-500/10 border border-orange-500/20' : ''
              }`}
            >
              <Play className="w-3 h-3 text-orange-400 mt-0.5 flex-shrink-0" />
              <div>
                <div className="text-xs font-medium text-slate-200">{scenario.label}</div>
                <div className="text-[9px] text-slate-500 mt-0.5">{scenario.description}</div>
                <div className="flex gap-2 mt-1 text-[8px]">
                  <span className="text-red-400">Severity: {'*'.repeat(scenario.event.severity)}</span>
                  <span className="text-slate-500">Routes: {scenario.event.affectedRouteIds.length}</span>
                  <span className="text-slate-500">Equipment: {scenario.event.affectedEquipmentIds.length}</span>
                </div>
              </div>
            </button>
          ))}
          {selected !== null && (
            <button
              onClick={clear}
              className="w-full mt-1 text-[10px] text-slate-500 hover:text-slate-300 py-1.5 border-t border-[#1e3a5f]"
            >
              Clear All Disruptions
            </button>
          )}
        </div>
      )}
    </div>
  );
}
