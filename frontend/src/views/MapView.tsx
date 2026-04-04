'use client';

import WorldMap from '@/components/map/WorldMap';

export default function MapView() {
  return (
    <div className="h-full w-full relative">
      <WorldMap />
      {/* Bottom ticker */}
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
          </div>
        </div>
      </div>
    </div>
  );
}
