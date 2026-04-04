"""
One-way sync: Neo4j (source of truth) -> PostgreSQL (analytics/reporting).
Runs at startup and can be triggered via API.
"""
import logging
from datetime import date, datetime
from typing import Any

from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.database.neo4j_client import Neo4jClient
from app.database.session import async_session
from app.database.models_pg import (
    SupplierProfile, RouteRecord, EquipmentRegistry,
)

logger = logging.getLogger(__name__)


def _parse_date(val: Any) -> date | None:
    if val is None:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, str):
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(val, fmt).date()
            except ValueError:
                continue
    return None


async def sync_suppliers() -> int:
    neo4j = await Neo4jClient.get_instance()
    query = """
    MATCH (s:Supplier)
    OPTIONAL MATCH (s)-[:LOCATED_NEAR]->(p:Port)
    RETURN s.supplierId AS neo4j_id,
           s.name AS name,
           s.country AS country,
           s.city AS city,
           s.category AS category,
           s.financialRating AS financial_rating,
           s.capacityUtilization AS capacity_utilization,
           coalesce(s.riskFlags, []) AS risk_flags,
           coalesce(s.certifications, []) AS certifications,
           coalesce(s.capabilities, []) AS capabilities
    """
    records = await neo4j.execute_read(query)
    count = 0
    async with async_session() as session:
        for r in records:
            risk_flags = r["risk_flags"] or []
            stmt = pg_insert(SupplierProfile).values(
                neo4j_id=r["neo4j_id"],
                name=r["name"],
                country=r["country"] or "",
                city=r["city"],
                category=r["category"],
                financial_rating=r["financial_rating"],
                capacity_utilization=r["capacity_utilization"],
                is_sanctioned="sanctioned" in risk_flags,
                risk_flags=risk_flags,
                certifications=r["certifications"] or [],
                capabilities=r["capabilities"] or [],
            ).on_conflict_do_update(
                index_elements=["neo4j_id"],
                set_={
                    "name": r["name"],
                    "financial_rating": r["financial_rating"],
                    "capacity_utilization": r["capacity_utilization"],
                    "is_sanctioned": "sanctioned" in risk_flags,
                    "risk_flags": risk_flags,
                },
            )
            await session.execute(stmt)
            count += 1
        await session.commit()
    return count


async def sync_routes() -> int:
    neo4j = await Neo4jClient.get_instance()
    query = """
    MATCH (r:ShippingRoute)
    OPTIONAL MATCH (r)-[:DEPARTS_FROM]->(op:Port)
    OPTIONAL MATCH (r)-[:ARRIVES_AT]->(dp:Port)
    RETURN r.routeId AS neo4j_id,
           r.name AS name,
           op.name AS origin_port,
           dp.name AS destination_port,
           r.totalDistanceNm AS distance_nm,
           r.estimatedTransitDays AS base_transit_days,
           r.shippingCost AS base_shipping_cost,
           r.insuranceCost AS base_insurance_cost
    """
    records = await neo4j.execute_read(query)
    count = 0
    async with async_session() as session:
        for r in records:
            stmt = pg_insert(RouteRecord).values(
                neo4j_id=r["neo4j_id"],
                name=r["name"],
                origin_port=r["origin_port"],
                destination_port=r["destination_port"],
                distance_nm=r["distance_nm"],
                base_transit_days=r["base_transit_days"],
                base_shipping_cost=r["base_shipping_cost"],
                base_insurance_cost=r["base_insurance_cost"],
            ).on_conflict_do_update(
                index_elements=["neo4j_id"],
                set_={
                    "name": r["name"],
                    "base_transit_days": r["base_transit_days"],
                    "base_shipping_cost": r["base_shipping_cost"],
                },
            )
            await session.execute(stmt)
            count += 1
        await session.commit()
    return count


async def sync_equipment() -> int:
    neo4j = await Neo4jClient.get_instance()
    query = """
    MATCH (e:Equipment)
    OPTIONAL MATCH (p:Project)-[:HAS_EQUIPMENT]->(e)
    OPTIONAL MATCH (e)-[:SUPPLIED_BY]->(s:Supplier)
    OPTIONAL MATCH (e)-[:SHIPPED_VIA]->(r:ShippingRoute)
    RETURN e.equipmentId AS neo4j_id,
           e.name AS name,
           e.category AS category,
           e.criticality AS criticality,
           e.weight AS weight_kg,
           e.hsCode AS hs_code,
           p.projectId AS project_neo4j_id,
           s.supplierId AS supplier_neo4j_id,
           r.routeId AS route_neo4j_id,
           e.requiredOnSiteDate AS required_on_site_date
    """
    records = await neo4j.execute_read(query)
    count = 0
    async with async_session() as session:
        for r in records:
            stmt = pg_insert(EquipmentRegistry).values(
                neo4j_id=r["neo4j_id"],
                name=r["name"],
                category=r["category"],
                criticality=r["criticality"],
                weight_kg=r["weight_kg"],
                hs_code=r["hs_code"],
                project_neo4j_id=r["project_neo4j_id"],
                supplier_neo4j_id=r["supplier_neo4j_id"],
                route_neo4j_id=r["route_neo4j_id"],
                required_on_site_date=_parse_date(r["required_on_site_date"]),
            ).on_conflict_do_update(
                index_elements=["neo4j_id"],
                set_={
                    "name": r["name"],
                    "criticality": r["criticality"],
                    "supplier_neo4j_id": r["supplier_neo4j_id"],
                    "route_neo4j_id": r["route_neo4j_id"],
                },
            )
            await session.execute(stmt)
            count += 1
        await session.commit()
    return count


async def sync_all() -> dict[str, Any]:
    suppliers = await sync_suppliers()
    routes = await sync_routes()
    equipment = await sync_equipment()
    return {"suppliers": suppliers, "routes": routes, "equipment": equipment}
