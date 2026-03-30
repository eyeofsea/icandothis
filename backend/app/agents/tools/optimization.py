"""Route and cost optimization algorithms for the SCM Risk Intelligence Platform."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def optimize_route(
    origin: str,
    destination: str,
    blocked_zones: List[str],
    available_routes: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Find optimal alternative route avoiding blocked zones.

    Evaluates available routes and returns the best one based on
    a composite score of transit time, cost, and risk.
    """
    if not available_routes:
        return {
            "found": False,
            "message": f"No alternative routes available from {origin} to {destination} avoiding blocked zones.",
            "origin": origin,
            "destination": destination,
            "blockedZones": blocked_zones,
        }

    scored_routes = []
    for route in available_routes:
        # Skip routes passing through blocked zones
        route_zones = [z.get("zoneId", "") for z in (route.get("zones") or [])]
        if any(bz in route_zones for bz in blocked_zones):
            continue

        transit_days = route.get("estimatedTransitDays") or 999
        cost = route.get("shippingCost") or 0
        zone_risk = max(
            (z.get("riskLevel", 0) for z in (route.get("zones") or [])),
            default=0,
        )

        # Normalize factors (lower is better for all)
        time_score = min(1.0, transit_days / 60.0)
        cost_score = min(1.0, cost / 500000.0) if cost > 0 else 0.5
        risk_score = zone_risk / 10.0

        # Weighted composite (lower = better)
        composite = 0.4 * time_score + 0.35 * cost_score + 0.25 * risk_score

        scored_routes.append({
            **route,
            "optimizationScore": round(1.0 - composite, 4),
            "timeScore": round(1.0 - time_score, 4),
            "costScore": round(1.0 - cost_score, 4),
            "riskScore": round(1.0 - risk_score, 4),
        })

    scored_routes.sort(key=lambda r: r["optimizationScore"], reverse=True)
    for rank, r in enumerate(scored_routes, 1):
        r["rank"] = rank

    if not scored_routes:
        return {
            "found": False,
            "message": "All available routes pass through blocked zones.",
            "origin": origin,
            "destination": destination,
            "blockedZones": blocked_zones,
        }

    return {
        "found": True,
        "bestRoute": scored_routes[0],
        "alternatives": scored_routes[1:],
        "totalOptions": len(scored_routes),
        "origin": origin,
        "destination": destination,
        "blockedZones": blocked_zones,
    }


