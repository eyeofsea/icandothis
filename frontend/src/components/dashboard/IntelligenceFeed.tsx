'use client';

import { useEffect, useRef } from 'react';
import {
  ExternalLink,
  AlertTriangle,
  Newspaper,
  TrendingUp,
  Shield,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { useFeedStore } from '@/stores/feedStore';
import { cn } from '@/lib/utils';

interface FeedItem {
  id: string;
  headline: string;
  source: string;
  url: string;
  timestamp: string;
  severity: number;
  category: 'news' | 'zone-alert';
  type: string;
}

const SEVERITY_STYLES: Record<number, { bg: string; border: string; text: string }> = {
  1: { bg: 'bg-slate-500/10', border: 'border-slate-500/20', text: 'text-slate-400' },
  2: { bg: 'bg-blue-500/10', border: 'border-blue-500/20', text: 'text-blue-400' },
  3: { bg: 'bg-yellow-500/10', border: 'border-yellow-500/20', text: 'text-yellow-400' },
  4: { bg: 'bg-orange-500/10', border: 'border-orange-500/20', text: 'text-orange-400' },
  5: { bg: 'bg-red-500/10', border: 'border-red-500/20', text: 'text-red-400' },
};

const CATEGORY_ICONS: Record<string, typeof Newspaper> = {
  news: Newspaper,
  geopolitical: AlertTriangle,
  economic: TrendingUp,
  security: Shield,
  'zone-alert': AlertTriangle,
};

function getSeverityStyle(severity: number) {
  const clamped = Math.max(1, Math.min(5, Math.round(severity)));
  return SEVERITY_STYLES[clamped];
}

function getCategoryIcon(type: string, category: string) {
  return CATEGORY_ICONS[type] ?? CATEGORY_ICONS[category] ?? Newspaper;
}

function SeverityBadge({ severity }: { severity: number }) {
  const style = getSeverityStyle(severity);
  return (
    <span
      className={cn(
        'inline-flex items-center justify-center rounded px-1.5 py-0.5 text-xs font-semibold border',
        style.bg,
        style.border,
        style.text,
      )}
    >
      {severity}
    </span>
  );
}

function LoadingIndicator() {
  return (
    <div className="flex items-center justify-center py-8">
      <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-600 border-t-blue-400" />
      <span className="ml-2 text-sm text-slate-400">피드 로딩 중...</span>
    </div>
  );
}

export default function IntelligenceFeed() {
  const { news, zoneRisks, loading, fetchNews, fetchAllZoneRisks } = useFeedStore();
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    fetchNews();
    fetchAllZoneRisks();

    intervalRef.current = setInterval(() => {
      fetchNews();
      fetchAllZoneRisks();
    }, 60_000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchNews, fetchAllZoneRisks]);

  const isLoading = loading.news && loading.risk && news.length === 0 && zoneRisks.length === 0;

  const newsItems: FeedItem[] = news.map((item) => ({
    id: item.id,
    headline: item.headline,
    source: item.source,
    url: item.url,
    timestamp: item.publishedDate,
    severity: item.severity,
    category: 'news' as const,
    type: item.type,
  }));

  const zoneAlertItems: FeedItem[] = zoneRisks
    .filter((zone) => zone.risk_level >= 7)
    .map((zone) => ({
      id: `zone-${zone.zone_id}`,
      headline: `${zone.zone_name} - 위험 수준 ${zone.risk_level}/10 (활성 위협 ${zone.active_threats}건)`,
      source: zone.source || 'Risk Monitor',
      url: zone.top_headlines?.[0]?.url ?? '',
      timestamp: zone.top_headlines?.[0]?.date ?? '',
      severity: Math.min(5, Math.ceil(zone.risk_level / 2)),
      category: 'zone-alert' as const,
      type: 'zone-alert',
    }));

  const feedItems = [...newsItems, ...zoneAlertItems]
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, 10);

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-white">Intelligence Feed</h2>
        {(loading.news || loading.risk) && (
          <div className="h-2 w-2 animate-pulse rounded-full bg-blue-400" />
        )}
      </div>

      {isLoading ? (
        <LoadingIndicator />
      ) : (
        <div className="max-h-[480px] space-y-2 overflow-y-auto pr-1">
          {feedItems.length === 0 ? (
            <p className="py-4 text-center text-sm text-slate-500">피드 항목이 없습니다</p>
          ) : (
            feedItems.map((item) => {
              const Icon = getCategoryIcon(item.type, item.category);
              const timeAgo = formatTimeAgo(item.timestamp);

              return (
                <div
                  key={item.id}
                  className={cn(
                    'group flex items-start gap-3 rounded-lg border border-slate-800/60 bg-slate-900/50 px-3 py-2.5 transition-colors hover:border-slate-700 hover:bg-slate-900',
                  )}
                >
                  <Icon className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" />

                  <div className="min-w-0 flex-1">
                    <div className="flex items-start gap-2">
                      <SeverityBadge severity={item.severity} />
                      <p className="text-sm leading-snug text-slate-200 line-clamp-2">
                        {item.headline}
                      </p>
                    </div>

                    <div className="mt-1.5 flex items-center gap-2 text-xs text-slate-500">
                      <span>{item.source}</span>
                      <span>·</span>
                      <span>{timeAgo}</span>
                    </div>
                  </div>

                  {item.url && (
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-0.5 flex shrink-0 items-center gap-1 rounded px-2 py-1 text-xs text-slate-400 transition-colors hover:bg-slate-800 hover:text-blue-400"
                    >
                      기사 보기
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}

function formatTimeAgo(dateString: string): string {
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      return '';
    }
    return formatDistanceToNow(date, { addSuffix: true });
  } catch {
    return '';
  }
}
