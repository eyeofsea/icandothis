'use client';

import { useEffect, useState } from 'react';
import {
  Newspaper,
  ExternalLink,
  RefreshCw,
  ArrowUpRight,
  ArrowRight,
  ArrowDownRight,
  Filter,
} from 'lucide-react';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import { useFeedStore } from '@/stores/feedStore';

const CATEGORIES = [
  { value: 'all', label: 'All Categories' },
  { value: 'maritime', label: 'Maritime' },
  { value: 'geopolitical', label: 'Geopolitical' },
  { value: 'weather', label: 'Weather' },
  { value: 'labor', label: 'Labor' },
  { value: 'canal', label: 'Canal' },
] as const;

const SEVERITY_OPTIONS = [
  { value: 'all', label: 'All Severity' },
  { value: '3', label: 'Severity >= 3' },
  { value: '4', label: 'Severity >= 4' },
] as const;

function severityColor(severity: number): string {
  if (severity >= 4) return 'bg-rose-500/20 text-rose-400 border-rose-500/30';
  if (severity >= 3) return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
  if (severity >= 2) return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
  return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
}

function typeColor(type: string): string {
  const map: Record<string, string> = {
    maritime: 'bg-sky-500/20 text-sky-400',
    geopolitical: 'bg-purple-500/20 text-purple-400',
    weather: 'bg-emerald-500/20 text-emerald-400',
    labor: 'bg-orange-500/20 text-orange-400',
    canal: 'bg-cyan-500/20 text-cyan-400',
  };
  return map[type] || 'bg-slate-500/20 text-slate-400';
}

function trendIcon(trend: string) {
  switch (trend) {
    case 'increasing':
      return <ArrowUpRight className="w-3.5 h-3.5 text-rose-400" />;
    case 'decreasing':
      return <ArrowDownRight className="w-3.5 h-3.5 text-emerald-400" />;
    default:
      return <ArrowRight className="w-3.5 h-3.5 text-slate-400" />;
  }
}

function trendText(trend: string) {
  switch (trend) {
    case 'increasing':
      return <span className="text-rose-400">Increasing</span>;
    case 'decreasing':
      return <span className="text-emerald-400">Decreasing</span>;
    default:
      return <span className="text-slate-400">Stable</span>;
  }
}

function riskBarColor(level: number): string {
  if (level >= 7) return 'bg-rose-500';
  if (level >= 4) return 'bg-amber-500';
  return 'bg-emerald-500';
}

