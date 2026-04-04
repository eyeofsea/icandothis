"""Service layer for supplier operations - bridges routers with agents."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.agents.supplier_agent import SupplierAgent
from app.agents.tools.neo4j_tools import query_neo4j

logger = logging.getLogger(__name__)

_supplier_cache: Dict[str, Dict[str, Any]] = {}


class SupplierService:
    """Service that bridges HTTP routers with the SupplierAgent."""

    def __init__(self) -> None:
        self._agent = SupplierAgent()

    async def find_supplier_alternatives(
        self,
        equipment_id: str,
        disrupted_zone_ids: Optional[List[str]] = None,
        required_certifications: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Find alternative suppliers for a specific equipment item.

        Args:
            equipment_id: Equipment ID to find alternatives for.
            disrupted_zone_ids: Zone IDs to exclude suppliers from.
            required_certifications: Required certifications.

        Returns:
            Supplier recommendations.
        """
        cache_key = f"supplier:{equipment_id}:{','.join(sorted(disrupted_zone_ids or []))}"
        if cache_key in _supplier_cache:
            return _supplier_cache[cache_key]

        equipment = await self._fetch_equipment(equipment_id)
        if not equipment:
            return {"error": f"Equipment {equipment_id} not found."}

        result = await self._agent.run(
            affected_equipment=[equipment],
            disrupted_zone_ids=disrupted_zone_ids,
            required_certifications=required_certifications,
        )

        _supplier_cache[cache_key] = result
        return result

    async def find_bulk_supplier_alternatives(
        self,
        equipment_ids: Optional[List[str]] = None,
        category: Optional[str] = None,
        disrupted_zone_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Find alternatives for multiple equipment items or a category.

        Args:
            equipment_ids: List of equipment IDs.
            category: Equipment category to find alternatives for.
            disrupted_zone_ids: Zone IDs to exclude.

        Returns:
            Bulk supplier recommendations.
        """
        equipment_list = []

        if equipment_ids:
            for eid in equipment_ids:
                eq = await self._fetch_equipment(eid)
                if eq:
                    equipment_list.append(eq)
        elif category:
            equipment_list = await self._fetch_equipment_by_category(category)

        if not equipment_list:
            # Fall back to all at-risk equipment
            equipment_list = await self._fetch_at_risk_equipment()

        if not equipment_list:
            return {
                "message": "No equipment found for supplier alternative analysis.",
                "recommendations": [],
            }

        return await self._agent.run(
            affected_equipment=equipment_list,
            disrupted_zone_ids=disrupted_zone_ids or [],
        )

    async def get_supplier_risk_profile(
        self, supplier_id: str
    ) -> Dict[str, Any]:
        """Get comprehensive risk profile for a supplier."""
        try:
            records = await query_neo4j(
                """
                MATCH (s:Supplier {supplierId: $supplierId})
                OPTIONAL MATCH (e:Equipment)-[:SUPPLIED_BY]->(s)
                OPTIONAL MATCH (p:Project)-[:HAS_EQUIPMENT]->(e)
                OPTIONAL MATCH (s)-[:LOCATED_IN]->(z:GeopoliticalZone)
                OPTIONAL MATCH (d:DisruptionEvent)-[:AFFECTS_ZONE]->(z)
                WHERE d.verificationStatus <> 'resolved'
                WITH s,
                     collect(DISTINCT e {.equipmentId, .name, .category, .criticality}) AS equipment,
                     collect(DISTINCT p {.projectId, .name}) AS projects,
                     collect(DISTINCT z {.zoneId, .name, .riskLevel}) AS zones,
                     collect(DISTINCT d {.eventId, .type, .severity}) AS disruptions
                RETURN s {
                    .supplierId, .name, .country, .region, .tier,
                    .capabilities, .certifications, .financialRating,
                    .onTimeDeliveryRate, .qualityRejectRate, .leadTimeDays,
                    .capacityUtilization, .riskFlags,
                    suppliedEquipment: equipment,
                    associatedProjects: projects,
                    locatedInZones: zones,
                    activeDisruptions: disruptions
                } AS supplier
                """,
                {"supplierId": supplier_id},
            )

            if records and records[0].get("supplier"):
                from app.agents.tools.scoring import calculate_supplier_risk_score
                supplier = records[0]["supplier"]
                supplier["riskScore"] = calculate_supplier_risk_score(supplier)

                # Determine risk level
                risk_score = supplier["riskScore"]
                if risk_score >= 7:
                    supplier["riskLevel"] = "critical"
                elif risk_score >= 5:
                    supplier["riskLevel"] = "high"
                elif risk_score >= 3:
                    supplier["riskLevel"] = "medium"
                else:
                    supplier["riskLevel"] = "low"

                return supplier
        except Exception as exc:
            logger.warning("Failed to get supplier risk profile: %s", exc)

        return {"error": f"Supplier {supplier_id} not found or query failed."}

    async def _fetch_equipment(self, equipment_id: str) -> Optional[Dict[str, Any]]:
        """Fetch equipment by ID."""
        try:
            records = await query_neo4j(
                """
                MATCH (e:Equipment {equipmentId: $equipmentId})
                RETURN e {
                    .equipmentId, .name, .category, .criticality,
                    .weight, .requiredOnSiteDate
                } AS equipment
                """,
                {"equipmentId": equipment_id},
            )
            if records and records[0].get("equipment"):
                return records[0]["equipment"]
        except Exception as exc:
            logger.warning("Failed to fetch equipment %s: %s", equipment_id, exc)
        return None

    async def _fetch_equipment_by_category(
        self, category: str
    ) -> List[Dict[str, Any]]:
        """Fetch equipment by category."""
        try:
            records = await query_neo4j(
                """
                MATCH (e:Equipment)
                WHERE e.category = $category
                RETURN e {
                    .equipmentId, .name, .category, .criticality,
                    .weight, .requiredOnSiteDate
                } AS equipment
                LIMIT 20
                """,
                {"category": category},
            )
            return [r["equipment"] for r in records if r.get("equipment")]
        except Exception as exc:
            logger.warning("Failed to fetch equipment by category: %s", exc)
            return []

    async def _fetch_at_risk_equipment(self) -> List[Dict[str, Any]]:
        """Fetch equipment that is currently at risk (on disrupted routes)."""
        try:
            records = await query_neo4j(
                """
                MATCH (e:Equipment)-[:SHIPPED_VIA]->(r:ShippingRoute)
                WHERE r.currentStatus IN ['disrupted', 'blocked']
                RETURN e {
                    .equipmentId, .name, .category, .criticality,
                    .weight, .requiredOnSiteDate,
                    routeStatus: r.currentStatus
                } AS equipment
                ORDER BY CASE e.criticality
                    WHEN 'critical' THEN 0 WHEN 'high' THEN 1
                    WHEN 'medium' THEN 2 ELSE 3 END
                LIMIT 20
                """
            )
            return [r["equipment"] for r in records if r.get("equipment")]
        except Exception as exc:
            logger.warning("Failed to fetch at-risk equipment: %s", exc)
            return []

    def clear_cache(self, equipment_id: Optional[str] = None) -> None:
        """Clear supplier cache."""
        if equipment_id:
            keys_to_remove = [k for k in _supplier_cache if f":{equipment_id}:" in k]
            for k in keys_to_remove:
                del _supplier_cache[k]
        else:
            _supplier_cache.clear()
