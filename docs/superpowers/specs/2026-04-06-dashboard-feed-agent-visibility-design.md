# Dashboard Feed Integration & Agent Visibility Design

## Problem

1. Backend API feeds (GDELT news, risk, freight, OFAC sanctions) are connected but frontend displays only mock data
2. No news article links — AlertFeed shows hardcoded alerts without source URLs
3. Claude AI agents (6 specialized + orchestrator) work behind the scenes with no visibility in the UI

## Solution: Incremental Integration (Approach A)

Add real-time data binding, new UI components, and agent status visibility while preserving existing dashboard structure.

---

## 1. Data Layer — feedStore

### New Zustand Store: `src/stores/feedStore.ts`

```typescript
interface FeedState {
  // News from GDELT
  news: NewsItem[];
  // Zone risk levels from GDELT
  zoneRisks: ZoneRisk[];
  // Agent statuses
  agentStatuses: AgentStatus[];
  // Loading flags
  loading: {
    news: boolean;
    risk: boolean;
    agents: boolean;
  };
  // Actions
  fetchNews: (category?: string) => Promise<void>;
  fetchAllZoneRisks: () => Promise<void>;
  fetchAgentStatuses: () => Promise<void>;
}

interface NewsItem {
  id: string;
  headline: string;
  source: string;
  url: string;          // original article URL
  publishedDate: string;
  location: string;
  tone: number;
  severity: number;     // 1-5
  type: string;         // maritime, geopolitical, weather, etc.
  zones: string[];      // matched zone IDs
  sourceType: string;   // "gdelt" or "fallback"
}

interface ZoneRisk {
  zone_id: string;
  zone_name: string;
  risk_level: number;   // 1-10
  trend: "stable" | "increasing" | "decreasing";
  active_threats: number;
  insurance_multiplier: number;
  article_count: number;
  source: string;       // "gdelt" or "simulated"
  top_headlines: { title: string; url: string; tone: number; date: string }[];
}

interface AgentStatus {
  name: string;
  status: "idle" | "analyzing" | "completed" | "error";
  lastRun?: string;     // ISO timestamp
  lastTask?: string;    // brief description
  resultSummary?: string;
}
```

### API Functions: additions to `src/lib/api.ts`

```typescript
fetchNewsFeed(category?: string): Promise<NewsItem[]>
  // GET /api/feeds/news/scan?category={category}
  // Maps response.eventCandidate to NewsItem

fetchAllZoneRisks(): Promise<ZoneRisk[]>
  // GET /api/feeds/risk/zones

fetchFreightRate(origin, dest, weight): Promise<FreightRate>
  // GET /api/feeds/freight/rate?origin=...&destination=...&weight_kg=...

screenSanctions(name, country): Promise<SanctionResult>
  // GET /api/feeds/sanctions/screen?name=...&country=...
```

### Auto-refresh Intervals

| Feed | Interval | Rationale |
|------|----------|-----------|
| News | 60s | GDELT rate limit (1 req/5s), balance freshness vs cost |
| Zone Risks | 60s | Same GDELT source, cache-friendly |
| Agent Status | On chat response | Updated when agents actually run |

---

## 2. Dashboard Changes — DashboardView

### KPI Cards — Mock to Real

Replace mock values in existing KPICards component with data from feedStore and API:

| Card | Current (mock) | After (real) |
|------|----------------|-------------|
| Portfolio Value | Hardcoded | `fetchDashboardKPIs().totalPortfolioValue` |
| At-Risk Assets | Hardcoded | `fetchDashboardKPIs().equipmentAtRisk` |
| Active Disruptions | Hardcoded | `disruptionStore.activeDisruptions.length` |
| Network Risk | Hardcoded | Average of `feedStore.zoneRisks[].risk_level` |
| Active Agents | N/A (new) | `feedStore.agentStatuses.filter(a => a.status !== 'idle').length` / 6 |

### New Component: IntelligenceFeed

Position: Below KPI cards, left column (beside Agent Activity panel).

Combines news, risk alerts, and freight updates in a single time-sorted feed.

Each item shows:
- Severity badge (color-coded)
- Category tag (maritime, geopolitical, sanctions, freight)
- Headline text
- Source + timestamp
- **"기사 보기 ↗" button** — opens `item.url` in new tab (`target="_blank"`)
- Matched zones (if any)

Items sourced from:
- `feedStore.news` — GDELT articles
- `feedStore.zoneRisks` where `risk_level >= 7` — high-risk zone alerts

Max display: 10 items, scrollable. "더 보기" link navigates to News view.

### New Component: AgentActivityPanel

Position: Below KPI cards, right column (beside Intelligence Feed).

Shows 6 agent cards in a compact grid:

