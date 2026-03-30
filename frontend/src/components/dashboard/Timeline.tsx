'use client';

import { useMemo, useState } from 'react';
import { useProjectStore } from '@/stores/projectStore';
import { CRITICALITY_COLORS } from '@/lib/constants';
import { ZoomIn, ZoomOut } from 'lucide-react';
import { differenceInDays, format, addMonths, startOfMonth } from 'date-fns';

export default function Timeline() {
  const { equipment, projects } = useProjectStore();
  const [zoom, setZoom] = useState(1);

  const today = new Date();
  const startDate = new Date('2026-03-01');
  const endDate = new Date('2028-01-01');
  const totalDays = differenceInDays(endDate, startDate);

  const months = useMemo(() => {
    const m = [];
    let d = startOfMonth(startDate);
    while (d < endDate) {
      m.push(d);
      d = addMonths(d, 1);
    }
    return m;
  }, []);

  const criticalEquipment = useMemo(() => {
    return equipment
      .filter((e) => e.criticality === 'Critical' || e.criticality === 'High')
      .sort((a, b) => new Date(a.deliveryDate).getTime() - new Date(b.deliveryDate).getTime());
  }, [equipment]);

  const todayOffset = (differenceInDays(today, startDate) / totalDays) * 100;

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Delivery Timeline</span>
        <div className="flex items-center gap-1">
          <button onClick={() => setZoom(Math.max(0.5, zoom - 0.25))} className="p-1 hover:bg-white/10 rounded">
            <ZoomOut className="w-3 h-3 text-slate-400" />
          </button>
          <button onClick={() => setZoom(Math.min(3, zoom + 0.25))} className="p-1 hover:bg-white/10 rounded">
            <ZoomIn className="w-3 h-3 text-slate-400" />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-x-auto overflow-y-auto">
        <div style={{ width: `${100 * zoom}%`, minWidth: '100%' }}>
          {/* Month headers */}
          <div className="flex border-b border-[#1e3a5f] mb-1 sticky top-0 bg-[#0a0e1a] z-10">
            {months.map((m, i) => {
              const offset = (differenceInDays(m, startDate) / totalDays) * 100;
              const width = (differenceInDays(addMonths(m, 1), m) / totalDays) * 100;
              return (
                <div
                  key={i}
                  className="text-[8px] text-slate-500 border-r border-[#1e3a5f]/30 px-0.5 py-1 flex-shrink-0"
                  style={{ width: `${width}%` }}
                >
                  {format(m, 'MMM yy')}
                </div>
              );
            })}
          </div>

          {/* Equipment bars */}
          <div className="relative">
            {/* Today marker */}
            <div
              className="absolute top-0 bottom-0 w-px bg-cyan-400/50 z-10"
              style={{ left: `${todayOffset}%` }}
            >
              <div className="absolute -top-0.5 -left-2 text-[7px] text-cyan-400 bg-[#0a0e1a] px-1 rounded">
                Today
              </div>
            </div>

            {criticalEquipment.map((eq) => {
              const proj = projects.find((p) => p.id === eq.projectId);
              const deliveryDate = new Date(eq.deliveryDate);
              const mfgStart = new Date(deliveryDate.getTime() - eq.leadTimeDays * 86400000);
              const barStart = Math.max(0, (differenceInDays(mfgStart, startDate) / totalDays) * 100);
              const barEnd = Math.min(100, (differenceInDays(deliveryDate, startDate) / totalDays) * 100);
              const barWidth = barEnd - barStart;
              const isDelayed = eq.status === 'delayed';
              const color = CRITICALITY_COLORS[eq.criticality];

              return (
                <div key={eq.id} className="flex items-center gap-1 py-1 group">
                  <div className="w-[90px] flex-shrink-0 text-[9px] text-slate-400 truncate pr-1" title={eq.name}>
                    {eq.name}
                  </div>
                  <div className="flex-1 relative h-4">
                    <div
                      className="absolute h-3 rounded-sm top-0.5 transition-all"
                      style={{
                        left: `${barStart}%`,
                        width: `${barWidth}%`,
                        background: isDelayed
                          ? `repeating-linear-gradient(45deg, ${color}40, ${color}40 3px, ${color}20 3px, ${color}20 6px)`
                          : `${color}40`,
                        border: `1px solid ${color}60`,
                      }}
                    >
                      {barWidth > 5 && (
                        <span className="absolute inset-0 flex items-center justify-center text-[7px] text-white/70 truncate px-1">
                          {eq.status}
                        </span>
                      )}
                    </div>
                    {isDelayed && (
                      <div
                        className="absolute h-3 rounded-sm top-0.5 bg-red-500/20 border border-red-500/40"
                        style={{
                          left: `${barEnd}%`,
                          width: `${Math.min(3, 100 - barEnd)}%`,
                        }}
                      />
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
