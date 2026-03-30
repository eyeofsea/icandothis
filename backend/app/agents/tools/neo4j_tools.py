"""LangChain-style tools wrapping Neo4j queries for the SCM Risk Intelligence Platform."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.database.neo4j_client import Neo4jClient


async def _get_client() -> Neo4jClient:
    return await Neo4jClient.get_instance()


async def query_neo4j(
    cypher: str, parameters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Execute an arbitrary Cypher query against the Neo4j knowledge graph."""
    client = await _get_client()
    return await client.execute_query(cypher, parameters or {})


async def find_affected_equipment(zone_id: str) -> List[Dict[str, Any]]:
    """Given a zone ID, traverse Event -> Zone -> Route -> Equipment to find affected equipment."""
    client = await _get_client()
    cypher = """
    MATCH (d:DisruptionEvent)-[:AFFECTS_ZONE]->(z:GeopoliticalZone {zoneId: $zoneId})
    OPTIONAL MATCH (r:ShippingRoute)-[:PASSES_THROUGH]->(z)
    OPTIONAL MATCH (e:Equipment)-[:SHIPPED_VIA]->(r)
    OPTIONAL MATCH (p:Project)-[:REQUIRES]->(e)
    RETURN DISTINCT
        e {
            .equipmentId, .name, .category, .criticality,
            .weight, .requiredOnSiteDate,
            routeId: r.routeId,
            routeName: r.name,
            routeStatus: r.currentStatus,
            projectId: p.projectId,
            projectName: p.name,
            disruptionId: d.eventId,
            disruptionType: d.type,
            disruptionSeverity: d.severity,
            zoneName: z.name,
            zoneRiskLevel: z.riskLevel
        } AS equipment
    ORDER BY CASE e.criticality
        WHEN 'critical' THEN 0 WHEN 'high' THEN 1
        WHEN 'medium' THEN 2 ELSE 3 END
    """
    records = await client.execute_read(cypher, {"zoneId": zone_id})
    return [r["equipment"] for r in records if r.get("equipment") and r["equipment"].get("equipmentId")]


