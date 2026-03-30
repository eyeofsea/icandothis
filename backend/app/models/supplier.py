from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class SupplierTier(str, Enum):
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"
    TIER_3 = "tier_3"


class SupplierBase(BaseModel):
    name: str
    country: str
    region: Optional[str] = None
    tier: SupplierTier = SupplierTier.TIER_1
    capabilities: List[str] = []
    certifications: List[str] = []
    financialRating: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    deliveryRate: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    qualityRate: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    leadTimeDays: Optional[int] = None
    capacityUtilization: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    riskFlags: List[str] = []
    contactEmail: Optional[str] = None
    contactPhone: Optional[str] = None


class SupplierCreate(SupplierBase):
    pass


class Supplier(SupplierBase):
    supplierId: str

    model_config = {"from_attributes": True}


class SupplierPerformance(BaseModel):
    supplierId: str
    supplierName: str
    onTimeDeliveryRate: float
    qualityPassRate: float
    averageLeadTimeDays: float
    totalOrdersCompleted: int
    activeOrders: int
    recentIssues: List[dict] = []


class SupplierAlternative(BaseModel):
    supplierId: str
    supplierName: str
    country: str
    matchScore: float
    capabilities: List[str]
    leadTimeDays: Optional[int] = None
    financialRating: Optional[float] = None
