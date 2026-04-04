from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.database.neo4j_client import get_neo4j
from app.models.equipment import Equipment, EquipmentImpact

router = APIRouter(prefix="/api/equipment", tags=["equipment"])


@router.get("", response_model=List[Equipment])
async def list_equipment(
    category: Optional[str] = Query(None, description="Filter by category"),
    criticality: Optional[str] = Query(None, description="Filter by criticality"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    db = await get_neo4j()
    where_clauses = []
    params: dict = {"limit": limit, "offset": offset}

    if category:
        where_clauses.append("e.category = $category")
        params["category"] = category
    if criticality:
        where_clauses.append("e.criticality = $criticality")
        params["criticality"] = criticality

    where = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    query = f"""
    MATCH (e:Equipment)
    {where}
    RETURN e {{
        .equipmentId, .name, .description, .category, .criticality,
        .weight, .hsCode, .requiredOnSiteDate, .installationSequencePriority,
        .specifications,
        dimensions: CASE WHEN e.dimLength IS NOT NULL
            THEN {{length: e.dimLength, width: e.dimWidth, height: e.dimHeight, unit: e.dimUnit}}
            ELSE null END
    }} AS equipment
    ORDER BY e.name
    SKIP $offset LIMIT $limit
    """
    records = await db.execute_read(query, params)
    return [record["equipment"] for record in records]


@router.get("/at-risk")
async def get_at_risk_equipment():
    db = await get_neo4j()
    query = """
    MATCH (e:Equipment)-[:SHIPPED_VIA]->(r:ShippingRoute)
    WHERE r.currentStatus IN ['disrupted', 'blocked', 'delayed']
    OPTIONAL MATCH (r)-[:PASSES_THROUGH]->(z:GeopoliticalZone)
    OPTIONAL MATCH (e)-[:SUPPLIED_BY]->(s:Supplier)
    OPTIONAL MATCH (p:Project)-[:HAS_EQUIPMENT]->(e)
    RETURN e {
        .equipmentId, .name, .criticality, .category,
        .requiredOnSiteDate,
        route: {routeId: r.routeId, name: r.name, status: r.currentStatus},
        affectedZones: collect(DISTINCT z.name),
        supplier: CASE WHEN s IS NOT NULL
            THEN {supplierId: s.supplierId, name: s.name}
            ELSE null END,
        project: CASE WHEN p IS NOT NULL
            THEN {projectId: p.projectId, name: p.name}
            ELSE null END
    } AS equipment
    ORDER BY
        CASE e.criticality
            WHEN 'critical' THEN 0
            WHEN 'high' THEN 1
            WHEN 'medium' THEN 2
            ELSE 3 END
    """
    records = await db.execute_read(query)
    return [record["equipment"] for record in records]


@router.get("/{equipment_id}", response_model=Equipment)
async def get_equipment(equipment_id: str):
    db = await get_neo4j()
    query = """
    MATCH (e:Equipment {equipmentId: $equipmentId})
    RETURN e {
        .equipmentId, .name, .description, .category, .criticality,
        .weight, .hsCode, .requiredOnSiteDate, .installationSequencePriority,
        .specifications,
        dimensions: CASE WHEN e.dimLength IS NOT NULL
            THEN {length: e.dimLength, width: e.dimWidth, height: e.dimHeight, unit: e.dimUnit}
            ELSE null END
    } AS equipment
    """
    records = await db.execute_read(query, {"equipmentId": equipment_id})
    if not records:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return records[0]["equipment"]


@router.get("/{equipment_id}/impact", response_model=EquipmentImpact)
async def get_equipment_impact(equipment_id: str):
    db = await get_neo4j()
    query = """
    MATCH (e:Equipment {equipmentId: $equipmentId})
    OPTIONAL MATCH (e)-[:SHIPPED_VIA]->(r:ShippingRoute)-[:PASSES_THROUGH]->(z:GeopoliticalZone)
    OPTIONAL MATCH (z)<-[:AFFECTS_ZONE]-(d:DisruptionEvent)
    WHERE d.verificationStatus <> 'resolved'
    WITH e, collect(DISTINCT {
        eventId: d.eventId,
        type: d.type,
        severity: d.severity,
        description: d.description,
        zone: z.name
    }) AS disruptions
    OPTIONAL MATCH (e)-[:SUPPLIED_BY]->(currentSupplier:Supplier)
    OPTIONAL MATCH (currentSupplier)-[:HAS_ALTERNATIVE]->(altSupplier:Supplier)
    WITH e, disruptions, collect(DISTINCT {
        supplierId: altSupplier.supplierId,
        name: altSupplier.name,
        country: altSupplier.country,
        leadTimeDays: altSupplier.leadTimeDays
    }) AS altSuppliers
    OPTIONAL MATCH (e)-[:SHIPPED_VIA]->(currentRoute:ShippingRoute)
    OPTIONAL MATCH (currentRoute)-[:HAS_ALTERNATIVE]->(altRoute:ShippingRoute)
    WHERE altRoute.currentStatus = 'active'
    WITH e, disruptions,
         [s IN altSuppliers WHERE s.supplierId IS NOT NULL] AS altSuppliers,
         collect(DISTINCT {
             routeId: altRoute.routeId,
             name: altRoute.name,
             estimatedTransitDays: altRoute.estimatedTransitDays,
             shippingCost: altRoute.shippingCost
         }) AS altRoutes
    RETURN {
        equipmentId: e.equipmentId,
        equipmentName: e.name,
        criticality: e.criticality,
        affectedByDisruptions: [d IN disruptions WHERE d.eventId IS NOT NULL],
        alternativeSuppliers: altSuppliers,
        alternativeRoutes: [r IN altRoutes WHERE r.routeId IS NOT NULL],
        delayRiskDays: CASE WHEN size([d IN disruptions WHERE d.eventId IS NOT NULL]) > 0
            THEN reduce(total = 0, d IN [x IN disruptions WHERE x.eventId IS NOT NULL] |
                total + coalesce(d.severity, 0) * 7)
            ELSE 0 END,
        costImpact: CASE WHEN size([d IN disruptions WHERE d.eventId IS NOT NULL]) > 0
            THEN size([d IN disruptions WHERE d.eventId IS NOT NULL]) * 25000.0
            ELSE 0.0 END
    } AS impact
    """
    records = await db.execute_read(query, {"equipmentId": equipment_id})
    if not records:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return records[0]["impact"]