async def find_alternative_suppliers(
    equipment_category: str,
    excluded_zones: Optional[List[str]] = None,
    required_certifications: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Find alternative suppliers for equipment category, excluding those in disrupted zones."""
    client = await _get_client()
    excluded_zones = excluded_zones or []
    required_certifications = required_certifications or []

    cypher = """
    MATCH (s:Supplier)-[:SUPPLIES]->(e:Equipment)
    WHERE e.category = $category
    // Exclude suppliers in disrupted zones
    AND NOT EXISTS {
        MATCH (s)-[:LOCATED_IN]->(z:GeopoliticalZone)
        WHERE z.zoneId IN $excludedZones
    }
    // Exclude sanctioned suppliers
    AND NOT 'sanctioned' IN s.riskFlags
    WITH s, collect(DISTINCT e.name) AS suppliedEquipment
    RETURN s {
        .supplierId, .name, .country, .region, .tier,
        .capabilities, .certifications, .financialRating,
        .deliveryRate, .qualityRate, .leadTimeDays,
        .capacityUtilization, .riskFlags,
        suppliedEquipment: suppliedEquipment
    } AS supplier
    ORDER BY s.deliveryRate DESC, s.qualityRate DESC
    """
    records = await client.execute_read(cypher, {
        "category": equipment_category,
        "excludedZones": excluded_zones,
    })
    results = [r["supplier"] for r in records if r.get("supplier")]

    # Filter by certifications if required
    if required_certifications:
        filtered = []
        for sup in results:
            certs = sup.get("certifications") or []
            if any(c in certs for c in required_certifications):
                filtered.append(sup)
        if filtered:
            results = filtered

    return results


async def find_alternative_routes(
    blocked_route_id: str,
    disrupted_zone_ids: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Find alternative routes that avoid disrupted zones."""
    client = await _get_client()
    disrupted_zone_ids = disrupted_zone_ids or []

    # First get the original route's origin and destination
    origin_dest_query = """
    MATCH (r:ShippingRoute {routeId: $routeId})
    RETURN r {
        .routeId, .name, .totalDistanceNm, .estimatedTransitDays,
        .shippingCost, .insuranceCost, .currentStatus
    } AS route
    """
    original_records = await client.execute_read(origin_dest_query, {"routeId": blocked_route_id})
    original_route = original_records[0]["route"] if original_records else {}

    # Find alternative routes not passing through disrupted zones
    cypher = """
    MATCH (alt:ShippingRoute)
    WHERE alt.routeId <> $blockedRouteId
      AND alt.currentStatus IN ['active', 'planned']
      AND NOT EXISTS {
          MATCH (alt)-[:PASSES_THROUGH]->(z:GeopoliticalZone)
          WHERE z.zoneId IN $disruptedZones
      }
    OPTIONAL MATCH (alt)-[:PASSES_THROUGH]->(zone:GeopoliticalZone)
    WITH alt, collect(zone {.zoneId, .name, .riskLevel}) AS zones
    RETURN alt {
        .routeId, .name, .totalDistanceNm, .estimatedTransitDays,
        .shippingCost, .insuranceCost, .currentStatus,
        zones: zones
    } AS route
    ORDER BY alt.estimatedTransitDays ASC
    """
    records = await client.execute_read(cypher, {
        "blockedRouteId": blocked_route_id,
        "disruptedZones": disrupted_zone_ids,
    })

    alternatives = []
    for rec in records:
        alt = rec["route"]
        if alt and alt.get("routeId"):
            orig_days = original_route.get("estimatedTransitDays") or 0
            orig_cost = original_route.get("shippingCost") or 0
            alt_days = alt.get("estimatedTransitDays") or 0
            alt_cost = alt.get("shippingCost") or 0
            alt["additionalDays"] = max(0, alt_days - orig_days)
            alt["additionalCost"] = max(0, alt_cost - orig_cost)
            alt["originalRoute"] = original_route
            alternatives.append(alt)

    return alternatives


async def get_equipment_details(equipment_id: str) -> Dict[str, Any]:
    """Get equipment with all its relationships (project, supplier, route, zone exposure)."""
    client = await _get_client()
    cypher = """
    MATCH (e:Equipment {equipmentId: $equipmentId})
    OPTIONAL MATCH (p:Project)-[:REQUIRES]->(e)
    OPTIONAL MATCH (s:Supplier)-[:SUPPLIES]->(e)
    OPTIONAL MATCH (e)-[:SHIPPED_VIA]->(r:ShippingRoute)
    OPTIONAL MATCH (r)-[:PASSES_THROUGH]->(z:GeopoliticalZone)
    OPTIONAL MATCH (d:DisruptionEvent)-[:AFFECTS_ZONE]->(z)
    WHERE d.verificationStatus <> 'resolved'
    RETURN e {
        .equipmentId, .name, .description, .category, .criticality,
        .weight, .dimensions, .hsCode, .requiredOnSiteDate,
        .installationSequencePriority, .specifications,
        project: p {.projectId, .name, .status, .totalValue, .criticalPathDeadline},
        supplier: s {.supplierId, .name, .country, .deliveryRate, .qualityRate, .leadTimeDays},
        route: r {.routeId, .name, .currentStatus, .estimatedTransitDays, .shippingCost},
        zones: collect(DISTINCT z {.zoneId, .name, .riskLevel, .currentStatus}),
        activeDisruptions: collect(DISTINCT d {.eventId, .type, .severity, .description})
    } AS equipment
    """
    records = await client.execute_read(cypher, {"equipmentId": equipment_id})
    if records and records[0].get("equipment"):
        return records[0]["equipment"]
    return {}


async def get_supplier_performance(supplier_id: str) -> Dict[str, Any]:
    """Get supplier metrics including delivery rate, quality, and order history."""
    client = await _get_client()
    cypher = """
    MATCH (s:Supplier {supplierId: $supplierId})
    OPTIONAL MATCH (s)-[:SUPPLIES]->(e:Equipment)
    OPTIONAL MATCH (p:Project)-[:REQUIRES]->(e)
    WITH s,
         collect(DISTINCT e {.equipmentId, .name, .category, .criticality}) AS equipment,
         collect(DISTINCT p {.projectId, .name}) AS projects
    RETURN s {
        .supplierId, .name, .country, .region, .tier,
        .capabilities, .certifications, .financialRating,
        .deliveryRate, .qualityRate, .leadTimeDays,
        .capacityUtilization, .riskFlags,
        suppliedEquipment: equipment,
        associatedProjects: projects,
        totalEquipmentCount: size(equipment)
    } AS supplier
    """
    records = await client.execute_read(cypher, {"supplierId": supplier_id})
    if records and records[0].get("supplier"):
        return records[0]["supplier"]
    return {}


async def get_project_risk_summary(project_id: str) -> Dict[str, Any]:
    """Get project with risk aggregation across its equipment, routes, and suppliers."""
    client = await _get_client()
    cypher = """
    MATCH (p:Project {projectId: $projectId})
    OPTIONAL MATCH (p)-[:REQUIRES]->(e:Equipment)
    OPTIONAL MATCH (e)-[:SHIPPED_VIA]->(r:ShippingRoute)
    OPTIONAL MATCH (s:Supplier)-[:SUPPLIES]->(e)
    OPTIONAL MATCH (r)-[:PASSES_THROUGH]->(z:GeopoliticalZone)
    OPTIONAL MATCH (d:DisruptionEvent)-[:AFFECTS_ZONE]->(z)
    WHERE d.verificationStatus <> 'resolved'
    WITH p, e, r, s, z, d
    RETURN p {
        .projectId, .name, .status, .country, .totalValue,
        .completionPct, .criticalPathDeadline, .riskTolerance,
        equipmentCount: count(DISTINCT e),
        criticalEquipment: count(DISTINCT CASE WHEN e.criticality = 'critical' THEN e END),
        disruptedRoutes: count(DISTINCT CASE WHEN r.currentStatus IN ['disrupted', 'blocked', 'delayed'] THEN r END),
        totalRoutes: count(DISTINCT r),
        activeDisruptions: count(DISTINCT d),
        supplierCount: count(DISTINCT s),
        maxZoneRisk: CASE WHEN max(z.riskLevel) IS NOT NULL THEN max(z.riskLevel) ELSE 0 END,
        affectedEquipmentIds: collect(DISTINCT CASE WHEN d IS NOT NULL THEN e.equipmentId END),
        disruptionDetails: collect(DISTINCT d {.eventId, .type, .severity, .description})
    } AS project
    """
    records = await client.execute_read(cypher, {"projectId": project_id})
    if records and records[0].get("project"):
        proj = records[0]["project"]
        # Calculate overall risk score
        critical_count = proj.get("criticalEquipment") or 0
        disrupted_routes = proj.get("disruptedRoutes") or 0
        active_disruptions = proj.get("activeDisruptions") or 0
        max_zone_risk = proj.get("maxZoneRisk") or 0
        total_equip = proj.get("equipmentCount") or 1

        risk_score = min(10.0, (
            (critical_count / total_equip) * 3.0 +
            (disrupted_routes / max(proj.get("totalRoutes") or 1, 1)) * 3.0 +
            (min(active_disruptions, 5) / 5) * 2.0 +
            (max_zone_risk / 10) * 2.0
        ))
        proj["overallRiskScore"] = round(risk_score, 2)
        return proj
    return {}
