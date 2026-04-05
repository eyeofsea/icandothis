import { create } from 'zustand';
import { DisruptionEvent, ImpactAnalysis, SupplierRecommendation, RouteAlternative } from '@/lib/types';
import { fetchDisruptions } from '@/lib/api';

// ===== API-to-Frontend Mapper =====

function mapDisruption(raw: Record<string, unknown>): DisruptionEvent {
  const affectedZones = (raw.affectedZones as string[]) ?? [];
  const verificationStatus = (raw.verificationStatus as string) ?? '';
  const type = (raw.type as string) ?? 'geopolitical';
  const description = (raw.description as string) ?? '';
  const severity = (raw.severity as number) ?? 3;

  let status: DisruptionEvent['status'];
  if (verificationStatus === 'resolved') {
    status = 'resolved';
  } else if (verificationStatus === 'monitoring') {
    status = 'monitoring';
  } else {
    status = 'active';
  }

  return {
    id: (raw.eventId as string) ?? '',
    type: mapDisruptionType(type),
    name: description.length > 60 ? description.slice(0, 57) + '...' : description || type,
    description,
    severity: Math.min(5, Math.max(1, severity)) as 1 | 2 | 3 | 4 | 5,
    startDate: (raw.startDate as string) ?? new Date().toISOString(),
    endDate: (raw.endDate as string) ?? undefined,
    affectedZoneIds: affectedZones,
    affectedRouteIds: [],
    affectedEquipmentIds: [],
    affectedProjectIds: [],
    location: deriveLocationFromZones(affectedZones),
    radius: severity * 50,
    status,
  };
}

function mapDisruptionType(type: string): DisruptionEvent['type'] {
  const typeMap: Record<string, DisruptionEvent['type']> = {
    geopolitical: 'geopolitical',
    weather: 'natural',
    port_closure: 'infrastructure',
    sanctions: 'economic',
    labor_strike: 'economic',
    piracy: 'geopolitical',
    pandemic: 'natural',
    canal_blockage: 'infrastructure',
    infrastructure_failure: 'infrastructure',
    regulatory: 'economic',
    natural: 'natural',
    economic: 'economic',
    infrastructure: 'infrastructure',
    cyber: 'cyber',
  };
  return typeMap[type] ?? 'geopolitical';
}

const ZONE_LOCATIONS: Record<string, { lat: number; lng: number }> = {
  'zone-1': { lat: 26.5, lng: 56.0 },
  'zone-2': { lat: 30.5, lng: 32.5 },
  'zone-3': { lat: 13.5, lng: 42.5 },
  'zone-4': { lat: 15.0, lng: 114.0 },
  'zone-5': { lat: 3.0, lng: 101.0 },
};

function deriveLocationFromZones(zoneIds: string[]): { lat: number; lng: number } {
  if (zoneIds.length === 0) return { lat: 25, lng: 45 };
  const firstKnown = zoneIds.find((id) => ZONE_LOCATIONS[id]);
  if (firstKnown) return ZONE_LOCATIONS[firstKnown];
  return { lat: 25, lng: 45 };
}

// ===== Mock Disruptions (fallback when API unavailable) =====

const MOCK_DISRUPTIONS: DisruptionEvent[] = [
  {
    id: 'DIS-001',
    type: 'geopolitical',
    name: 'Strait of Hormuz Tension',
    description: 'Military escalation near Strait of Hormuz threatens maritime traffic. Iran-US tensions causing shipping delays and rerouting.',
    severity: 5,
    startDate: '2026-03-15T00:00:00Z',
    affectedZoneIds: ['zone-1'],
    affectedRouteIds: ['route-001', 'route-003'],
    affectedEquipmentIds: ['eq-001', 'eq-002', 'eq-005', 'eq-008'],
    affectedProjectIds: ['proj-001', 'proj-002'],
    location: { lat: 26.5, lng: 56.0 },
    radius: 250,
    status: 'active',
  },
  {
    id: 'DIS-002',
    type: 'infrastructure',
    name: 'Suez Canal Obstruction',
    description: 'Container vessel grounded in Suez Canal blocking northbound traffic. Estimated 7-14 day clearance.',
    severity: 4,
    startDate: '2026-03-28T00:00:00Z',
    affectedZoneIds: ['zone-2'],
    affectedRouteIds: ['route-002', 'route-004'],
    affectedEquipmentIds: ['eq-003', 'eq-004', 'eq-006'],
    affectedProjectIds: ['proj-001', 'proj-003'],
    location: { lat: 30.5, lng: 32.5 },
    radius: 200,
    status: 'active',
  },
  {
    id: 'DIS-003',
    type: 'natural',
    name: 'Japan Earthquake — Port Damage',
    description: 'Magnitude 7.2 earthquake damaged Yokohama port infrastructure. Crane and berth capacity reduced by 60%.',
    severity: 4,
    startDate: '2026-04-01T00:00:00Z',
    affectedZoneIds: ['zone-4'],
    affectedRouteIds: ['route-005'],
    affectedEquipmentIds: ['eq-007', 'eq-009', 'eq-010'],
    affectedProjectIds: ['proj-002'],
    location: { lat: 35.4, lng: 139.6 },
    radius: 150,
    status: 'active',
  },
  {
    id: 'DIS-004',
    type: 'economic',
    name: 'China Tariff Escalation',
    description: 'New 25% tariff on industrial equipment exports from China. Affects rotating and static equipment categories.',
    severity: 3,
    startDate: '2026-03-01T00:00:00Z',
    affectedZoneIds: ['zone-4'],
    affectedRouteIds: ['route-006'],
    affectedEquipmentIds: ['eq-011', 'eq-012'],
    affectedProjectIds: ['proj-001', 'proj-003'],
    location: { lat: 31.2, lng: 121.5 },
    radius: 300,
    status: 'monitoring',
  },
  {
    id: 'DIS-005',
    type: 'geopolitical',
    name: 'Russia Sanctions — Steel Supply',
    description: 'Expanded sanctions on Russian steel exports. Major supplier Severstal blocked from fulfilling orders.',
    severity: 3,
    startDate: '2026-02-15T00:00:00Z',
    affectedZoneIds: ['zone-5'],
    affectedRouteIds: ['route-007'],
    affectedEquipmentIds: ['eq-013', 'eq-014'],
    affectedProjectIds: ['proj-002'],
    location: { lat: 59.9, lng: 30.3 },
    radius: 200,
    status: 'active',
  },
];

