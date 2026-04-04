import { create } from 'zustand';
import {
  Project, Equipment, Supplier, ShippingRoute, GeopoliticalZone, Port,
} from '@/lib/types';
import {
  fetchProjects, fetchEquipment, fetchSuppliers, fetchRoutes,
} from '@/lib/api';

// ===== API-to-Frontend Mappers =====

function mapProject(raw: Record<string, unknown>): Project {
  const coords = raw.coordinates as { lat: number; lng: number } | null;
  return {
    id: (raw.projectId as string) ?? '',
    name: (raw.name as string) ?? '',
    client: (raw.client as string) ?? '',
    value: (raw.totalValue as number) ?? 0,
    completionPercent: (raw.completionPct as number) ?? 0,
    status: mapProjectStatus(raw.status as string),
    location: coords ?? { lat: 0, lng: 0 },
    country: (raw.country as string) ?? '',
    equipmentIds: (raw.equipmentIds as string[]) ?? [],
    startDate: (raw.criticalPathDeadline as string) ?? '',
    endDate: (raw.criticalPathDeadline as string) ?? '',
  };
}

function mapProjectStatus(status: string | undefined): Project['status'] {
  const normalized = (status ?? '').toLowerCase().replace(/[_\s]/g, '-');
  if (['on-track', 'at-risk', 'delayed', 'critical'].includes(normalized)) {
    return normalized as Project['status'];
  }
  return 'on-track';
}

function mapEquipment(raw: Record<string, unknown>): Equipment {
  const supplier = raw.supplier as { supplierId?: string } | null;
  const route = raw.route as { routeId?: string } | null;
  const project = raw.project as { projectId?: string } | null;
  return {
    id: (raw.equipmentId as string) ?? '',
    name: (raw.name as string) ?? '',
    type: (raw.category as string) ?? '',
    category: mapEquipmentCategory(raw.category as string),
    criticality: mapCriticality(raw.criticality as string),
    projectId: project?.projectId ?? '',
    supplierId: supplier?.supplierId ?? '',
    routeId: route?.routeId ?? '',
    value: 0,
    weight: (raw.weight as number) ?? 0,
    status: 'ordered',
    riskScore: 0,
    deliveryDate: (raw.requiredOnSiteDate as string) ?? '',
    leadTimeDays: 0,
  };
}

function mapEquipmentCategory(cat: string | undefined): Equipment['category'] {
  const valid: Equipment['category'][] = ['rotating', 'static', 'electrical', 'instrumentation', 'piping', 'valves'];
  const normalized = (cat ?? '').toLowerCase();
  if (valid.includes(normalized as Equipment['category'])) {
    return normalized as Equipment['category'];
  }
  return 'static';
}

function mapCriticality(crit: string | undefined): Equipment['criticality'] {
  const normalized = (crit ?? '').toLowerCase();
  if (normalized === 'critical') return 'Critical';
  if (normalized === 'high') return 'High';
  if (normalized === 'medium') return 'Medium';
  if (normalized === 'low') return 'Low';
  return 'Medium';
}

function mapSupplier(raw: Record<string, unknown>): Supplier {
  const capabilities = (raw.capabilities as string[]) ?? [];
  const firstCap = capabilities[0]?.toLowerCase() ?? '';
  return {
    id: (raw.supplierId as string) ?? '',
    name: (raw.name as string) ?? '',
    country: (raw.country as string) ?? '',
    location: { lat: 0, lng: 0 },
    category: mapEquipmentCategory(firstCap),
    capacity: Math.round(((raw.capacityUtilization as number) ?? 0) * 100) || 0,
    qualityScore: Math.round(((raw.qualityRate as number) ?? 0) * 100) || 0,
    onTimeDelivery: Math.round(((raw.deliveryRate as number) ?? 0) * 100) || 0,
    certifications: (raw.certifications as string[]) ?? [],
    riskScore: ((raw.riskFlags as string[]) ?? []).length * 15,
    activeOrders: 0,
    leadTimeDays: (raw.leadTimeDays as number) ?? 0,
  };
}

