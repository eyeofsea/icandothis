from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.database.neo4j_client import get_neo4j
from app.models.supplier import Supplier, SupplierAlternative, SupplierPerformance

router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])


@router.get("", response_model=List[Supplier])
async def list_suppliers(
    country: Optional[str] = Query(None),
    tier: Optional[str] = Query(None),
    capability: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    db = await get_neo4j()
    where_clauses = []
    params: dict = {"limit": limit, "offset": offset}

    if country:
        where_clauses.append("s.country = $country")
        params["country"] = country
    if tier:
        where_clauses.append("s.tier = $tier")
        params["tier"] = tier
    if capability:
        where_clauses.append("$capability IN s.capabilities")
        params["capability"] = capability

    where = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    query = f"""
    MATCH (s:Supplier)
    {where}
    RETURN s {{
        .supplierId, .name, .country, .region, .tier,
        .capabilities, .certifications, .financialRating,
        .onTimeDeliveryRate, .qualityRejectRate, .leadTimeDays,
        .capacityUtilization, .riskFlags, .contactEmail, .contactPhone
    }} AS supplier
    ORDER BY s.name
    SKIP $offset LIMIT $limit
    """
    records = await db.execute_read(query, params)
    return [record["supplier"] for record in records]


@router.get("/{supplier_id}", response_model=Supplier)
async def get_supplier(supplier_id: str):
    db = await get_neo4j()
    query = """
    MATCH (s:Supplier {supplierId: $supplierId})
    RETURN s {
        .supplierId, .name, .country, .region, .tier,
        .capabilities, .certifications, .financialRating,
        .onTimeDeliveryRate, .qualityRejectRate, .leadTimeDays,
        .capacityUtilization, .riskFlags, .contactEmail, .contactPhone
    } AS supplier
    """
    records = await db.execute_read(query, {"supplierId": supplier_id})
    if not records:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return records[0]["supplier"]


@router.get("/{supplier_id}/alternatives", response_model=List[SupplierAlternative])
async def get_supplier_alternatives(supplier_id: str):
    db = await get_neo4j()
    query = """
    MATCH (s:Supplier {supplierId: $supplierId})
    MATCH (alt:Supplier)
    WHERE alt <> s
      AND any(cap IN s.capabilities WHERE cap IN alt.capabilities)
    WITH s, alt,
         toFloat(size([cap IN s.capabilities WHERE cap IN alt.capabilities]))
         / toFloat(size(s.capabilities)) AS capOverlap
    WHERE capOverlap >= 0.3
    RETURN {
        supplierId: alt.supplierId,
        supplierName: alt.name,
        country: alt.country,
        matchScore: round(capOverlap * 100.0, 1),
        capabilities: alt.capabilities,
        leadTimeDays: alt.leadTimeDays,
        financialRating: alt.financialRating
    } AS alternative
    ORDER BY capOverlap DESC
    LIMIT 10
    """
    records = await db.execute_read(query, {"supplierId": supplier_id})
    if not records and not await _supplier_exists(db, supplier_id):
        raise HTTPException(status_code=404, detail="Supplier not found")
    return [record["alternative"] for record in records]


@router.get("/{supplier_id}/performance", response_model=SupplierPerformance)
async def get_supplier_performance(supplier_id: str):
    db = await get_neo4j()
    query = """
    MATCH (s:Supplier {supplierId: $supplierId})
    OPTIONAL MATCH (e:Equipment)-[supplied:SUPPLIED_BY]->(s)
    OPTIONAL MATCH (ae:Equipment)-[active:SUPPLIED_BY]->(s)
    WHERE ae.status = 'in_progress'
    OPTIONAL MATCH (ce:Equipment)-[completed:SUPPLIED_BY]->(s)
    WHERE ce.status = 'delivered'
    OPTIONAL MATCH (s)-[issue:HAS_ISSUE]->(i)
    WHERE i.createdAt > datetime() - duration('P90D')
    RETURN {
        supplierId: s.supplierId,
        supplierName: s.name,
        onTimeDeliveryRate: coalesce(s.onTimeDeliveryRate, 0.0),
        qualityPassRate: 100.0 - coalesce(s.qualityRejectRate, 0.0),
        averageLeadTimeDays: toFloat(coalesce(s.leadTimeDays, 0)),
        totalOrdersCompleted: count(DISTINCT ce),
        activeOrders: count(DISTINCT ae),
        recentIssues: collect(DISTINCT CASE WHEN i IS NOT NULL
            THEN {type: labels(i)[0], description: i.description, date: toString(i.createdAt)}
            ELSE null END)
    } AS performance
    """
    records = await db.execute_read(query, {"supplierId": supplier_id})
    if not records:
        raise HTTPException(status_code=404, detail="Supplier not found")
    result = records[0]["performance"]
    result["recentIssues"] = [i for i in result.get("recentIssues", []) if i is not None]
    return result


async def _supplier_exists(db, supplier_id: str) -> bool:
    query = "MATCH (s:Supplier {supplierId: $supplierId}) RETURN count(s) > 0 AS exists"
    records = await db.execute_read(query, {"supplierId": supplier_id})
    return records[0]["exists"] if records else False
