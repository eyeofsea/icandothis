'use client';

import { useMapStore } from '@/stores/mapStore';
import { Eye, EyeOff, Layers } from 'lucide-react';
import { cn } from '@/lib/utils';
import Card from '@/components/ui/Card';

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
    <Card 
      variant="glass" 
      padding="sm" 
      className="absolute bottom-16 right-6 z-[1000] min-w-[180px] shadow-2xl border-white/10"
    >
      <div className="flex items-center gap-2 mb-3 pb-2 border-b border-white/5">
        <Layers className="w-3.5 h-3.5 text-sky-400" />
        <span className="text-[10px] font-black text-white uppercase tracking-widest">Map Layers</span>
      </div>
      
      <div className="space-y-1">
        {LAYERS.map((layer) => {
          const visible = visibleLayers[layer.key];
          return (
            <button
              key={layer.key}
              onClick={() => toggleLayer(layer.key)}
              className={cn(
                "group flex items-center gap-3 w-full text-left rounded-lg px-2 py-1.5 transition-all duration-200",
                visible ? "bg-white/[0.03] text-slate-200" : "opacity-50 text-slate-500 grayscale"
              )}
            >
              <div className="relative w-4 flex justify-center">
                {visible ? (
                  <Eye className="w-3.5 h-3.5 text-sky-500 group-hover:text-sky-400" />
                ) : (
                  <EyeOff className="w-3.5 h-3.5" />
                )}
              </div>
              
              <div
                className="w-3 h-3 rounded-sm flex-shrink-0 shadow-sm border border-white/10"
                style={{
                  background: layer.color,
                  borderRadius: layer.shape === 'circle' || layer.shape === 'dot' || layer.shape === 'pulse' ? '50%' : '3px',
                }}
              />
              
              <span className="text-[10px] font-bold uppercase tracking-tighter flex-1">
                {layer.label}
              </span>
            </button>
          );
        })}
      </div>
    </Card>
  );
}