function mapRoute(raw: Record<string, unknown>): ShippingRoute {
  const waypoints = (raw.waypoints as Array<{ lat?: number; lng?: number; name?: string }>) ?? [];
  const originWp = waypoints[0];
  const destWp = waypoints[waypoints.length - 1];
  return {
    id: (raw.routeId as string) ?? '',
    name: (raw.name as string) ?? '',
    origin: {
      lat: originWp?.lat ?? 0,
      lng: originWp?.lng ?? 0,
      port: originWp?.name ?? '',
    },
    destination: {
      lat: destWp?.lat ?? 0,
      lng: destWp?.lng ?? 0,
      port: destWp?.name ?? '',
    },
    waypoints: waypoints.map((wp) => ({ lat: wp.lat ?? 0, lng: wp.lng ?? 0 })),
    distanceNm: (raw.totalDistanceNm as number) ?? 0,
    transitDays: (raw.estimatedTransitDays as number) ?? 0,
    status: mapRouteStatus(raw.currentStatus as string),
    riskScore: 0,
    equipmentIds: [],
    costPerTon: (raw.shippingCost as number) ?? 0,
  };
}

function mapRouteStatus(status: string | undefined): ShippingRoute['status'] {
  const normalized = (status ?? '').toLowerCase();
  if (['active', 'disrupted', 'blocked', 'alternative'].includes(normalized)) {
    return normalized as ShippingRoute['status'];
  }
  if (normalized === 'delayed') return 'disrupted';
  return 'active';
}

// ===== Fallback Mock Data =====

const MOCK_PROJECTS: Project[] = [
  {
    id: 'proj-1', name: 'Jafurah Gas Processing', client: 'Saudi Aramco',
    value: 4_200_000_000, completionPercent: 62, status: 'on-track',
    location: { lat: 25.35, lng: 49.05 }, country: 'Saudi Arabia',
    equipmentIds: ['eq-1', 'eq-2', 'eq-3', 'eq-4'], startDate: '2024-01-15', endDate: '2027-06-30',
  },
  {
    id: 'proj-2', name: 'Hail & Ghasha Offshore', client: 'ADNOC',
    value: 3_800_000_000, completionPercent: 45, status: 'on-track',
    location: { lat: 24.45, lng: 53.0 }, country: 'UAE',
    equipmentIds: ['eq-5', 'eq-6', 'eq-7'], startDate: '2024-03-01', endDate: '2028-01-15',
  },
  {
    id: 'proj-3', name: 'Al-Zour LNG Terminal', client: 'KIPIC',
    value: 3_200_000_000, completionPercent: 78, status: 'at-risk',
    location: { lat: 28.73, lng: 48.42 }, country: 'Kuwait',
    equipmentIds: ['eq-8', 'eq-9', 'eq-10'], startDate: '2023-06-10', endDate: '2026-12-31',
  },
  {
    id: 'proj-4', name: 'Duqm Refinery', client: 'OQ',
    value: 3_600_000_000, completionPercent: 55, status: 'on-track',
    location: { lat: 19.66, lng: 57.7 }, country: 'Oman',
    equipmentIds: ['eq-11', 'eq-12'], startDate: '2024-02-20', endDate: '2027-09-01',
  },
  {
    id: 'proj-5', name: 'Ras Laffan Petrochemical', client: 'QatarEnergy',
    value: 2_800_000_000, completionPercent: 35, status: 'on-track',
    location: { lat: 25.93, lng: 51.54 }, country: 'Qatar',
    equipmentIds: ['eq-13', 'eq-14', 'eq-15'], startDate: '2024-09-01', endDate: '2028-06-30',
  },
];

