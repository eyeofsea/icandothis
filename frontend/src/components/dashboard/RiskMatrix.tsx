'use client';

import { useMemo, useState } from 'react';
import { ArrowUpDown } from 'lucide-react';
import { useProjectStore } from '@/stores/projectStore';
import { useMapStore } from '@/stores/mapStore';
import { formatCurrency } from '@/lib/utils';
import Badge from '@/components/ui/Badge';
import RiskBar from '@/components/ui/RiskBar';
import { cn } from '@/lib/utils';

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

    return filtered.slice(0, 10); // Show only top 10 in dashboard
  }, [equipment, projects, suppliers, routes, sortKey, sortAsc, filterCriticality]);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(false); }
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Filter Criticality</span>
          <select
            value={filterCriticality}
            onChange={(e) => setFilterCriticality(e.target.value)}
            className="text-[10px] bg-slate-900 border border-slate-800 rounded px-2 py-1 text-slate-300 outline-none focus:border-sky-500/50 transition-colors uppercase font-bold"
          >
            <option value="all">ALL</option>
            <option value="Critical">CRITICAL</option>
            <option value="High">HIGH</option>
            <option value="Medium">MEDIUM</option>
            <option value="Low">LOW</option>
          </select>
        </div>
        <div className="text-[10px] text-slate-500 font-bold uppercase tracking-tighter">
          Top {rows.length} Risks
        </div>
      </div>

      <div className="flex-1 overflow-auto scrollbar-hide -mx-4 px-4">
        <table className="w-full text-[11px] border-separate border-spacing-0">
          <thead className="sticky top-0 bg-slate-900/80 backdrop-blur-md z-10">
            <tr className="text-slate-500">
              <th className="text-left py-2 px-2 font-black uppercase tracking-widest border-b border-white/5">Asset</th>
              <th className="text-left py-2 px-2 font-black uppercase tracking-widest border-b border-white/5 hidden xl:table-cell">Project</th>
              <th className="text-left py-2 px-2 font-black uppercase tracking-widest border-b border-white/5">
                <button onClick={() => toggleSort('criticality')} className="flex items-center gap-0.5 hover:text-white transition-colors">
                  Crit {sortKey === 'criticality' && <ArrowUpDown className="w-2.5 h-2.5 text-sky-400" />}
                </button>
              </th>
              <th className="text-left py-2 px-2 font-black uppercase tracking-widest border-b border-white/5">
                <button onClick={() => toggleSort('riskScore')} className="flex items-center gap-0.5 hover:text-white transition-colors">
                  Risk {sortKey === 'riskScore' && <ArrowUpDown className="w-2.5 h-2.5 text-sky-400" />}
                </button>
              </th>
              <th className="text-right py-2 px-2 font-black uppercase tracking-widest border-b border-white/5">Status</th>
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
                className="group border-b border-white/[0.02] hover:bg-white/[0.04] cursor-pointer transition-all duration-150"
              >
                <td className="py-2.5 px-2">
                  <div className="text-slate-200 font-bold truncate max-w-[120px] group-hover:text-sky-400 transition-colors">{row.name}</div>
                  <div className="text-slate-600 text-[9px] font-bold tracking-tighter uppercase">{formatCurrency(row.value)}</div>
                </td>
                <td className="py-2.5 px-2 text-slate-500 font-medium hidden xl:table-cell truncate max-w-[100px]">{row.projectName}</td>
                <td className="py-2.5 px-2">
                  <Badge 
                    intent={row.criticality === 'Critical' ? 'critical' : row.criticality === 'High' ? 'high' : row.criticality === 'Medium' ? 'medium' : 'low'}
                    variant="glass"
                    className="px-1.5 py-0 rounded-md"
                  >
                    {row.criticality.substring(0, 3)}
                  </Badge>
                </td>
                <td className="py-2.5 px-2 min-w-[100px]">
                  <RiskBar score={row.riskScore} size="sm" showLabel />
                </td>
                <td className="py-2.5 px-2 text-right">
                  <span className={cn(
                    "text-[9px] font-black uppercase tracking-tighter",
                    row.status === 'delayed' ? 'text-rose-400' : row.status === 'in-transit' ? 'text-sky-400' : 'text-slate-500'
                  )}>
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
