export const MAP_CONFIG = {
  center: [25, 45] as [number, number],
  zoom: 3,
  minZoom: 2,
  maxZoom: 18,
  tileUrl: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
  tileAttribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>',
};

export const RISK_COLORS = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
};

export const CRITICALITY_COLORS: Record<string, string> = {
  Critical: '#ef4444',
  High: '#f97316',
  Medium: '#eab308',
  Low: '#22c55e',
};

export const CATEGORY_COLORS: Record<string, string> = {
  rotating: '#3b82f6',
  static: '#22c55e',
  electrical: '#eab308',
  instrumentation: '#a855f7',
  piping: '#f97316',
  valves: '#ef4444',
};

export const STATUS_COLORS: Record<string, string> = {
  'on-track': '#22c55e',
  'at-risk': '#eab308',
  delayed: '#f97316',
  critical: '#ef4444',
  active: '#22c55e',
  disrupted: '#ef4444',
  blocked: '#991b1b',
  alternative: '#3b82f6',
  operational: '#22c55e',
  congested: '#eab308',
  limited: '#f97316',
  closed: '#ef4444',
};

export const ROUTE_COLORS = {
  active: '#22c55e',
  disrupted: '#ef4444',
  blocked: '#7f1d1d',
  alternative: '#3b82f6',
};

export const ZONE_RISK_COLORS = {
  low: 'rgba(34,197,94,0.15)',
  medium: 'rgba(234,179,8,0.2)',
  high: 'rgba(249,115,22,0.25)',
  critical: 'rgba(239,68,68,0.3)',
};

export const NODE_COLORS: Record<string, string> = {
  project: '#3b82f6',
  equipment: '#f97316',
  supplier: '#22c55e',
  route: '#a855f7',
  zone: '#ef4444',
  disruption: '#dc2626',
  port: '#06b6d4',
};