const MOCK_EQUIPMENT: Equipment[] = [
  { id: 'eq-1', name: 'Gas Turbine Generator', type: 'Turbine', category: 'rotating', criticality: 'Critical', projectId: 'proj-1', supplierId: 'sup-1', routeId: 'rt-1', value: 45_000_000, weight: 180, status: 'in-transit', riskScore: 35, deliveryDate: '2026-08-15', currentPosition: { lat: 12.5, lng: 52.0 }, leadTimeDays: 365 },
  { id: 'eq-2', name: 'Main Air Compressor', type: 'Compressor', category: 'rotating', criticality: 'Critical', projectId: 'proj-1', supplierId: 'sup-2', routeId: 'rt-2', value: 28_000_000, weight: 95, status: 'manufacturing', riskScore: 42, deliveryDate: '2026-10-01', leadTimeDays: 300 },
  { id: 'eq-3', name: 'Heat Recovery Steam Gen.', type: 'HRSG', category: 'static', criticality: 'High', projectId: 'proj-1', supplierId: 'sup-3', routeId: 'rt-3', value: 32_000_000, weight: 220, status: 'ordered', riskScore: 28, deliveryDate: '2027-01-15', leadTimeDays: 420 },
  { id: 'eq-4', name: 'DCS Control System', type: 'Control System', category: 'instrumentation', criticality: 'High', projectId: 'proj-1', supplierId: 'sup-4', routeId: 'rt-4', value: 12_000_000, weight: 8, status: 'ready', riskScore: 15, deliveryDate: '2026-06-01', leadTimeDays: 180 },
  { id: 'eq-5', name: 'Subsea Xmas Tree', type: 'Xmas Tree', category: 'valves', criticality: 'Critical', projectId: 'proj-2', supplierId: 'sup-5', routeId: 'rt-1', value: 18_000_000, weight: 25, status: 'manufacturing', riskScore: 55, deliveryDate: '2026-12-01', leadTimeDays: 350 },
  { id: 'eq-6', name: 'FPSO Turret System', type: 'Turret', category: 'static', criticality: 'Critical', projectId: 'proj-2', supplierId: 'sup-6', routeId: 'rt-5', value: 65_000_000, weight: 450, status: 'manufacturing', riskScore: 48, deliveryDate: '2027-03-15', leadTimeDays: 540 },
  { id: 'eq-7', name: 'Subsea Manifold', type: 'Manifold', category: 'piping', criticality: 'High', projectId: 'proj-2', supplierId: 'sup-5', routeId: 'rt-1', value: 8_500_000, weight: 40, status: 'ordered', riskScore: 38, deliveryDate: '2026-11-01', leadTimeDays: 280 },
  { id: 'eq-8', name: 'LNG Cryogenic Exchanger', type: 'Heat Exchanger', category: 'static', criticality: 'Critical', projectId: 'proj-3', supplierId: 'sup-3', routeId: 'rt-3', value: 55_000_000, weight: 300, status: 'in-transit', riskScore: 62, deliveryDate: '2026-07-20', currentPosition: { lat: 8.0, lng: 68.0 }, leadTimeDays: 480 },
  { id: 'eq-9', name: 'BOG Compressor', type: 'Compressor', category: 'rotating', criticality: 'High', projectId: 'proj-3', supplierId: 'sup-2', routeId: 'rt-2', value: 22_000_000, weight: 65, status: 'delayed', riskScore: 78, deliveryDate: '2026-06-10', leadTimeDays: 320 },
  { id: 'eq-10', name: 'ESD Valve Package', type: 'Valve Package', category: 'valves', criticality: 'Medium', projectId: 'proj-3', supplierId: 'sup-7', routeId: 'rt-6', value: 4_200_000, weight: 12, status: 'ready', riskScore: 20, deliveryDate: '2026-05-15', leadTimeDays: 150 },
  { id: 'eq-11', name: 'Crude Distillation Column', type: 'Column', category: 'static', criticality: 'Critical', projectId: 'proj-4', supplierId: 'sup-8', routeId: 'rt-7', value: 38_000_000, weight: 280, status: 'manufacturing', riskScore: 45, deliveryDate: '2027-02-28', leadTimeDays: 400 },
  { id: 'eq-12', name: 'Hydrogen Compressor', type: 'Compressor', category: 'rotating', criticality: 'High', projectId: 'proj-4', supplierId: 'sup-1', routeId: 'rt-1', value: 16_000_000, weight: 50, status: 'ordered', riskScore: 30, deliveryDate: '2026-11-15', leadTimeDays: 290 },
  { id: 'eq-13', name: 'Ethylene Cracker', type: 'Reactor', category: 'static', criticality: 'Critical', projectId: 'proj-5', supplierId: 'sup-3', routeId: 'rt-3', value: 72_000_000, weight: 350, status: 'ordered', riskScore: 40, deliveryDate: '2027-06-01', leadTimeDays: 520 },
  { id: 'eq-14', name: 'Polyethylene Reactor', type: 'Reactor', category: 'static', criticality: 'High', projectId: 'proj-5', supplierId: 'sup-9', routeId: 'rt-8', value: 48_000_000, weight: 200, status: 'ordered', riskScore: 35, deliveryDate: '2027-04-15', leadTimeDays: 450 },
  { id: 'eq-15', name: 'MCC Lineup', type: 'Motor Control Center', category: 'electrical', criticality: 'Medium', projectId: 'proj-5', supplierId: 'sup-10', routeId: 'rt-6', value: 6_500_000, weight: 15, status: 'manufacturing', riskScore: 22, deliveryDate: '2026-09-01', leadTimeDays: 200 },
];

