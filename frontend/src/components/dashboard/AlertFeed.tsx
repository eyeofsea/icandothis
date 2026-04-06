'use client';

import { useEffect, useRef } from 'react';
import { AlertTriangle, Info, AlertCircle, Bell, Zap, ExternalLink } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { useFeedStore } from '@/stores/feedStore';
import { useDisruptionStore } from '@/stores/disruptionStore';
import { cn } from '@/lib/utils';
import { NewsItem } from '@/lib/types';

type AlertSeverity = 'info' | 'warning' | 'critical';

interface AlertItem {
  id: string;
  severity: AlertSeverity;
  message: string;
  timestamp: string;
  source: string;
  url?: string;
}

const severityConfig = {
  info: { icon: Info, color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20' },
  warning: { icon: AlertTriangle, color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20' },
  critical: { icon: AlertCircle, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20' },
};

function mapNewsSeverity(severity: number): AlertSeverity {
  if (severity >= 5) return 'critical';
  if (severity >= 3) return 'warning';
  return 'info';
}

function newsToAlert(item: NewsItem): AlertItem {
  return {
    id: `news-${item.id}`,
    severity: mapNewsSeverity(item.severity),
    message: item.headline,
    timestamp: item.publishedDate,
    source: item.source,
    url: item.url || undefined,
  };
}

const MAX_ITEMS = 12;

export default function AlertFeed() {
  const scrollRef = useRef<HTMLDivElement>(null);
  const news = useFeedStore((s) => s.news);
  const fetchNews = useFeedStore((s) => s.fetchNews);
  const activeDisruptions = useDisruptionStore((s) => s.activeDisruptions);

  useEffect(() => {
    fetchNews();
  }, [fetchNews]);

  const newsAlerts: AlertItem[] = news.map(newsToAlert);

  const disruptionAlerts: AlertItem[] = activeDisruptions.map((d) => ({
    id: `disruption-${d.id}`,
    severity: mapNewsSeverity(d.severity),
    message: d.description,
    timestamp: d.startDate,
    source: 'Disruption Monitor',
  }));

  const allAlerts = [...newsAlerts, ...disruptionAlerts]
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, MAX_ITEMS);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 mb-2">
        <Bell className="w-3.5 h-3.5 text-slate-400" />
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Live Feed</span>
        <span className="ml-auto text-[9px] text-slate-500">{allAlerts.length} alerts</span>
      </div>
      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-1.5">
        {allAlerts.map((alert) => {
          const config = severityConfig[alert.severity];
          const Icon = config.icon;
          return (
            <div
              key={alert.id}
              className={cn(
                'flex items-start gap-2 p-2 rounded-md border',
                config.bg,
                config.border,
                alert.severity === 'critical' && 'animate-pulse-alert',
              )}
            >
              <Icon className={cn('w-3.5 h-3.5 flex-shrink-0 mt-0.5', config.color)} />
              <div className="flex-1 min-w-0">
                <p className="text-[11px] text-slate-300 leading-tight">{alert.message}</p>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-[9px] text-slate-500">
                    {formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true })}
                  </span>
                  <span className="text-[9px] text-slate-600">{alert.source}</span>
                </div>
                {alert.url && (
                  <a
                    href={alert.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 mt-1 text-[10px] text-sky-400 hover:text-sky-300 transition-colors"
                  >
                    기사 보기
                    <ExternalLink className="w-2.5 h-2.5" />
                  </a>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
