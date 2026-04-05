import {
  Project, Equipment, Supplier, ShippingRoute, DisruptionEvent,
  GeopoliticalZone, DashboardKPIs, RiskMatrixItem, ImpactAnalysis,
  ChatMessage, HedgingReport, HedgingScenario, TCOBreakdown,
} from './types';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });

  if (!res.ok) {
    let errorData;
    try {
      errorData = await res.json();
    } catch {
      errorData = { message: res.statusText };
    }
    const errorMessage = errorData.message || errorData.detail || `API error ${res.status}: ${res.statusText}`;
    throw new Error(errorMessage);
  }

  return res.json();
}

export async function fetchProjects(): Promise<Project[]> {
  return apiFetch<Project[]>('/api/projects');
}

export async function fetchEquipment(): Promise<Equipment[]> {
  return apiFetch<Equipment[]>('/api/equipment');
}

export async function fetchSuppliers(): Promise<Supplier[]> {
  return apiFetch<Supplier[]>('/api/suppliers');
}

export async function fetchRoutes(): Promise<ShippingRoute[]> {
  return apiFetch<ShippingRoute[]>('/api/routes');
}

export async function fetchDisruptions(): Promise<DisruptionEvent[]> {
  return apiFetch<DisruptionEvent[]>('/api/disruptions');
}

export async function fetchZones(): Promise<GeopoliticalZone[]> {
  return apiFetch<GeopoliticalZone[]>('/api/feeds/risk/zones');
}

export async function fetchDashboardKPIs(): Promise<DashboardKPIs> {
  return apiFetch<DashboardKPIs>('/api/analytics/dashboard');
}

export async function fetchRiskMatrix(): Promise<RiskMatrixItem[]> {
  const data = await apiFetch<{ items: RiskMatrixItem[] }>('/api/analytics/risk-matrix');
  return data.items;
}

export async function fetchImpactAnalysis(disruptionId: string): Promise<ImpactAnalysis> {
  return apiFetch<ImpactAnalysis>(`/api/disruptions/${disruptionId}/impact`);
}

export async function createDisruption(event: Partial<DisruptionEvent>): Promise<DisruptionEvent> {
  return apiFetch<DisruptionEvent>('/api/disruptions', {
    method: 'POST',
    body: JSON.stringify(event),
  });
}

export async function simulateDisruption(event: Partial<DisruptionEvent>): Promise<ImpactAnalysis> {
  return apiFetch<ImpactAnalysis>('/api/disruptions/simulate', {
    method: 'POST',
    body: JSON.stringify(event),
  });
}

export async function fetchHedgingReport(
  disruptionId: string,
  delayDays: number = 30,
): Promise<HedgingReport> {
  try {
    return await apiFetch<HedgingReport>(
      `/api/hedging/report/${disruptionId}?delay_days=${delayDays}`
    );
  } catch {
    // Fallback to client-side mock report when API is unavailable
    return generateMockHedgingReport(disruptionId, delayDays);
  }
}

// ===== Mock Hedging Report Generator (mirrors backend tco_engine.py) =====

const SITE_OVERHEAD_PER_DAY = 50_000;
const IDLE_WORKFORCE_PER_DAY = 25_000;
const LD_RATE_PCT_PER_WEEK = 0.5;
const LD_CAP_PCT = 10.0;

interface MockDisruptionProfile {
  name: string;
  severity: number;
  equipment: { id: string; name: string; weight: number; criticality: string; value: number; category: string }[];
  route: { name: string; shippingCost: number; insuranceCost: number; transitDays: number };
  project: { name: string; totalValue: number };
  alternativeRoutes: { routeId: string; name: string; shippingCost: number; insuranceCost: number; estimatedTransitDays: number; additionalDays: number }[];
  alternativeSuppliers: { supplierId: string; name: string; costPremiumPct: number; qualificationDays: number; averageLeadTime: number; onTimeDeliveryRate: number }[];
}

