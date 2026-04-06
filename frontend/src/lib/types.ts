// ===== Core Ontology Types =====

export interface Project {
  id: string;
  name: string;
  client: string;
  value: number;
  completionPercent: number;
  status: "on-track" | "at-risk" | "delayed" | "critical";
  location: { lat: number; lng: number };
  country: string;
  equipmentIds: string[];
  startDate: string;
  endDate: string;
}

export interface Equipment {
  id: string;
  name: string;
  type: string;
  category: "rotating" | "static" | "electrical" | "instrumentation" | "piping" | "valves";
  criticality: "Critical" | "High" | "Medium" | "Low";
  projectId: string;
  supplierId: string;
  routeId: string;
  value: number;
  weight: number;
  status: "ordered" | "manufacturing" | "ready" | "in-transit" | "delivered" | "delayed";
  riskScore: number;
  deliveryDate: string;
  currentPosition?: { lat: number; lng: number };
  leadTimeDays: number;
}

export interface Supplier {
  id: string;
  name: string;
  country: string;
  location: { lat: number; lng: number };
  category: "rotating" | "static" | "electrical" | "instrumentation" | "piping" | "valves";
  capacity: number;
  qualityScore: number;
  onTimeDelivery: number;
  certifications: string[];
  riskScore: number;
  activeOrders: number;
  leadTimeDays: number;
}

export interface ShippingRoute {
  id: string;
  name: string;
  origin: { lat: number; lng: number; port: string };
  destination: { lat: number; lng: number; port: string };
  waypoints: { lat: number; lng: number }[];
  distanceNm: number;
  transitDays: number;
  status: "active" | "disrupted" | "blocked" | "alternative";
  riskScore: number;
  equipmentIds: string[];
  costPerTon: number;
}

export interface Port {
  id: string;
  name: string;
  country: string;
  location: { lat: number; lng: number };
  capacity: number;
  congestionLevel: number;
  status: "operational" | "congested" | "limited" | "closed";
}

export interface GeopoliticalZone {
  id: string;
  name: string;
  riskLevel: "low" | "medium" | "high" | "critical";
  boundaries: { lat: number; lng: number }[];
  description: string;
  activeThreats: string[];
}

export interface DisruptionEvent {
  id: string;
  type: "geopolitical" | "natural" | "economic" | "infrastructure" | "cyber";
  name: string;
  description: string;
  severity: 1 | 2 | 3 | 4 | 5;
  startDate: string;
  endDate?: string;
  affectedZoneIds: string[];
  affectedRouteIds: string[];
  affectedEquipmentIds: string[];
  affectedProjectIds: string[];
  location: { lat: number; lng: number };
  radius: number;
  status: "active" | "resolved" | "monitoring";
}

export interface PurchaseOrder {
  id: string;
  equipmentId: string;
  supplierId: string;
  value: number;
  status: "pending" | "confirmed" | "in-production" | "shipped" | "delivered";
  orderDate: string;
  expectedDelivery: string;
}

export interface RFQ {
  id: string;
  equipmentId: string;
  supplierIds: string[];
  status: "draft" | "sent" | "responses-received" | "awarded";
  deadline: string;
}

export interface Quotation {
  id: string;
  rfqId: string;
  supplierId: string;
  price: number;
  leadTimeDays: number;
  validUntil: string;
}

// ===== Analysis Types =====

export interface ImpactAnalysis {
  disruptionId: string;
  totalCostImpact: number;
  affectedProjectsCount: number;
  affectedEquipmentCount: number;
  affectedRoutesCount: number;
  delayDays: number;
  cascadeChain: CascadeStep[];
  recommendations: SupplierRecommendation[];
  routeAlternatives: RouteAlternative[];
}

export interface CascadeStep {
  level: number;
  type: "event" | "zone" | "route" | "equipment" | "project";
  count: number;
  items: { id: string; name: string; impact: string }[];
}

export interface SupplierRecommendation {
  currentSupplierId: string;
  alternativeSupplierId: string;
  equipmentId: string;
  costDelta: number;
  leadTimeDelta: number;
  qualityDelta: number;
  overallScore: number;
  reasoning: string;
}

export interface RouteAlternative {
  currentRouteId: string;
  alternativeRouteId: string;
  transitTimeDelta: number;
  costDelta: number;
  riskReduction: number;
  waypoints: { lat: number; lng: number }[];
}

export interface CostAnalysis {
  noActionCost: number;
  mitigationScenarios: {
    name: string;
    cost: number;
    savings: number;
    riskReduction: number;
    implementationDays: number;
  }[];
  totalPotentialSavings: number;
  roi: number;
}

// ===== UI Types =====

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  agentName?: string;
  isStreaming?: boolean;
}

export interface AgentStatus {
  name: string;
  status: "idle" | "thinking" | "analyzing" | "responding";
  currentTask?: string;
}

export interface DashboardKPIs {
  totalPortfolioValue: number;
  atRiskValue: number;
  activeDisruptions: number;
  averageRiskScore: number;
  criticalItemsCount: number;
  potentialSavings: number;
  trends: {
    portfolioTrend: number;
    riskTrend: number;
    disruptionTrend: number;
  };
}

export interface RiskMatrixItem {
  equipmentId: string;
  equipmentName: string;
  projectName: string;
  supplierName: string;
  routeName: string;
  criticality: "Critical" | "High" | "Medium" | "Low";
  riskScore: number;
  status: string;
  value: number;
}

// ===== Hedging Report Types =====

export interface TCOBreakdown {
  shipping_cost: number;
  insurance_cost: number;
  delay_penalties: number;
  site_overhead: number;
  idle_workforce: number;
  storage_cost: number;
  total: number;
  delay_days: number;
}

export interface HedgingScenario {
  rank: number;
  name: string;
  scenario_type: string;
  total: number;
  net_savings: number;
  savings_pct: number;
  benefit_cost_ratio: number;
  implementation_cost: number;
  residual_delay_days: number;
  alternative_id?: string;
  alternative_details?: Record<string, unknown>;
}

export interface HedgingReport {
  disruption_id: string;
  disruption_name: string;
  severity: number;
  delay_days: number;
  affected_equipment_count: number;
  affected_project_count: number;
  baseline_tco: TCOBreakdown;
  scenarios: HedgingScenario[];
  executive_summary: string;
}

// ===== Graph Types =====

export interface GraphNode {
  id: string;
  label: string;
  type: "project" | "equipment" | "supplier" | "route" | "zone" | "disruption" | "port";
  data: Record<string, unknown>;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

export interface GraphEdge {
  id: string;
  source: string | GraphNode;
  target: string | GraphNode;
  label: string;
  type: string;
  strength?: number;
}

// ===== Feed Types =====

export interface NewsItem {
  id: string;
  headline: string;
  source: string;
  url: string;
  publishedDate: string;
  location: string;
  tone: number;
  severity: number;
  type: string;
  zones: string[];
  sourceType: string;
}

export interface ZoneRisk {
  zone_id: string;
  zone_name: string;
  risk_level: number;
  trend: "stable" | "increasing" | "decreasing";
  active_threats: number;
  insurance_multiplier: number;
  article_count: number;
  source: string;
  top_headlines: { title: string; url: string; tone: number; date: string }[];
}

export interface FeedAgentStatus {
  name: string;
  status: "idle" | "analyzing" | "completed" | "error";
  lastRun?: string;
  lastTask?: string;
  resultSummary?: string;
}
