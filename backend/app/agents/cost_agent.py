"""Cost/ROI Analysis Agent for the SCM Risk Intelligence Platform.

Takes mitigation scenarios from supplier and route agents, calculates total
disruption cost for the no-action scenario, and compares mitigation options.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.agents.tools.optimization import (
    calculate_delay_penalty,
    calculate_roi,
    calculate_total_disruption_cost,
    compare_scenarios,
)

logger = logging.getLogger(__name__)

# Default cost parameters
DEFAULT_SITE_OVERHEAD_PER_DAY = 50000.0  # $50K/day
DEFAULT_IDLE_WORKFORCE_PER_DAY = 25000.0
DEFAULT_LD_RATE_PCT_PER_WEEK = 0.5  # 0.5% of PO value per week
DEFAULT_SYSTEM_ANNUAL_COST = 500000.0  # Platform cost per year


class CostAgent:
    """Calculates disruption costs, compares mitigation scenarios, and computes ROI."""

    def __init__(self) -> None:
        self.name = "CostAgent"

    async def run(
        self,
        affected_projects: List[Dict[str, Any]],
        affected_equipment: List[Dict[str, Any]],
        supplier_recommendations: Optional[Dict[str, Any]] = None,
        route_recommendations: Optional[Dict[str, Any]] = None,
        delay_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Run full cost analysis including no-action cost, mitigation scenarios, and ROI.

        Args:
            affected_projects: List of project dicts with totalValue, etc.
            affected_equipment: List of affected equipment dicts.
            supplier_recommendations: Output from SupplierAgent.run().
            route_recommendations: Output from RouteAgent.run().
            delay_days: Estimated delay in days for the no-action scenario.

        Returns:
            Full cost analysis with scenario comparison and ROI.
        """
        logger.info(
            "CostAgent.run: analyzing costs for %d projects, %d equipment, %d day delay",
            len(affected_projects), len(affected_equipment), delay_days,
        )

        # Step 1: Calculate no-action (do-nothing) cost
        no_action_cost = calculate_total_disruption_cost(
            affected_projects=affected_projects,
            affected_equipment=affected_equipment,
            delay_days=delay_days,
            site_overhead_per_day=DEFAULT_SITE_OVERHEAD_PER_DAY,
            idle_workforce_per_day=DEFAULT_IDLE_WORKFORCE_PER_DAY,
        )

        total_no_action = no_action_cost["totalDisruptionCost"]

        # Step 2: Build mitigation scenarios
        scenarios = self._build_scenarios(
            total_no_action,
            delay_days,
            supplier_recommendations,
            route_recommendations,
            affected_projects,
            affected_equipment,
        )

        # Step 3: Compare scenarios
        comparison = compare_scenarios(scenarios)

        # Step 4: Calculate platform ROI
        # Assume the platform helps avoid or reduce disruption costs
        best_scenario = comparison.get("bestScenario")
        platform_savings = best_scenario.get("netSavings", 0) if best_scenario else 0
        # Annualize: assume 2-3 disruptions per year
        annual_savings = platform_savings * 2.5
        roi_analysis = calculate_roi(
            savings=annual_savings,
            system_cost=DEFAULT_SYSTEM_ANNUAL_COST,
            period_years=1.0,
        )

        return {
            "noActionCost": no_action_cost,
            "mitigationScenarios": comparison,
            "roiAnalysis": roi_analysis,
            "delayDays": delay_days,
            "affectedProjectCount": len(affected_projects),
            "affectedEquipmentCount": len(affected_equipment),
            "summary": self._generate_summary(
                no_action_cost, comparison, roi_analysis, delay_days
            ),
        }

    def _build_scenarios(
        self,
        no_action_total: float,
        delay_days: int,
        supplier_recs: Optional[Dict[str, Any]],
        route_recs: Optional[Dict[str, Any]],
        projects: List[Dict[str, Any]],
        equipment: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Build mitigation scenario dicts for comparison."""
        daily_cost_rate = DEFAULT_SITE_OVERHEAD_PER_DAY + DEFAULT_IDLE_WORKFORCE_PER_DAY
        scenarios: List[Dict[str, Any]] = []

        # Scenario 1: Reroute shipping (if route recommendations available)
        if route_recs and route_recs.get("routeRecommendations"):
            recs = route_recs["routeRecommendations"]
            total_reroute_cost = 0.0
            max_additional_days = 0
            for rec in recs:
                best = rec.get("bestAlternative")
                if best:
                    total_reroute_cost += best.get("costDelta", 0)
                    max_additional_days = max(
                        max_additional_days, best.get("additionalDays", 0)
                    )

            residual_delay = min(delay_days, max_additional_days)

            scenarios.append({
                "name": "Route Rerouting",
                "description": (
                    f"Reroute {len(recs)} blocked route(s) via alternative shipping lanes. "
                    f"Reduces delay from {delay_days} to {residual_delay} days."
                ),
                "implementationCost": total_reroute_cost,
                "residualDelayDays": residual_delay,
                "riskReduction": 0.6,
                "noActionCost": no_action_total,
                "dailyCostRate": daily_cost_rate,
                "timeToImplementDays": 3,
            })

        # Scenario 2: Switch suppliers (if supplier recommendations available)
        if supplier_recs and supplier_recs.get("recommendations"):
            recs = supplier_recs["recommendations"]
            total_switch_cost = 0.0
            max_additional_days = 0
            switches_available = 0

            for rec in recs:
                impact = rec.get("switchImpact", {})
                if impact.get("feasible"):
                    total_switch_cost += abs(impact.get("estimatedCostImpact", 0))
                    max_additional_days = max(
                        max_additional_days,
                        impact.get("totalAdditionalDays", 0),
                    )
                    switches_available += 1

            if switches_available > 0:
                residual_delay = min(delay_days, max_additional_days)
                scenarios.append({
                    "name": "Supplier Switch",
                    "description": (
                        f"Switch {switches_available} equipment item(s) to alternative suppliers. "
                        f"Reduces delay from {delay_days} to {residual_delay} days."
                    ),
                    "implementationCost": total_switch_cost,
                    "residualDelayDays": residual_delay,
                    "riskReduction": 0.5,
                    "noActionCost": no_action_total,
                    "dailyCostRate": daily_cost_rate,
                    "timeToImplementDays": 7,
                })

        # Scenario 3: Combined reroute + supplier switch
        if len(scenarios) >= 2:
            reroute = scenarios[0]
            switch = scenarios[1]
            combined_cost = reroute["implementationCost"] + switch["implementationCost"]
            combined_residual = min(
                reroute["residualDelayDays"],
                switch["residualDelayDays"],
            )
            # Combined approach usually reduces residual further
            combined_residual = max(0, combined_residual - 5)

            scenarios.append({
                "name": "Combined: Reroute + Supplier Switch",
                "description": (
                    "Execute both rerouting and supplier switching simultaneously "
                    f"for maximum delay reduction to {combined_residual} days."
                ),
                "implementationCost": combined_cost,
                "residualDelayDays": combined_residual,
                "riskReduction": 0.8,
                "noActionCost": no_action_total,
                "dailyCostRate": daily_cost_rate,
                "timeToImplementDays": 7,
            })

        # Scenario 4: Air freight for critical items
        air_eligible_count = sum(
            1 for eq in equipment
            if (eq.get("weight") or 0) <= 5.0
            and str(eq.get("criticality", "")).lower() == "critical"
        )
        if air_eligible_count > 0:
            avg_weight_kg = 2000  # Rough average
            air_cost = air_eligible_count * avg_weight_kg * 8.0  # $8/kg
            air_residual = max(0, delay_days - (delay_days - 3))  # Air freight is ~3 days

            scenarios.append({
                "name": "Air Freight Critical Items",
                "description": (
                    f"Air freight {air_eligible_count} critical equipment item(s) "
                    f"weighing under 5 tons. Transit time: ~3 days."
                ),
                "implementationCost": air_cost,
                "residualDelayDays": air_residual,
                "riskReduction": 0.4,
                "noActionCost": no_action_total,
                "dailyCostRate": daily_cost_rate,
                "timeToImplementDays": 1,
            })

        # Scenario 5: Accept delay (buffer schedule)
        if delay_days <= 14:
            scenarios.append({
                "name": "Accept Delay (Schedule Buffer)",
                "description": (
                    f"Absorb the {delay_days}-day delay using project schedule buffers. "
                    "No additional cost if within contractual tolerance."
                ),
                "implementationCost": 0,
                "residualDelayDays": delay_days,
                "riskReduction": 0.0,
                "noActionCost": no_action_total,
                "dailyCostRate": daily_cost_rate,
                "timeToImplementDays": 0,
            })

        # Always include no-action as baseline
        scenarios.append({
            "name": "No Action (Baseline)",
            "description": (
                f"Do nothing and absorb full {delay_days}-day delay with all associated costs."
            ),
            "implementationCost": 0,
            "residualDelayDays": delay_days,
            "riskReduction": 0.0,
            "noActionCost": no_action_total,
            "dailyCostRate": daily_cost_rate,
            "timeToImplementDays": 0,
        })

        return scenarios

    def _generate_summary(
        self,
        no_action_cost: Dict[str, Any],
        comparison: Dict[str, Any],
        roi_analysis: Dict[str, Any],
        delay_days: int,
    ) -> str:
        """Generate human-readable cost analysis summary."""
        total_no_action = no_action_cost.get("totalDisruptionCost", 0)

        lines = [
            "COST ANALYSIS SUMMARY",
            f"",
            f"No-Action Scenario ({delay_days} days delay):",
            f"  Total disruption cost: ${total_no_action:,.0f}",
            f"  - LD penalties: ${no_action_cost.get('totalLdPenalty', 0):,.0f}",
            f"  - Site overhead: ${no_action_cost.get('siteOverhead', 0):,.0f}",
            f"  - Idle workforce: ${no_action_cost.get('idleWorkforceCost', 0):,.0f}",
            f"  - Storage costs: ${no_action_cost.get('storageCost', 0):,.0f}",
            f"  - Rework risk: ${no_action_cost.get('reworkRiskCost', 0):,.0f}",
        ]

        best = comparison.get("bestScenario")
        if best and best.get("name") != "No Action (Baseline)":
            lines.extend([
                f"",
                f"Recommended Mitigation: {best.get('name', 'Unknown')}",
                f"  Implementation cost: ${best.get('implementationCost', 0):,.0f}",
                f"  Residual delay: {best.get('residualDelayDays', 0)} days",
                f"  Net savings: ${best.get('netSavings', 0):,.0f}",
                f"  Benefit-cost ratio: {best.get('benefitCostRatio', 0):.1f}x",
            ])

        scenarios = comparison.get("scenarios", [])
        if len(scenarios) > 1:
            lines.append("")
            lines.append("All Scenarios (ranked by net savings):")
            for s in scenarios:
                lines.append(
                    f"  {s.get('rank', '?')}. {s.get('name', 'Unknown')}: "
                    f"${s.get('netSavings', 0):,.0f} net savings "
                    f"(cost: ${s.get('implementationCost', 0):,.0f}, "
                    f"residual: {s.get('residualDelayDays', 0)}d)"
                )

        lines.extend([
            f"",
            f"Platform ROI Analysis:",
            f"  Annual platform cost: ${roi_analysis.get('system_cost', 0):,.0f}",
            f"  Estimated annual savings: ${roi_analysis.get('total_savings', 0):,.0f}",
            f"  ROI: {roi_analysis.get('roi_pct', 0):.0f}%",
            f"  Payback period: {roi_analysis.get('payback_months', 'N/A')} months",
        ])

        return "\n".join(lines)
