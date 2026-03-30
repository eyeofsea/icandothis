"""Impact Analysis Agent for the SCM Risk Intelligence Platform.

Takes a DisruptionEvent and affected zones, performs graph traversal to identify
all affected equipment, routes, projects, and suppliers, then calculates risk
scores and cascade effects.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Dict, List, Optional

from app.agents.tools.neo4j_tools import (
    find_affected_equipment,
    query_neo4j,
)
from app.agents.tools.scoring import (
    calculate_disruption_impact_score,
    calculate_equipment_risk_score,
)

logger = logging.getLogger(__name__)


class ImpactAgent:
    """Analyzes the impact of a disruption event across the supply chain graph."""

    def __init__(self) -> None:
        self.name = "ImpactAgent"

    async def run(
        self,
        event: Dict[str, Any],
        affected_zone_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Run full impact analysis for a disruption event.

        Args:
            event: DisruptionEvent dict with eventId, type, severity, etc.
            affected_zone_ids: List of zone IDs affected by the event.

        Returns:
            Structured ImpactReport with risk matrix per project.
        """
        logger.info("ImpactAgent.run: analyzing event %s", event.get("eventId", "unknown"))
        affected_zone_ids = affected_zone_ids or event.get("affectedZones", [])
        severity = event.get("severity", 3)

        # Step 1: Graph traversal - find affected equipment per zone
        all_affected_equipment: List[Dict[str, Any]] = []
        for zone_id in affected_zone_ids:
            try:
                equipment_list = await find_affected_equipment(zone_id)
                all_affected_equipment.extend(equipment_list)
            except Exception as exc:
                logger.warning("Failed to query equipment for zone %s: %s", zone_id, exc)

        # Deduplicate by equipmentId
        seen_ids: set = set()
        unique_equipment: List[Dict[str, Any]] = []
        for eq in all_affected_equipment:
            eid = eq.get("equipmentId")
            if eid and eid not in seen_ids:
                seen_ids.add(eid)
                unique_equipment.append(eq)

        # Step 2: Calculate risk score for each affected equipment
        equipment_risks: List[Dict[str, Any]] = []
        for eq in unique_equipment:
            risk_score = calculate_equipment_risk_score(eq)
            equipment_risks.append({
                **eq,
                "riskScore": risk_score,
            })

        # Sort by risk score descending
        equipment_risks.sort(key=lambda e: e.get("riskScore", 0), reverse=True)

        # Step 3: Aggregate affected routes
        affected_routes = await self._find_affected_routes(affected_zone_ids)

        # Step 4: Aggregate affected projects
        project_risk_matrix = await self._build_project_risk_matrix(
            equipment_risks, affected_routes, severity
        )

        # Step 5: Find affected suppliers
        affected_suppliers = await self._find_affected_suppliers(affected_zone_ids)

        # Step 6: Assess critical path impact
        critical_path_items = [
            e for e in equipment_risks
            if str(e.get("criticality", "")).lower() == "critical"
        ]

        # Step 7: Identify cascade effects
        cascade_effects = self._identify_cascade_effects(
            equipment_risks, project_risk_matrix, affected_routes
        )

        # Step 8: Calculate overall disruption impact score
        impact_score = calculate_disruption_impact_score(
            event,
            {
                "equipment": equipment_risks,
                "projects": list(project_risk_matrix.values()),
                "routes": affected_routes,
            },
        )

        # Estimate delay
        estimated_delay_days = self._estimate_delay(severity, len(affected_routes), len(critical_path_items))

        return {
            "eventId": event.get("eventId"),
            "eventType": event.get("type"),
            "severity": severity,
            "impactScore": impact_score,
            "estimatedDelayDays": estimated_delay_days,
            "affectedZones": affected_zone_ids,
            "affectedEquipment": equipment_risks,
            "affectedEquipmentCount": len(equipment_risks),
            "criticalPathItems": critical_path_items,
            "criticalPathItemCount": len(critical_path_items),
            "affectedRoutes": affected_routes,
            "affectedRouteCount": len(affected_routes),
            "affectedSuppliers": affected_suppliers,
            "affectedSupplierCount": len(affected_suppliers),
            "projectRiskMatrix": project_risk_matrix,
            "cascadeEffects": cascade_effects,
            "summary": self._generate_summary(
                event, equipment_risks, affected_routes,
                project_risk_matrix, estimated_delay_days, impact_score,
            ),
        }

    async def _find_affected_routes(
        self, zone_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Find all routes passing through affected zones."""
        if not zone_ids:
            return []
        try:
            cypher = """
            MATCH (r:ShippingRoute)-[:PASSES_THROUGH]->(z:GeopoliticalZone)
            WHERE z.zoneId IN $zoneIds
            WITH r, collect(z {.zoneId, .name, .riskLevel}) AS affectedZones
            RETURN r {
                .routeId, .name, .currentStatus, .estimatedTransitDays,
                .shippingCost, .totalDistanceNm,
                affectedZones: affectedZones
            } AS route
            """
            records = await query_neo4j(cypher, {"zoneIds": zone_ids})
            return [rec["route"] for rec in records if rec.get("route") and rec["route"].get("routeId")]
        except Exception as exc:
            logger.warning("Failed to find affected routes: %s", exc)
            return []

    async def _find_affected_suppliers(
        self, zone_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Find suppliers located in affected zones."""
        if not zone_ids:
            return []
        try:
            cypher = """
            MATCH (s:Supplier)-[:LOCATED_IN]->(z:GeopoliticalZone)
            WHERE z.zoneId IN $zoneIds
            RETURN s {
                .supplierId, .name, .country, .tier,
                .capabilities, .deliveryRate, .qualityRate,
                zone: z.name
            } AS supplier
            """
            records = await query_neo4j(cypher, {"zoneIds": zone_ids})
            return [rec["supplier"] for rec in records if rec.get("supplier") and rec["supplier"].get("supplierId")]
        except Exception as exc:
            logger.warning("Failed to find affected suppliers: %s", exc)
            return []

    async def _build_project_risk_matrix(
        self,
        equipment_risks: List[Dict[str, Any]],
        affected_routes: List[Dict[str, Any]],
        severity: int,
    ) -> Dict[str, Dict[str, Any]]:
        """Build a risk matrix per project."""
        project_map: Dict[str, Dict[str, Any]] = {}

        for eq in equipment_risks:
            pid = eq.get("projectId")
            if not pid:
                continue
            if pid not in project_map:
                project_map[pid] = {
                    "projectId": pid,
                    "projectName": eq.get("projectName", "Unknown"),
                    "affectedEquipment": [],
                    "criticalEquipmentCount": 0,
                    "highRiskEquipmentCount": 0,
                    "totalRiskScore": 0.0,
                    "maxRiskScore": 0.0,
                    "affectedRouteCount": 0,
                    "estimatedDelayDays": 0,
                }

            proj = project_map[pid]
            proj["affectedEquipment"].append({
                "equipmentId": eq.get("equipmentId"),
                "name": eq.get("name"),
                "criticality": eq.get("criticality"),
                "riskScore": eq.get("riskScore", 0),
            })
            risk = eq.get("riskScore", 0)
            proj["totalRiskScore"] += risk
            proj["maxRiskScore"] = max(proj["maxRiskScore"], risk)

            if str(eq.get("criticality", "")).lower() == "critical":
                proj["criticalEquipmentCount"] += 1
            if risk >= 7.0:
                proj["highRiskEquipmentCount"] += 1

        # Add route impacts
        disrupted_route_ids = {r.get("routeId") for r in affected_routes}
        for pid, proj in project_map.items():
            route_count = sum(
                1 for eq in proj["affectedEquipment"]
                if eq.get("routeId") in disrupted_route_ids
            )
            proj["affectedRouteCount"] = route_count
            equip_count = len(proj["affectedEquipment"])
            avg_risk = proj["totalRiskScore"] / equip_count if equip_count > 0 else 0
            proj["averageRiskScore"] = round(avg_risk, 2)
            proj["overallProjectRisk"] = round(
                min(10.0, avg_risk * 0.6 + proj["maxRiskScore"] * 0.4), 2
            )
            proj["estimatedDelayDays"] = self._estimate_delay(
                severity, route_count, proj["criticalEquipmentCount"]
            )

        return project_map

    def _identify_cascade_effects(
        self,
        equipment_risks: List[Dict[str, Any]],
        project_risk_matrix: Dict[str, Dict[str, Any]],
        affected_routes: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Identify cascading effects across the supply chain."""
        cascades: List[Dict[str, Any]] = []

        # Equipment dependency cascades (installation sequence)
        critical_items = [
            e for e in equipment_risks
            if str(e.get("criticality", "")).lower() == "critical"
        ]
        if critical_items:
            cascades.append({
                "type": "installation_sequence",
                "description": (
                    f"{len(critical_items)} critical equipment item(s) delayed. "
                    "Downstream installation activities will be blocked until these arrive."
                ),
                "severity": "high",
                "affectedItems": [e.get("equipmentId") for e in critical_items],
            })

        # Multi-project impact
        multi_proj_count = len(project_risk_matrix)
        if multi_proj_count > 1:
            cascades.append({
                "type": "multi_project_impact",
                "description": (
                    f"Disruption affects {multi_proj_count} projects simultaneously. "
                    "Resource contention for alternative suppliers and routes expected."
                ),
                "severity": "high" if multi_proj_count > 3 else "medium",
                "affectedProjects": list(project_risk_matrix.keys()),
            })

        # Route bottleneck
        blocked_routes = [
            r for r in affected_routes
            if str(r.get("currentStatus", "")).lower() in ("blocked", "disrupted")
        ]
        if len(blocked_routes) > 1:
            cascades.append({
                "type": "route_bottleneck",
                "description": (
                    f"{len(blocked_routes)} routes simultaneously disrupted. "
                    "Alternative route capacity may be insufficient for all rerouted cargo."
                ),
                "severity": "high",
                "affectedRoutes": [r.get("routeId") for r in blocked_routes],
            })

        # Supplier concentration risk
        supplier_zones: Dict[str, int] = {}
        for eq in equipment_risks:
            zone = eq.get("zoneName", "unknown")
            supplier_zones[zone] = supplier_zones.get(zone, 0) + 1
        concentrated = {z: c for z, c in supplier_zones.items() if c >= 3}
        if concentrated:
            cascades.append({
                "type": "supplier_concentration",
                "description": (
                    f"High supplier concentration in disrupted zones: "
                    f"{', '.join(f'{z} ({c} items)' for z, c in concentrated.items())}."
                ),
                "severity": "medium",
                "zones": concentrated,
            })

        return cascades

    def _estimate_delay(
        self, severity: int, route_count: int, critical_count: int
    ) -> int:
        """Estimate delay in days based on severity and affected items."""
        base_delay = severity * 7  # 7 days per severity level
        route_factor = min(route_count, 5) * 3  # 3 days per affected route
        critical_factor = min(critical_count, 10) * 5  # 5 days per critical item
        return base_delay + route_factor + critical_factor

    def _generate_summary(
        self,
        event: Dict[str, Any],
        equipment_risks: List[Dict[str, Any]],
        affected_routes: List[Dict[str, Any]],
        project_risk_matrix: Dict[str, Dict[str, Any]],
        estimated_delay_days: int,
        impact_score: float,
    ) -> str:
        """Generate a human-readable impact summary."""
        event_type = event.get("type", "unknown")
        severity = event.get("severity", 0)
        description = event.get("description", "")

        critical_count = sum(
            1 for e in equipment_risks
            if str(e.get("criticality", "")).lower() == "critical"
        )
        high_risk_count = sum(
            1 for e in equipment_risks if e.get("riskScore", 0) >= 7.0
        )

        lines = [
            f"IMPACT ANALYSIS: {event_type.upper()} (Severity {severity}/5)",
            f"Event: {description}",
            f"Impact Score: {impact_score}/10",
            f"",
            f"Affected Equipment: {len(equipment_risks)} items",
            f"  - Critical path items: {critical_count}",
            f"  - High risk (score >= 7): {high_risk_count}",
            f"Affected Routes: {len(affected_routes)}",
            f"Affected Projects: {len(project_risk_matrix)}",
            f"Estimated Delay: {estimated_delay_days} days",
        ]

        if project_risk_matrix:
            lines.append("")
            lines.append("Project Risk Summary:")
            for pid, proj in sorted(
                project_risk_matrix.items(),
                key=lambda x: x[1].get("overallProjectRisk", 0),
                reverse=True,
            ):
                lines.append(
                    f"  - {proj.get('projectName', pid)}: "
                    f"Risk {proj.get('overallProjectRisk', 0)}/10, "
                    f"{len(proj.get('affectedEquipment', []))} equipment items, "
                    f"est. {proj.get('estimatedDelayDays', 0)} days delay"
                )

        return "\n".join(lines)
