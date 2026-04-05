import uuid
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.database.neo4j_client import get_neo4j
from app.models.disruption import (
    DisruptionEvent,
    DisruptionEventCreate,
    DisruptionImpact,
    DisruptionSimulationRequest,
    DisruptionSimulationResult,
)

router = APIRouter(prefix="/api/disruptions", tags=["disruptions"])


@router.get("")
async def list_disruptions(
    event_type: Optional[str] = Query(None, alias="type"),
    severity: Optional[int] = Query(None, ge=1, le=5),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    db = await get_neo4j()
    where_clauses = []
    params: dict = {"limit": limit, "offset": offset}

    if event_type:
        where_clauses.append("d.type = $type")
        params["type"] = event_type
    if severity:
        where_clauses.append("d.severity = $severity")
        params["severity"] = severity
    if status:
        where_clauses.append("d.verificationStatus = $status")
        params["status"] = status

    where = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    query = f"""
    MATCH (d:DisruptionEvent)
    {where}
    OPTIONAL MATCH (d)-[:AFFECTS_ZONE]->(z:GeopoliticalZone)
    WITH d, collect(z.zoneId) AS zones
    RETURN {{
        eventId: d.eventId, name: d.name, type: d.type,
        severity: d.severity, startDate: toString(d.startDate),
        endDate: toString(d.endDate), source: d.source,
        verificationStatus: d.verificationStatus,
        description: d.description,
        createdAt: toString(d.createdAt),
        status: d.status,
        affectedZones: zones,
        affectedZoneIds: zones
    }} AS disruption
    ORDER BY d.severity DESC, d.startDate DESC
    SKIP $offset LIMIT $limit
    """
    records = await db.execute_read(query, params)
    return [record["disruption"] for record in records]


@router.post("", response_model=DisruptionEvent, status_code=201)
async def create_disruption(event: DisruptionEventCreate):
    db = await get_neo4j()
    event_id = f"DISRUPT-{uuid.uuid4().hex[:8].upper()}"

    query = """
    CREATE (d:DisruptionEvent {
        eventId: $eventId,
        name: $name,
        type: $type,
        severity: $severity,
        startDate: date($startDate),
        endDate: CASE WHEN $endDate IS NOT NULL THEN date($endDate) ELSE null END,
        source: $source,
        verificationStatus: $verificationStatus,
        status: $status,
        description: $description,
        createdAt: datetime()
    })
    WITH d
    UNWIND CASE WHEN size($affectedZones) > 0 THEN $affectedZones ELSE [null] END AS zoneId
    OPTIONAL MATCH (z:GeopoliticalZone {zoneId: zoneId})
    FOREACH (_ IN CASE WHEN z IS NOT NULL THEN [1] ELSE [] END |
        CREATE (d)-[:AFFECTS_ZONE]->(z)
    )
    WITH d
    OPTIONAL MATCH (d)-[:AFFECTS_ZONE]->(z:GeopoliticalZone)
    WITH d, collect(z.zoneId) AS zones
    RETURN d {
        .eventId, .name, .type, .severity,
        startDate: toString(d.startDate),
        endDate: toString(d.endDate),
        .source, .verificationStatus, .status, .description,
        createdAt: toString(d.createdAt),
        affectedZones: zones,
        affectedZoneIds: zones
    } AS disruption
    """
    params = {
        "eventId": event_id,
        "name": event.name or f"Disruption {event_id}",
        "type": event.type.value,
        "severity": event.severity,
        "startDate": event.startDate.isoformat(),
        "endDate": event.endDate.isoformat() if event.endDate else None,
        "source": event.source,
        "verificationStatus": event.verificationStatus.value,
        "status": event.status.value,
        "description": event.description,
        "affectedZones": event.affectedZones,
    }
    records = await db.execute_write(query, params)
    if not records:
        raise HTTPException(status_code=500, detail="Failed to create disruption event")
    return records[0]["disruption"]


@router.get("/{event_id}/impact", response_model=DisruptionImpact)
async def get_disruption_impact(event_id: str):
    db = await get_neo4j()
    query = """
    MATCH (d:DisruptionEvent {eventId: $eventId})
    OPTIONAL MATCH (d)-[:AFFECTS_ZONE]->(z:GeopoliticalZone)
    OPTIONAL MATCH (r:ShippingRoute)-[:PASSES_THROUGH]->(z)
    OPTIONAL MATCH (e:Equipment)-[:SHIPPED_VIA]->(r)
    OPTIONAL MATCH (p:Project)-[:HAS_EQUIPMENT]->(e)
    OPTIONAL MATCH (s:Supplier)-[:LOCATED_IN]->(z)
    WITH d,
         collect(DISTINCT {
             projectId: p.projectId,
             name: p.name,
             country: p.country,
             status: p.status
         }) AS projects,
         collect(DISTINCT {
             equipmentId: e.equipmentId,
             name: e.name,
             criticality: e.criticality
         }) AS equipment,
         collect(DISTINCT {
             routeId: r.routeId,
             name: r.name,
             currentStatus: r.currentStatus
         }) AS routes,
         collect(DISTINCT {
             supplierId: s.supplierId,
             name: s.name,
             country: s.country
         }) AS suppliers
    RETURN {
        eventId: d.eventId,
        description: d.description,
        severity: d.severity,
        affectedProjects: [p IN projects WHERE p.projectId IS NOT NULL],
        affectedEquipment: [e IN equipment WHERE e.equipmentId IS NOT NULL],
        affectedRoutes: [r IN routes WHERE r.routeId IS NOT NULL],
        affectedSuppliers: [s IN suppliers WHERE s.supplierId IS NOT NULL],
        estimatedDelayDays: d.severity * 14,
        estimatedCostImpact: d.severity * size([e IN equipment WHERE e.equipmentId IS NOT NULL]) * 30000.0
    } AS impact
    """
    records = await db.execute_read(query, {"eventId": event_id})
    if not records:
        raise HTTPException(status_code=404, detail="Disruption event not found")
    return records[0]["impact"]


@router.post("/simulate", response_model=DisruptionSimulationResult)
async def simulate_disruption(request: DisruptionSimulationRequest):
    db = await get_neo4j()
    query = """
    UNWIND $affectedZones AS zoneName
    OPTIONAL MATCH (z:GeopoliticalZone)
    WHERE z.zoneId = zoneName OR z.name CONTAINS zoneName
    WITH collect(z) AS zones
    UNWIND CASE WHEN size(zones) > 0 THEN zones ELSE [null] END AS z
    OPTIONAL MATCH (r:ShippingRoute)-[:PASSES_THROUGH]->(z)
    OPTIONAL MATCH (e:Equipment)-[:SHIPPED_VIA]->(r)
    OPTIONAL MATCH (p:Project)-[:HAS_EQUIPMENT]->(e)
    OPTIONAL MATCH (s:Supplier)-[:LOCATED_IN]->(z)
    WITH
        collect(DISTINCT {
            projectId: p.projectId,
            name: p.name,
            country: p.country,
            totalValue: p.totalValue
        }) AS projects,
        collect(DISTINCT {
            equipmentId: e.equipmentId,
            name: e.name,
            criticality: e.criticality,
            weight: e.weight
        }) AS equipment,
        collect(DISTINCT {
            routeId: r.routeId,
            name: r.name,
            shippingCost: r.shippingCost,
            estimatedTransitDays: r.estimatedTransitDays
        }) AS routes,
        collect(DISTINCT {
            supplierId: s.supplierId,
            name: s.name,
            country: s.country,
            capabilities: s.capabilities
        }) AS suppliers
    RETURN {
        impactedProjects: [p IN projects WHERE p.projectId IS NOT NULL],
        impactedEquipment: [e IN equipment WHERE e.equipmentId IS NOT NULL],
        impactedRoutes: [r IN routes WHERE r.routeId IS NOT NULL],
        impactedSuppliers: [s IN suppliers WHERE s.supplierId IS NOT NULL],
        totalEstimatedCost: size([e IN equipment WHERE e.equipmentId IS NOT NULL]) * $severity * 25000.0
            + size([r IN routes WHERE r.routeId IS NOT NULL]) * $severity * 15000.0,
        totalDelayDays: $severity * $durationFactor,
        riskScore: toFloat($severity) * 2.0
            + size([e IN equipment WHERE e.equipmentId IS NOT NULL]) * 0.5
            + size([r IN routes WHERE r.routeId IS NOT NULL]) * 0.3
    } AS result
    """
    params = {
        "affectedZones": request.affectedZones if request.affectedZones else ["__none__"],
        "severity": request.severity,
        "durationFactor": max(1, request.durationDays // 7),
    }
    records = await db.execute_read(query, params)

    sim_result = records[0]["result"] if records else {}

    recommendations = []
    impacted_routes = sim_result.get("impactedRoutes", [])
    impacted_suppliers = sim_result.get("impactedSuppliers", [])
    impacted_equipment = sim_result.get("impactedEquipment", [])

    if impacted_routes:
        recommendations.append(
            f"Identify alternative shipping routes for {len(impacted_routes)} affected route(s)."
        )
    if impacted_suppliers:
        recommendations.append(
            f"Pre-qualify backup suppliers to cover {len(impacted_suppliers)} affected supplier(s)."
        )
    if impacted_equipment:
        critical = [e for e in impacted_equipment if e.get("criticality") == "critical"]
        if critical:
            recommendations.append(
                f"Expedite procurement for {len(critical)} critical equipment item(s)."
            )
    if request.severity >= 4:
        recommendations.append("Activate emergency procurement protocols and escalate to senior management.")
    if request.durationDays > 60:
        recommendations.append("Consider strategic buffer stock for long-duration disruption scenarios.")

    return DisruptionSimulationResult(
        scenario={
            "type": request.type.value,
            "severity": request.severity,
            "affectedZones": request.affectedZones,
            "durationDays": request.durationDays,
            "description": request.description,
        },
        impactedProjects=sim_result.get("impactedProjects", []),
        impactedEquipment=sim_result.get("impactedEquipment", []),
        impactedRoutes=impacted_routes,
        impactedSuppliers=impacted_suppliers,
        totalEstimatedCost=sim_result.get("totalEstimatedCost", 0.0),
        totalDelayDays=sim_result.get("totalDelayDays", 0),
        riskScore=min(sim_result.get("riskScore", 0.0), 10.0),
        recommendations=recommendations,
    )
