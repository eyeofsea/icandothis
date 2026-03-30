"""Route Optimization Agent for the SCM Risk Intelligence Platform.

Takes blocked routes and equipment specs, finds alternative routes avoiding
disrupted zones, evaluates multimodal options, and returns ranked alternatives.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.agents.tools.neo4j_tools import (
    find_alternative_routes,
    query_neo4j,
)
from app.agents.tools.optimization import (
    calculate_rerouting_cost,
    optimize_route,
)
from app.agents.tools.scoring import calculate_route_risk_score

logger = logging.getLogger(__name__)


# Air freight threshold: 5 metric tons
AIR_FREIGHT_MAX_WEIGHT_TONS = 5.0
AIR_FREIGHT_COST_PER_KG = 8.0  # USD per kg
AIR_FREIGHT_TRANSIT_DAYS = 3


class RouteAgent:
    """Finds and ranks alternative routes for blocked shipping lanes."""

    def __init__(self) -> None:
        self.name = "RouteAgent"

    async def run(
        self,
        blocked_routes: List[Dict[str, Any]],
        equipment_list: Optional[List[Dict[str, Any]]] = None,
        disrupted_zone_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Find and rank alternative routes for blocked shipping lanes.

        Args:
            blocked_routes: Routes that are blocked/disrupted with routeId, name, etc.
            equipment_list: Equipment that needs rerouting (for weight/dimension checks).
            disrupted_zone_ids: Zone IDs to avoid.

        Returns:
            Ranked route alternatives per blocked route with cost/time trade-offs.
        """
        logger.info("RouteAgent.run: processing %d blocked routes", len(blocked_routes))
        disrupted_zone_ids = disrupted_zone_ids or []
        equipment_list = equipment_list or []

        route_recommendations: List[Dict[str, Any]] = []

        for blocked in blocked_routes:
            route_id = blocked.get("routeId", "")
            route_name = blocked.get("name", "Unknown")

            # Find alternative sea/land routes
            try:
                alternatives = await find_alternative_routes(
                    blocked_route_id=route_id,
                    disrupted_zone_ids=disrupted_zone_ids,
                )
            except Exception as exc:
                logger.warning("Failed to find alternatives for route %s: %s", route_id, exc)
                alternatives = []

            # Score each alternative
            scored_alternatives = []
            for alt in alternatives:
                risk_score = calculate_route_risk_score(alt)
                rerouting_cost = calculate_rerouting_cost(blocked, alt)

                scored_alternatives.append({
                    **alt,
                    "riskScore": risk_score,
                    "reroutingCost": rerouting_cost,
                    "costDelta": rerouting_cost.get("totalCostDelta", 0),
                    "leadTimeDelta": alt.get("additionalDays", 0),
                    "qualityScore": max(0, 1.0 - risk_score / 10.0),
                    "certMatch": 0.8,  # Routes don't have cert matching
                    "relationshipScore": 0.7,
                })

            # Sort by composite of time and cost
            scored_alternatives.sort(
                key=lambda a: (
                    0.4 * (a.get("additionalDays", 0) / max(1, max((x.get("additionalDays", 1) for x in scored_alternatives), default=1)))
                    + 0.35 * (a.get("costDelta", 0) / max(1, max((x.get("costDelta", 1) for x in scored_alternatives), default=1)))
                    + 0.25 * (a.get("riskScore", 0) / 10.0)
                )
            )

            for rank, alt in enumerate(scored_alternatives, 1):
                alt["rank"] = rank

            # Check air freight feasibility for associated equipment
            air_freight_options = self._evaluate_air_freight(equipment_list, blocked)

            # Evaluate multimodal options
            multimodal_options = self._evaluate_multimodal(
                blocked, scored_alternatives, equipment_list
            )

            route_recommendations.append({
                "blockedRoute": {
                    "routeId": route_id,
                    "name": route_name,
                    "status": blocked.get("currentStatus"),
                    "originalTransitDays": blocked.get("estimatedTransitDays"),
                    "originalCost": blocked.get("shippingCost"),
                },
                "alternativeCount": len(scored_alternatives),
                "alternatives": scored_alternatives[:5],  # Top 5
                "bestAlternative": scored_alternatives[0] if scored_alternatives else None,
                "airFreightOptions": air_freight_options,
                "multimodalOptions": multimodal_options,
                "recommendation": self._make_recommendation(
                    scored_alternatives, air_freight_options, multimodal_options
                ),
            })

        # Overall summary
        total_blocked = len(blocked_routes)
        routes_with_alts = sum(1 for r in route_recommendations if r["alternativeCount"] > 0)

        return {
            "routeRecommendations": route_recommendations,
            "totalBlockedRoutes": total_blocked,
            "routesWithAlternatives": routes_with_alts,
            "routesWithoutAlternatives": total_blocked - routes_with_alts,
            "disruptedZonesAvoided": disrupted_zone_ids,
            "summary": self._generate_summary(route_recommendations),
        }

    def _evaluate_air_freight(
        self,
        equipment_list: List[Dict[str, Any]],
        blocked_route: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Check which equipment items are eligible for air freight (< 5 tons)."""
        options = []
        for eq in equipment_list:
            weight_tons = (eq.get("weight") or 0)  # Weight assumed in metric tons
            equip_id = eq.get("equipmentId", "unknown")
            equip_name = eq.get("name", "Unknown")

            if weight_tons <= 0:
                continue

            if weight_tons <= AIR_FREIGHT_MAX_WEIGHT_TONS:
                weight_kg = weight_tons * 1000
                air_cost = weight_kg * AIR_FREIGHT_COST_PER_KG
                original_cost = blocked_route.get("shippingCost") or 0
                cost_delta = air_cost - original_cost

                original_days = blocked_route.get("estimatedTransitDays") or 30
                days_saved = original_days - AIR_FREIGHT_TRANSIT_DAYS

                options.append({
                    "equipmentId": equip_id,
                    "equipmentName": equip_name,
                    "weightTons": weight_tons,
                    "feasible": True,
                    "airFreightCost": round(air_cost, 2),
                    "costDelta": round(cost_delta, 2),
                    "transitDays": AIR_FREIGHT_TRANSIT_DAYS,
                    "daysSaved": max(0, days_saved),
                    "costPerDaySaved": round(cost_delta / max(1, days_saved), 2) if days_saved > 0 else 0,
                })
            else:
                options.append({
                    "equipmentId": equip_id,
                    "equipmentName": equip_name,
                    "weightTons": weight_tons,
                    "feasible": False,
                    "reason": f"Weight ({weight_tons:.1f}t) exceeds air freight limit ({AIR_FREIGHT_MAX_WEIGHT_TONS}t).",
                })

        return options

    def _evaluate_multimodal(
        self,
        blocked_route: Dict[str, Any],
        sea_alternatives: List[Dict[str, Any]],
        equipment_list: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Evaluate multimodal transport options (sea + rail, sea + truck, etc.)."""
        options = []
        original_days = blocked_route.get("estimatedTransitDays") or 30
        original_cost = blocked_route.get("shippingCost") or 50000

        # Option 1: Partial sea + overland (rail/truck for the blocked segment)
        if sea_alternatives:
            best_sea = sea_alternatives[0] if sea_alternatives else {}
            sea_days = best_sea.get("estimatedTransitDays") or original_days
            sea_cost = best_sea.get("shippingCost") or original_cost

            # Rail option: typically 30% more expensive than sea but faster
            rail_segment_cost = original_cost * 0.3
            rail_segment_days = max(3, original_days // 4)
            total_rail_days = max(sea_days - 5, rail_segment_days + sea_days // 2)
            total_rail_cost = sea_cost * 0.6 + rail_segment_cost

            options.append({
                "mode": "sea_rail",
                "description": "Partial sea route with rail connection for blocked segment",
                "estimatedTransitDays": total_rail_days,
                "estimatedCost": round(total_rail_cost, 2),
                "additionalDays": total_rail_days - original_days,
                "additionalCost": round(total_rail_cost - original_cost, 2),
                "reliability": 0.85,
                "maxWeightTons": 500,  # Rail can handle heavy items
            })

        # Option 2: Truck (for shorter distances / lighter items)
        truck_cost = original_cost * 1.5  # Truck typically 50% more than sea
        truck_days = max(5, original_days // 2)  # Faster but limited range

        max_weight_for_truck = 40.0  # 40 tons max for standard trucking
        light_equipment = [
            eq for eq in equipment_list
            if (eq.get("weight") or 0) <= max_weight_for_truck
        ]

        if light_equipment:
            options.append({
                "mode": "truck",
                "description": "Overland trucking for items under 40 tons",
                "estimatedTransitDays": truck_days,
                "estimatedCost": round(truck_cost, 2),
                "additionalDays": truck_days - original_days,
                "additionalCost": round(truck_cost - original_cost, 2),
                "reliability": 0.90,
                "maxWeightTons": max_weight_for_truck,
                "eligibleEquipmentCount": len(light_equipment),
            })

        # Option 3: Expedited sea (premium carrier, faster vessel)
        expedited_cost = original_cost * 1.8
        expedited_days = max(7, int(original_days * 0.7))

        options.append({
            "mode": "expedited_sea",
            "description": "Premium carrier with expedited service",
            "estimatedTransitDays": expedited_days,
            "estimatedCost": round(expedited_cost, 2),
            "additionalDays": expedited_days - original_days,
            "additionalCost": round(expedited_cost - original_cost, 2),
            "reliability": 0.80,
            "maxWeightTons": 10000,  # No practical weight limit
        })

        return options

    def _make_recommendation(
        self,
        sea_alternatives: List[Dict[str, Any]],
        air_options: List[Dict[str, Any]],
        multimodal_options: List[Dict[str, Any]],
    ) -> str:
        """Generate a recommendation based on all available options."""
        if sea_alternatives:
            best = sea_alternatives[0]
            add_days = best.get("additionalDays", 0)
            add_cost = best.get("costDelta", 0)

            if add_days <= 7 and add_cost <= 50000:
                return (
                    f"Primary recommendation: Reroute via '{best.get('name', 'alternative')}'. "
                    f"Additional {add_days} days and ${add_cost:,.0f} cost - acceptable trade-off."
                )

        feasible_air = [a for a in air_options if a.get("feasible")]
        if feasible_air:
            return (
                f"Consider air freight for {len(feasible_air)} eligible item(s) "
                f"to minimize delays. Sea rerouting available as fallback."
            )

        if multimodal_options:
            best_multi = min(multimodal_options, key=lambda m: m.get("additionalDays", 999))
            return (
                f"Recommend multimodal option: {best_multi.get('description', 'alternative')} "
                f"with estimated {best_multi.get('estimatedTransitDays', 'unknown')} days transit."
            )

        return "No viable alternatives found. Recommend engaging logistics broker for spot market options."

    def _generate_summary(
        self, route_recommendations: List[Dict[str, Any]]
    ) -> str:
        """Generate human-readable route optimization summary."""
        total = len(route_recommendations)
        with_alts = sum(1 for r in route_recommendations if r["alternativeCount"] > 0)

        lines = [
            "ROUTE OPTIMIZATION SUMMARY",
            f"Blocked routes analyzed: {total}",
            f"Routes with alternatives: {with_alts}",
            f"Routes without alternatives: {total - with_alts}",
        ]

        for rec in route_recommendations:
            blocked = rec["blockedRoute"]
            lines.append("")
            lines.append(f"Route: {blocked.get('name', 'Unknown')} ({blocked.get('routeId', '')})")
            lines.append(f"  Status: {blocked.get('status', 'unknown')}")

            if rec.get("bestAlternative"):
                best = rec["bestAlternative"]
                lines.append(f"  Best alternative: {best.get('name', 'Unknown')}")
                lines.append(
                    f"    +{best.get('additionalDays', 0)} days, "
                    f"+${best.get('costDelta', 0):,.0f}"
                )
                lines.append(f"    Risk score: {best.get('riskScore', 0)}/10")

            air_feasible = [a for a in rec.get("airFreightOptions", []) if a.get("feasible")]
            if air_feasible:
                lines.append(f"  Air freight eligible: {len(air_feasible)} item(s)")

            lines.append(f"  Recommendation: {rec.get('recommendation', 'N/A')}")

        return "\n".join(lines)
