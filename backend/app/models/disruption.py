from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class DisruptionType(str, Enum):
    GEOPOLITICAL = "geopolitical"
    WEATHER = "weather"
    PORT_CLOSURE = "port_closure"
    SANCTIONS = "sanctions"
    LABOR_STRIKE = "labor_strike"
    PIRACY = "piracy"
    PANDEMIC = "pandemic"
    CANAL_BLOCKAGE = "canal_blockage"
    INFRASTRUCTURE_FAILURE = "infrastructure_failure"
    REGULATORY = "regulatory"


class VerificationStatus(str, Enum):
    UNVERIFIED = "unverified"
    CONFIRMED = "confirmed"
    MONITORING = "monitoring"
    RESOLVED = "resolved"


class ZoneType(str, Enum):
    MARITIME = "maritime"
    LAND = "land"
    PORT = "port"
    CANAL = "canal"
    STRAIT = "strait"
    AIRSPACE = "airspace"


class ZoneStatus(str, Enum):
    STABLE = "stable"
    ELEVATED_RISK = "elevated_risk"
    HIGH_RISK = "high_risk"
    ACTIVE_CONFLICT = "active_conflict"
    RESTRICTED = "restricted"
    CLOSED = "closed"


class GeopoliticalZoneBase(BaseModel):
    name: str
    type: ZoneType
    coordinates: List[dict] = []
    riskLevel: int = Field(default=1, ge=1, le=10)
    currentStatus: ZoneStatus = ZoneStatus.STABLE
    controllingEntity: Optional[str] = None
    description: Optional[str] = None


class GeopoliticalZone(GeopoliticalZoneBase):
    zoneId: str

    model_config = {"from_attributes": True}


class PortBase(BaseModel):
    name: str
    country: str
    lat: float
    lng: float
    unlocode: Optional[str] = None
    maxVesselDraft: Optional[float] = None
    berthCount: Optional[int] = None
    currentStatus: str = "operational"
    congestionLevel: Optional[float] = Field(default=None, ge=0.0, le=100.0)


class Port(PortBase):
    portId: str

    model_config = {"from_attributes": True}


class DisruptionEventBase(BaseModel):
    type: DisruptionType
    severity: int = Field(ge=1, le=5)
    startDate: date
    endDate: Optional[date] = None
    affectedZones: List[str] = []
    source: Optional[str] = None
    verificationStatus: VerificationStatus = VerificationStatus.UNVERIFIED
    description: str


class DisruptionEventCreate(DisruptionEventBase):
    pass


class DisruptionEvent(DisruptionEventBase):
    eventId: str
    createdAt: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DisruptionImpact(BaseModel):
    eventId: str
    description: str
    severity: int
    affectedProjects: List[dict] = []
    affectedEquipment: List[dict] = []
    affectedRoutes: List[dict] = []
    affectedSuppliers: List[dict] = []
    estimatedDelayDays: int = 0
    estimatedCostImpact: float = 0.0


class DisruptionSimulationRequest(BaseModel):
    type: DisruptionType
    severity: int = Field(ge=1, le=5)
    affectedZones: List[str] = []
    durationDays: int = 30
    description: str = ""


class DisruptionSimulationResult(BaseModel):
    scenario: dict
    impactedProjects: List[dict] = []
    impactedEquipment: List[dict] = []
    impactedRoutes: List[dict] = []
    impactedSuppliers: List[dict] = []
    totalEstimatedCost: float = 0.0
    totalDelayDays: int = 0
    riskScore: float = 0.0
    recommendations: List[str] = []
