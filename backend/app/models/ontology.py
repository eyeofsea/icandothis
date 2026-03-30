from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class OntologyNode(BaseModel):
    id: str
    label: str
    type: str
    properties: Dict[str, Any] = {}


class OntologyEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str
    properties: Dict[str, Any] = {}


class OntologyGraph(BaseModel):
    nodes: List[OntologyNode] = []
    edges: List[OntologyEdge] = []
    nodeCount: int = 0
    edgeCount: int = 0


class GraphPath(BaseModel):
    nodes: List[OntologyNode] = []
    edges: List[OntologyEdge] = []
    totalCost: Optional[float] = None
    totalDistance: Optional[float] = None
    hops: int = 0


class RelationshipType(BaseModel):
    name: str
    sourceType: str
    targetType: str
    properties: List[str] = []
    description: Optional[str] = None


class OntologySchema(BaseModel):
    nodeTypes: List[str] = []
    relationshipTypes: List[RelationshipType] = []
    totalNodes: int = 0
    totalRelationships: int = 0