// ===== Store =====

interface DisruptionState {
  activeDisruptions: DisruptionEvent[];
  affectedEquipmentIds: string[];
  affectedRouteIds: string[];
  impactAnalysis: ImpactAnalysis | null;
  recommendations: SupplierRecommendation[];
  routeAlternatives: RouteAlternative[];
  loading: boolean;
  error: string | null;
  addDisruption: (d: DisruptionEvent) => void;
  removeDisruption: (id: string) => void;
  setImpactAnalysis: (analysis: ImpactAnalysis | null) => void;
  setRecommendations: (recs: SupplierRecommendation[]) => void;
  setRouteAlternatives: (alts: RouteAlternative[]) => void;
  clearDisruptions: () => void;
  fetchDisruptions: () => Promise<void>;
}

let fetchInitiated = false;

export const useDisruptionStore = create<DisruptionState>((set, get) => ({
  activeDisruptions: MOCK_DISRUPTIONS,
  affectedEquipmentIds: [],
  affectedRouteIds: [],
  impactAnalysis: null,
  recommendations: [],
  routeAlternatives: [],
  loading: false,
  error: null,
  addDisruption: (d) =>
    set((state) => ({
      activeDisruptions: [...state.activeDisruptions, d],
      affectedEquipmentIds: Array.from(
        new Set([...state.affectedEquipmentIds, ...d.affectedEquipmentIds])
      ),
      affectedRouteIds: Array.from(
        new Set([...state.affectedRouteIds, ...d.affectedRouteIds])
      ),
    })),
  removeDisruption: (id) =>
    set((state) => ({
      activeDisruptions: state.activeDisruptions.filter((d) => d.id !== id),
    })),
  setImpactAnalysis: (analysis) => set({ impactAnalysis: analysis }),
  setRecommendations: (recs) => set({ recommendations: recs }),
  setRouteAlternatives: (alts) => set({ routeAlternatives: alts }),
  clearDisruptions: () =>
    set({
      activeDisruptions: [],
      affectedEquipmentIds: [],
      affectedRouteIds: [],
      impactAnalysis: null,
      recommendations: [],
      routeAlternatives: [],
    }),
  fetchDisruptions: async () => {
    if (get().loading) return;
    set({ loading: true, error: null });

    try {
      const rawDisruptions = await fetchDisruptions();
      const mapped = (rawDisruptions as unknown as Record<string, unknown>[]).map(mapDisruption);
      const active = mapped.filter((d) => d.status === 'active' || d.status === 'monitoring');

      const allEquipmentIds = Array.from(
        new Set(active.flatMap((d) => d.affectedEquipmentIds))
      );
      const allRouteIds = Array.from(
        new Set(active.flatMap((d) => d.affectedRouteIds))
      );

      set({
        activeDisruptions: active,
        affectedEquipmentIds: allEquipmentIds,
        affectedRouteIds: allRouteIds,
        loading: false,
        error: null,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch disruptions';
      console.error('disruptionStore fetchDisruptions error:', message);
      // Keep mock disruptions as fallback when API is unavailable
      set({ loading: false, error: message });
    }
  },
}));

// Lazy initialization: trigger fetch on first access
const originalSubscribe = useDisruptionStore.subscribe;
useDisruptionStore.subscribe = (...args) => {
  if (!fetchInitiated) {
    fetchInitiated = true;
    useDisruptionStore.getState().fetchDisruptions();
  }
  return originalSubscribe(...args);
};

const originalGetState = useDisruptionStore.getState;
useDisruptionStore.getState = () => {
  if (!fetchInitiated) {
    fetchInitiated = true;
    const state = originalGetState();
    state.fetchDisruptions();
    return originalGetState();
  }
  return originalGetState();
};
