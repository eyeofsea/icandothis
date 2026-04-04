from fastapi import APIRouter

from app.database.neo4j_client import get_neo4j

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/dashboard")
async def get_dashboard():
    db = await get_neo4j()
    query = """
    OPTIONAL MATCH (p:Project)
    WITH count(p) AS totalProjects, collect(p) AS projects
    OPTIONAL MATCH (e:Equipment)
    WITH totalProjects, projects, count(e) AS totalEquipment
    OPTIONAL MATCH (s:Supplier)
    WITH totalProjects, projects, totalEquipment, count(s) AS totalSuppliers
    OPTIONAL MATCH (r:ShippingRoute)
    WITH totalProjects, projects, totalEquipment, totalSuppliers,
         count(r) AS totalRoutes,
         count(CASE WHEN r.currentStatus IN ['disrupted', 'blocked', 'delayed'] THEN 1 END) AS disruptedRoutes
    OPTIONAL MATCH (d:DisruptionEvent)
    WHERE d.verificationStatus <> 'resolved'
    WITH totalProjects, projects, totalEquipment, totalSuppliers,
         totalRoutes, disruptedRoutes,
         count(d) AS activeDisruptions
    OPTIONAL MATCH (eqRisk:Equipment)-[:SHIPPED_VIA]->(rr:ShippingRoute)
    WHERE rr.currentStatus IN ['disrupted', 'blocked', 'delayed']
    WITH totalProjects, projects, totalEquipment, totalSuppliers,
         totalRoutes, disruptedRoutes, activeDisruptions,
         count(DISTINCT eqRisk) AS equipmentAtRisk
    RETURN {
        totalProjects: totalProjects,
        totalEquipment: totalEquipment,
        totalSuppliers: totalSuppliers,
        totalRoutes: totalRoutes,
        disruptedRoutes: disruptedRoutes,
        activeDisruptions: activeDisruptions,
        equipmentAtRisk: equipmentAtRisk,
        avgProjectCompletion: CASE WHEN totalProjects > 0
            THEN reduce(total = 0.0, proj IN projects | total + coalesce(proj.completionPct, 0.0)) / totalProjects
            ELSE 0.0 END,
        totalPortfolioValue: reduce(total = 0.0, proj IN projects | total + coalesce(proj.totalValue, 0.0)),
        overallRiskScore: CASE WHEN totalRoutes > 0
            THEN round(toFloat(disruptedRoutes) / totalRoutes * 10.0, 1)
            ELSE 0.0 END
    } AS dashboard
    """
    records = await db.execute_read(query)
    return records[0]["dashboard"] if records else {}


@router.get("/risk-matrix")
async def get_risk_matrix():
    db = await get_neo4j()
    query = """
    MATCH (p:Project)-[:HAS_EQUIPMENT]->(e:Equipment)
    OPTIONAL MATCH (e)-[:SHIPPED_VIA]->(r:ShippingRoute)
    OPTIONAL MATCH (r)-[:PASSES_THROUGH]->(z:GeopoliticalZone)
    OPTIONAL MATCH (e)-[:SUPPLIED_BY]->(s:Supplier)
    WITH p, e,
         CASE e.criticality
             WHEN 'critical' THEN 5
             WHEN 'high' THEN 4
             WHEN 'medium' THEN 3
             ELSE 2 END AS impactScore,
         CASE
             WHEN r.currentStatus = 'blocked' THEN 5
             WHEN r.currentStatus = 'disrupted' THEN 4
             WHEN r.currentStatus = 'delayed' THEN 3
             WHEN size(s.riskFlags) > 2 THEN 3
             WHEN coalesce(z.riskLevel, 0) > 7 THEN 4
             WHEN coalesce(z.riskLevel, 0) > 4 THEN 3
             ELSE 1 END AS likelihoodScore,
         r, s
    RETURN {
        equipmentId: e.equipmentId,
        equipmentName: e.name,
        projectId: p.projectId,
        projectName: p.name,
        category: e.category,
        criticality: e.criticality,
        impactScore: impactScore,
        likelihoodScore: likelihoodScore,
        riskScore: impactScore * likelihoodScore,
        routeStatus: r.currentStatus,
        supplierRiskFlags: s.riskFlags
    } AS item
    ORDER BY item.riskScore DESC
    LIMIT 100
    """
    records = await db.execute_read(query)
    items = [record["item"] for record in records]

    matrix = {"critical": [], "high": [], "medium": [], "low": []}
    for item in items:
        score = item.get("riskScore", 0)
        if score >= 20:
            matrix["critical"].append(item)
        elif score >= 12:
            matrix["high"].append(item)
        elif score >= 6:
            matrix["medium"].append(item)
        else:
            matrix["low"].append(item)

    return {
        "items": items,
        "matrix": matrix,
        "summary": {
            "critical": len(matrix["critical"]),
            "high": len(matrix["high"]),
            "medium": len(matrix["medium"]),
            "low": len(matrix["low"]),
        },
    }