def calculate_rerouting_cost(
    original_route: Dict[str, Any],
    alternative_route: Dict[str, Any],
    equipment: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Calculate cost delta between original and alternative route."""
    orig_shipping = original_route.get("shippingCost") or 0
    orig_insurance = original_route.get("insuranceCost") or 0
    orig_days = original_route.get("estimatedTransitDays") or 0

    alt_shipping = alternative_route.get("shippingCost") or 0
    alt_insurance = alternative_route.get("insuranceCost") or 0
    alt_days = alternative_route.get("estimatedTransitDays") or 0

    shipping_delta = alt_shipping - orig_shipping
    insurance_delta = alt_insurance - orig_insurance
    day_delta = alt_days - orig_days

    # Additional costs for heavy/oversized equipment
    equipment_surcharge = 0.0
    if equipment:
        weight = equipment.get("weight") or 0
        if weight > 100:  # Over 100 tons, heavy-lift surcharge
            equipment_surcharge = weight * 50  # $50/ton surcharge
        elif weight > 50:
            equipment_surcharge = weight * 25

    total_delta = shipping_delta + insurance_delta + equipment_surcharge

    # Warehouse/storage costs if delay occurs
    storage_cost_per_day = 2500.0  # $2,500/day average
    storage_cost = max(0, day_delta) * storage_cost_per_day

    return {
        "shippingCostDelta": round(shipping_delta, 2),
        "insuranceCostDelta": round(insurance_delta, 2),
        "equipmentSurcharge": round(equipment_surcharge, 2),
        "storageCost": round(storage_cost, 2),
        "totalCostDelta": round(total_delta + storage_cost, 2),
        "additionalDays": day_delta,
        "originalRoute": {
            "routeId": original_route.get("routeId"),
            "name": original_route.get("name"),
            "cost": orig_shipping + orig_insurance,
            "days": orig_days,
        },
        "alternativeRoute": {
            "routeId": alternative_route.get("routeId"),
            "name": alternative_route.get("name"),
            "cost": alt_shipping + alt_insurance,
            "days": alt_days,
        },
    }


def calculate_delay_penalty(
    project: Dict[str, Any],
    delay_days: int,
    ld_rate_pct_per_week: float = 0.5,
) -> Dict[str, Any]:
    """
    Calculate contractual Liquidated Damages for project delay.

    Default LD rate: 0.5% of PO value per week of delay.
    Typical cap: 10% of total value.
    """
    total_value = project.get("totalValue") or 0
    if total_value <= 0 or delay_days <= 0:
        return {
            "projectId": project.get("projectId"),
            "projectName": project.get("name"),
            "delayDays": delay_days,
            "ldPenalty": 0.0,
            "ldRatePerWeek": ld_rate_pct_per_week,
            "weeklyPenalty": 0.0,
            "cappedAt": 0.0,
            "isCapped": False,
        }

    delay_weeks = delay_days / 7.0
    weekly_penalty = total_value * (ld_rate_pct_per_week / 100.0)
    raw_penalty = weekly_penalty * delay_weeks

    # LD cap at 10% of total value
    ld_cap = total_value * 0.10
    actual_penalty = min(raw_penalty, ld_cap)
    is_capped = raw_penalty > ld_cap

    return {
        "projectId": project.get("projectId"),
        "projectName": project.get("name"),
        "delayDays": delay_days,
        "delayWeeks": round(delay_weeks, 1),
        "ldPenalty": round(actual_penalty, 2),
        "ldRatePerWeek": ld_rate_pct_per_week,
        "weeklyPenalty": round(weekly_penalty, 2),
        "rawPenalty": round(raw_penalty, 2),
        "cappedAt": round(ld_cap, 2),
        "isCapped": is_capped,
    }


def calculate_total_disruption_cost(
    affected_projects: List[Dict[str, Any]],
    affected_equipment: List[Dict[str, Any]],
    delay_days: int = 30,
    site_overhead_per_day: float = 50000.0,
    idle_workforce_per_day: float = 25000.0,
) -> Dict[str, Any]:
    """
    Full cost model for a disruption scenario (no-action case).

    Includes:
    - Delay penalties (contractual LD)
    - Extended site overhead
    - Idle workforce costs
    - Equipment storage costs
    - Potential rework costs
    """
    # Delay penalties per project
    ld_penalties = []
    total_ld = 0.0
    for proj in affected_projects:
        penalty = calculate_delay_penalty(proj, delay_days)
        ld_penalties.append(penalty)
        total_ld += penalty["ldPenalty"]

    # Site overhead
    site_overhead = delay_days * site_overhead_per_day

    # Idle workforce
    idle_workforce = delay_days * idle_workforce_per_day

    # Equipment storage/demurrage
    storage_cost = 0.0
    for equip in affected_equipment:
        weight = equip.get("weight") or 10
        criticality = str(equip.get("criticality", "medium")).lower()
        daily_rate = 500.0  # Base daily storage
        if weight > 100:
            daily_rate = 2000.0
        elif weight > 50:
            daily_rate = 1000.0
        if criticality == "critical":
            daily_rate *= 1.5  # Premium storage for critical items
        storage_cost += daily_rate * delay_days

    # Rework risk (5% chance of rework for critical equipment)
    rework_cost = 0.0
    for equip in affected_equipment:
        if str(equip.get("criticality", "")).lower() == "critical":
            estimated_value = (equip.get("weight") or 50) * 1000  # Rough proxy
            rework_cost += estimated_value * 0.05

    total_cost = total_ld + site_overhead + idle_workforce + storage_cost + rework_cost

    return {
        "delayDays": delay_days,
        "ldPenalties": ld_penalties,
        "totalLdPenalty": round(total_ld, 2),
        "siteOverhead": round(site_overhead, 2),
        "siteOverheadPerDay": site_overhead_per_day,
        "idleWorkforceCost": round(idle_workforce, 2),
        "idleWorkforcePerDay": idle_workforce_per_day,
        "storageCost": round(storage_cost, 2),
        "reworkRiskCost": round(rework_cost, 2),
        "totalDisruptionCost": round(total_cost, 2),
        "affectedProjectCount": len(affected_projects),
        "affectedEquipmentCount": len(affected_equipment),
        "breakdown": {
            "ldPenalties": round(total_ld / total_cost * 100, 1) if total_cost > 0 else 0,
            "siteOverhead": round(site_overhead / total_cost * 100, 1) if total_cost > 0 else 0,
            "idleWorkforce": round(idle_workforce / total_cost * 100, 1) if total_cost > 0 else 0,
            "storage": round(storage_cost / total_cost * 100, 1) if total_cost > 0 else 0,
            "reworkRisk": round(rework_cost / total_cost * 100, 1) if total_cost > 0 else 0,
        },
    }


def compare_scenarios(
    scenarios: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Side-by-side comparison of mitigation scenarios.

    Each scenario should have:
    - name: scenario label
    - implementationCost: cost to execute the mitigation
    - residualDelayDays: remaining delay after mitigation
    - riskReduction: how much risk is reduced (0-1)
    - description: what the scenario entails
    """
    if not scenarios:
        return {"scenarios": [], "recommendation": "No scenarios provided."}

    evaluated = []
    for scenario in scenarios:
        impl_cost = scenario.get("implementationCost", 0)
        residual_delay = scenario.get("residualDelayDays", 0)
        no_action_cost = scenario.get("noActionCost", 0)
        risk_reduction = scenario.get("riskReduction", 0)

        # Net savings = what you would have lost minus (implementation cost + residual cost)
        residual_cost = residual_delay * scenario.get("dailyCostRate", 75000)
        net_savings = no_action_cost - impl_cost - residual_cost
        benefit_cost_ratio = net_savings / impl_cost if impl_cost > 0 else float("inf")

        evaluated.append({
            **scenario,
            "residualCost": round(residual_cost, 2),
            "netSavings": round(net_savings, 2),
            "benefitCostRatio": round(benefit_cost_ratio, 2),
            "totalCost": round(impl_cost + residual_cost, 2),
        })

    # Sort by net savings (highest first)
    evaluated.sort(key=lambda s: s["netSavings"], reverse=True)
    for rank, s in enumerate(evaluated, 1):
        s["rank"] = rank

    best = evaluated[0] if evaluated else None
    recommendation = ""
    if best:
        if best["netSavings"] > 0:
            recommendation = (
                f"Recommended: '{best.get('name', 'Scenario 1')}' with net savings of "
                f"${best['netSavings']:,.0f} and benefit-cost ratio of {best['benefitCostRatio']:.1f}x."
            )
        else:
            recommendation = (
                "No scenario provides positive net savings. Consider accepting the delay "
                "or exploring additional mitigation options."
            )

    return {
        "scenarios": evaluated,
        "recommendation": recommendation,
        "bestScenario": best,
    }


def calculate_roi(
    savings: float,
    system_cost: float,
    period_years: float = 1.0,
) -> Dict[str, Any]:
    """
    Calculate ROI for the risk intelligence platform.

    ROI = (Net Savings - System Cost) / System Cost * 100
    """
    if system_cost <= 0:
        return {
            "roi_pct": 0.0,
            "net_benefit": savings,
            "payback_months": 0,
            "message": "System cost must be positive.",
        }

    net_benefit = savings - system_cost
    roi_pct = (net_benefit / system_cost) * 100

    # Payback period
    monthly_savings = savings / (period_years * 12) if period_years > 0 else 0
    payback_months = system_cost / monthly_savings if monthly_savings > 0 else float("inf")

    return {
        "roi_pct": round(roi_pct, 1),
        "net_benefit": round(net_benefit, 2),
        "total_savings": round(savings, 2),
        "system_cost": round(system_cost, 2),
        "payback_months": round(payback_months, 1) if payback_months != float("inf") else None,
        "annualized_savings": round(savings / period_years, 2) if period_years > 0 else 0,
        "period_years": period_years,
        "verdict": "positive" if roi_pct > 0 else "negative",
    }
