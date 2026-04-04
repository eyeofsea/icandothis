'use client';

import { useMemo, useState } from 'react';
import { useProjectStore } from '@/stores/projectStore';
import { formatCurrency } from '@/lib/utils';
import { STATUS_COLORS } from '@/lib/constants';
import { Package, AlertTriangle, DollarSign, FolderKanban, Eye } from 'lucide-react';
import SearchBar from '@/components/ui/SearchBar';
import Badge from '@/components/ui/Badge';
import ProjectDetailModal from '@/components/detail/ProjectDetailModal';

export default function ProjectsView() {
  const { projects, equipment } = useProjectStore();
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const totalValue = projects.reduce((s, p) => s + p.value, 0);
  const totalEquip = equipment.length;
  const atRiskProjects = projects.filter((p) => p.status === 'at-risk' || p.status === 'critical').length;


  const filtered = useMemo(() => {
    let list = projects;
    if (search) {
      const q = search.toLowerCase();
      list = list.filter((p) => p.name.toLowerCase().includes(q) || p.client.toLowerCase().includes(q));
    }
    if (filterStatus !== 'all') list = list.filter((p) => p.status === filterStatus);
    return list;
  }, [projects, search, filterStatus]);

  const statusVariant = (s: string) => {
    switch (s) {
      case 'on-track': return 'success' as const;
      case 'at-risk': return 'warning' as const;
      case 'delayed': return 'high' as const;
      case 'critical': return 'critical' as const;
      default: return 'default' as const;
    }
  };

  return (
    <div className="h-full overflow-y-auto p-5">
      <div className="mb-5">
        <h2 className="text-lg font-bold text-white">Projects</h2>
        <p className="text-xs text-slate-500 mt-0.5">EPC mega-project portfolio overview</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-3 mb-5">
        <div className="glass-card p-4 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <DollarSign className="w-4 h-4 text-green-400" />
            <span className="text-[10px] uppercase text-slate-500 font-semibold tracking-wider">Total Value</span>
          </div>
          <div className="text-xl font-bold text-white">{formatCurrency(totalValue)}</div>
        </div>
        <div className="glass-card p-4 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <FolderKanban className="w-4 h-4 text-cyan-400" />
            <span className="text-[10px] uppercase text-slate-500 font-semibold tracking-wider">Projects</span>
          </div>
          <div className="text-xl font-bold text-white">{projects.length}</div>
        </div>
        <div className="glass-card p-4 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Package className="w-4 h-4 text-purple-400" />
            <span className="text-[10px] uppercase text-slate-500 font-semibold tracking-wider">Equipment</span>
          </div>
          <div className="text-xl font-bold text-white">{totalEquip}</div>
        </div>
        <div className="glass-card p-4 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-red-400" />
            <span className="text-[10px] uppercase text-slate-500 font-semibold tracking-wider">At Risk</span>
          </div>
          <div className="text-xl font-bold text-white">{atRiskProjects}</div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-4">
        <SearchBar value={search} onChange={setSearch} placeholder="Search projects or clients..." className="w-64" />
        <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)} className="text-xs bg-[#1a2236] border border-[#1e3a5f] rounded-md px-2 py-1.5 text-slate-300 outline-none">
          <option value="all">All Status</option>
          <option value="on-track">On Track</option>
          <option value="at-risk">At Risk</option>
          <option value="delayed">Delayed</option>
          <option value="critical">Critical</option>
        </select>
      </div>

      {/* Project Grid */}
      <div className="grid grid-cols-2 gap-4">
        {filtered.map((proj) => {
          const projEquip = equipment.filter((e) => e.projectId === proj.id);
          const atRiskCount = projEquip.filter((e) => e.riskScore >= 60).length;
          const statusColor = STATUS_COLORS[proj.status] || '#22c55e';

          return (
            <div key={proj.id} className="glass-card p-5 rounded-lg hover:bg-white/[0.03] transition-all group">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="flex items-center gap-2">
                    <div className="w-2.5 h-2.5 rounded-full" style={{ background: statusColor, boxShadow: `0 0 6px ${statusColor}60` }} />
                    <h3 className="text-sm font-semibold text-white">{proj.name}</h3>
                  </div>
                  <div className="text-[11px] text-slate-500 mt-0.5 ml-[18px]">{proj.client}</div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={statusVariant(proj.status)}>{proj.status}</Badge>
                  <button onClick={() => setSelectedId(proj.id)} className="p-1.5 rounded-md hover:bg-white/10 text-slate-500 hover:text-cyan-400 transition-colors opacity-0 group-hover:opacity-100">
                    <Eye className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              <div className="flex items-center gap-4 mb-3">
                <span className="text-lg font-bold text-white">{formatCurrency(proj.value)}</span>
                <span className="text-xs text-slate-500">{proj.country}</span>
              </div>

              {/* Progress */}
              <div className="mb-3">
                <div className="flex justify-between text-[10px] text-slate-500 mb-1">
                  <span>Progress</span>
                  <span className="font-medium text-slate-300">{proj.completionPercent}%</span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-700/50">
                  <div className="h-full rounded-full transition-all" style={{ width: `${proj.completionPercent}%`, background: statusColor }} />
                </div>
              </div>

              {/* Equipment stats */}
              <div className="flex items-center gap-3 text-[10px]">
                <div className="flex items-center gap-1 text-slate-400">
                  <Package className="w-3 h-3" /> {projEquip.length} equipment
                </div>
                {atRiskCount > 0 && (
                  <div className="flex items-center gap-1 text-red-400">
                    <AlertTriangle className="w-3 h-3" /> {atRiskCount} at risk
                  </div>
                )}
                <span className="text-slate-500">{proj.startDate} → {proj.endDate}</span>
              </div>
            </div>
          );
        })}
      </div>

      <ProjectDetailModal projectId={selectedId} onClose={() => setSelectedId(null)} />
    </div>
  );
}