export default function NewsView() {
  const [category, setCategory] = useState('all');
  const [severityFilter, setSeverityFilter] = useState('all');
  const { news, zoneRisks, loading, fetchNews, fetchAllZoneRisks } = useFeedStore();

  useEffect(() => {
    const cat = category === 'all' ? undefined : category;
    fetchNews(cat);
    fetchAllZoneRisks();
  }, [category, fetchNews, fetchAllZoneRisks]);

  const filteredNews = news.filter((item) => {
    if (severityFilter !== 'all') {
      const minSev = parseInt(severityFilter, 10);
      if (item.severity < minSev) return false;
    }
    return true;
  });

  const handleRefresh = () => {
    const cat = category === 'all' ? undefined : category;
    fetchNews(cat);
    fetchAllZoneRisks();
  };

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-sky-500/10 flex items-center justify-center border border-sky-400/20">
            <Newspaper className="w-5 h-5 text-sky-400" />
          </div>
          <div>
            <h2 className="text-xl font-black text-white tracking-tight uppercase">
              News & Intelligence
            </h2>
            <p className="text-[11px] text-slate-500 font-bold uppercase tracking-wider mt-0.5">
              GDELT-powered global risk monitoring
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 px-1 py-1 rounded-lg bg-slate-900/50 border border-slate-800">
            <Filter className="w-3.5 h-3.5 text-slate-500 ml-2" />
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="bg-transparent text-xs text-slate-300 border-none outline-none cursor-pointer px-1 py-1"
            >
              {CATEGORIES.map((c) => (
                <option key={c.value} value={c.value} className="bg-slate-900">
                  {c.label}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1 px-1 py-1 rounded-lg bg-slate-900/50 border border-slate-800">
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-transparent text-xs text-slate-300 border-none outline-none cursor-pointer px-2 py-1"
            >
              {SEVERITY_OPTIONS.map((s) => (
                <option key={s.value} value={s.value} className="bg-slate-900">
                  {s.label}
                </option>
              ))}
            </select>
          </div>

          <Button
            variant="primary"
            size="sm"
            icon={RefreshCw}
            loading={loading.news}
            onClick={handleRefresh}
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* News Cards */}
      <div className="space-y-3">
        {filteredNews.length === 0 && !loading.news && (
          <Card className="py-12 text-center">
            <p className="text-slate-500 text-sm">No articles match the current filters.</p>
          </Card>
        )}
        {filteredNews.map((item) => (
          <Card key={item.id} padding="sm" className="hover:border-slate-600/50 transition-colors">
            <div className="flex flex-col gap-2 p-2">
              <div className="flex items-start gap-3">
                {/* Severity badge */}
                <div
                  className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center text-xs font-black border ${severityColor(item.severity)}`}
                >
                  {item.severity}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${typeColor(item.type)}`}
                    >
                      {item.type}
                    </span>
                  </div>

                  <h4 className="text-sm font-semibold text-slate-100 leading-snug line-clamp-2">
                    {item.headline}
                  </h4>

                  <div className="flex items-center gap-3 mt-1.5 text-[11px] text-slate-500">
                    <span>{item.source}</span>
                    <span className="text-slate-700">|</span>
                    <span>{new Date(item.publishedDate).toLocaleDateString()}</span>
                    <span className="text-slate-700">|</span>
                    <span>
                      Tone:{' '}
                      <span
                        className={
                          item.tone < -2
                            ? 'text-rose-400'
                            : item.tone > 2
                              ? 'text-emerald-400'
                              : 'text-slate-400'
                        }
                      >
                        {item.tone > 0 ? '+' : ''}
                        {item.tone.toFixed(1)}
                      </span>
                    </span>
                  </div>

                  {item.zones.length > 0 && (
                    <div className="flex items-center gap-1.5 mt-2">
                      {item.zones.map((zone) => (
                        <span
                          key={zone}
                          className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-800 text-slate-400 border border-slate-700/50"
                        >
                          {zone}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Action links */}
                <div className="flex flex-col gap-1.5 flex-shrink-0">
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 px-2.5 py-1 rounded-md text-[10px] font-bold text-sky-400 bg-sky-500/10 border border-sky-500/20 hover:bg-sky-500/20 transition-colors"
                  >
                    <ExternalLink className="w-3 h-3" />
                    View Article
                  </a>
                  <button className="flex items-center gap-1 px-2.5 py-1 rounded-md text-[10px] font-bold text-amber-400 bg-amber-500/10 border border-amber-500/20 hover:bg-amber-500/20 transition-colors">
                    <ArrowRight className="w-3 h-3" />
                    Impact Analysis
                  </button>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Zone Risk Summary */}
      {zoneRisks.length > 0 && (
        <Card title="Zone Risk Summary" subtitle="Top Risk Zones" padding="md">
          <div className="space-y-4 mt-2">
            {zoneRisks.slice(0, 5).map((zone) => (
              <div key={zone.zone_id} className="flex items-center gap-4">
                <span className="text-xs text-slate-300 font-medium w-40 truncate">
                  {zone.zone_name}
                </span>
                <div className="flex-1 h-3 rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${riskBarColor(zone.risk_level)}`}
                    style={{ width: `${Math.min(zone.risk_level * 10, 100)}%` }}
                  />
                </div>
                <span className="text-xs font-bold text-slate-200 w-8 text-right">
                  {zone.risk_level.toFixed(1)}
                </span>
                <div className="flex items-center gap-1 w-24">
                  {trendIcon(zone.trend)}
                  <span className="text-[10px] font-medium">{trendText(zone.trend)}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
