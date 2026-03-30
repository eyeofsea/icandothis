"""Service layer for route operations - bridges routers with agents."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.agents.route_agent import RouteAgent
from app.agents.tools.neo4j_tools import find_alternative_routes, query_neo4j

logger = logging.getLogger(__name__)

_route_cache: Dict[str, Dict[str, Any]] = {}


class RoutingService:
    """Service that bridges HTTP routers with the RouteAgent."""

    def __init__(self) -> None:
        self._agent = RouteAgent()

    async def find_route_alternatives(
        self,
        route_id: str,
        disrupted_zone_ids: Optional[List[str]] = None,
        equipment_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Find alternatives for a specific blocked route.

        Args:
            route_id: The blocked route ID.
            disrupted_zone_ids: Zone IDs to avoid.
            equipment_ids: Equipment IDs shipped on this route.

        Returns:
            Route alternatives with cost/time analysis.
        """
        cache_key = f"route:{route_id}:{','.join(sorted(disrupted_zone_ids or []))}"
        if cache_key in _route_cache:
            return _route_cache[cache_key]

        # Fetch the blocked route
        blocked_route = await self._fetch_route(route_id)
        if not blocked_route:
            return {"error": f"Route {route_id} not found."}

        # Fetch equipment if IDs provided
        equipment_list = []
        if equipment_ids:
            equipment_list = await self._fetch_equipment(equipment_ids)

        result = await self._agent.run(
            blocked_routes=[blocked_route],
            equipment_list=equipment_list,
            disrupted_zone_ids=disrupted_zone_ids or [],
        )

        _route_cache[cache_key] = result
        return result

    async def find_all_disrupted_route_alternatives(
        self,
        disrupted_zone_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Find alternatives for all currently disrupted/blocked routes."""
        # Fetch all disrupted routes
        try:
            records = await query_neo4j(
                """
                MATCH (r:ShippingRoute)
                WHERE r.currentStatus IN ['disrupted', 'blocked']
                RETURN r {
                    .routeId, .name, .currentStatus,
                    .estimatedTransitDays, .shippingCost, .insuranceCost,
                    .totalDistanceNm
                } AS route
                """
            )
            blocked_routes = [r["route"] for r in records if r.get("route")]
        except Exception as exc:
            logger.warning("Failed to fetch disrupted routes: %s", exc)
            blocked_routes = []

        if not blocked_routes:
            return {
                "message": "No disrupted or blocked routes found.",
                "routeRecommendations": [],
            }

        # Fetch equipment on blocked routes
        route_ids = [r.get("routeId") for r in blocked_routes if r.get("routeId")]
        equipment_list = await self._fetch_equipment_on_routes(route_ids)

        return await self._agent.run(
            blocked_routes=blocked_routes,
            equipment_list=equipment_list,
            disrupted_zone_ids=disrupted_zone_ids or [],
        )

    async def get_route_risk_assessment(self, route_id: str) -> Dict[str, Any]:
        """Get risk assessment for a specific route."""
        try:
            records = await query_neo4j(
                """
                MATCH (r:ShippingRoute {routeId: $routeId})
                OPTIONAL MATCH (r)-[:PASSES_THROUGH]->(z:GeopoliticalZone)
                OPTIONAL MATCH (d:DisruptionEvent)-[:AFFECTS_ZONE]->(z)
                WHERE d.verificationStatus <> 'resolved'
                WITH r,
                     collect(DISTINCT z {.zoneId, .name, .riskLevel, .currentStatus}) AS zones,
                     collect(DISTINCT d {.eventId, .type, .severity}) AS disruptions
                RETURN r {
                    .routeId, .name, .currentStatus, .estimatedTransitDays,
                    .shippingCost, .totalDistanceNm,
                    zones: zones,
                    activeDisruptions: disruptions
                } AS route
                """,
                {"routeId": route_id},
            )
            if records and records[0].get("route"):
                from app.agents.tools.scoring import calculate_route_risk_score
                route = records[0]["route"]
                route["riskScore"] = calculate_route_risk_score(route)
                return route
        except Exception as exc:
            logger.warning("Failed to assess route %s: %s", route_id, exc)

        return {"error": f"Route {route_id} not found or query failed."}

    async def _fetch_route(self, route_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a route from Neo4j."""
        try:
            records = await query_neo4j(
                """
                MATCH (r:ShippingRoute {routeId: $routeId})
                RETURN r {
                    .routeId, .name, .currentStatus,
                    .estimatedTransitDays, .shippingCost, .insuranceCost,
                    .totalDistanceNm
                } AS route
                """,
                {"routeId": route_id},
            )
            if records and records[0].get("route"):
                return records[0]["route"]
        except Exception as exc:
            logger.warning("Failed to fetch route %s: %s", route_id, exc)
        return None

    async def _fetch_equipment(
        self, equipment_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Fetch equipment by IDs."""
        try:
            records = await query_neo4j(
                """
                UNWIND $ids AS eid
                MATCH (e:Equipment {equipmentId: eid})
                RETURN e {
                    .equipmentId, .name, .category, .criticality, .weight
                } AS equipment
                """,
                {"ids": equipment_ids},
            )
            return [r["equipment"] for r in records if r.get("equipment")]
        except Exception as exc:
            logger.warning("Failed to fetch equipment: %s", exc)
            return []

    async def _fetch_equipment_on_routes(
        self, route_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Fetch equipment shipped via given routes."""
        try:
            records = await query_neo4j(
                """
                UNWIND $routeIds AS rid
                MATCH (e:Equipment)-[:SHIPPED_VIA]->(r:ShippingRoute {routeId: rid})
                RETURN e {
                    .equipmentId, .name, .category, .criticality, .weight,
                    routeId: r.routeId
                } AS equipment
                """,
                {"routeIds": route_ids},
            )
            return [r["equipment"] for r in records if r.get("equipment")]
        except Exception as exc:
            logger.warning("Failed to fetch equipment on routes: %s", exc)
            return []

    def clear_cache(self, route_id: Optional[str] = None) -> None:
        """Clear route cache."""
        if route_id:
            keys_to_remove = [k for k in _route_cache if k.startswith(f"route:{route_id}")]
            for k in keys_to_remove:
                del _route_cache[k]
        else:
            _route_cache.clear()
