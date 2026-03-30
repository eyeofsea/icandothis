'use client';

import { useState } from 'react';
import { useDisruptionStore } from '@/stores/disruptionStore';
import { DisruptionEvent } from '@/lib/types';
import { Zap, Plus } from 'lucide-react';

const EVENT_TYPES: DisruptionEvent['type'][] = ['geopolitical', 'natural', 'economic', 'infrastructure', 'cyber'];

const ZONE_OPTIONS = [
  { id: 'zone-1', name: 'Strait of Hormuz' },
  { id: 'zone-2', name: 'Suez Canal' },
  { id: 'zone-3', name: 'Red Sea / Bab el-Mandeb' },
  { id: 'zone-4', name: 'South China Sea' },
  { id: 'zone-5', name: 'Malacca Strait' },
];

export default function EventInjector() {
  const { addDisruption } = useDisruptionStore();
  const [eventType, setEventType] = useState<DisruptionEvent['type']>('geopolitical');
  const [severity, setSeverity] = useState(3);
  const [selectedZones, setSelectedZones] = useState<string[]>([]);
  const [description, setDescription] = useState('');
  const [name, setName] = useState('');

  const handleSubmit = () => {
    if (!name.trim()) return;

    const event: DisruptionEvent = {
      id: `dis-custom-${Date.now()}`,
      type: eventType,
      name: name.trim(),
      description: description.trim() || `Custom ${eventType} disruption event`,
      severity: severity as 1 | 2 | 3 | 4 | 5,
      startDate: new Date().toISOString(),
      affectedZoneIds: selectedZones,
      affectedRouteIds: [],
      affectedEquipmentIds: [],
      affectedProjectIds: [],
      location: { lat: 25, lng: 45 },
      radius: severity * 50,
      status: 'active',
    };

    addDisruption(event);
    setName('');
    setDescription('');
    setSeverity(3);
    setSelectedZones([]);
  };

  const toggleZone = (zoneId: string) => {
    setSelectedZones((prev) =>
      prev.includes(zoneId) ? prev.filter((z) => z !== zoneId) : [...prev, zoneId]
    );
  };

  return (
    <div className="space-y-3">
      <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Custom Event</span>

      <div>
        <label className="text-[9px] text-slate-500 block mb-1">Event Name</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g., Port Strike"
          className="w-full bg-[#0a0e1a] border border-[#1e3a5f] rounded px-2 py-1.5 text-xs text-slate-200 placeholder-slate-600 outline-none focus:border-blue-500/50"
        />
      </div>

      <div>
        <label className="text-[9px] text-slate-500 block mb-1">Event Type</label>
        <select
          value={eventType}
          onChange={(e) => setEventType(e.target.value as DisruptionEvent['type'])}
          className="w-full bg-[#0a0e1a] border border-[#1e3a5f] rounded px-2 py-1.5 text-xs text-slate-200 outline-none"
        >
          {EVENT_TYPES.map((t) => (
            <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="text-[9px] text-slate-500 block mb-1">Severity: {severity}/5</label>
        <input
          type="range"
          min={1}
          max={5}
          value={severity}
          onChange={(e) => setSeverity(Number(e.target.value))}
          className="w-full accent-orange-500"
        />
        <div className="flex justify-between text-[8px] text-slate-600">
          <span>Low</span>
          <span>Critical</span>
        </div>
      </div>

      <div>
        <label className="text-[9px] text-slate-500 block mb-1">Affected Zones</label>
        <div className="flex flex-wrap gap-1">
          {ZONE_OPTIONS.map((zone) => (
            <button
              key={zone.id}
              onClick={() => toggleZone(zone.id)}
              className={`text-[9px] px-2 py-0.5 rounded-full border transition-colors ${
                selectedZones.includes(zone.id)
                  ? 'bg-red-500/20 border-red-500/40 text-red-300'
                  : 'border-[#1e3a5f] text-slate-500 hover:text-slate-300'
              }`}
            >
              {zone.name}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="text-[9px] text-slate-500 block mb-1">Description</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Describe the disruption event..."
          rows={2}
          className="w-full bg-[#0a0e1a] border border-[#1e3a5f] rounded px-2 py-1.5 text-xs text-slate-200 placeholder-slate-600 outline-none focus:border-blue-500/50 resize-none"
        />
      </div>

      <button
        onClick={handleSubmit}
        disabled={!name.trim()}
        className="w-full flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-orange-600 hover:bg-orange-500 disabled:bg-slate-700 disabled:text-slate-500 text-xs font-medium text-white transition-colors"
      >
        <Plus className="w-3.5 h-3.5" />
        Simulate Event
      </button>
    </div>
  );
}
