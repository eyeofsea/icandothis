'use client';

import { useState, useMemo } from 'react';
import { AlertTriangle, Info, AlertCircle, Zap, Bell } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import SearchBar from '@/components/ui/SearchBar';
import Badge from '@/components/ui/Badge';

interface Alert {
  id: string;
  severity: 'info' | 'warning' | 'critical' | 'success';
  message: string;
  timestamp: string;
  category: string;
}

const ALERTS: Alert[] = [
  { id: 'a1', severity: 'warning', message: 'Elevated congestion at Port of Shanghai - delays expected 2-4 days', timestamp: new Date(Date.now() - 120000).toISOString(), category: 'Port' },
  { id: 'a2', severity: 'info', message: 'Gas Turbine Generator in transit - ETA Dammam 15 Aug 2026', timestamp: new Date(Date.now() - 300000).toISOString(), category: 'Equipment' },
  { id: 'a3', severity: 'critical', message: 'BOG Compressor delivery delayed - supplier reports manufacturing issue', timestamp: new Date(Date.now() - 600000).toISOString(), category: 'Equipment' },
  { id: 'a4', severity: 'info', message: 'DCS Control System ready for shipment from Yokogawa', timestamp: new Date(Date.now() - 900000).toISOString(), category: 'Equipment' },
  { id: 'a5', severity: 'warning', message: 'Red Sea / Bab el-Mandeb threat level elevated - rerouting advisory', timestamp: new Date(Date.now() - 1200000).toISOString(), category: 'Geopolitical' },
  { id: 'a6', severity: 'success', message: 'ESD Valve Package cleared customs - delivery on schedule', timestamp: new Date(Date.now() - 1800000).toISOString(), category: 'Equipment' },
  { id: 'a7', severity: 'info', message: 'Quarterly supplier audit completed for Siemens Energy - score: 96%', timestamp: new Date(Date.now() - 3600000).toISOString(), category: 'Supplier' },
  { id: 'a8', severity: 'warning', message: 'Strait of Hormuz naval activity detected - monitoring situation', timestamp: new Date(Date.now() - 5400000).toISOString(), category: 'Geopolitical' },
];

const severityConfig = {
  info: { icon: Info, color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20', badge: 'info' as const },
  warning: { icon: AlertTriangle, color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20', badge: 'warning' as const },
  critical: { icon: AlertCircle, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20', badge: 'critical' as const },
  success: { icon: Zap, color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/20', badge: 'success' as const },
};

export default function AlertsView() {
  const [search, setSearch] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('all');

  const filtered = useMemo(() => {
    let list = ALERTS;
    if (search) {
      const q = search.toLowerCase();
      list = list.filter((a) => a.message.toLowerCase().includes(q));
    }
    if (filterSeverity !== 'all') list = list.filter((a) => a.severity === filterSeverity);
    return list;
  }, [search, filterSeverity]);

  const counts = {
    critical: ALERTS.filter((a) => a.severity === 'critical').length,
    warning: ALERTS.filter((a) => a.severity === 'warning').length,
    info: ALERTS.filter((a) => a.severity === 'info').length,
    success: ALERTS.filter((a) => a.severity === 'success').length,
  };

  return (
    <div className="h-full overflow-y-auto p-5">
      <div className="mb-5">
        <h2 className="text-lg font-bold text-white">Alerts</h2>
        <p className="text-xs text-slate-500 mt-0.5">Live feed of supply chain events and disruptions</p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-4 gap-3 mb-5">
        {[
          { label: 'Critical', count: counts.critical, color: 'text-red-400', bg: 'bg-red-500/10' },
          { label: 'Warning', count: counts.warning, color: 'text-yellow-400', bg: 'bg-yellow-500/10' },
          { label: 'Info', count: counts.info, color: 'text-blue-400', bg: 'bg-blue-500/10' },
          { label: 'Success', count: counts.success, color: 'text-green-400', bg: 'bg-green-500/10' },
        ].map((item) => (
          <div key={item.label} className={`glass-card p-4 rounded-lg flex items-center gap-3 ${item.bg}`}>
            <Bell className={`w-5 h-5 ${item.color}`} />
            <div>
              <div className={`text-xl font-bold ${item.color}`}>{item.count}</div>
              <div className="text-[10px] text-slate-500">{item.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-4">
        <SearchBar value={search} onChange={setSearch} placeholder="Search alerts..." className="w-64" />
        <select value={filterSeverity} onChange={(e) => setFilterSeverity(e.target.value)} className="text-xs bg-[#1a2236] border border-[#1e3a5f] rounded-md px-2 py-1.5 text-slate-300 outline-none">
          <option value="all">All Severity</option>
          <option value="critical">Critical</option>
          <option value="warning">Warning</option>
          <option value="info">Info</option>
          <option value="success">Success</option>
        </select>
      </div>

      {/* Alert List */}
      <div className="space-y-2">
        {filtered.map((alert) => {
          const config = severityConfig[alert.severity];
          const Icon = config.icon;
          return (
            <div key={alert.id} className={`flex items-start gap-3 p-4 rounded-lg border glass-card ${config.bg} ${config.border}`}>
              <Icon className={`w-5 h-5 flex-shrink-0 mt-0.5 ${config.color}`} />
              <div className="flex-1">
                <p className="text-sm text-slate-200 leading-relaxed">{alert.message}</p>
                <div className="flex items-center gap-3 mt-2">
                  <span className="text-[10px] text-slate-500">
                    {formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true })}
                  </span>
                  <Badge variant={config.badge}>{alert.severity}</Badge>
                  <Badge variant="default">{alert.category}</Badge>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
