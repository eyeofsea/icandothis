from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class RouteStatus(str, Enum):
    ACTIVE = "active"
    DISRUPTED = "disrupted"
    BLOCKED = "blocked"
    DELAYED = "delayed"
    PLANNED = "planned"


class Waypoint(BaseModel):
    name: str
    lat: float
    lng: float
    type: str = "port"
    estimatedArrival: Optional[str] = None


class CarrierOption(BaseModel):
    carrierName: str
    vesselType: Optional[str] = None
    transitDays: Optional[int] = None
    cost: Optional[float] = None
    reliability: Optional[float] = None


class ShippingRouteBase(BaseModel):
    name: str
    waypoints: List[Waypoint] = []
    totalDistanceNm: Optional[float] = None
    estimatedTransitDays: Optional[int] = None
    shippingCost: Optional[float] = None
    insuranceCost: Optional[float] = None
    carrierOptions: List[CarrierOption] = []
    currentStatus: RouteStatus = RouteStatus.PLANNED


class ShippingRouteCreate(ShippingRouteBase):
    pass


class ShippingRoute(ShippingRouteBase):
    routeId: str

    model_config = {"from_attributes": True}


class RouteAlternative(BaseModel):
    routeId: str
    routeName: str
    totalDistanceNm: float
    estimatedTransitDays: int
    shippingCost: float
    additionalCost: float
    additionalDays: int
    riskScore: float
