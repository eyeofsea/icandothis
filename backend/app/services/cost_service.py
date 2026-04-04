"""Service layer for cost analysis - bridges routers with agents."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.agents.cost_agent import CostAgent
from app.agents.tools.neo4j_tools import query_neo4j

logger = logging.getLogger(__name__)

_cost_cache: Dict[str, Dict[str, Any]] = {}


class CostService:
    """Service that bridges HTTP routers with the CostAgent."""

    def __init__(self) -> None:
        self._agent = CostAgent()

    async def analyze_disruption_cost(
        self,
        event_id: str,
        delay_days: int = 30,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """
        Analyze full cost impact of a disruption event.

        Args:
            event_id: Disruption event ID.
            delay_days: Estimated delay in days.
            force_refresh: Skip cache.

        Returns:
            Cost analysis with scenario comparison.
        """
        cache_key = f"cost:{event_id}:{delay_days}"
        if not force_refresh and cache_key in _cost_cache:
            return _cost_cache[cache_key]

        # Fetch affected projects and equipment
        affected_data = await self._fetch_affected_data(event_id)
        if not affected_data.get("projects") and not affected_data.get("equipment"):
            return {
                "eventId": event_id,
                "message": "No affected projects or equipment found for this event.",
                "noActionCost": {"totalDisruptionCost": 0},
            }

        result = await self._agent.run(
            affected_projects=affected_data["projects"],
            affected_equipment=affected_data["equipment"],
            supplier_recommendations=affected_data.get("supplierRecommendations"),
            route_recommendations=affected_data.get("routeRecommendations"),
            delay_days=delay_days,
        )

        result["eventId"] = event_id
        _cost_cache[cache_key] = result
        return result

    async def analyze_project_cost(
        self,
        project_id: str,
        delay_days: int = 30,
    ) -> Dict[str, Any]:
        """Analyze cost impact for a specific project."""
        # Fetch project
        try:
            records = await query_neo4j(
                """
                MATCH (p:Project {projectId: $projectId})
                RETURN p {
                    .projectId, .name, .totalValue, .status,
                    .criticalPathDeadline
                } AS project
                """,
                {"projectId": project_id},
            )
            project = records[0]["project"] if records and records[0].get("project") else None
        except Exception as exc:
            logger.warning("Failed to fetch project %s: %s", project_id, exc)
            project = None

        if not project:
            return {"error": f"Project {project_id} not found."}

        # Fetch affected equipment for this project
        try:
            records = await query_neo4j(
                """
                MATCH (p:Project {projectId: $projectId})-[:HAS_EQUIPMENT]->(e:Equipment)
                OPTIONAL MATCH (e)-[:SHIPPED_VIA]->(r:ShippingRoute)
                WHERE r.currentStatus IN ['disrupted', 'blocked', 'delayed']
                RETURN e {
                    .equipmentId, .name, .criticality, .weight, .category,
                    routeStatus: r.currentStatus
                } AS equipment
                """,
                {"projectId": project_id},
            )
            equipment = [r["equipment"] for r in records if r.get("equipment") and r["equipment"].get("equipmentId")]
        except Exception as exc:
            logger.warning("Failed to fetch project equipment: %s", exc)
            equipment = []

        return await self._agent.run(
            affected_projects=[project],
            affected_equipment=equipment,
            delay_days=delay_days,
        )

    async def compare_mitigation_scenarios(
        self,
        scenarios: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Compare custom mitigation scenarios."""
        from app.agents.tools.optimization import compare_scenarios
        return compare_scenarios(scenarios)

    async def calculate_platform_roi(
        self,
        annual_disruption_cost: Optional[float] = None,
        system_cost: float = 500000.0,
    ) -> Dict[str, Any]:
        """
        Calculate platform ROI based on total disruption exposure.

        If annual_disruption_cost not provided, estimates from current data.
        """
        if annual_disruption_cost is None:
            annual_disruption_cost = await self._estimate_annual_exposure()

        # Assume platform reduces disruption cost by 30-50%
        reduction_pct = 0.40
        annual_savings = annual_disruption_cost * reduction_pct

        from app.agents.tools.optimization import calculate_roi
        roi = calculate_roi(
            savings=annual_savings,
            system_cost=system_cost,
            period_years=1.0,
        )
        roi["annualDisruptionExposure"] = round(annual_disruption_cost, 2)
        roi["reductionAssumption"] = f"{reduction_pct * 100:.0f}%"

        return roi

    async def _fetch_affected_data(
        self, event_id: str
    ) -> Dict[str, Any]:
        """Fetch all data affected by a disruption event."""
        projects: List[Dict[str, Any]] = []
        equipment: List[Dict[str, Any]] = []

        try:
            records = await query_neo4j(
                """
                MATCH (d:DisruptionEvent {eventId: $eventId})-[:AFFECTS_ZONE]->(z:GeopoliticalZone)
                OPTIONAL MATCH (r:ShippingRoute)-[:PASSES_THROUGH]->(z)
                OPTIONAL MATCH (e:Equipment)-[:SHIPPED_VIA]->(r)
                OPTIONAL MATCH (p:Project)-[:HAS_EQUIPMENT]->(e)
                WITH collect(DISTINCT p {
                    .projectId, .name, .totalValue, .status,
                    .criticalPathDeadline
                }) AS projects,
                collect(DISTINCT e {
                    .equipmentId, .name, .criticality, .weight, .category,
                    routeStatus: r.currentStatus
                }) AS equipment
                RETURN {
                    projects: [p IN projects WHERE p.projectId IS NOT NULL],
                    equipment: [e IN equipment WHERE e.equipmentId IS NOT NULL]
                } AS data
                """,
                {"eventId": event_id},
            )
            if records and records[0].get("data"):
                data = records[0]["data"]
                projects = data.get("projects", [])
                equipment = data.get("equipment", [])
        except Exception as exc:
            logger.warning("Failed to fetch affected data for %s: %s", event_id, exc)

        return {"projects": projects, "equipment": equipment}

    async def _estimate_annual_exposure(self) -> float:
        """Estimate annual disruption cost exposure from current data."""
        try:
            records = await query_neo4j(
                """
                MATCH (p:Project)
                WHERE p.status IN ['procurement', 'in_transit', 'construction']
                WITH sum(COALESCE(p.totalValue, 0)) AS totalPortfolioValue,
                     count(p) AS projectCount
                OPTIONAL MATCH (d:DisruptionEvent)
                WHERE d.verificationStatus <> 'resolved'
                WITH totalPortfolioValue, projectCount,
                     count(d) AS activeDisruptions,
                     avg(d.severity) AS avgSeverity
                RETURN {
                    totalPortfolioValue: totalPortfolioValue,
                    projectCount: projectCount,
                    activeDisruptions: activeDisruptions,
                    avgSeverity: avgSeverity
                } AS exposure
                """
            )
            if records and records[0].get("exposure"):
                exp = records[0]["exposure"]
                portfolio = exp.get("totalPortfolioValue") or 0
                # Rough estimate: 2-5% of portfolio value at risk annually
                return portfolio * 0.03
        except Exception as exc:
            logger.warning("Failed to estimate exposure: %s", exc)

        # Default estimate
        return 5000000.0

    def clear_cache(self, event_id: Optional[str] = None) -> None:
        """Clear cost cache."""
        if event_id:
            keys_to_remove = [k for k in _cost_cache if k.startswith(f"cost:{event_id}")]
            for k in keys_to_remove:
                del _cost_cache[k]
        else:
            _cost_cache.clear()