const MOCK_SUPPLIERS: Supplier[] = [
  { id: 'sup-1', name: 'Mitsubishi Heavy Industries', country: 'Japan', location: { lat: 34.69, lng: 135.50 }, category: 'rotating', capacity: 85, qualityScore: 95, onTimeDelivery: 92, certifications: ['ISO 9001', 'API 616', 'ASME'], riskScore: 25, activeOrders: 12, leadTimeDays: 365 },
  { id: 'sup-2', name: 'Siemens Energy', country: 'Germany', location: { lat: 52.52, lng: 13.41 }, category: 'rotating', capacity: 90, qualityScore: 96, onTimeDelivery: 94, certifications: ['ISO 9001', 'API 617', 'ATEX'], riskScore: 18, activeOrders: 8, leadTimeDays: 300 },
  { id: 'sup-3', name: 'Doosan Enerbility', country: 'South Korea', location: { lat: 35.18, lng: 129.08 }, category: 'static', capacity: 88, qualityScore: 91, onTimeDelivery: 88, certifications: ['ISO 9001', 'ASME U', 'ASME S'], riskScore: 30, activeOrders: 15, leadTimeDays: 420 },
  { id: 'sup-4', name: 'Yokogawa Electric', country: 'Japan', location: { lat: 35.65, lng: 139.74 }, category: 'instrumentation', capacity: 95, qualityScore: 97, onTimeDelivery: 96, certifications: ['ISO 9001', 'IEC 61508', 'SIL3'], riskScore: 12, activeOrders: 20, leadTimeDays: 180 },
  { id: 'sup-5', name: 'TechnipFMC', country: 'UK', location: { lat: 51.51, lng: -0.13 }, category: 'valves', capacity: 78, qualityScore: 93, onTimeDelivery: 85, certifications: ['ISO 9001', 'API 6A', 'API 17D'], riskScore: 35, activeOrders: 6, leadTimeDays: 350 },
  { id: 'sup-6', name: 'MODEC', country: 'Japan', location: { lat: 35.68, lng: 139.77 }, category: 'static', capacity: 70, qualityScore: 90, onTimeDelivery: 82, certifications: ['ISO 9001', 'DNV GL', 'ABS'], riskScore: 40, activeOrders: 3, leadTimeDays: 540 },
  { id: 'sup-7', name: 'Emerson Electric', country: 'USA', location: { lat: 38.63, lng: -90.20 }, category: 'valves', capacity: 92, qualityScore: 94, onTimeDelivery: 91, certifications: ['ISO 9001', 'API 6D', 'SIL3'], riskScore: 15, activeOrders: 25, leadTimeDays: 150 },
  { id: 'sup-8', name: 'L&T Heavy Engineering', country: 'India', location: { lat: 19.08, lng: 72.88 }, category: 'static', capacity: 82, qualityScore: 88, onTimeDelivery: 84, certifications: ['ISO 9001', 'ASME U', 'NBBI R'], riskScore: 32, activeOrders: 10, leadTimeDays: 400 },
  { id: 'sup-9', name: 'Sinopec Engineering', country: 'China', location: { lat: 39.91, lng: 116.40 }, category: 'static', capacity: 94, qualityScore: 85, onTimeDelivery: 80, certifications: ['ISO 9001', 'ASME U', 'GB/T'], riskScore: 45, activeOrders: 18, leadTimeDays: 450 },
  { id: 'sup-10', name: 'ABB', country: 'Switzerland', location: { lat: 47.38, lng: 8.54 }, category: 'electrical', capacity: 93, qualityScore: 96, onTimeDelivery: 93, certifications: ['ISO 9001', 'IEC 61439', 'ATEX'], riskScore: 14, activeOrders: 30, leadTimeDays: 200 },
];