@router.get("/cost-impact")
async def get_cost_impact():
    db = await get_neo4j()
    query = """
    MATCH (p:Project)-[:HAS_EQUIPMENT]->(e:Equipment)-[:SHIPPED_VIA]->(r:ShippingRoute)
    WHERE r.currentStatus IN ['disrupted', 'blocked', 'delayed']
    OPTIONAL MATCH (r)-[:PASSES_THROUGH]->(z:GeopoliticalZone)
    OPTIONAL MATCH (z)<-[:AFFECTS_ZONE]-(d:DisruptionEvent)
    WHERE d.verificationStatus <> 'resolved'
    WITH p, e, r, d,
         CASE r.currentStatus
             WHEN 'blocked' THEN coalesce(r.shippingCost, 0.0) * 2.5
             WHEN 'disrupted' THEN coalesce(r.shippingCost, 0.0) * 1.5
             WHEN 'delayed' THEN coalesce(r.shippingCost, 0.0) * 0.3
             ELSE 0.0 END AS reroutingCost,
         CASE e.criticality
             WHEN 'critical' THEN 100000.0
             WHEN 'high' THEN 50000.0
             WHEN 'medium' THEN 20000.0
             ELSE 5000.0 END AS delayPenalty,
         CASE r.currentStatus
             WHEN 'blocked' THEN coalesce(r.insuranceCost, 0.0) * 3.0
             WHEN 'disrupted' THEN coalesce(r.insuranceCost, 0.0) * 2.0
             ELSE coalesce(r.insuranceCost, 0.0) * 1.2 END AS insuranceSurcharge
    WITH p,
         collect({
             equipmentId: e.equipmentId,
             equipmentName: e.name,
             criticality: e.criticality,
             routeId: r.routeId,
             routeName: r.name,
             routeStatus: r.currentStatus,
             reroutingCost: reroutingCost,
             delayPenalty: delayPenalty,
             insuranceSurcharge: insuranceSurcharge,
             totalItemCost: reroutingCost + delayPenalty + insuranceSurcharge,
             disruption: CASE WHEN d IS NOT NULL
                 THEN {eventId: d.eventId, type: d.type, severity: d.severity}
                 ELSE null END
         }) AS impactItems,
         sum(reroutingCost + delayPenalty + insuranceSurcharge) AS projectTotalCost
    RETURN {
        projectId: p.projectId,
        projectName: p.name,
        projectValue: p.totalValue,
        totalCostImpact: projectTotalCost,
        costImpactPct: CASE WHEN p.totalValue > 0
            THEN round(projectTotalCost / p.totalValue * 100.0, 2)
            ELSE 0.0 END,
        affectedItems: size(impactItems),
        breakdown: impactItems
    } AS projectImpact
    ORDER BY projectTotalCost DESC
    """
    records = await db.execute_read(query)
    project_impacts = [record["projectImpact"] for record in records]

    total_cost = sum(p.get("totalCostImpact", 0) for p in project_impacts)
    total_rerouting = sum(
        item.get("reroutingCost", 0)
        for p in project_impacts
        for item in p.get("breakdown", [])
    )
    total_penalties = sum(
        item.get("delayPenalty", 0)
        for p in project_impacts
        for item in p.get("breakdown", [])
    )
    total_insurance = sum(
        item.get("insuranceSurcharge", 0)
        for p in project_impacts
        for item in p.get("breakdown", [])
    )

    return {
        "projectImpacts": project_impacts,
        "totals": {
            "totalCostImpact": total_cost,
            "reroutingCosts": total_rerouting,
            "delayPenalties": total_penalties,
            "insuranceSurcharges": total_insurance,
            "projectsAffected": len(project_impacts),
        },
    }
