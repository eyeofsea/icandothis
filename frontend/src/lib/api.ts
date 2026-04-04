import {
  Project, Equipment, Supplier, ShippingRoute, DisruptionEvent,
  GeopoliticalZone, DashboardKPIs, RiskMatrixItem, ImpactAnalysis,
  ChatMessage, HedgingReport,
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
  return apiFetch<GeopoliticalZone[]>('/api/zones');
}

export async function fetchDashboardKPIs(): Promise<DashboardKPIs> {
  return apiFetch<DashboardKPIs>('/api/dashboard/kpis');
}

export async function fetchRiskMatrix(): Promise<RiskMatrixItem[]> {
  return apiFetch<RiskMatrixItem[]>('/api/dashboard/risk-matrix');
}

export async function fetchImpactAnalysis(disruptionId: string): Promise<ImpactAnalysis> {
  return apiFetch<ImpactAnalysis>(`/api/analysis/impact/${disruptionId}`);
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
  return apiFetch<HedgingReport>(
    `/api/hedging/report/${disruptionId}?delay_days=${delayDays}`
  );
}

export async function sendChatMessage(message: string, context?: Record<string, unknown>): Promise<ChatMessage> {
  return apiFetch<ChatMessage>('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ message, context }),
  });
}