const MOCK_ROUTES: ShippingRoute[] = [
  { id: 'rt-1', name: 'Japan - Persian Gulf (Hormuz)', origin: { lat: 34.69, lng: 135.50, port: 'Kobe' }, destination: { lat: 26.23, lng: 50.55, port: 'Dammam' }, waypoints: [{ lat: 30.0, lng: 130.0 }, { lat: 22.0, lng: 114.0 }, { lat: 13.0, lng: 100.0 }, { lat: 7.0, lng: 80.0 }, { lat: 12.5, lng: 52.0 }, { lat: 26.0, lng: 56.5 }], distanceNm: 6800, transitDays: 22, status: 'active', riskScore: 45, equipmentIds: ['eq-1', 'eq-5', 'eq-7', 'eq-12'], costPerTon: 45 },
  { id: 'rt-2', name: 'Europe - Persian Gulf (Suez)', origin: { lat: 53.55, lng: 9.99, port: 'Hamburg' }, destination: { lat: 26.23, lng: 50.55, port: 'Dammam' }, waypoints: [{ lat: 43.3, lng: 5.4 }, { lat: 37.0, lng: 15.0 }, { lat: 31.27, lng: 32.31 }, { lat: 27.0, lng: 34.0 }, { lat: 12.6, lng: 43.1 }], distanceNm: 6200, transitDays: 20, status: 'active', riskScore: 38, equipmentIds: ['eq-2', 'eq-9'], costPerTon: 52 },
  { id: 'rt-3', name: 'Korea - Persian Gulf', origin: { lat: 35.18, lng: 129.08, port: 'Busan' }, destination: { lat: 29.37, lng: 47.98, port: 'Shuaiba' }, waypoints: [{ lat: 25.0, lng: 120.0 }, { lat: 15.0, lng: 108.0 }, { lat: 5.0, lng: 95.0 }, { lat: 8.0, lng: 68.0 }, { lat: 12.6, lng: 43.1 }, { lat: 26.0, lng: 56.5 }], distanceNm: 7200, transitDays: 24, status: 'active', riskScore: 42, equipmentIds: ['eq-3', 'eq-8', 'eq-13'], costPerTon: 48 },
  { id: 'rt-4', name: 'Japan - Gulf (Air Freight)', origin: { lat: 35.65, lng: 139.74, port: 'Tokyo/Narita' }, destination: { lat: 24.45, lng: 54.65, port: 'Abu Dhabi' }, waypoints: [{ lat: 30.0, lng: 120.0 }, { lat: 28.0, lng: 90.0 }, { lat: 26.0, lng: 60.0 }], distanceNm: 4200, transitDays: 3, status: 'active', riskScore: 10, equipmentIds: ['eq-4'], costPerTon: 850 },
  { id: 'rt-5', name: 'Japan - UAE Direct', origin: { lat: 35.68, lng: 139.77, port: 'Yokohama' }, destination: { lat: 25.27, lng: 55.29, port: 'Jebel Ali' }, waypoints: [{ lat: 28.0, lng: 128.0 }, { lat: 18.0, lng: 110.0 }, { lat: 8.0, lng: 85.0 }, { lat: 12.0, lng: 55.0 }, { lat: 22.0, lng: 60.0 }], distanceNm: 6500, transitDays: 21, status: 'active', riskScore: 40, equipmentIds: ['eq-6'], costPerTon: 42 },
  { id: 'rt-6', name: 'USA - Gulf (Suez)', origin: { lat: 29.95, lng: -90.07, port: 'New Orleans' }, destination: { lat: 26.23, lng: 50.55, port: 'Dammam' }, waypoints: [{ lat: 28.0, lng: -80.0 }, { lat: 36.0, lng: -5.6 }, { lat: 37.0, lng: 15.0 }, { lat: 31.27, lng: 32.31 }, { lat: 27.0, lng: 34.0 }, { lat: 12.6, lng: 43.1 }], distanceNm: 9500, transitDays: 32, status: 'active', riskScore: 35, equipmentIds: ['eq-10', 'eq-15'], costPerTon: 55 },
  { id: 'rt-7', name: 'India - Oman Direct', origin: { lat: 19.08, lng: 72.88, port: 'Mumbai' }, destination: { lat: 19.66, lng: 57.7, port: 'Duqm' }, waypoints: [{ lat: 18.0, lng: 65.0 }], distanceNm: 1200, transitDays: 5, status: 'active', riskScore: 18, equipmentIds: ['eq-11'], costPerTon: 28 },
  { id: 'rt-8', name: 'China - Qatar', origin: { lat: 31.23, lng: 121.47, port: 'Shanghai' }, destination: { lat: 25.93, lng: 51.54, port: 'Ras Laffan' }, waypoints: [{ lat: 22.0, lng: 114.0 }, { lat: 10.0, lng: 100.0 }, { lat: 5.0, lng: 80.0 }, { lat: 12.6, lng: 43.1 }, { lat: 26.0, lng: 56.5 }], distanceNm: 6400, transitDays: 21, status: 'active', riskScore: 50, equipmentIds: ['eq-14'], costPerTon: 40 },
];

