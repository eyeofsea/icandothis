from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.database.neo4j_client import get_neo4j
from app.models.route import RouteAlternative, ShippingRoute

router = APIRouter(prefix="/api/routes", tags=["routes"])


@router.get("", response_model=List[ShippingRoute])
async def list_routes(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    db = await get_neo4j()
    where_clauses = []
    params: dict = {"limit": limit, "offset": offset}

    if status:
        where_clauses.append("r.currentStatus = $status")
        params["status"] = status

    where = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    query = f"""
    MATCH (r:ShippingRoute)
    {where}
    RETURN r {{
        .routeId, .name, .totalDistanceNm, .estimatedTransitDays,
        .shippingCost, .insuranceCost, .currentStatus
    }} AS route
    ORDER BY r.name
    SKIP $offset LIMIT $limit
    """
    records = await db.execute_read(query, params)
    return [record["route"] for record in records]


@router.get("/disrupted")
async def get_disrupted_routes():
    db = await get_neo4j()
    query = """
    MATCH (r:ShippingRoute)
    WHERE r.currentStatus IN ['disrupted', 'blocked', 'delayed']
    OPTIONAL MATCH (r)-[:PASSES_THROUGH]->(z:GeopoliticalZone)
    OPTIONAL MATCH (z)<-[:AFFECTS_ZONE]-(d:DisruptionEvent)
    WHERE d.verificationStatus <> 'resolved'
    OPTIONAL MATCH (e:Equipment)-[:SHIPPED_VIA]->(r)
    OPTIONAL MATCH (p:Project)-[:HAS_EQUIPMENT]->(e)
    RETURN r {
        .routeId, .name, .currentStatus, .totalDistanceNm,
        .estimatedTransitDays, .shippingCost,
        affectedZones: collect(DISTINCT {
            zoneId: z.zoneId,
            name: z.name,
            riskLevel: z.riskLevel
        }),
        disruptions: collect(DISTINCT {
            eventId: d.eventId,
            type: d.type,
            severity: d.severity,
            description: d.description
        }),
        affectedEquipment: collect(DISTINCT {
            equipmentId: e.equipmentId,
            name: e.name,
            criticality: e.criticality,
            projectId: p.projectId,
            projectName: p.name
        })
    } AS route
    ORDER BY
        CASE r.currentStatus
            WHEN 'blocked' THEN 0
            WHEN 'disrupted' THEN 1
            ELSE 2 END
    """
    records = await db.execute_read(query)
    results = []
    for record in records:
        route = record["route"]
        route["affectedZones"] = [z for z in route["affectedZones"] if z.get("zoneId")]
        route["disruptions"] = [d for d in route["disruptions"] if d.get("eventId")]
        route["affectedEquipment"] = [e for e in route["affectedEquipment"] if e.get("equipmentId")]
        results.append(route)
    return results


@router.get("/{route_id}", response_model=ShippingRoute)
async def get_route(route_id: str):
    db = await get_neo4j()
    query = """
    MATCH (r:ShippingRoute {routeId: $routeId})
    RETURN r {
        .routeId, .name, .totalDistanceNm, .estimatedTransitDays,
        .shippingCost, .insuranceCost, .currentStatus
    } AS route
    """
    records = await db.execute_read(query, {"routeId": route_id})
    if not records:
        raise HTTPException(status_code=404, detail="Route not found")
    return records[0]["route"]


@router.get("/{route_id}/alternatives", response_model=List[RouteAlternative])
async def get_route_alternatives(route_id: str):
    db = await get_neo4j()
    query = """
    MATCH (original:ShippingRoute {routeId: $routeId})
    OPTIONAL MATCH (original)-[:HAS_ALTERNATIVE]->(alt:ShippingRoute)
    WHERE alt.currentStatus = 'active'
    WITH original, alt
    WHERE alt IS NOT NULL
    RETURN {
        routeId: alt.routeId,
        routeName: alt.name,
        totalDistanceNm: coalesce(alt.totalDistanceNm, 0.0),
        estimatedTransitDays: coalesce(alt.estimatedTransitDays, 0),
        shippingCost: coalesce(alt.shippingCost, 0.0),
        additionalCost: coalesce(alt.shippingCost, 0.0) - coalesce(original.shippingCost, 0.0),
        additionalDays: coalesce(alt.estimatedTransitDays, 0) - coalesce(original.estimatedTransitDays, 0),
        riskScore: CASE alt.currentStatus
            WHEN 'active' THEN 1.0
            WHEN 'delayed' THEN 5.0
            WHEN 'disrupted' THEN 8.0
            WHEN 'blocked' THEN 10.0
            ELSE 3.0 END
    } AS alternative
    ORDER BY alternative.riskScore ASC, alternative.additionalDays ASC
    LIMIT 10
    """
    records = await db.execute_read(query, {"routeId": route_id})
    return [record["alternative"] for record in records]
