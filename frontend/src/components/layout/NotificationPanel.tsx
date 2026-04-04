'use client';

import { useState, useMemo } from 'react';
import { X, Bell, Check, Trash2, AlertTriangle, Info, AlertCircle, Zap } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import Badge from '@/components/ui/Badge';

interface Notification {
  id: string;
  severity: 'info' | 'warning' | 'critical' | 'success';
  message: string;
  timestamp: string;
  read: boolean;
}

const INITIAL_NOTIFICATIONS: Notification[] = [
  { id: 'n1', severity: 'warning', message: 'Elevated congestion at Port of Shanghai - delays expected 2-4 days', timestamp: new Date(Date.now() - 120000).toISOString(), read: false },
  { id: 'n2', severity: 'info', message: 'Gas Turbine Generator in transit - ETA Dammam 15 Aug 2026', timestamp: new Date(Date.now() - 300000).toISOString(), read: false },
  { id: 'n3', severity: 'critical', message: 'BOG Compressor delivery delayed - supplier reports manufacturing issue', timestamp: new Date(Date.now() - 600000).toISOString(), read: false },
  { id: 'n4', severity: 'info', message: 'DCS Control System ready for shipment from Yokogawa', timestamp: new Date(Date.now() - 900000).toISOString(), read: true },
  { id: 'n5', severity: 'warning', message: 'Red Sea / Bab el-Mandeb threat level elevated - rerouting advisory', timestamp: new Date(Date.now() - 1200000).toISOString(), read: false },
  { id: 'n6', severity: 'success', message: 'ESD Valve Package cleared customs - delivery on schedule', timestamp: new Date(Date.now() - 1800000).toISOString(), read: true },
  { id: 'n7', severity: 'info', message: 'Quarterly supplier audit completed for Siemens Energy - score: 96%', timestamp: new Date(Date.now() - 3600000).toISOString(), read: true },
  { id: 'n8', severity: 'warning', message: 'Strait of Hormuz naval activity detected - monitoring situation', timestamp: new Date(Date.now() - 5400000).toISOString(), read: false },
];

const severityConfig = {
  info: { icon: Info, color: 'text-blue-400', badge: 'info' as const },
  warning: { icon: AlertTriangle, color: 'text-yellow-400', badge: 'warning' as const },
  critical: { icon: AlertCircle, color: 'text-red-400', badge: 'critical' as const },
  success: { icon: Zap, color: 'text-green-400', badge: 'success' as const },
};

type FilterType = 'all' | 'unread' | 'critical' | 'warning';

interface NotificationPanelProps {
  open: boolean;
  onClose: () => void;
}

export default function NotificationPanel({ open, onClose }: NotificationPanelProps) {
  const [notifications, setNotifications] = useState<Notification[]>(INITIAL_NOTIFICATIONS);
  const [filter, setFilter] = useState<FilterType>('all');

  const filtered = useMemo(() => {
    switch (filter) {
      case 'unread': return notifications.filter((n) => !n.read);
      case 'critical': return notifications.filter((n) => n.severity === 'critical');
      case 'warning': return notifications.filter((n) => n.severity === 'warning');
      default: return notifications;
    }
  }, [notifications, filter]);

  const unreadCount = notifications.filter((n) => !n.read).length;

  const markRead = (id: string) => {
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
  };

  const markAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const remove = (id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[150]" onClick={onClose}>
      <div
        className="absolute right-0 top-0 h-full w-[380px] bg-[#0c1220] border-l border-[#1e3a5f]/60 shadow-2xl flex flex-col animate-in slide-in-from-right"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-[#1e3a5f]/60">
          <div className="flex items-center gap-2">
            <Bell className="w-4 h-4 text-cyan-400" />
            <span className="text-sm font-semibold text-white">Notifications</span>
            {unreadCount > 0 && <Badge variant="info">{unreadCount} new</Badge>}
          </div>
          <div className="flex items-center gap-1">
            <button onClick={markAllRead} className="p-1.5 rounded-md hover:bg-white/5 text-slate-400 hover:text-white transition-colors" title="Mark all read">
              <Check className="w-3.5 h-3.5" />
            </button>
            <button onClick={onClose} className="p-1.5 rounded-md hover:bg-white/5 text-slate-400 hover:text-white transition-colors">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex gap-1 px-4 py-2 border-b border-[#1e3a5f]/40">
          {(['all', 'unread', 'critical', 'warning'] as FilterType[]).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-2.5 py-1 rounded-md text-[10px] font-medium transition-colors ${
                filter === f ? 'bg-cyan-500/15 text-cyan-400' : 'text-slate-500 hover:text-slate-300 hover:bg-white/5'
              }`}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto">
          {filtered.length === 0 ? (
            <div className="flex items-center justify-center h-32 text-xs text-slate-500">No notifications</div>
          ) : (
            filtered.map((n) => {
              const config = severityConfig[n.severity];
              const Icon = config.icon;
              return (
                <div
                  key={n.id}
                  className={`flex items-start gap-2.5 px-4 py-3 border-b border-[#1e3a5f]/30 hover:bg-white/[0.02] transition-colors ${
                    !n.read ? 'bg-cyan-500/[0.03]' : ''
                  }`}
                >
                  <Icon className={`w-4 h-4 flex-shrink-0 mt-0.5 ${config.color}`} />
                  <div className="flex-1 min-w-0">
                    <p className={`text-[11px] leading-relaxed ${n.read ? 'text-slate-400' : 'text-slate-200'}`}>{n.message}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[9px] text-slate-500">
                        {formatDistanceToNow(new Date(n.timestamp), { addSuffix: true })}
                      </span>
                      <Badge variant={config.badge}>{n.severity}</Badge>
                    </div>
                  </div>
                  <div className="flex items-center gap-0.5">
                    {!n.read && (
                      <button onClick={() => markRead(n.id)} className="p-1 rounded hover:bg-white/10 text-slate-500 hover:text-cyan-400" title="Mark read">
                        <Check className="w-3 h-3" />
                      </button>
                    )}
                    <button onClick={() => remove(n.id)} className="p-1 rounded hover:bg-white/10 text-slate-500 hover:text-red-400" title="Delete">
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