const MOCK_ZONES: GeopoliticalZone[] = [
  { id: 'zone-1', name: 'Strait of Hormuz', riskLevel: 'high', boundaries: [{ lat: 27.2, lng: 56.0 }, { lat: 26.0, lng: 56.8 }, { lat: 25.5, lng: 57.0 }, { lat: 26.0, lng: 55.0 }, { lat: 27.0, lng: 55.0 }], description: 'Critical chokepoint for ~21% of global oil transit', activeThreats: ['Naval tensions', 'Mine risk'] },
  { id: 'zone-2', name: 'Suez Canal', riskLevel: 'medium', boundaries: [{ lat: 31.5, lng: 32.0 }, { lat: 30.0, lng: 32.8 }, { lat: 29.8, lng: 33.0 }, { lat: 31.3, lng: 33.2 }], description: 'Critical trade route connecting Mediterranean and Red Sea', activeThreats: ['Houthi missile activity', 'Congestion'] },
  { id: 'zone-3', name: 'Red Sea / Bab el-Mandeb', riskLevel: 'high', boundaries: [{ lat: 15.0, lng: 41.0 }, { lat: 12.0, lng: 43.0 }, { lat: 12.5, lng: 44.0 }, { lat: 15.5, lng: 42.0 }], description: 'Southern approach to Suez Canal', activeThreats: ['Houthi attacks on shipping', 'Piracy'] },
  { id: 'zone-4', name: 'South China Sea', riskLevel: 'medium', boundaries: [{ lat: 23.0, lng: 113.0 }, { lat: 18.0, lng: 110.0 }, { lat: 8.0, lng: 112.0 }, { lat: 8.0, lng: 117.0 }, { lat: 20.0, lng: 120.0 }], description: 'Disputed territorial waters with heavy shipping traffic', activeThreats: ['Territorial disputes', 'Naval exercises'] },
  { id: 'zone-5', name: 'Malacca Strait', riskLevel: 'low', boundaries: [{ lat: 4.0, lng: 98.0 }, { lat: 1.2, lng: 103.5 }, { lat: 1.5, lng: 104.5 }, { lat: 5.0, lng: 100.0 }], description: 'Major shipping chokepoint between Indian and Pacific oceans', activeThreats: ['Congestion'] },
];

