'use client';

import { useMapStore } from '@/stores/mapStore';
import { Eye, EyeOff } from 'lucide-react';

const LAYERS = [
  { key: 'projects' as const, label: 'Projects', color: '#22c55e', shape: 'diamond' },
  { key: 'suppliers' as const, label: 'Suppliers', color: '#3b82f6', shape: 'circle' },
  { key: 'routes' as const, label: 'Routes', color: '#06b6d4', shape: 'line' },
  { key: 'equipment' as const, label: 'Equipment', color: '#f97316', shape: 'dot' },
  { key: 'zones' as const, label: 'Risk Zones', color: '#ef4444', shape: 'area' },
  { key: 'disruptions' as const, label: 'Disruptions', color: '#dc2626', shape: 'pulse' },
  { key: 'alternatives' as const, label: 'Alt. Routes', color: '#3b82f6', shape: 'dash' },
];

export default function MapLegend() {
  const { visibleLayers, toggleLayer } = useMapStore();

  return (
    <div className="absolute bottom-4 left-4 glass-card p-3 z-[1000] min-w-[160px]">
      <div className="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">Layers</div>
      <div className="space-y-1.5">
        {LAYERS.map((layer) => {
          const visible = visibleLayers[layer.key];
          return (
            <button
              key={layer.key}
              onClick={() => toggleLayer(layer.key)}
              className="flex items-center gap-2 w-full text-left text-xs group hover:bg-white/5 rounded px-1.5 py-1 transition-colors"
            >
              <span className="w-4 flex justify-center">
                {visible ? (
                  <Eye className="w-3 h-3 text-slate-400 group-hover:text-white" />
                ) : (
                  <EyeOff className="w-3 h-3 text-slate-600" />
                )}
              </span>
              <span
                className="w-3 h-3 rounded-sm flex-shrink-0"
                style={{
                  background: visible ? layer.color : '#334155',
                  opacity: visible ? 1 : 0.4,
                  borderRadius: layer.shape === 'circle' || layer.shape === 'dot' || layer.shape === 'pulse' ? '50%' : '2px',
                  border: layer.shape === 'area' ? `1px dashed ${layer.color}` : 'none',
                  width: layer.shape === 'line' || layer.shape === 'dash' ? '12px' : '12px',
                  height: layer.shape === 'line' || layer.shape === 'dash' ? '2px' : '12px',
                  borderStyle: layer.shape === 'dash' ? 'dashed' : undefined,
                }}
              />
              <span className={visible ? 'text-slate-300' : 'text-slate-600'}>{layer.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