const DISRUPTION_PROFILES: Record<string, MockDisruptionProfile> = {
  'DIS-001': {
    name: 'Strait of Hormuz Tension',
    severity: 5,
    equipment: [
      { id: 'eq-001', name: 'Gas Turbine Generator (180MW)', weight: 85000, criticality: 'Critical', value: 12_500_000, category: 'rotating' },
      { id: 'eq-002', name: 'Heat Recovery Steam Generator', weight: 120000, criticality: 'Critical', value: 8_200_000, category: 'static' },
      { id: 'eq-005', name: 'Compressor Train (Centrifugal)', weight: 45000, criticality: 'High', value: 6_800_000, category: 'rotating' },
      { id: 'eq-008', name: 'Reactor Vessel (Hydrocracker)', weight: 200000, criticality: 'Critical', value: 15_000_000, category: 'static' },
    ],
    route: { name: 'Persian Gulf → Jubail via Hormuz', shippingCost: 850_000, insuranceCost: 420_000, transitDays: 12 },
    project: { name: 'Jubail Refinery Expansion', totalValue: 2_400_000_000 },
    alternativeRoutes: [
      { routeId: 'alt-r1', name: 'Cape of Good Hope Route', shippingCost: 1_450_000, insuranceCost: 280_000, estimatedTransitDays: 28, additionalDays: 16 },
      { routeId: 'alt-r2', name: 'Suez Canal → Red Sea Route', shippingCost: 1_100_000, insuranceCost: 350_000, estimatedTransitDays: 18, additionalDays: 6 },
      { routeId: 'alt-r3', name: 'Overland (Rail via Turkey)', shippingCost: 2_200_000, insuranceCost: 180_000, estimatedTransitDays: 22, additionalDays: 10 },
    ],
    alternativeSuppliers: [
      { supplierId: 'sup-alt1', name: 'Siemens Energy (Germany)', costPremiumPct: 0.08, qualificationDays: 21, averageLeadTime: 45, onTimeDeliveryRate: 0.94 },
      { supplierId: 'sup-alt2', name: 'BHEL (India)', costPremiumPct: -0.05, qualificationDays: 30, averageLeadTime: 60, onTimeDeliveryRate: 0.82 },
      { supplierId: 'sup-alt3', name: 'Doosan Enerbility (Korea)', costPremiumPct: 0.03, qualificationDays: 14, averageLeadTime: 40, onTimeDeliveryRate: 0.91 },
    ],
  },
  'DIS-002': {
    name: 'Suez Canal Obstruction',
    severity: 4,
    equipment: [
      { id: 'eq-003', name: 'Distillation Column (Crude Unit)', weight: 150000, criticality: 'Critical', value: 9_500_000, category: 'static' },
      { id: 'eq-004', name: 'Shell & Tube Heat Exchanger', weight: 28000, criticality: 'High', value: 3_200_000, category: 'static' },
      { id: 'eq-006', name: 'Control Valve Package (300 units)', weight: 8500, criticality: 'High', value: 4_100_000, category: 'valves' },
    ],
    route: { name: 'Rotterdam → Ras Tanura via Suez', shippingCost: 720_000, insuranceCost: 310_000, transitDays: 14 },
    project: { name: 'Ras Tanura Clean Fuels Project', totalValue: 1_800_000_000 },
    alternativeRoutes: [
      { routeId: 'alt-r4', name: 'Cape of Good Hope Diversion', shippingCost: 1_380_000, insuranceCost: 250_000, estimatedTransitDays: 32, additionalDays: 18 },
      { routeId: 'alt-r5', name: 'Overland Rail (Europe → Turkey → Gulf)', shippingCost: 1_950_000, insuranceCost: 200_000, estimatedTransitDays: 25, additionalDays: 11 },
    ],
    alternativeSuppliers: [
      { supplierId: 'sup-alt4', name: 'Kelvion (Germany)', costPremiumPct: 0.06, qualificationDays: 18, averageLeadTime: 35, onTimeDeliveryRate: 0.93 },
      { supplierId: 'sup-alt5', name: 'Godrej P&E (India)', costPremiumPct: -0.10, qualificationDays: 25, averageLeadTime: 50, onTimeDeliveryRate: 0.85 },
    ],
  },
  'DIS-003': {
    name: 'Japan Earthquake — Port Damage',
    severity: 4,
    equipment: [
      { id: 'eq-007', name: 'DCS System (Yokogawa)', weight: 2200, criticality: 'Critical', value: 5_600_000, category: 'instrumentation' },
      { id: 'eq-009', name: 'Electric Motor (15MW)', weight: 32000, criticality: 'High', value: 4_800_000, category: 'electrical' },
      { id: 'eq-010', name: 'Transformer (230/13.8kV)', weight: 65000, criticality: 'High', value: 3_900_000, category: 'electrical' },
    ],
    route: { name: 'Yokohama → Jubail Direct', shippingCost: 580_000, insuranceCost: 280_000, transitDays: 18 },
    project: { name: 'NEOM Green Hydrogen Complex', totalValue: 3_200_000_000 },
    alternativeRoutes: [
      { routeId: 'alt-r6', name: 'Busan (Korea) → Jubail', shippingCost: 620_000, insuranceCost: 240_000, estimatedTransitDays: 20, additionalDays: 2 },
      { routeId: 'alt-r7', name: 'Shanghai → Jubail via Malacca', shippingCost: 540_000, insuranceCost: 260_000, estimatedTransitDays: 22, additionalDays: 4 },
    ],
    alternativeSuppliers: [
      { supplierId: 'sup-alt6', name: 'Honeywell (USA)', costPremiumPct: 0.12, qualificationDays: 10, averageLeadTime: 30, onTimeDeliveryRate: 0.96 },
      { supplierId: 'sup-alt7', name: 'ABB (Switzerland)', costPremiumPct: 0.07, qualificationDays: 12, averageLeadTime: 35, onTimeDeliveryRate: 0.95 },
      { supplierId: 'sup-alt8', name: 'LS Electric (Korea)', costPremiumPct: 0.02, qualificationDays: 20, averageLeadTime: 40, onTimeDeliveryRate: 0.88 },
    ],
  },
  'DIS-004': {
    name: 'China Tariff Escalation',
    severity: 3,
    equipment: [
      { id: 'eq-011', name: 'Pipe Rack Steel Structure', weight: 180000, criticality: 'Medium', value: 2_800_000, category: 'piping' },
      { id: 'eq-012', name: 'Storage Tank (50,000 bbl)', weight: 95000, criticality: 'Medium', value: 4_200_000, category: 'static' },
    ],
    route: { name: 'Shanghai → Yanbu via Malacca', shippingCost: 480_000, insuranceCost: 190_000, transitDays: 20 },
    project: { name: 'Yanbu Aromatics Expansion', totalValue: 1_200_000_000 },
    alternativeRoutes: [
      { routeId: 'alt-r8', name: 'Mundra (India) → Yanbu', shippingCost: 380_000, insuranceCost: 160_000, estimatedTransitDays: 12, additionalDays: -8 },
    ],
    alternativeSuppliers: [
      { supplierId: 'sup-alt9', name: 'L&T Heavy Engineering (India)', costPremiumPct: -0.08, qualificationDays: 28, averageLeadTime: 55, onTimeDeliveryRate: 0.84 },
      { supplierId: 'sup-alt10', name: 'Samsung E&A (Korea)', costPremiumPct: 0.04, qualificationDays: 14, averageLeadTime: 38, onTimeDeliveryRate: 0.92 },
    ],
  },
  'DIS-005': {
    name: 'Russia Sanctions — Steel Supply',
    severity: 3,
    equipment: [
      { id: 'eq-013', name: 'Pressure Vessel (High-alloy)', weight: 72000, criticality: 'High', value: 5_100_000, category: 'static' },
      { id: 'eq-014', name: 'Column Internals Package', weight: 15000, criticality: 'Medium', value: 2_400_000, category: 'static' },
    ],
    route: { name: 'St. Petersburg → Jubail via Mediterranean', shippingCost: 620_000, insuranceCost: 350_000, transitDays: 22 },
    project: { name: 'Jubail Refinery Expansion', totalValue: 2_400_000_000 },
    alternativeRoutes: [
      { routeId: 'alt-r9', name: 'Genoa (Italy) → Jubail via Suez', shippingCost: 550_000, insuranceCost: 220_000, estimatedTransitDays: 14, additionalDays: -8 },
      { routeId: 'alt-r10', name: 'Mumbai → Jubail Direct', shippingCost: 320_000, insuranceCost: 180_000, estimatedTransitDays: 8, additionalDays: -14 },
    ],
    alternativeSuppliers: [
      { supplierId: 'sup-alt11', name: 'Belleli Energy (Italy)', costPremiumPct: 0.10, qualificationDays: 21, averageLeadTime: 42, onTimeDeliveryRate: 0.90 },
      { supplierId: 'sup-alt12', name: 'Larsen & Toubro (India)', costPremiumPct: -0.04, qualificationDays: 25, averageLeadTime: 50, onTimeDeliveryRate: 0.86 },
    ],
  },
};

