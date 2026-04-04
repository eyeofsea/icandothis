"""Risk scoring algorithms for the SCM Risk Intelligence Platform."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional


def _parse_date(d: Any) -> Optional[date]:
    """Parse a date from various formats."""
    if d is None:
        return None
    if isinstance(d, date):
        return d
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, str):
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
            try:
                return datetime.strptime(d, fmt).date()
            except ValueError:
                continue
    return None


CRITICALITY_WEIGHTS = {
    "critical": 1.0,
    "high": 0.75,
    "medium": 0.5,
    "low": 0.25,
}


def calculate_equipment_risk_score(equipment_data: Dict[str, Any]) -> float:
    """
    Calculate risk score for equipment (0-10) based on:
    - Criticality level
    - Equipment value (weight as proxy)
    - Deadline proximity
    - Route risk level
    - Active disruptions exposure
    """
    score = 0.0

    # Criticality factor (0-3 points)
    criticality = str(equipment_data.get("criticality", "medium")).lower()
    score += CRITICALITY_WEIGHTS.get(criticality, 0.5) * 3.0

    # Deadline proximity factor (0-2.5 points)
    required_date = _parse_date(equipment_data.get("requiredOnSiteDate"))
    if required_date:
        today = date.today()
        days_remaining = (required_date - today).days
        if days_remaining <= 0:
            score += 2.5  # Already overdue
        elif days_remaining <= 30:
            score += 2.0
        elif days_remaining <= 60:
            score += 1.5
        elif days_remaining <= 90:
            score += 1.0
        elif days_remaining <= 180:
            score += 0.5

    # Route risk (0-2 points)
    route_status = str(equipment_data.get("routeStatus", "active")).lower()
    route_status_scores = {
        "blocked": 2.0,
        "disrupted": 1.5,
        "delayed": 1.0,
        "active": 0.0,
        "planned": 0.0,
    }
    score += route_status_scores.get(route_status, 0.5)

    # Zone risk level (0-1.5 points)
    zone_risk = equipment_data.get("zoneRiskLevel") or 0
    if isinstance(zone_risk, (int, float)):
        score += min(1.5, zone_risk / 10 * 1.5)

    # Disruption severity (0-1 point)
    disruption_severity = equipment_data.get("disruptionSeverity") or 0
    if isinstance(disruption_severity, (int, float)):
        score += min(1.0, disruption_severity / 5)

    return round(min(10.0, max(0.0, score)), 2)


def calculate_supplier_risk_score(supplier_data: Dict[str, Any]) -> float:
    """
    Calculate supplier risk score (0-10, higher = more risky) based on:
    - Delivery rate (inverse)
    - Quality rate (inverse)
    - Financial rating (inverse)
    - Capacity utilization
    - Risk flags count
    """
    score = 0.0

    # Delivery rate risk (0-3 points) - lower delivery = higher risk
    delivery_rate = supplier_data.get("onTimeDeliveryRate")
    if delivery_rate is not None:
        score += (1.0 - delivery_rate / 100.0) * 3.0
    else:
        score += 1.5  # Unknown = moderate risk

    # Quality reject rate risk (0-2.5 points) - higher reject = higher risk
    quality_reject_rate = supplier_data.get("qualityRejectRate")
    if quality_reject_rate is not None:
        score += (quality_reject_rate / 100.0) * 2.5
    else:
        score += 1.25

    # Financial rating risk (0-2 points)
    financial_rating = supplier_data.get("financialRating")
    if financial_rating is not None:
        score += (1.0 - financial_rating / 10.0) * 2.0
    else:
        score += 1.0

    # Capacity utilization risk (0-1.5 points) - over 90% = risky
    capacity = supplier_data.get("capacityUtilization")
    if capacity is not None:
        if capacity > 90:
            score += 1.5
        elif capacity > 80:
            score += 1.0
        elif capacity > 70:
            score += 0.5
    else:
        score += 0.5

    # Risk flags (0-1 point)
    risk_flags = supplier_data.get("riskFlags") or []
    flag_count = len(risk_flags) if isinstance(risk_flags, list) else 0
    score += min(1.0, flag_count * 0.33)

    return round(min(10.0, max(0.0, score)), 2)


def calculate_route_risk_score(route_data: Dict[str, Any]) -> float:
    """
    Calculate route risk score (0-10) based on:
    - Zones it passes through and their risk levels
    - Current route status
    - Active disruptions in route zones
    """
    score = 0.0

    # Route status (0-3 points)
    status = str(route_data.get("currentStatus", "active")).lower()
    status_scores = {
        "blocked": 3.0,
        "disrupted": 2.5,
        "delayed": 1.5,
        "active": 0.0,
        "planned": 0.5,
    }
    score += status_scores.get(status, 1.0)

    # Zone risk levels (0-4 points)
    zones = route_data.get("zones") or []
    if zones:
        max_risk = 0
        total_risk = 0
        for z in zones:
            risk = z.get("riskLevel") or 0
            max_risk = max(max_risk, risk)
            total_risk += risk
        avg_risk = total_risk / len(zones) if zones else 0
        score += (max_risk / 10) * 2.0 + (avg_risk / 10) * 2.0
    else:
        score += 1.0  # Unknown zones = some risk

    # Active disruptions in zones (0-3 points)
    disruptions = route_data.get("activeDisruptions") or []
    if isinstance(disruptions, list):
        max_severity = 0
        for d in disruptions:
            sev = d.get("severity") or 0
            max_severity = max(max_severity, sev)
        score += min(3.0, max_severity / 5 * 3.0)
    elif isinstance(disruptions, (int, float)):
        score += min(3.0, disruptions)

    return round(min(10.0, max(0.0, score)), 2)


def calculate_disruption_impact_score(
    disruption: Dict[str, Any],
    affected_items: Dict[str, Any],
) -> float:
    """
    Calculate overall disruption impact score (0-10) based on:
    - Disruption severity
    - Number and criticality of affected equipment
    - Number of affected projects
    - Number of affected routes
    """
    score = 0.0

    # Disruption severity (0-3 points)
    severity = disruption.get("severity") or 1
    score += (severity / 5) * 3.0

    # Affected equipment count and criticality (0-3 points)
    equipment = affected_items.get("equipment") or []
    if equipment:
        critical_count = sum(
            1 for e in equipment
            if str(e.get("criticality", "")).lower() == "critical"
        )
        high_count = sum(
            1 for e in equipment
            if str(e.get("criticality", "")).lower() == "high"
        )
        equip_score = min(3.0, critical_count * 0.6 + high_count * 0.3 + len(equipment) * 0.1)
        score += equip_score

    # Affected projects (0-2 points)
    projects = affected_items.get("projects") or []
    score += min(2.0, len(projects) * 0.5)

    # Affected routes (0-2 points)
    routes = affected_items.get("routes") or []
    score += min(2.0, len(routes) * 0.4)

    return round(min(10.0, max(0.0, score)), 2)


def rank_alternatives(
    alternatives: List[Dict[str, Any]],
    weights: Optional[Dict[str, float]] = None,
) -> List[Dict[str, Any]]:
    """
    Multi-criteria ranking for supplier or route alternatives.

    Default weights:
    - costDelta: 0.3 (lower is better)
    - leadTimeDelta: 0.3 (lower is better)
    - qualityScore: 0.2 (higher is better)
    - certMatch: 0.1 (higher is better)
    - relationshipScore: 0.1 (higher is better)
    """
    if not alternatives:
        return []

    default_weights = {
        "costDelta": 0.3,
        "leadTimeDelta": 0.3,
        "qualityScore": 0.2,
        "certMatch": 0.1,
        "relationshipScore": 0.1,
    }
    w = {**default_weights, **(weights or {})}

    # Normalize and calculate scores
    max_cost_delta = max(
        (abs(a.get("costDelta", 0)) for a in alternatives), default=1
    ) or 1
    max_lead_time = max(
        (abs(a.get("leadTimeDelta", 0)) for a in alternatives), default=1
    ) or 1

    scored = []
    for alt in alternatives:
        cost_norm = 1.0 - min(1.0, abs(alt.get("costDelta", 0)) / max_cost_delta)
        lt_norm = 1.0 - min(1.0, abs(alt.get("leadTimeDelta", 0)) / max_lead_time)
        quality = min(1.0, (alt.get("qualityScore", 0.5)))
        cert = min(1.0, alt.get("certMatch", 0.5))
        rel = min(1.0, alt.get("relationshipScore", 0.5))

        composite = (
            w["costDelta"] * cost_norm
            + w["leadTimeDelta"] * lt_norm
            + w["qualityScore"] * quality
            + w["certMatch"] * cert
            + w["relationshipScore"] * rel
        )
        alt_copy = {**alt, "compositeScore": round(composite, 4)}
        scored.append(alt_copy)

    scored.sort(key=lambda x: x["compositeScore"], reverse=True)
    for rank, item in enumerate(scored, 1):
        item["rank"] = rank

    return scored
