'use client';

import WorldMap from '@/components/map/WorldMap';
import { cn } from '@/lib/utils';
import { AlertTriangle, Info, Zap, Globe } from 'lucide-react';

const TICKER_ITEMS = [
  { type: 'alert', text: 'RED SEA: Threat level elevated - routing adjustments advised', icon: AlertTriangle, color: 'text-rose-400' },
  { type: 'info', text: 'TRANSIT: GE Gas Turbine 9HA.02 - ETA Suez Canal 15 AUG', icon: Globe, color: 'text-sky-400' },
  { type: 'risk', text: 'INCIDENT: BOG Compressor delayed (78d) - High criticality', icon: Zap, color: 'text-rose-500' },
  { type: 'info', text: 'CUSTOMS: ESD Valve Package cleared Shanghai Port', icon: Info, color: 'text-emerald-400' },
  { type: 'alert', text: 'CONGESTION: Singapore port wait time +48h', icon: AlertTriangle, color: 'text-amber-400' },
];

export default function MapView() {
  return (
    <div className="h-full w-full relative group">
      <WorldMap />
      
      {/* View Title Overlay */}
      <div className="absolute top-6 left-20 z-[1000] pointer-events-none">
        <h2 className="text-2xl font-black text-white tracking-tighter uppercase drop-shadow-2xl">
          Global <span className="text-sky-500">Logistics</span> Node
        </h2>
        <div className="flex items-center gap-2 mt-1">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Live SAT-COM Feed Active</span>
        </div>
      </div>

      {/* Bottom ticker - Pro version */}
      <div className="absolute bottom-0 left-0 right-0 h-10 bg-slate-950/80 backdrop-blur-md border-t border-white/5 flex items-center z-[1000] overflow-hidden">
        <div className="flex-shrink-0 bg-sky-500 px-4 h-full flex items-center z-10 shadow-glow-blue/20">
          <span className="text-[10px] font-black text-slate-950 uppercase tracking-widest">Intel Feed</span>
        </div>
        
        <div className="flex-1 overflow-hidden relative h-full flex items-center">
          <div className="ticker-scroll flex items-center gap-12 whitespace-nowrap px-8">
            {[...TICKER_ITEMS, ...TICKER_ITEMS].map((item, i) => (
              <div key={i} className="flex items-center gap-2">
                <item.icon className={cn("w-3 h-3", item.color)} />
                <span className="text-[10px] font-bold text-slate-300 uppercase tracking-tight">{item.text}</span>
              </div>
            ))}
          </div>
          
          {/* Gradient masks */}
          <div className="absolute inset-y-0 left-0 w-12 bg-gradient-to-r from-slate-950/80 to-transparent z-10" />
          <div className="absolute inset-y-0 right-0 w-12 bg-gradient-to-l from-slate-950/80 to-transparent z-10" />
        </div>
      </div>
    </div>
  );
}