```
┌─────────────────────┐
│ ● ImpactAgent  idle │
│ ● SupplierAgent idle│
│ ● RouteAgent   idle │
│ ● CostAgent    idle │
│ ● NewsAgent    done │
│   "5 articles found"│
│ ● DisruptionAgent   │
│   idle              │
└─────────────────────┘
```

Status dot colors:
- Green (idle) — ready
- Orange pulse (analyzing) — currently working
- Blue (completed) — finished, shows result summary
- Red (error) — failed, shows error message

---

## 3. AlertFeed Changes

### Replace Mock with Real Data

Current: 8 hardcoded MOCK_ALERTS array.

After: Fetch from `feedStore.news` + `disruptionStore.activeDisruptions`.

### Add Article Link Button

Each alert card gets:
- Existing: severity badge, message, timestamp
- **New:** "기사 보기 ↗" button (only when `item.url` exists)
- **New:** source attribution text (e.g., "via GDELT · globaltimes.cn")

```tsx
{item.url && (
  <a href={item.url} target="_blank" rel="noopener noreferrer"
     className="text-xs text-blue-400 hover:text-blue-300">
    기사 보기 ↗
  </a>
)}
```

---

## 4. TopBar Agent Status

### Agent Status Indicator in Header

Add to existing TopBar component, between Scenario selector and notification bell:

```
│ 🤖 2/6 active │ ImpactAgent 분석중... │
```

- Shows count: active agents / total agents
- Shows current working agent name + task (scrolling if multiple)
- Green dot when all idle, orange pulse when any active
- Click → scrolls to Agent Activity panel on dashboard

Data source: `feedStore.agentStatuses`

---

## 5. News & Intelligence View

### New View: NewsView.tsx

Added to Sidebar navigation below "Alerts".

### Layout

**Top: Filter Bar**
- Category dropdown: All / Maritime / Geopolitical / Weather / Labor / Canal
- Severity filter: All / >= 3 / >= 4
- Refresh button

**Middle: News Cards List**

Each card shows:
- Severity badge (1-5, color-coded)
- Category tag
- Headline (bold)
- Source domain + published date + tone score
- Matched zones list
- Two action buttons:
  - "기사 보기 ↗" — opens original article URL in new tab
  - "영향 분석 →" — navigates to ImpactView with zone context

**Bottom: Zone Risk Summary**

Horizontal bar chart for all 5 zones:
- Zone name + risk level number
- Filled bar (colored by risk: green < 4, yellow 4-7, red > 7)
- Trend arrow (↑ increasing, → stable, ↓ decreasing)
- Data from `feedStore.zoneRisks`

### Navigation

Add to Sidebar.tsx nav items array:
```typescript
{ id: "news", label: "News", icon: Newspaper }
```

Add to page.tsx view switch:
```typescript
case "news": return <NewsView />;
```

---

## 6. Files to Create/Modify

### New Files
| File | Purpose |
|------|---------|
| `src/stores/feedStore.ts` | Zustand store for feeds + agent status |
| `src/components/dashboard/IntelligenceFeed.tsx` | Real-time intelligence feed |
| `src/components/dashboard/AgentActivityPanel.tsx` | Agent status grid |
| `src/views/NewsView.tsx` | Full news & intelligence view |

### Modified Files
| File | Change |
|------|--------|
| `src/lib/api.ts` | Add fetchNewsFeed, fetchAllZoneRisks functions |
| `src/lib/types.ts` | Add NewsItem, ZoneRisk, AgentStatus interfaces |
| `src/components/dashboard/AlertFeed.tsx` | Mock → real data, add article link buttons |
| `src/components/dashboard/KPICards.tsx` | Mock → real API data |
| `src/components/layout/TopBar.tsx` | Add agent status indicator |
| `src/components/layout/Sidebar.tsx` | Add "News" nav item |
| `src/views/DashboardView.tsx` | Add IntelligenceFeed + AgentActivityPanel |
| `src/app/page.tsx` | Add NewsView to view switch |
| `src/hooks/useAgentChat.ts` | Emit agent status updates to feedStore |

---

## 7. Agent Status Flow

```
User sends chat message
  → useAgentChat calls POST /api/agents/chat
  → Backend Orchestrator routes to agents
  → Response includes agent metadata
  → useAgentChat extracts agent status
  → feedStore.agentStatuses updated
  → TopBar + AgentActivityPanel re-render
```

Agent status is derived from chat responses, not a separate polling endpoint. When the orchestrator responds, it includes which agents were invoked and their results. The frontend maps this to the AgentStatus interface.

---

## 8. Fallback Behavior

All feed components gracefully handle API failures:
- Show "데이터 로딩 중..." skeleton during fetch
- On error, show last cached data + "오프라인" badge
- If no cached data, show "실시간 데이터를 불러올 수 없습니다" message
- Never crash — always render something
