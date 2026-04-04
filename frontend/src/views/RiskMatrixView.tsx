'use client';

import { useMemo, useState } from 'react';
import { ArrowUpDown, Eye } from 'lucide-react';
import { useProjectStore } from '@/stores/projectStore';
import { formatCurrency } from '@/lib/utils';
import { CRITICALITY_COLORS } from '@/lib/constants';
import SearchBar from '@/components/ui/SearchBar';
import Badge from '@/components/ui/Badge';
import RiskBar from '@/components/ui/RiskBar';
import EquipmentDetailModal from '@/components/detail/EquipmentDetailModal';

type SortKey = 'riskScore' | 'value' | 'criticality' | 'status' | 'name';
type RiskRange = 'all' | '0-30' | '30-60' | '60-100';

export default function RiskMatrixView() {
  const { equipment, projects, suppliers } = useProjectStore();
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('riskScore');
  const [sortAsc, setSortAsc] = useState(false);
  const [filterCriticality, setFilterCriticality] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterRiskRange, setFilterRiskRange] = useState<RiskRange>('all');
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const rows = useMemo(() => {
    const mapped = equipment.map((eq) => ({
      ...eq,
      projectName: projects.find((p) => p.id === eq.projectId)?.name || '-',
      supplierName: suppliers.find((s) => s.id === eq.supplierId)?.name || '-',
    }));

    let filtered = mapped;
    if (search) {
      const q = search.toLowerCase();
      filtered = filtered.filter((r) => r.name.toLowerCase().includes(q) || r.projectName.toLowerCase().includes(q) || r.supplierName.toLowerCase().includes(q));
    }
    if (filterCriticality !== 'all') filtered = filtered.filter((r) => r.criticality === filterCriticality);
    if (filterStatus !== 'all') filtered = filtered.filter((r) => r.status === filterStatus);
    if (filterRiskRange !== 'all') {
      const [lo, hi] = filterRiskRange.split('-').map(Number);
      filtered = filtered.filter((r) => r.riskScore >= lo && r.riskScore < hi);
    }

    const critOrder: Record<string, number> = { Critical: 4, High: 3, Medium: 2, Low: 1 };
    filtered.sort((a, b) => {
      let cmp = 0;
      if (sortKey === 'riskScore') cmp = a.riskScore - b.riskScore;
      else if (sortKey === 'value') cmp = a.value - b.value;
      else if (sortKey === 'criticality') cmp = (critOrder[a.criticality] || 0) - (critOrder[b.criticality] || 0);
      else if (sortKey === 'name') cmp = a.name.localeCompare(b.name);
      else cmp = a.status.localeCompare(b.status);
      return sortAsc ? cmp : -cmp;
    });

    return filtered;
  }, [equipment, projects, suppliers, search, sortKey, sortAsc, filterCriticality, filterStatus, filterRiskRange]);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(false); }
  };

  const SortBtn = ({ k, label }: { k: SortKey; label: string }) => (
    <button onClick={() => toggleSort(k)} className="flex items-center gap-1 hover:text-slate-300 transition-colors">
      {label} <ArrowUpDown className="w-3 h-3" />
    </button>
  );

  return (
    <div className="h-full flex flex-col p-5">
      <div className="mb-4">
        <h2 className="text-lg font-bold text-white">Risk Matrix</h2>
        <p className="text-xs text-slate-500 mt-0.5">Equipment risk assessment and monitoring</p>
      </div>

      {/* Search + Filters */}
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <SearchBar value={search} onChange={setSearch} placeholder="Search equipment, project, supplier..." className="w-72" />
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-slate-500">Criticality:</span>
          <select value={filterCriticality} onChange={(e) => setFilterCriticality(e.target.value)} className="text-xs bg-[#1a2236] border border-[#1e3a5f] rounded-md px-2 py-1.5 text-slate-300 outline-none">
            <option value="all">All</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-slate-500">Status:</span>
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)} className="text-xs bg-[#1a2236] border border-[#1e3a5f] rounded-md px-2 py-1.5 text-slate-300 outline-none">
            <option value="all">All</option>
            <option value="ordered">Ordered</option>
            <option value="manufacturing">Manufacturing</option>
            <option value="ready">Ready</option>
            <option value="in-transit">In Transit</option>
            <option value="delayed">Delayed</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-slate-500">Risk:</span>
          <select value={filterRiskRange} onChange={(e) => setFilterRiskRange(e.target.value as RiskRange)} className="text-xs bg-[#1a2236] border border-[#1e3a5f] rounded-md px-2 py-1.5 text-slate-300 outline-none">
            <option value="all">All</option>
            <option value="60-100">High (60-100)</option>
            <option value="30-60">Medium (30-60)</option>
            <option value="0-30">Low (0-30)</option>
          </select>
        </div>
        <span className="ml-auto text-[10px] text-slate-500">{rows.length} items</span>
      </div>

      {/* Table */}
      <div className="flex-1 glass-card rounded-lg overflow-hidden">
        <div className="h-full overflow-auto">
          <table className="w-full text-xs">
            <thead className="sticky top-0 bg-[#111827] z-10">
              <tr className="text-slate-500 border-b border-[#1e3a5f]">
                <th className="text-left py-3 px-4 font-medium"><SortBtn k="name" label="Equipment" /></th>
                <th className="text-left py-3 px-3 font-medium">Value</th>
                <th className="text-left py-3 px-3 font-medium">Project</th>
                <th className="text-left py-3 px-3 font-medium">Supplier</th>
                <th className="text-left py-3 px-3 font-medium"><SortBtn k="criticality" label="Criticality" /></th>
                <th className="text-left py-3 px-3 font-medium w-36"><SortBtn k="riskScore" label="Risk Score" /></th>
                <th className="text-left py-3 px-3 font-medium"><SortBtn k="status" label="Status" /></th>
                <th className="text-center py-3 px-3 font-medium w-16">Details</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id} className="border-b border-[#1e3a5f]/30 hover:bg-white/[0.03] transition-colors">
                  <td className="py-3 px-4 font-medium text-slate-200">{row.name}</td>
                  <td className="py-3 px-3 text-slate-400">{formatCurrency(row.value)}</td>
                  <td className="py-3 px-3 text-slate-400">{row.projectName}</td>
                  <td className="py-3 px-3 text-slate-400">{row.supplierName}</td>
                  <td className="py-3 px-3">
                    <span
                      className="inline-block px-2 py-0.5 rounded text-[10px] font-semibold"
                      style={{ color: CRITICALITY_COLORS[row.criticality], background: `${CRITICALITY_COLORS[row.criticality]}20` }}
                    >
                      {row.criticality}
                    </span>
                  </td>
                  <td className="py-3 px-3">
                    <RiskBar score={row.riskScore} />
                  </td>
                  <td className="py-3 px-3">
                    <Badge variant={row.status === 'delayed' ? 'critical' : row.status === 'in-transit' ? 'info' : row.status === 'ready' ? 'success' : 'default'}>
                      {row.status}
                    </Badge>
                  </td>
                  <td className="py-3 px-3 text-center">
                    <button onClick={() => setSelectedId(row.id)} className="p-1.5 rounded-md hover:bg-white/10 text-slate-500 hover:text-cyan-400 transition-colors">
                      <Eye className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <EquipmentDetailModal equipmentId={selectedId} onClose={() => setSelectedId(null)} />
    </div>
  );
}
