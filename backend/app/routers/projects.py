from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.database.neo4j_client import get_neo4j
from app.models.project import Project, ProjectRiskSummary

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("")
async def list_projects(
    status: Optional[str] = Query(None, description="Filter by status"),
    country: Optional[str] = Query(None, description="Filter by country"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    db = await get_neo4j()
    where_clauses = []
    params: dict = {"limit": limit, "offset": offset}

    if status:
        where_clauses.append("p.status = $status")
        params["status"] = status
    if country:
        where_clauses.append("p.country = $country")
        params["country"] = country

    where = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    query = f"""
    MATCH (p:Project)
    {where}
    RETURN p {{
        .projectId, .name, .client, .country, .region,
        .type, .status, .totalValue, .completionPct,
        .criticalPathDeadline, .riskTolerance,
        coordinates: CASE WHEN p.lat IS NOT NULL
            THEN {{lat: p.lat, lng: p.lng}} ELSE null END
    }} AS project
    ORDER BY p.name
    SKIP $offset LIMIT $limit
    """
    records = await db.execute_read(query, params)
    return [record["project"] for record in records]


@router.get("/{project_id}")
async def get_project(project_id: str):
    db = await get_neo4j()
    query = """
    MATCH (p:Project {projectId: $projectId})
    RETURN p {
        .projectId, .name, .client, .country, .region,
        .type, .status, .totalValue, .completionPct,
        .criticalPathDeadline, .riskTolerance,
        coordinates: CASE WHEN p.lat IS NOT NULL
            THEN {lat: p.lat, lng: p.lng} ELSE null END
    } AS project
    """
    records = await db.execute_read(query, {"projectId": project_id})
    if not records:
        raise HTTPException(status_code=404, detail="Project not found")
    return records[0]["project"]


@router.get("/{project_id}/equipment")
async def get_project_equipment(project_id: str):
    db = await get_neo4j()
    query = """
    MATCH (p:Project {projectId: $projectId})-[:HAS_EQUIPMENT]->(e:Equipment)
    OPTIONAL MATCH (e)-[:SUPPLIED_BY]->(s:Supplier)
    OPTIONAL MATCH (e)-[:SHIPPED_VIA]->(r:ShippingRoute)
    RETURN e {
        .equipmentId, .name, .description, .category, .criticality,
        .weight, .hsCode, .requiredOnSiteDate, .installationSequencePriority,
        .specifications,
        dimensions: CASE WHEN e.dimLength IS NOT NULL
            THEN {length: e.dimLength, width: e.dimWidth, height: e.dimHeight, unit: e.dimUnit}
            ELSE null END,
        supplier: CASE WHEN s IS NOT NULL
            THEN {supplierId: s.supplierId, name: s.name, country: s.country}
            ELSE null END,
        route: CASE WHEN r IS NOT NULL
            THEN {routeId: r.routeId, name: r.name, currentStatus: r.currentStatus}
            ELSE null END
    } AS equipment
    ORDER BY e.installationSequencePriority
    """
    records = await db.execute_read(query, {"projectId": project_id})
    return [record["equipment"] for record in records]


@router.get("/{project_id}/risk-summary", response_model=ProjectRiskSummary)
async def get_project_risk_summary(project_id: str):
    db = await get_neo4j()
    query = """
    MATCH (p:Project {projectId: $projectId})
    OPTIONAL MATCH (p)-[:HAS_EQUIPMENT]->(e:Equipment)
    OPTIONAL MATCH (e)-[:SHIPPED_VIA]->(r:ShippingRoute)
    WHERE r.currentStatus IN ['disrupted', 'blocked', 'delayed']
    WITH p, e, r,
         CASE WHEN r IS NOT NULL THEN 1 ELSE 0 END AS routeDisrupted
    OPTIONAL MATCH (e)-[:SUPPLIED_BY]->(s:Supplier)
    WHERE size(s.riskFlags) > 0
    WITH p,
         count(DISTINCT e) AS totalEquipment,
         count(DISTINCT CASE WHEN routeDisrupted = 1 THEN e END) AS eqAtRisk,
         count(DISTINCT r) AS disruptedRoutes,
         count(DISTINCT s) AS suppliersWithIssues
    OPTIONAL MATCH (p)-[:HAS_EQUIPMENT]->(e2:Equipment)-[:SHIPPED_VIA]->(r2:ShippingRoute)
    WHERE r2.currentStatus IN ['disrupted', 'blocked', 'delayed']
    OPTIONAL MATCH (r2)-[:PASSES_THROUGH]->(z:GeopoliticalZone)
    WITH p, totalEquipment, eqAtRisk, disruptedRoutes, suppliersWithIssues,
         collect(DISTINCT {
             equipmentId: e2.equipmentId,
             name: e2.name,
             criticality: e2.criticality,
             routeStatus: r2.currentStatus,
             zone: z.name
         }) AS criticalItems
    RETURN {
        projectId: p.projectId,
        projectName: p.name,
        overallRiskScore: CASE WHEN totalEquipment > 0
            THEN toFloat(eqAtRisk) / totalEquipment * 10.0
            ELSE 0.0 END,
        equipmentAtRisk: eqAtRisk,
        disruptedRoutes: disruptedRoutes,
        supplierIssues: suppliersWithIssues,
        estimatedCostImpact: eqAtRisk * 50000.0,
        criticalItems: [item IN criticalItems WHERE item.equipmentId IS NOT NULL]
    } AS summary
    """
    records = await db.execute_read(query, {"projectId": project_id})
    if not records:
        raise HTTPException(status_code=404, detail="Project not found")
    return records[0]["summary"]
