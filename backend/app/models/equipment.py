from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EquipmentCategory(str, Enum):
    ROTATING = "rotating"
    STATIC = "static"
    ELECTRICAL = "electrical"
    INSTRUMENTATION = "instrumentation"
    PIPING = "piping"
    STRUCTURAL = "structural"
    HVAC = "hvac"
    SAFETY = "safety"
    VALVES = "valves"

    @classmethod
    def _missing_(cls, value: object) -> "EquipmentCategory | None":
        if isinstance(value, str):
            lower = value.lower()
            for member in cls:
                if member.value == lower:
                    return member
        return None


class CriticalityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @classmethod
    def _missing_(cls, value: object) -> "CriticalityLevel | None":
        if isinstance(value, str):
            lower = value.lower()
            for member in cls:
                if member.value == lower:
                    return member
        return None


class Dimensions(BaseModel):
    length: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    unit: str = "m"


class EquipmentBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: EquipmentCategory
    criticality: CriticalityLevel
    weight: Optional[float] = None
    dimensions: Optional[Dimensions] = None
    hsCode: Optional[str] = None
    requiredOnSiteDate: Optional[date] = None
    installationSequencePriority: int = Field(default=0, ge=0)
    specifications: Dict[str, Any] = {}


class EquipmentCreate(EquipmentBase):
    pass


class Equipment(EquipmentBase):
    equipmentId: str

    model_config = {"from_attributes": True}


class EquipmentImpact(BaseModel):
    equipmentId: str
    equipmentName: str
    criticality: CriticalityLevel
    affectedByDisruptions: List[dict] = []
    alternativeSuppliers: List[dict] = []
    alternativeRoutes: List[dict] = []
    delayRiskDays: int = 0
    costImpact: float = 0.0
