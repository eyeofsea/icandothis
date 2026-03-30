from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ProjectType(str, Enum):
    OIL_GAS = "oil_gas"
    RENEWABLE = "renewable"
    PETROCHEMICAL = "petrochemical"
    MINING = "mining"
    INFRASTRUCTURE = "infrastructure"
    POWER = "power"
    WATER = "water"


class ProjectStatus(str, Enum):
    PLANNING = "planning"
    PROCUREMENT = "procurement"
    IN_TRANSIT = "in_transit"
    CONSTRUCTION = "construction"
    COMMISSIONING = "commissioning"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"


class Coordinates(BaseModel):
    lat: float
    lng: float


class ProjectBase(BaseModel):
    name: str
    client: str
    country: str
    region: str
    coordinates: Optional[Coordinates] = None
    type: ProjectType
    status: ProjectStatus
    totalValue: Optional[float] = None
    completionPct: float = Field(default=0.0, ge=0.0, le=100.0)
    criticalPathDeadline: Optional[date] = None
    riskTolerance: float = Field(default=0.5, ge=0.0, le=1.0)


class ProjectCreate(ProjectBase):
    pass


class Project(ProjectBase):
    projectId: str

    model_config = {"from_attributes": True}


class ProjectRiskSummary(BaseModel):
    projectId: str
    projectName: str
    overallRiskScore: float
    equipmentAtRisk: int
    disruptedRoutes: int
    supplierIssues: int
    estimatedCostImpact: float
    criticalItems: list[dict] = []
