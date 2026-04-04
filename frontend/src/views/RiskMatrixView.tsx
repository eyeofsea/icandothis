'use client';

import { useMemo, useState } from 'react';
import { ArrowUpDown, Eye, Filter, Download, Search } from 'lucide-react';
import { useProjectStore } from '@/stores/projectStore';
import { formatCurrency, cn } from '@/lib/utils';
import Badge from '@/components/ui/Badge';
import RiskBar from '@/components/ui/RiskBar';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import Input from '@/components/ui/Input';
import EquipmentDetailModal from '@/components/detail/EquipmentDetailModal';

type SortKey = 'riskScore' | 'value' | 'criticality' | 'status' | 'name';
type RiskRange = 'all' | '0-30' | '30-60' | '60-100';

export default function RiskMatrixView() {
  const { equipment, projects, suppliers } = useProjectStore();
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('riskScore');
  const [sortAsc, setSortAsc] = useState(false);
  const [filterCriticality, setFilterCriticality] = useState('all');
  const [filterStatus] = useState('all');
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

  return (
    <div className="h-full flex flex-col p-6 space-y-6 overflow-hidden">
      {/* Header section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 flex-shrink-0">
        <div>
          <h2 className="text-xl font-black text-white tracking-tight uppercase">Risk Intelligence</h2>
          <p className="text-[11px] text-slate-500 font-bold uppercase tracking-wider mt-0.5">Comprehensive asset risk mapping & auditing</p>
        </div>
        
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" icon={Filter}>Configure</Button>
          <Button variant="primary" size="sm" icon={Download}>Report</Button>
        </div>
      </div>

      <Card variant="glass" padding="none" className="flex-1 flex flex-col min-h-0">
        {/* Table Controls */}
        <div className="px-5 py-4 border-b border-white/5 bg-white/2 flex flex-wrap items-center gap-4">
          <div className="w-80">
            <Input 
              icon={Search} 
              placeholder="Search assets, projects..." 
              value={search} 
              onChange={(e) => setSearch(e.target.value)}
              className="h-9"
            />
          </div>
          
          <div className="h-6 w-[1px] bg-slate-800/60" />

          <div className="flex items-center gap-4">
            <div className="flex flex-col">
              <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-1">Criticality</span>
              <select 
                value={filterCriticality} 
                onChange={(e) => setFilterCriticality(e.target.value)}
                className="text-[11px] bg-slate-900 border border-slate-800 rounded px-2 py-1 text-slate-300 outline-none focus:border-sky-500/50 transition-colors"
              >
                <option value="all">ALL LEVELS</option>
                <option value="Critical">CRITICAL</option>
                <option value="High">HIGH</option>
                <option value="Medium">MEDIUM</option>
                <option value="Low">LOW</option>
              </select>
            </div>

            <div className="flex flex-col">
              <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-1">Risk Range</span>
              <select 
                value={filterRiskRange} 
                onChange={(e) => setFilterRiskRange(e.target.value as RiskRange)}
                className="text-[11px] bg-slate-900 border border-slate-800 rounded px-2 py-1 text-slate-300 outline-none focus:border-sky-500/50 transition-colors"
              >
                <option value="all">ALL SCORES</option>
                <option value="60-100">HIGH (60-100)</option>
                <option value="30-60">MED (30-60)</option>
                <option value="0-30">LOW (0-30)</option>
              </select>
            </div>
          </div>

          <div className="ml-auto flex items-center gap-3">
            <span className="text-[10px] font-bold text-slate-600 uppercase tracking-tighter">
              Showing <span className="text-sky-400">{rows.length}</span> of {equipment.length} assets
            </span>
          </div>
        </div>

        {/* The Table */}
        <div className="flex-1 overflow-auto scrollbar-thin">
          <table className="w-full text-xs border-separate border-spacing-0">
            <thead className="sticky top-0 bg-slate-900/90 backdrop-blur-md z-10 shadow-sm">
              <tr className="text-slate-500">
                <th className="text-left py-4 px-5 font-black uppercase tracking-widest border-b border-white/5">
                  <button onClick={() => toggleSort('name')} className="flex items-center gap-1.5 hover:text-white transition-colors">
                    Asset ID {sortKey === 'name' && <ArrowUpDown className="w-3 h-3 text-sky-400" />}
                  </button>
                </th>
                <th className="text-left py-4 px-3 font-black uppercase tracking-widest border-b border-white/5">Project</th>
                <th className="text-left py-4 px-3 font-black uppercase tracking-widest border-b border-white/5">
                  <button onClick={() => toggleSort('criticality')} className="flex items-center gap-1.5 hover:text-white transition-colors">
                    Criticality {sortKey === 'criticality' && <ArrowUpDown className="w-3 h-3 text-sky-400" />}
                  </button>
                </th>
                <th className="text-left py-4 px-3 font-black uppercase tracking-widest border-b border-white/5">
                  <button onClick={() => toggleSort('riskScore')} className="flex items-center gap-1.5 hover:text-white transition-colors">
                    Risk Assessment {sortKey === 'riskScore' && <ArrowUpDown className="w-3 h-3 text-sky-400" />}
                  </button>
                </th>
                <th className="text-left py-4 px-3 font-black uppercase tracking-widest border-b border-white/5">Status</th>
                <th className="text-center py-4 px-5 font-black uppercase tracking-widest border-b border-white/5">Actions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr 
                  key={row.id} 
                  className={cn(
                    "group border-b border-white/[0.02] hover:bg-white/[0.03] transition-all duration-150",
                    i % 2 === 1 && "bg-white/[0.01]"
                  )}
                >
                  <td className="py-4 px-5">
                    <div className="font-bold text-slate-200 group-hover:text-sky-400 transition-colors">{row.name}</div>
                    <div className="text-[10px] text-slate-600 font-medium mt-0.5">{row.supplierName}</div>
                  </td>
                  <td className="py-4 px-3">
                    <div className="text-slate-400 font-medium">{row.projectName}</div>
                    <div className="text-[10px] text-slate-600 font-bold tracking-tighter mt-0.5 uppercase">{formatCurrency(row.value)}</div>
                  </td>
                  <td className="py-4 px-3">
                    <Badge 
                      intent={row.criticality === 'Critical' ? 'critical' : row.criticality === 'High' ? 'high' : row.criticality === 'Medium' ? 'medium' : 'low'}
                      variant="glass"
                    >
                      {row.criticality}
                    </Badge>
                  </td>
                  <td className="py-4 px-3 min-w-[160px]">
                    <RiskBar score={row.riskScore} showLabel />
                  </td>
                  <td className="py-4 px-3">
                    <Badge 
                      intent={row.status === 'delayed' ? 'critical' : row.status === 'in-transit' ? 'info' : row.status === 'ready' ? 'success' : 'default'}
                      variant="solid"
                      className="rounded-md px-1.5"
                    >
                      {row.status}
                    </Badge>
                  </td>
                  <td className="py-4 px-5 text-center">
                    <button 
                      onClick={() => setSelectedId(row.id)} 
                      className="p-2 rounded-lg bg-slate-800/50 border border-slate-700/50 text-slate-500 hover:text-sky-400 hover:border-sky-500/30 hover:shadow-glow-blue/20 transition-all"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <EquipmentDetailModal equipmentId={selectedId} onClose={() => setSelectedId(null)} />
    </div>
  );
}