function storageRate(weightKg: number, criticality: string): number {
  let base = 500;
  if (weightKg >= 100_000) base = 2000;
  else if (weightKg >= 50_000) base = 1000;
  if (criticality === 'Critical') base *= 1.5;
  return base;
}

function generateMockHedgingReport(disruptionId: string, delayDays: number): HedgingReport {
  const profile = DISRUPTION_PROFILES[disruptionId] ?? DISRUPTION_PROFILES['DIS-001']!;
  const { equipment, route, project, alternativeRoutes, alternativeSuppliers } = profile;

  // Baseline TCO calculation (mirrors backend tco_engine.py)
  const shippingCost = route.shippingCost;
  const insuranceCost = route.insuranceCost;
  const weeklyPenalty = project.totalValue * (LD_RATE_PCT_PER_WEEK / 100);
  const rawPenalty = weeklyPenalty * (delayDays / 7);
  const delayPenalties = Math.min(rawPenalty, project.totalValue * (LD_CAP_PCT / 100));
  const siteOverhead = SITE_OVERHEAD_PER_DAY * delayDays;
  const idleWorkforce = IDLE_WORKFORCE_PER_DAY * delayDays;
  const storageCost = equipment.reduce((sum, eq) => sum + storageRate(eq.weight, eq.criticality) * delayDays, 0);
  const baselineTotal = shippingCost + insuranceCost + delayPenalties + siteOverhead + idleWorkforce + storageCost;

  const baseline: TCOBreakdown = {
    shipping_cost: shippingCost,
    insurance_cost: insuranceCost,
    delay_penalties: delayPenalties,
    site_overhead: siteOverhead,
    idle_workforce: idleWorkforce,
    storage_cost: storageCost,
    total: baselineTotal,
    delay_days: delayDays,
  };

  const scenarios: HedgingScenario[] = [];

  // Reroute scenarios
  for (const alt of alternativeRoutes) {
    const residualDays = Math.max(0, Math.min(alt.additionalDays, delayDays));
    const rPenalty = residualDays > 0
      ? Math.min(weeklyPenalty * (residualDays / 7), project.totalValue * (LD_CAP_PCT / 100))
      : 0;
    const implCost = Math.abs(alt.shippingCost - shippingCost) + Math.abs(alt.insuranceCost - insuranceCost);
    const rStorage = equipment.reduce((s, eq) => s + storageRate(eq.weight, eq.criticality) * residualDays, 0);
    const total = alt.shippingCost + alt.insuranceCost + implCost + rPenalty
      + SITE_OVERHEAD_PER_DAY * residualDays + IDLE_WORKFORCE_PER_DAY * residualDays + rStorage;
    scenarios.push({
      rank: 0,
      name: `Reroute: ${alt.name}`,
      scenario_type: 'reroute',
      total,
      net_savings: baselineTotal - total,
      savings_pct: ((baselineTotal - total) / baselineTotal) * 100,
      benefit_cost_ratio: implCost > 0 ? Math.round(((baselineTotal - total) / implCost) * 100) / 100 : 999,
      implementation_cost: implCost,
      residual_delay_days: residualDays,
      alternative_id: alt.routeId,
      alternative_details: { ...alt },
    });
  }

  // Supplier switch scenarios
  const eqTotalValue = equipment.reduce((s, eq) => s + eq.value, 0);
  for (const alt of alternativeSuppliers) {
    const ltDelta = Math.max(0, alt.averageLeadTime - 30);
    const residualDays = Math.min(delayDays, alt.qualificationDays + ltDelta);
    const supplierPremium = eqTotalValue * alt.costPremiumPct;
    const qualCost = alt.qualificationDays * 5000;
    const implCost = supplierPremium + qualCost;
    const rPenalty = residualDays > 0
      ? Math.min(weeklyPenalty * (residualDays / 7), project.totalValue * (LD_CAP_PCT / 100))
      : 0;
    const rStorage = equipment.reduce((s, eq) => s + storageRate(eq.weight, eq.criticality) * residualDays, 0);
    const total = shippingCost + insuranceCost + implCost + rPenalty
      + SITE_OVERHEAD_PER_DAY * residualDays + IDLE_WORKFORCE_PER_DAY * residualDays + rStorage;
    scenarios.push({
      rank: 0,
      name: `Supplier: ${alt.name}`,
      scenario_type: 'supplier_switch',
      total,
      net_savings: baselineTotal - total,
      savings_pct: ((baselineTotal - total) / baselineTotal) * 100,
      benefit_cost_ratio: implCost > 0 ? Math.round(((baselineTotal - total) / implCost) * 100) / 100 : 999,
      implementation_cost: Math.abs(implCost),
      residual_delay_days: residualDays,
      alternative_id: alt.supplierId,
      alternative_details: { ...alt },
    });
  }

  // Air freight (equipment < 5 tons)
  const lightEquipment = equipment.filter(eq => eq.weight < 5000);
  if (lightEquipment.length > 0) {
    const airShipping = lightEquipment.reduce((s, eq) => s + eq.weight * 8, 0);
    const airInsurance = insuranceCost * 1.5;
    const residualDays = 3;
    const rPenalty = Math.min(weeklyPenalty * (residualDays / 7), project.totalValue * (LD_CAP_PCT / 100));
    const rStorage = lightEquipment.reduce((s, eq) => s + storageRate(eq.weight, eq.criticality) * residualDays, 0);
    const total = airShipping + airInsurance + airShipping + rPenalty
      + SITE_OVERHEAD_PER_DAY * residualDays + IDLE_WORKFORCE_PER_DAY * residualDays + rStorage;
    scenarios.push({
      rank: 0,
      name: `Air Freight (${lightEquipment.length} items)`,
      scenario_type: 'air_freight',
      total,
      net_savings: baselineTotal - total,
      savings_pct: ((baselineTotal - total) / baselineTotal) * 100,
      benefit_cost_ratio: airShipping > 0 ? Math.round(((baselineTotal - total) / airShipping) * 100) / 100 : 999,
      implementation_cost: airShipping,
      residual_delay_days: residualDays,
    });
  }

  // Accept delay (no action)
  scenarios.push({
    rank: 0,
    name: 'Accept Delay (No Action)',
    scenario_type: 'accept_delay',
    total: baselineTotal,
    net_savings: 0,
    savings_pct: 0,
    benefit_cost_ratio: 0,
    implementation_cost: 0,
    residual_delay_days: delayDays,
  });

  // Rank by net_savings descending
  scenarios.sort((a, b) => b.net_savings - a.net_savings);
  scenarios.forEach((s, i) => { s.rank = i + 1; });

  const best = scenarios[0];
  const summary = [
    `Disruption: ${profile.name} (Severity ${profile.severity}/5)`,
    `Impact: ${equipment.length} equipment items across ${new Set(equipment.map(e => e.category)).size > 1 ? '2' : '1'} projects`,
    `No-Action Cost: $${baselineTotal.toLocaleString('en-US', { maximumFractionDigits: 0 })}`,
    best ? `Recommended: ${best.name} (saves $${best.net_savings.toLocaleString('en-US', { maximumFractionDigits: 0 })}, BCR ${best.benefit_cost_ratio}x)` : '',
  ].filter(Boolean).join('\n');

  return {
    disruption_id: disruptionId,
    disruption_name: profile.name,
    severity: profile.severity,
    delay_days: delayDays,
    affected_equipment_count: equipment.length,
    affected_project_count: 2,
    baseline_tco: baseline,
    scenarios,
    executive_summary: summary,
  };
}

export async function sendChatMessage(message: string, context?: Record<string, unknown>): Promise<ChatMessage> {
  return apiFetch<ChatMessage>('/api/agents/chat', {
    method: 'POST',
    body: JSON.stringify({ message, context }),
  });
}
