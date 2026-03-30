#!/usr/bin/env python3
"""
Neo4j Database Seed Script for SCM Risk Intelligence Platform.

Reads JSON files from data/seed/ and populates the Neo4j graph database with
all nodes and relationships for the supply chain risk knowledge graph.

Usage:
    python backend/app/database/seed.py
    python -m backend.app.database.seed
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

from neo4j import GraphDatabase


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "scmrisk2024")

# Resolve project root (three levels up from this file)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
SEED_DIR = PROJECT_ROOT / "data" / "seed"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(filepath: Path) -> Any:
    """Load and return parsed JSON from *filepath*."""
    with open(filepath, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_all_seed_files() -> Dict[str, Any]:
    """Load every JSON file under data/seed/ into a dict keyed by stem name."""
    data: Dict[str, Any] = {}
    if not SEED_DIR.is_dir():
        print(f"[WARN] Seed directory not found: {SEED_DIR}")
        return data
    for fp in sorted(SEED_DIR.glob("*.json")):
        key = fp.stem  # e.g. "projects", "suppliers", "equipment", ...
        data[key] = load_json(fp)
        print(f"  Loaded {fp.name} ({len(data[key]) if isinstance(data[key], list) else 1} records)")
    return data


def props_for_cypher(record: dict, exclude: List[str] | None = None) -> dict:
    """Return a copy of *record* suitable for Cypher parameter injection.

    Converts nested dicts/lists to JSON strings so they can be stored as Neo4j
    properties (Neo4j does not support nested maps natively).
    """
    exclude = set(exclude or [])
    clean: dict = {}
    for k, v in record.items():
        if k in exclude:
            continue
        if isinstance(v, (dict, list)):
            clean[k] = json.dumps(v)
        else:
            clean[k] = v
    return clean


# ---------------------------------------------------------------------------
# Schema: constraints & indexes
# ---------------------------------------------------------------------------

CONSTRAINTS = [
    ("Project", "projectId"),
    ("Supplier", "supplierId"),
    ("Equipment", "equipmentId"),
    ("Port", "portId"),
    ("ShippingRoute", "routeId"),
    ("GeopoliticalZone", "zoneId"),
    ("PurchaseOrder", "poId"),
]

INDEXES = [
    ("Project", "name"),
    ("Project", "country"),
    ("Supplier", "name"),
    ("Supplier", "country"),
    ("Equipment", "name"),
    ("Equipment", "category"),
    ("Equipment", "criticality"),
    ("Port", "name"),
    ("Port", "country"),
    ("ShippingRoute", "name"),
    ("GeopoliticalZone", "name"),
    ("PurchaseOrder", "status"),
]


def create_constraints(session) -> None:
    print("\n--- Creating constraints ---")
    for label, prop in CONSTRAINTS:
        cname = f"constraint_{label.lower()}_{prop.lower()}"
        query = (
            f"CREATE CONSTRAINT {cname} IF NOT EXISTS "
            f"FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE"
        )
        session.run(query)
        print(f"  Constraint: {label}.{prop} UNIQUE")


def create_indexes(session) -> None:
    print("\n--- Creating indexes ---")
    for label, prop in INDEXES:
        iname = f"index_{label.lower()}_{prop.lower()}"
        query = (
            f"CREATE INDEX {iname} IF NOT EXISTS "
            f"FOR (n:{label}) ON (n.{prop})"
        )
        session.run(query)
        print(f"  Index: {label}.{prop}")


# ---------------------------------------------------------------------------
# Node creation helpers (batch via UNWIND)
# ---------------------------------------------------------------------------

def create_projects(session, records: List[dict]) -> int:
    query = """
    UNWIND $rows AS row
    MERGE (p:Project {projectId: row.projectId})
    SET p += row
    """
    rows = [props_for_cypher(r) for r in records]
    session.run(query, rows=rows)
    print(f"  Created {len(rows)} Project nodes")
    return len(rows)


def create_suppliers(session, records: List[dict]) -> int:
    query = """
    UNWIND $rows AS row
    MERGE (s:Supplier {supplierId: row.supplierId})
    SET s += row
    """
    rows = [props_for_cypher(r) for r in records]
    session.run(query, rows=rows)
    print(f"  Created {len(rows)} Supplier nodes")
    return len(rows)


def create_equipment(session, records: List[dict]) -> int:
    query = """
    UNWIND $rows AS row
    MERGE (e:Equipment {equipmentId: row.equipmentId})
    SET e += row
    """
    rows = [props_for_cypher(r) for r in records]
    session.run(query, rows=rows)
    print(f"  Created {len(rows)} Equipment nodes")
    return len(rows)


def create_ports(session, records: List[dict]) -> int:
    query = """
    UNWIND $rows AS row
    MERGE (p:Port {portId: row.portId})
    SET p += row
    """
    rows = [props_for_cypher(r) for r in records]
    session.run(query, rows=rows)
    print(f"  Created {len(rows)} Port nodes")
    return len(rows)


def create_routes(session, records: List[dict]) -> int:
    query = """
    UNWIND $rows AS row
    MERGE (r:ShippingRoute {routeId: row.routeId})
    SET r += row
    """
    rows = [props_for_cypher(r) for r in records]
    session.run(query, rows=rows)
    print(f"  Created {len(rows)} ShippingRoute nodes")
    return len(rows)


def create_zones(session, records: List[dict]) -> int:
    query = """
    UNWIND $rows AS row
    MERGE (z:GeopoliticalZone {zoneId: row.zoneId})
    SET z += row
    """
    rows = [props_for_cypher(r) for r in records]
    session.run(query, rows=rows)
    print(f"  Created {len(rows)} GeopoliticalZone nodes")
    return len(rows)


def create_purchase_orders(session, records: List[dict]) -> int:
    # Normalize: accept either "poId" or "poNumber" as the primary key
    rows = []
    for r in records:
        clean = props_for_cypher(r)
        if "poNumber" in clean and "poId" not in clean:
            clean["poId"] = clean["poNumber"]
        rows.append(clean)
    query = """
    UNWIND $rows AS row
    MERGE (po:PurchaseOrder {poId: row.poId})
    SET po += row
    """
    session.run(query, rows=rows)
    print(f"  Created {len(rows)} PurchaseOrder nodes")
    return len(rows)


# ---------------------------------------------------------------------------
# Relationship creation helpers (batch via UNWIND)
# ---------------------------------------------------------------------------

def create_project_equipment_rels(session, equipment_records: List[dict]) -> int:
    """Project -[:HAS_EQUIPMENT]-> Equipment"""
    pairs = []
    for eq in equipment_records:
        pid = eq.get("projectId")
        eid = eq.get("equipmentId")
        if pid and eid:
            pairs.append({"pid": pid, "eid": eid})
    if not pairs:
        return 0
    query = """
    UNWIND $pairs AS pair
    MATCH (p:Project {projectId: pair.pid})
    MATCH (e:Equipment {equipmentId: pair.eid})
    MERGE (p)-[:HAS_EQUIPMENT]->(e)
    """
    session.run(query, pairs=pairs)
    print(f"  Created {len(pairs)} HAS_EQUIPMENT relationships")
    return len(pairs)


def create_equipment_po_rels(session, equipment_records: List[dict]) -> int:
    """Equipment -[:ORDERED_VIA]-> PurchaseOrder"""
    pairs = []
    for eq in equipment_records:
        eid = eq.get("equipmentId")
        po_id = eq.get("purchaseOrderId") or eq.get("poId")
        if eid and po_id:
            pairs.append({"eid": eid, "poId": po_id})
    if not pairs:
        return 0
    query = """
    UNWIND $pairs AS pair
    MATCH (e:Equipment {equipmentId: pair.eid})
    MATCH (po:PurchaseOrder {poId: pair.poId})
    MERGE (e)-[:ORDERED_VIA]->(po)
    """
    session.run(query, pairs=pairs)
    print(f"  Created {len(pairs)} ORDERED_VIA relationships")
    return len(pairs)


def create_po_supplier_rels(session, po_records: List[dict]) -> int:
    """PurchaseOrder -[:ISSUED_TO]-> Supplier"""
    pairs = []
    for po in po_records:
        po_id = po.get("poId")
        sid = po.get("supplierId")
        if po_id and sid:
            pairs.append({"poId": po_id, "sid": sid})
    if not pairs:
        return 0
    query = """
    UNWIND $pairs AS pair
    MATCH (po:PurchaseOrder {poId: pair.poId})
    MATCH (s:Supplier {supplierId: pair.sid})
    MERGE (po)-[:ISSUED_TO]->(s)
    """
    session.run(query, pairs=pairs)
    print(f"  Created {len(pairs)} ISSUED_TO relationships")
    return len(pairs)


def create_equipment_supplier_rels(session, equipment_records: List[dict]) -> int:
    """Equipment -[:SUPPLIED_BY]-> Supplier"""
    pairs = []
    for eq in equipment_records:
        eid = eq.get("equipmentId")
        sid = eq.get("supplierId")
        if eid and sid:
            pairs.append({"eid": eid, "sid": sid})
    if not pairs:
        return 0
    query = """
    UNWIND $pairs AS pair
    MATCH (e:Equipment {equipmentId: pair.eid})
    MATCH (s:Supplier {supplierId: pair.sid})
    MERGE (e)-[:SUPPLIED_BY]->(s)
    """
    session.run(query, pairs=pairs)
    print(f"  Created {len(pairs)} SUPPLIED_BY relationships")
    return len(pairs)


def create_equipment_route_rels(session, equipment_records: List[dict]) -> int:
    """Equipment -[:SHIPPED_VIA]-> ShippingRoute"""
    pairs = []
    for eq in equipment_records:
        eid = eq.get("equipmentId")
        rid = eq.get("routeId")
        if eid and rid:
            pairs.append({"eid": eid, "rid": rid})
    if not pairs:
        return 0
    query = """
    UNWIND $pairs AS pair
    MATCH (e:Equipment {equipmentId: pair.eid})
    MATCH (r:ShippingRoute {routeId: pair.rid})
    MERGE (e)-[:SHIPPED_VIA]->(r)
    """
    session.run(query, pairs=pairs)
    print(f"  Created {len(pairs)} SHIPPED_VIA relationships")
    return len(pairs)


def create_route_zone_rels(session, route_records: List[dict]) -> int:
    """ShippingRoute -[:PASSES_THROUGH]-> GeopoliticalZone"""
    pairs = []
    for rt in route_records:
        rid = rt.get("routeId")
        zones = rt.get("passesThrough") or rt.get("passesThroughZones") or rt.get("zones") or []
        for zid in zones:
            pairs.append({"rid": rid, "zid": zid})
    if not pairs:
        return 0
    query = """
    UNWIND $pairs AS pair
    MATCH (r:ShippingRoute {routeId: pair.rid})
    MATCH (z:GeopoliticalZone {zoneId: pair.zid})
    MERGE (r)-[:PASSES_THROUGH]->(z)
    """
    session.run(query, pairs=pairs)
    print(f"  Created {len(pairs)} PASSES_THROUGH relationships")
    return len(pairs)


def create_route_port_rels(session, route_records: List[dict]) -> int:
    """ShippingRoute -[:DEPARTS_FROM]-> Port and -[:ARRIVES_AT]-> Port"""
    departs = []
    arrives = []
    for rt in route_records:
        rid = rt.get("routeId")
        # Try explicit fields first, then fall back to first/last waypoint
        dep = rt.get("departurePortId") or rt.get("originPortId")
        arr = rt.get("arrivalPortId") or rt.get("destinationPortId")
        if not dep or not arr:
            waypoints = rt.get("waypoints", [])
            if waypoints:
                if not dep:
                    first_wp = waypoints[0]
                    dep = first_wp.get("portId") if isinstance(first_wp, dict) else first_wp
                if not arr:
                    last_wp = waypoints[-1]
                    arr = last_wp.get("portId") if isinstance(last_wp, dict) else last_wp
        if rid and dep:
            departs.append({"rid": rid, "pid": dep})
        if rid and arr:
            arrives.append({"rid": rid, "pid": arr})

    count = 0
    if departs:
        session.run("""
            UNWIND $pairs AS pair
            MATCH (r:ShippingRoute {routeId: pair.rid})
            MATCH (p:Port {portId: pair.pid})
            MERGE (r)-[:DEPARTS_FROM]->(p)
        """, pairs=departs)
        count += len(departs)
        print(f"  Created {len(departs)} DEPARTS_FROM relationships")

    if arrives:
        session.run("""
            UNWIND $pairs AS pair
            MATCH (r:ShippingRoute {routeId: pair.rid})
            MATCH (p:Port {portId: pair.pid})
            MERGE (r)-[:ARRIVES_AT]->(p)
        """, pairs=arrives)
        count += len(arrives)
        print(f"  Created {len(arrives)} ARRIVES_AT relationships")

    return count


def create_supplier_port_rels(session, supplier_records: List[dict]) -> int:
    """Supplier -[:LOCATED_NEAR]-> Port"""
    pairs = []
    for sup in supplier_records:
        sid = sup.get("supplierId")
        pid = sup.get("nearestPortId") or sup.get("portId")
        if sid and pid:
            pairs.append({"sid": sid, "pid": pid})
    if not pairs:
        return 0
    query = """
    UNWIND $pairs AS pair
    MATCH (s:Supplier {supplierId: pair.sid})
    MATCH (p:Port {portId: pair.pid})
    MERGE (s)-[:LOCATED_NEAR]->(p)
    """
    session.run(query, pairs=pairs)
    print(f"  Created {len(pairs)} LOCATED_NEAR relationships")
    return len(pairs)


def create_supplier_alternative_rels(session, supplier_records: List[dict]) -> int:
    """Supplier -[:HAS_ALTERNATIVE]-> Supplier"""
    pairs = []
    for sup in supplier_records:
        sid = sup.get("supplierId")
        alts = sup.get("alternativeSuppliers") or sup.get("alternatives") or []
        for alt in alts:
            alt_id = alt if isinstance(alt, str) else alt.get("supplierId")
            if sid and alt_id:
                pairs.append({"sid": sid, "altId": alt_id})
    if not pairs:
        return 0
    query = """
    UNWIND $pairs AS pair
    MATCH (s1:Supplier {supplierId: pair.sid})
    MATCH (s2:Supplier {supplierId: pair.altId})
    MERGE (s1)-[:HAS_ALTERNATIVE]->(s2)
    """
    session.run(query, pairs=pairs)
    print(f"  Created {len(pairs)} HAS_ALTERNATIVE (Supplier) relationships")
    return len(pairs)


def create_route_alternative_rels(session, route_records: List[dict]) -> int:
    """ShippingRoute -[:HAS_ALTERNATIVE]-> ShippingRoute"""
    pairs = []
    for rt in route_records:
        rid = rt.get("routeId")
        alts = rt.get("alternativeRoutes") or rt.get("alternatives") or []
        for alt in alts:
            alt_id = alt if isinstance(alt, str) else alt.get("routeId")
            if rid and alt_id:
                pairs.append({"rid": rid, "altId": alt_id})
    if not pairs:
        return 0
    query = """
    UNWIND $pairs AS pair
    MATCH (r1:ShippingRoute {routeId: pair.rid})
    MATCH (r2:ShippingRoute {routeId: pair.altId})
    MERGE (r1)-[:HAS_ALTERNATIVE]->(r2)
    """
    session.run(query, pairs=pairs)
    print(f"  Created {len(pairs)} HAS_ALTERNATIVE (Route) relationships")
    return len(pairs)


def create_equipment_substitute_rels(session, equipment_records: List[dict]) -> int:
    """Equipment -[:HAS_SUBSTITUTE]-> Equipment"""
    pairs = []
    for eq in equipment_records:
        eid = eq.get("equipmentId")
        subs = eq.get("substitutes") or eq.get("alternativeEquipment") or []
        for sub in subs:
            sub_id = sub if isinstance(sub, str) else sub.get("equipmentId")
            if eid and sub_id:
                pairs.append({"eid": eid, "subId": sub_id})
    if not pairs:
        return 0
    query = """
    UNWIND $pairs AS pair
    MATCH (e1:Equipment {equipmentId: pair.eid})
    MATCH (e2:Equipment {equipmentId: pair.subId})
    MERGE (e1)-[:HAS_SUBSTITUTE]->(e2)
    """
    session.run(query, pairs=pairs)
    print(f"  Created {len(pairs)} HAS_SUBSTITUTE relationships")
    return len(pairs)


# ---------------------------------------------------------------------------
# Main seeding logic
# ---------------------------------------------------------------------------

def clear_database(session) -> None:
    """Delete all nodes and relationships."""
    print("\n--- Clearing existing data ---")
    result = session.run("MATCH (n) RETURN count(n) AS cnt")
    record = result.single()
    existing = record["cnt"] if record else 0
    print(f"  Existing nodes: {existing}")
    if existing > 0:
        # Delete in batches to avoid memory issues on large graphs
        session.run("MATCH (n) DETACH DELETE n")
        print("  All nodes and relationships deleted.")
    else:
        print("  Database is already empty.")


def seed_nodes(session, data: Dict[str, Any]) -> Dict[str, int]:
    """Create all node types from seed data. Returns counts per type."""
    print("\n--- Creating nodes ---")
    counts: Dict[str, int] = {}

    if "projects" in data:
        counts["Project"] = create_projects(session, data["projects"])

    if "suppliers" in data:
        counts["Supplier"] = create_suppliers(session, data["suppliers"])

    if "equipment" in data:
        counts["Equipment"] = create_equipment(session, data["equipment"])

    if "ports" in data:
        counts["Port"] = create_ports(session, data["ports"])

    if "routes" in data:
        counts["ShippingRoute"] = create_routes(session, data["routes"])
    elif "shipping_routes" in data:
        counts["ShippingRoute"] = create_routes(session, data["shipping_routes"])

    if "zones" in data:
        counts["GeopoliticalZone"] = create_zones(session, data["zones"])
    elif "geopolitical_zones" in data:
        counts["GeopoliticalZone"] = create_zones(session, data["geopolitical_zones"])

    if "purchase_orders" in data:
        counts["PurchaseOrder"] = create_purchase_orders(session, data["purchase_orders"])
    elif "purchaseOrders" in data:
        counts["PurchaseOrder"] = create_purchase_orders(session, data["purchaseOrders"])

    return counts


def create_relationships_from_file(session, rels_data: dict) -> Dict[str, int]:
    """Create alternative relationships from the relationships.json file."""
    counts: Dict[str, int] = {}

    # Supplier alternatives
    supplier_alts = rels_data.get("supplierAlternatives", [])
    if supplier_alts:
        pairs = [{"sid": r["supplierId"], "altId": r["alternativeId"]} for r in supplier_alts]
        session.run("""
            UNWIND $pairs AS pair
            MATCH (s1:Supplier {supplierId: pair.sid})
            MATCH (s2:Supplier {supplierId: pair.altId})
            MERGE (s1)-[:HAS_ALTERNATIVE]->(s2)
        """, pairs=pairs)
        print(f"  Created {len(pairs)} HAS_ALTERNATIVE (Supplier) from relationships.json")
        counts["HAS_ALTERNATIVE (Supplier) file"] = len(pairs)

    # Route alternatives
    route_alts = rels_data.get("routeAlternatives", [])
    if route_alts:
        pairs = [{"rid": r["routeId"], "altId": r["alternativeId"]} for r in route_alts]
        session.run("""
            UNWIND $pairs AS pair
            MATCH (r1:ShippingRoute {routeId: pair.rid})
            MATCH (r2:ShippingRoute {routeId: pair.altId})
            MERGE (r1)-[:HAS_ALTERNATIVE]->(r2)
        """, pairs=pairs)
        print(f"  Created {len(pairs)} HAS_ALTERNATIVE (Route) from relationships.json")
        counts["HAS_ALTERNATIVE (Route) file"] = len(pairs)

    # Equipment substitutes
    eq_subs = rels_data.get("equipmentSubstitutes", [])
    if eq_subs:
        pairs = [{"eid": r["equipmentId"], "subId": r["substituteId"]} for r in eq_subs]
        session.run("""
            UNWIND $pairs AS pair
            MATCH (e1:Equipment {equipmentId: pair.eid})
            MATCH (e2:Equipment {equipmentId: pair.subId})
            MERGE (e1)-[:HAS_SUBSTITUTE]->(e2)
        """, pairs=pairs)
        print(f"  Created {len(pairs)} HAS_SUBSTITUTE from relationships.json")
        counts["HAS_SUBSTITUTE file"] = len(pairs)

    return counts


def seed_relationships(session, data: Dict[str, Any]) -> Dict[str, int]:
    """Create all relationship types from seed data. Returns counts per type."""
    print("\n--- Creating relationships ---")
    counts: Dict[str, int] = {}

    equipment = data.get("equipment", [])
    suppliers = data.get("suppliers", [])
    routes = data.get("routes") or data.get("shipping_routes", [])
    purchase_orders = data.get("purchase_orders") or data.get("purchaseOrders", [])

    counts["HAS_EQUIPMENT"] = create_project_equipment_rels(session, equipment)
    counts["ORDERED_VIA"] = create_equipment_po_rels(session, equipment)
    counts["ISSUED_TO"] = create_po_supplier_rels(session, purchase_orders)
    counts["SUPPLIED_BY"] = create_equipment_supplier_rels(session, equipment)
    counts["SHIPPED_VIA"] = create_equipment_route_rels(session, equipment)
    counts["PASSES_THROUGH"] = create_route_zone_rels(session, routes)
    counts["DEPARTS_FROM + ARRIVES_AT"] = create_route_port_rels(session, routes)
    counts["LOCATED_NEAR"] = create_supplier_port_rels(session, suppliers)
    counts["HAS_ALTERNATIVE (Supplier)"] = create_supplier_alternative_rels(session, suppliers)
    counts["HAS_ALTERNATIVE (Route)"] = create_route_alternative_rels(session, routes)
    counts["HAS_SUBSTITUTE"] = create_equipment_substitute_rels(session, equipment)

    # Also process relationships.json if present
    rels_data = data.get("relationships")
    if rels_data and isinstance(rels_data, dict):
        file_counts = create_relationships_from_file(session, rels_data)
        counts.update(file_counts)

    return counts


def print_summary(node_counts: Dict[str, int], rel_counts: Dict[str, int], elapsed: float) -> None:
    total_nodes = sum(node_counts.values())
    total_rels = sum(rel_counts.values())
    print("\n" + "=" * 60)
    print("  SEED COMPLETE")
    print("=" * 60)
    print(f"\n  Nodes created:         {total_nodes}")
    for label, cnt in node_counts.items():
        print(f"    {label:.<30} {cnt}")
    print(f"\n  Relationships created: {total_rels}")
    for rtype, cnt in rel_counts.items():
        print(f"    {rtype:.<30} {cnt}")
    print(f"\n  Time elapsed: {elapsed:.2f}s")
    print("=" * 60)


def run_seed() -> None:
    """Main entry point: connect, clear, seed, summarize."""
    print("=" * 60)
    print("  SCM Risk Intelligence - Neo4j Seed Script")
    print("=" * 60)
    print(f"\n  Neo4j URI:   {NEO4J_URI}")
    print(f"  Neo4j User:  {NEO4J_USER}")
    print(f"  Seed Dir:    {SEED_DIR}")

    # Load seed data
    print("\n--- Loading seed data ---")
    data = load_all_seed_files()
    if not data:
        print("[ERROR] No seed data found. Ensure JSON files exist in data/seed/")
        sys.exit(1)

    # Connect to Neo4j
    print(f"\n--- Connecting to Neo4j at {NEO4J_URI} ---")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        print("  Connected successfully.")
    except Exception as exc:
        print(f"[ERROR] Failed to connect to Neo4j: {exc}")
        sys.exit(1)

    start = time.time()

    with driver.session(database="neo4j") as session:
        clear_database(session)
        create_constraints(session)
        create_indexes(session)
        node_counts = seed_nodes(session, data)
        rel_counts = seed_relationships(session, data)

    elapsed = time.time() - start
    print_summary(node_counts, rel_counts, elapsed)

    driver.close()
    print("\nDone. Neo4j connection closed.")


if __name__ == "__main__":
    run_seed()
