'use client';

import { useState, useRef } from 'react';
import { AlertTriangle, Info, AlertCircle, Bell, Zap } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface Alert {
  id: string;
  severity: 'info' | 'warning' | 'critical' | 'success';
  message: string;
  timestamp: string;
}

const MOCK_ALERTS: Alert[] = [
  { id: 'a1', severity: 'warning', message: 'Elevated congestion at Port of Shanghai - delays expected 2-4 days', timestamp: new Date(Date.now() - 120000).toISOString() },
  { id: 'a2', severity: 'info', message: 'Gas Turbine Generator in transit - ETA Dammam 15 Aug 2026', timestamp: new Date(Date.now() - 300000).toISOString() },
  { id: 'a3', severity: 'critical', message: 'BOG Compressor delivery delayed - supplier reports manufacturing issue', timestamp: new Date(Date.now() - 600000).toISOString() },
  { id: 'a4', severity: 'info', message: 'DCS Control System ready for shipment from Yokogawa', timestamp: new Date(Date.now() - 900000).toISOString() },
  { id: 'a5', severity: 'warning', message: 'Red Sea / Bab el-Mandeb threat level elevated - rerouting advisory', timestamp: new Date(Date.now() - 1200000).toISOString() },
  { id: 'a6', severity: 'success', message: 'ESD Valve Package cleared customs - delivery on schedule', timestamp: new Date(Date.now() - 1800000).toISOString() },
  { id: 'a7', severity: 'info', message: 'Quarterly supplier audit completed for Siemens Energy - score: 96%', timestamp: new Date(Date.now() - 3600000).toISOString() },
  { id: 'a8', severity: 'warning', message: 'Strait of Hormuz naval activity detected - monitoring situation', timestamp: new Date(Date.now() - 5400000).toISOString() },
];

const severityConfig = {
  info: { icon: Info, color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20' },
  warning: { icon: AlertTriangle, color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20' },
  critical: { icon: AlertCircle, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20' },
  success: { icon: Zap, color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/20' },
};

export default function AlertFeed() {
  const [alerts] = useState<Alert[]>(MOCK_ALERTS);
  const scrollRef = useRef<HTMLDivElement>(null);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 mb-2">
        <Bell className="w-3.5 h-3.5 text-slate-400" />
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Live Feed</span>
        <span className="ml-auto text-[9px] text-slate-500">{alerts.length} alerts</span>
      </div>
      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-1.5">
        {alerts.map((alert) => {
          const config = severityConfig[alert.severity];
          const Icon = config.icon;
          return (
            <div
              key={alert.id}
              className={`flex items-start gap-2 p-2 rounded-md border ${config.bg} ${config.border} ${
                alert.severity === 'critical' ? 'animate-pulse-alert' : ''
              }`}
            >
              <Icon className={`w-3.5 h-3.5 flex-shrink-0 mt-0.5 ${config.color}`} />
              <div className="flex-1 min-w-0">
                <p className="text-[11px] text-slate-300 leading-tight">{alert.message}</p>
                <span className="text-[9px] text-slate-500 mt-0.5 block">
                  {formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true })}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
