"""
Pure-function TCO calculation engine.
No database access — takes data in, returns numbers out.
"""
from typing import Any

# Cost constants
SITE_OVERHEAD_PER_DAY = 50_000
IDLE_WORKFORCE_PER_DAY = 25_000
LD_RATE_PCT_PER_WEEK = 0.5  # % of project value
LD_CAP_PCT = 10.0
STORAGE_RATES = {  # USD/day by weight tier
    100_000: 2_000,  # >100t
    50_000: 1_000,   # >50t
    0: 500,          # base
}
CRITICAL_STORAGE_MULTIPLIER = 1.5
QUALIFICATION_COST_PER_DAY = 5_000


def _storage_rate(weight_kg: float, criticality: str) -> float:
    base = 500
    for threshold, rate in sorted(STORAGE_RATES.items(), reverse=True):
        if weight_kg >= threshold:
            base = rate
            break
    if criticality in ("Critical", "critical"):
        base *= CRITICAL_STORAGE_MULTIPLIER
    return base


def calculate_baseline_tco(
    equipment: list[dict[str, Any]],
    route: dict[str, Any],
    project: dict[str, Any],
    delay_days: int,
) -> dict[str, Any]:
    shipping_cost = route.get("shippingCost", 0)
    insurance_cost = route.get("insuranceCost", 0)

    # Delay penalties (LD)
    project_value = project.get("totalValue", 0)
    if delay_days > 0 and project_value > 0:
        weekly_penalty = project_value * (LD_RATE_PCT_PER_WEEK / 100)
        raw_penalty = weekly_penalty * (delay_days / 7)
        delay_penalties = min(raw_penalty, project_value * (LD_CAP_PCT / 100))
    else:
        delay_penalties = 0

    site_overhead = SITE_OVERHEAD_PER_DAY * delay_days
    idle_workforce = IDLE_WORKFORCE_PER_DAY * delay_days

    storage_cost = 0
    for eq in equipment:
        weight = eq.get("weight", 0)
        crit = eq.get("criticality", "Medium")
        storage_cost += _storage_rate(weight, crit) * delay_days

    total = shipping_cost + insurance_cost + delay_penalties + site_overhead + idle_workforce + storage_cost

    return {
        "shipping_cost": shipping_cost,
        "insurance_cost": insurance_cost,
        "delay_penalties": delay_penalties,
        "site_overhead": site_overhead,
        "idle_workforce": idle_workforce,
        "storage_cost": storage_cost,
        "delay_days": delay_days,
        "total": total,
    }


def calculate_scenario_tco(
    baseline: dict[str, Any],
    equipment: list[dict[str, Any]],
    project: dict[str, Any],
    scenario_type: str,
    original_delay_days: int,
    residual_delay_days: int,
    alternative_route: dict[str, Any] | None = None,
    alternative_supplier: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "scenario_type": scenario_type,
        "original_delay_days": original_delay_days,
        "residual_delay_days": residual_delay_days,
    }

    if scenario_type == "reroute" and alternative_route:
        result["shipping_cost"] = alternative_route.get("shippingCost", 0)
        result["insurance_cost"] = alternative_route.get("insuranceCost", 0)
        result["transit_days_delta"] = (
            alternative_route.get("estimatedTransitDays", 0)
            - baseline.get("delay_days", 0)
        )
        result["implementation_cost"] = abs(
            result["shipping_cost"] - baseline["shipping_cost"]
        ) + abs(result["insurance_cost"] - baseline["insurance_cost"])
        result["qualification_cost"] = 0

    elif scenario_type == "supplier_switch" and alternative_supplier:
        cost_premium = alternative_supplier.get("costPremiumPct", 0)
        eq_total_value = sum(eq.get("value", 0) for eq in equipment)
        result["shipping_cost"] = baseline["shipping_cost"]
        result["insurance_cost"] = baseline["insurance_cost"]
        result["supplier_premium"] = eq_total_value * cost_premium
        qual_days = alternative_supplier.get("qualificationDays", 14)
        result["qualification_cost"] = qual_days * QUALIFICATION_COST_PER_DAY
        result["implementation_cost"] = result["supplier_premium"] + result["qualification_cost"]

    elif scenario_type == "air_freight":
        total_weight_kg = sum(eq.get("weight", 0) for eq in equipment)
        result["shipping_cost"] = total_weight_kg * 8  # $8/kg
        result["insurance_cost"] = baseline["insurance_cost"] * 1.5
        result["implementation_cost"] = result["shipping_cost"]
        result["qualification_cost"] = 0

    else:
        result["shipping_cost"] = baseline.get("shipping_cost", 0)
        result["insurance_cost"] = baseline.get("insurance_cost", 0)
        result["implementation_cost"] = 0
        result["qualification_cost"] = 0

    # Recalculate delay-dependent costs with residual delay
    project_value = project.get("totalValue", 0)
    if residual_delay_days > 0 and project_value > 0:
        weekly_penalty = project_value * (LD_RATE_PCT_PER_WEEK / 100)
        raw_penalty = weekly_penalty * (residual_delay_days / 7)
        result["delay_penalties"] = min(raw_penalty, project_value * (LD_CAP_PCT / 100))
    else:
        result["delay_penalties"] = 0

    result["site_overhead"] = SITE_OVERHEAD_PER_DAY * residual_delay_days
    result["idle_workforce"] = IDLE_WORKFORCE_PER_DAY * residual_delay_days

    storage_cost = 0
    for eq in equipment:
        storage_cost += _storage_rate(eq.get("weight", 0), eq.get("criticality", "Medium")) * residual_delay_days
    result["storage_cost"] = storage_cost

    result["total"] = (
        result.get("shipping_cost", 0)
        + result.get("insurance_cost", 0)
        + result.get("implementation_cost", 0)
        + result["delay_penalties"]
        + result["site_overhead"]
        + result["idle_workforce"]
        + result["storage_cost"]
    )

    return result


def compare_tco(
    baseline: dict[str, Any],
    scenarios: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    baseline_total = baseline["total"]
    ranked = []
    for s in scenarios:
        scenario_total = s["total"]
        impl_cost = s.get("implementation_cost", 0)
        net_savings = baseline_total - scenario_total
        bcr = (net_savings / impl_cost) if impl_cost > 0 else float("inf")
        ranked.append({
            **s,
            "baseline_total": baseline_total,
            "net_savings": net_savings,
            "savings_pct": (net_savings / baseline_total * 100) if baseline_total > 0 else 0,
            "benefit_cost_ratio": round(bcr, 2),
        })

    ranked.sort(key=lambda x: x["net_savings"], reverse=True)
    for i, s in enumerate(ranked):
        s["rank"] = i + 1

    return ranked
