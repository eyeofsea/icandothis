import { create } from 'zustand';
import { NewsItem, ZoneRisk, FeedAgentStatus } from '@/lib/types';
import { fetchNewsFeed, fetchAllZoneRisks } from '@/lib/api';

const AGENT_NAMES = [
  'ImpactAgent',
  'SupplierAgent',
  'RouteAgent',
  'CostAgent',
  'NewsAgent',
  'DisruptionAgent',
];

interface FeedState {
  news: NewsItem[];
  zoneRisks: ZoneRisk[];
  agentStatuses: FeedAgentStatus[];
  loading: { news: boolean; risk: boolean };
  lastUpdated: { news: string | null; risk: string | null };

  fetchNews: (category?: string) => Promise<void>;
  fetchAllZoneRisks: () => Promise<void>;
  updateAgentStatus: (name: string, status: FeedAgentStatus['status'], task?: string, summary?: string) => void;
  resetAgentStatuses: () => void;
}

const defaultAgentStatuses: FeedAgentStatus[] = AGENT_NAMES.map((name) => ({
  name,
  status: 'idle' as const,
}));

export const useFeedStore = create<FeedState>((set, get) => ({
  news: [],
  zoneRisks: [],
  agentStatuses: [...defaultAgentStatuses],
  loading: { news: false, risk: false },
  lastUpdated: { news: null, risk: null },

  fetchNews: async (category?: string) => {
    set((s) => ({ loading: { ...s.loading, news: true } }));
    try {
      const items = await fetchNewsFeed(category);
      const existing = get().news;
      const existingIds = new Set(existing.map((n) => n.id));
      const merged = [...items.filter((n) => !existingIds.has(n.id)), ...existing].slice(0, 50);
      set({ news: merged, lastUpdated: { ...get().lastUpdated, news: new Date().toISOString() } });
    } catch {
      // keep existing data
    } finally {
      set((s) => ({ loading: { ...s.loading, news: false } }));
    }
  },

  fetchAllZoneRisks: async () => {
    set((s) => ({ loading: { ...s.loading, risk: true } }));
    try {
      const risks = await fetchAllZoneRisks();
      if (risks.length > 0) {
        set({ zoneRisks: risks, lastUpdated: { ...get().lastUpdated, risk: new Date().toISOString() } });
      }
    } catch {
      // keep existing data
    } finally {
      set((s) => ({ loading: { ...s.loading, risk: false } }));
    }
  },

  updateAgentStatus: (name, status, task?, summary?) => {
    set((s) => ({
      agentStatuses: s.agentStatuses.map((a) =>
        a.name === name
          ? { ...a, status, lastTask: task || a.lastTask, resultSummary: summary || a.resultSummary, lastRun: new Date().toISOString() }
          : a
      ),
    }));
  },

  resetAgentStatuses: () => {
    set({ agentStatuses: [...defaultAgentStatuses] });
  },
}));
