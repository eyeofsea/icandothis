from fastapi import APIRouter, HTTPException

from app.database.neo4j_client import get_neo4j
from app.models.ontology import GraphPath, OntologyGraph, OntologyNode, OntologyEdge

router = APIRouter(prefix="/api/ontology", tags=["ontology"])


@router.get("/graph", response_model=OntologyGraph)
async def get_full_graph(limit: int = 500):
    db = await get_neo4j()

    node_query = """
    MATCH (n)
    WHERE n:Project OR n:Equipment OR n:Supplier OR n:ShippingRoute
       OR n:DisruptionEvent OR n:GeopoliticalZone OR n:Port
    WITH n, labels(n)[0] AS nodeType
    RETURN {
        id: coalesce(n.projectId, n.equipmentId, n.supplierId, n.routeId,
                     n.eventId, n.zoneId, n.portId, elementId(n)),
        label: coalesce(n.name, n.description, 'Unknown'),
        type: nodeType,
        properties: properties(n)
    } AS node
    LIMIT $limit
    """
    node_records = await db.execute_read(node_query, {"limit": limit})
    nodes = [record["node"] for record in node_records]

    edge_query = """
    MATCH (a)-[r]->(b)
    WHERE (a:Project OR a:Equipment OR a:Supplier OR a:ShippingRoute
           OR a:DisruptionEvent OR a:GeopoliticalZone OR a:Port)
      AND (b:Project OR b:Equipment OR b:Supplier OR b:ShippingRoute
           OR b:DisruptionEvent OR b:GeopoliticalZone OR b:Port)
    WITH a, r, b
    RETURN {
        id: elementId(r),
        source: coalesce(a.projectId, a.equipmentId, a.supplierId, a.routeId,
                         a.eventId, a.zoneId, a.portId, elementId(a)),
        target: coalesce(b.projectId, b.equipmentId, b.supplierId, b.routeId,
                         b.eventId, b.zoneId, b.portId, elementId(b)),
        type: type(r),
        properties: properties(r)
    } AS edge
    LIMIT $limit
    """
    edge_records = await db.execute_read(edge_query, {"limit": limit})
    edges = [record["edge"] for record in edge_records]

    return OntologyGraph(
        nodes=nodes,
        edges=edges,
        nodeCount=len(nodes),
        edgeCount=len(edges),
    )


@router.get("/path/{source_id}/{target_id}", response_model=GraphPath)
async def get_shortest_path(source_id: str, target_id: str):
    db = await get_neo4j()
    query = """
    MATCH (start), (end)
    WHERE coalesce(start.projectId, start.equipmentId, start.supplierId,
                   start.routeId, start.eventId, start.zoneId, start.portId) = $sourceId
      AND coalesce(end.projectId, end.equipmentId, end.supplierId,
                   end.routeId, end.eventId, end.zoneId, end.portId) = $targetId
    WITH start, end
    LIMIT 1
    CALL apoc.algo.dijkstra(start, end, '', 'weight') YIELD path, weight
    WITH path, weight,
         nodes(path) AS pathNodes,
         relationships(path) AS pathRels
    RETURN {
        nodes: [n IN pathNodes | {
            id: coalesce(n.projectId, n.equipmentId, n.supplierId, n.routeId,
                         n.eventId, n.zoneId, n.portId, elementId(n)),
            label: coalesce(n.name, n.description, 'Unknown'),
            type: labels(n)[0],
            properties: properties(n)
        }],
        edges: [r IN pathRels | {
            id: elementId(r),
            source: coalesce(startNode(r).projectId, startNode(r).equipmentId,
                             startNode(r).supplierId, startNode(r).routeId,
                             startNode(r).eventId, startNode(r).zoneId,
                             startNode(r).portId, elementId(startNode(r))),
            target: coalesce(endNode(r).projectId, endNode(r).equipmentId,
                             endNode(r).supplierId, endNode(r).routeId,
                             endNode(r).eventId, endNode(r).zoneId,
                             endNode(r).portId, elementId(endNode(r))),
            type: type(r),
            properties: properties(r)
        }],
        totalCost: weight,
        hops: size(pathRels)
    } AS pathResult
    """
    records = await db.execute_read(query, {"sourceId": source_id, "targetId": target_id})

    if not records:
        fallback_query = """
        MATCH (start), (end)
        WHERE coalesce(start.projectId, start.equipmentId, start.supplierId,
                       start.routeId, start.eventId, start.zoneId, start.portId) = $sourceId
          AND coalesce(end.projectId, end.equipmentId, end.supplierId,
                       end.routeId, end.eventId, end.zoneId, end.portId) = $targetId
        WITH start, end
        LIMIT 1
        MATCH path = shortestPath((start)-[*..15]-(end))
        WITH path, nodes(path) AS pathNodes, relationships(path) AS pathRels
        RETURN {
            nodes: [n IN pathNodes | {
                id: coalesce(n.projectId, n.equipmentId, n.supplierId, n.routeId,
                             n.eventId, n.zoneId, n.portId, elementId(n)),
                label: coalesce(n.name, n.description, 'Unknown'),
                type: labels(n)[0],
                properties: properties(n)
            }],
            edges: [r IN pathRels | {
                id: elementId(r),
                source: coalesce(startNode(r).projectId, startNode(r).equipmentId,
                                 startNode(r).supplierId, startNode(r).routeId,
                                 startNode(r).eventId, startNode(r).zoneId,
                                 startNode(r).portId, elementId(startNode(r))),
                target: coalesce(endNode(r).projectId, endNode(r).equipmentId,
                                 endNode(r).supplierId, endNode(r).routeId,
                                 endNode(r).eventId, endNode(r).zoneId,
                                 endNode(r).portId, elementId(endNode(r))),
                type: type(r),
                properties: properties(r)
            }],
            totalCost: null,
            hops: size(pathRels)
        } AS pathResult
        """
        records = await db.execute_read(fallback_query, {"sourceId": source_id, "targetId": target_id})

    if not records:
        raise HTTPException(status_code=404, detail="No path found between the specified entities")

    result = records[0]["pathResult"]
    return GraphPath(
        nodes=result["nodes"],
        edges=result["edges"],
        totalCost=result.get("totalCost"),
        hops=result.get("hops", 0),
    )
