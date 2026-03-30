'use client';

import { useMemo, useState } from 'react';
import { ArrowUpDown } from 'lucide-react';
import { useProjectStore } from '@/stores/projectStore';
import { useMapStore } from '@/stores/mapStore';
import { formatCurrency, riskColor } from '@/lib/utils';
import { CRITICALITY_COLORS } from '@/lib/constants';

type SortKey = 'riskScore' | 'value' | 'criticality' | 'status';

export default function RiskMatrix() {
  const { equipment, projects, suppliers, routes } = useProjectStore();
  const { setSelectedEquipment, setMapCenter } = useMapStore();
  const [sortKey, setSortKey] = useState<SortKey>('riskScore');
  const [sortAsc, setSortAsc] = useState(false);
  const [filterCriticality, setFilterCriticality] = useState<string>('all');

  const rows = useMemo(() => {
    const mapped = equipment.map((eq) => {
      const proj = projects.find((p) => p.id === eq.projectId);
      const sup = suppliers.find((s) => s.id === eq.supplierId);
      const route = routes.find((r) => r.id === eq.routeId);
      return {
        ...eq,
        projectName: proj?.name || '-',
        supplierName: sup?.name || '-',
        routeName: route?.name || '-',
      };
    });

    const filtered = filterCriticality === 'all' ? mapped : mapped.filter((r) => r.criticality === filterCriticality);

    const critOrder: Record<string, number> = { Critical: 4, High: 3, Medium: 2, Low: 1 };
    filtered.sort((a, b) => {
      let cmp = 0;
      if (sortKey === 'riskScore') cmp = a.riskScore - b.riskScore;
      else if (sortKey === 'value') cmp = a.value - b.value;
      else if (sortKey === 'criticality') cmp = (critOrder[a.criticality] || 0) - (critOrder[b.criticality] || 0);
      else cmp = a.status.localeCompare(b.status);
      return sortAsc ? cmp : -cmp;
    });

    return filtered;
  }, [equipment, projects, suppliers, routes, sortKey, sortAsc, filterCriticality]);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(false); }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs text-slate-400">Filter:</span>
        <select
          value={filterCriticality}
          onChange={(e) => setFilterCriticality(e.target.value)}
          className="text-xs bg-[#1a2236] border border-[#1e3a5f] rounded px-2 py-1 text-slate-300 outline-none"
        >
          <option value="all">All</option>
          <option value="Critical">Critical</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>
      </div>

      <div className="flex-1 overflow-auto">
        <table className="w-full text-[11px]">
          <thead className="sticky top-0 bg-[#0a0e1a]">
            <tr className="text-slate-500 border-b border-[#1e3a5f]">
              <th className="text-left py-1.5 px-1 font-medium">Equipment</th>
              <th className="text-left py-1.5 px-1 font-medium hidden xl:table-cell">Project</th>
              <th className="text-left py-1.5 px-1 font-medium">
                <button onClick={() => toggleSort('criticality')} className="flex items-center gap-0.5 hover:text-slate-300">
                  Crit. <ArrowUpDown className="w-2.5 h-2.5" />
                </button>
              </th>
              <th className="text-left py-1.5 px-1 font-medium">
                <button onClick={() => toggleSort('riskScore')} className="flex items-center gap-0.5 hover:text-slate-300">
                  Risk <ArrowUpDown className="w-2.5 h-2.5" />
                </button>
              </th>
              <th className="text-left py-1.5 px-1 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={row.id}
                onClick={() => {
                  setSelectedEquipment(row.id);
                  if (row.currentPosition) setMapCenter([row.currentPosition.lat, row.currentPosition.lng]);
                }}
                className="border-b border-[#1e3a5f]/50 hover:bg-white/[0.03] cursor-pointer transition-colors"
              >
                <td className="py-1.5 px-1">
                  <div className="text-slate-200 font-medium truncate max-w-[120px]">{row.name}</div>
                  <div className="text-slate-500 text-[9px]">{formatCurrency(row.value)}</div>
                </td>
                <td className="py-1.5 px-1 text-slate-400 hidden xl:table-cell truncate max-w-[80px]">{row.projectName}</td>
                <td className="py-1.5 px-1">
                  <span
                    className="inline-block px-1.5 py-0.5 rounded text-[9px] font-semibold"
                    style={{
                      color: CRITICALITY_COLORS[row.criticality],
                      background: `${CRITICALITY_COLORS[row.criticality]}20`,
                    }}
                  >
                    {row.criticality}
                  </span>
                </td>
                <td className="py-1.5 px-1">
                  <div className="flex items-center gap-1">
                    <div className="w-8 h-1.5 rounded-full bg-slate-700 overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{
                          width: `${row.riskScore}%`,
                          background: row.riskScore >= 70 ? '#ef4444' : row.riskScore >= 50 ? '#f97316' : row.riskScore >= 30 ? '#eab308' : '#22c55e',
                        }}
                      />
                    </div>
                    <span className={riskColor(row.riskScore)}>{row.riskScore}</span>
                  </div>
                </td>
                <td className="py-1.5 px-1">
                  <span className={`text-[9px] ${row.status === 'delayed' ? 'text-red-400' : row.status === 'in-transit' ? 'text-cyan-400' : 'text-slate-400'}`}>
                    {row.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