const MOCK_PORTS: Port[] = [
  { id: 'port-1', name: 'Dammam / King Abdulaziz', country: 'Saudi Arabia', location: { lat: 26.43, lng: 50.10 }, capacity: 90, congestionLevel: 35, status: 'operational' },
  { id: 'port-2', name: 'Jebel Ali', country: 'UAE', location: { lat: 25.01, lng: 55.06 }, capacity: 95, congestionLevel: 42, status: 'operational' },
  { id: 'port-3', name: 'Kobe', country: 'Japan', location: { lat: 34.69, lng: 135.20 }, capacity: 88, congestionLevel: 28, status: 'operational' },
  { id: 'port-4', name: 'Hamburg', country: 'Germany', location: { lat: 53.54, lng: 9.97 }, capacity: 92, congestionLevel: 45, status: 'operational' },
  { id: 'port-5', name: 'Busan', country: 'South Korea', location: { lat: 35.10, lng: 129.03 }, capacity: 94, congestionLevel: 38, status: 'operational' },
  { id: 'port-6', name: 'Shanghai', country: 'China', location: { lat: 31.23, lng: 121.47 }, capacity: 97, congestionLevel: 55, status: 'congested' },
];

// ===== Store =====

interface ProjectState {
  projects: Project[];
  equipment: Equipment[];
  suppliers: Supplier[];
  routes: ShippingRoute[];
  zones: GeopoliticalZone[];
  ports: Port[];
  loading: boolean;
  error: string | null;
  fetchAll: () => void;
}

let fetchInitiated = false;

export const useProjectStore = create<ProjectState>((set, get) => ({
  projects: [],
  equipment: [],
  suppliers: [],
  routes: [],
  zones: MOCK_ZONES,
  ports: MOCK_PORTS,
  loading: false,
  error: null,
  fetchAll: async () => {
    if (get().loading) return;
    set({ loading: true, error: null });

    try {
      const [projectsRaw, equipmentRaw, suppliersRaw, routesRaw] = await Promise.all([
        fetchProjects().catch(() => null),
        fetchEquipment().catch(() => null),
        fetchSuppliers().catch(() => null),
        fetchRoutes().catch(() => null),
      ]);

      const projects = projectsRaw
        ? (projectsRaw as unknown as Record<string, unknown>[]).map(mapProject)
        : MOCK_PROJECTS;
      const equipment = equipmentRaw
        ? (equipmentRaw as unknown as Record<string, unknown>[]).map(mapEquipment)
        : MOCK_EQUIPMENT;
      const suppliers = suppliersRaw
        ? (suppliersRaw as unknown as Record<string, unknown>[]).map(mapSupplier)
        : MOCK_SUPPLIERS;
      const routes = routesRaw
        ? (routesRaw as unknown as Record<string, unknown>[]).map(mapRoute)
        : MOCK_ROUTES;

      set({
        projects,
        equipment,
        suppliers,
        routes,
        zones: MOCK_ZONES,
        ports: MOCK_PORTS,
        loading: false,
        error: null,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch data';
      console.error('projectStore fetchAll error, falling back to mock data:', message);
      set({
        projects: MOCK_PROJECTS,
        equipment: MOCK_EQUIPMENT,
        suppliers: MOCK_SUPPLIERS,
        routes: MOCK_ROUTES,
        zones: MOCK_ZONES,
        ports: MOCK_PORTS,
        loading: false,
        error: message,
      });
    }
  },
}));

// Lazy initialization: trigger fetchAll on first subscription
const originalSubscribe = useProjectStore.subscribe;
useProjectStore.subscribe = (...args) => {
  if (!fetchInitiated) {
    fetchInitiated = true;
    useProjectStore.getState().fetchAll();
  }
  return originalSubscribe(...args);
};

// Also trigger on first getState call from components
const originalGetState = useProjectStore.getState;
useProjectStore.getState = () => {
  if (!fetchInitiated) {
    fetchInitiated = true;
    const state = originalGetState();
    state.fetchAll();
    return originalGetState();
  }
  return originalGetState();
};
