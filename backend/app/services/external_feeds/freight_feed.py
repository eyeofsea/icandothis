"""
Freight rate feed — fetches current shipping cost data.

Production with API key: Integrates with Freightos/Xeneta API.
Without API key: Uses real fuel price data from EIA API (free) to
compute realistic freight rates adjusted by current bunker fuel costs.
Falls back to profile-based simulation when all APIs are unavailable.
"""
import logging
import random
from datetime import date
from typing import Any, Optional

from app.config import settings
from app.services.external_feeds.base import ExternalFeed

logger = logging.getLogger(__name__)

# EIA (US Energy Information Administration) — free, no key required for some endpoints
EIA_PETROLEUM_URL = "https://api.eia.gov/v2/petroleum/pri/spt/data/"

# Route distance profiles (nautical miles) for rate calculation
ROUTE_PROFILES: dict[str, dict[str, Any]] = {
    # (origin_keyword, destination_keyword) → distance and risk premium
    "default": {"distance_nm": 5000, "risk_premium": 1.0},
    "asia_europe": {"distance_nm": 11000, "risk_premium": 1.15},
    "asia_middleeast": {"distance_nm": 4500, "risk_premium": 1.25},
    "europe_middleeast": {"distance_nm": 6000, "risk_premium": 1.20},
    "asia_americas": {"distance_nm": 12000, "risk_premium": 1.10},
    "europe_americas": {"distance_nm": 4500, "risk_premium": 1.05},
}

# Keywords for route matching
REGION_KEYWORDS: dict[str, list[str]] = {
    "asia": ["china", "japan", "korea", "singapore", "malaysia", "taiwan", "vietnam", "india", "mumbai", "shanghai", "busan", "yokohama"],
    "europe": ["rotterdam", "hamburg", "antwerp", "felixstowe", "piraeus", "uk", "germany", "netherlands", "france", "italy", "genoa"],
    "middleeast": ["dubai", "jebel", "ras al", "qatar", "saudi", "bahrain", "oman", "iran", "hormuz", "persian"],
    "americas": ["houston", "new york", "los angeles", "long beach", "santos", "usa", "brazil", "mexico"],
}


class FreightRateFeed(ExternalFeed):
    """Freight rate data provider with real fuel-price adjustment."""

    FREIGHTOS_URL = "https://api.freightos.com/v1"  # for premium API key users

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or settings.FREIGHT_API_KEY or None
        super().__init__(api_key=key, cache_ttl_minutes=240)
        self._fuel_price: Optional[float] = None  # cached bunker fuel price

    async def get_route_rate(self, origin: str, destination: str, weight_kg: float) -> dict[str, Any]:
        cache_key = f"freight:{origin}:{destination}:{int(weight_kg)}"
        return await self.get(cache_key, origin=origin, destination=destination, weight_kg=weight_kg)

    async def fetch(self, origin: str = "", destination: str = "", weight_kg: float = 0, **kwargs: Any) -> dict[str, Any]:
        # If premium Freightos API key is available, use it
        if self.api_key:
            try:
                resp = await self._client.get(
                    f"{self.FREIGHTOS_URL}/rates",
                    params={"origin": origin, "dest": destination, "weight": weight_kg},
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                resp.raise_for_status()
                data = resp.json()
                data["source"] = "freightos"
                return data
            except Exception as exc:
                logger.warning("Freightos API failed: %s — using fuel-adjusted calculation", exc)

        # Compute rate using real fuel prices + route profiles
        return await self._compute_fuel_adjusted_rate(origin, destination, weight_kg)

    def fallback(self, **kwargs: Any) -> dict[str, Any]:
        return self._compute_static_rate(
            kwargs.get("origin", ""), kwargs.get("destination", ""), kwargs.get("weight_kg", 10000)
        )

    async def _compute_fuel_adjusted_rate(
        self, origin: str, destination: str, weight_kg: float
    ) -> dict[str, Any]:
        """Compute freight rate adjusted by real fuel prices from EIA."""
        fuel_price = await self._get_fuel_price()
        route = self._match_route(origin, destination)

        distance_nm = route["distance_nm"]
        risk_premium = route["risk_premium"]

        # Base rate model:
        # - Base transport cost per ton per 1000nm
        # - Fuel surcharge based on real bunker fuel price
        # - Risk premium based on route geopolitics
        tons = weight_kg / 1000
        base_rate_per_ton_per_1000nm = 8.0  # industry baseline USD

        base_cost = base_rate_per_ton_per_1000nm * tons * (distance_nm / 1000)

        # Fuel surcharge: bunker fuel price relative to baseline ($400/ton baseline)
        fuel_baseline = 400.0
        if fuel_price and fuel_price > 0:
            fuel_ratio = fuel_price / fuel_baseline
            fuel_surcharge_pct = max(0.0, (fuel_ratio - 1.0) * 0.5 + 0.10)
            fuel_source = "eia"
        else:
            fuel_surcharge_pct = 0.12
            fuel_source = "estimated"

        # Insurance: base 1.5% + risk premium
        insurance_pct = 0.015 * risk_premium

        estimated_cost = base_cost * (1 + fuel_surcharge_pct) * risk_premium
        insurance_cost = base_cost * insurance_pct

        return {
            "origin": origin,
            "destination": destination,
            "weight_kg": weight_kg,
            "distance_nm": distance_nm,
            "base_rate_per_ton": round(base_rate_per_ton_per_1000nm * (distance_nm / 1000), 2),
            "fuel_surcharge_pct": round(fuel_surcharge_pct, 4),
            "fuel_price_per_ton": round(fuel_price, 2) if fuel_price else None,
            "insurance_pct": round(insurance_pct, 4),
            "risk_premium": risk_premium,
            "estimated_cost": round(estimated_cost, 2),
            "insurance_cost": round(insurance_cost, 2),
            "total_cost": round(estimated_cost + insurance_cost, 2),
            "currency": "USD",
            "source": f"computed (fuel: {fuel_source})",
            "valid_until": (date.today()).isoformat(),
            "route_matched": route.get("name", "default"),
        }

    async def _get_fuel_price(self) -> float:
        """Fetch current bunker fuel / crude oil price from EIA API."""
        if self._fuel_price is not None:
            return self._fuel_price

        try:
            # EIA API v2 — WTI crude oil spot price (proxy for bunker fuel)
            resp = await self._client.get(
                EIA_PETROLEUM_URL,
                params={
                    "frequency": "daily",
                    "data[0]": "value",
                    "facets[product][]": "EPCBRENT",  # Brent crude
                    "sort[0][column]": "period",
                    "sort[0][direction]": "desc",
                    "length": "1",
                    "api_key": "DEMO_KEY",  # EIA provides a demo key
                },
            )
            resp.raise_for_status()
            data = resp.json()

            records = data.get("response", {}).get("data", [])
            if records:
                crude_price = float(records[0].get("value", 80))
                # Convert crude oil $/barrel to bunker fuel $/ton (rough multiplier)
                # ~7.33 barrels per ton, bunker ≈ 60-70% of crude price
                self._fuel_price = crude_price * 7.33 * 0.65
                logger.info("EIA fuel price fetched: crude=$%.2f/bbl → bunker=$%.2f/ton",
                            crude_price, self._fuel_price)
                return self._fuel_price

        except Exception as exc:
            logger.warning("EIA API failed: %s — using estimated fuel price", exc)

        # Fallback fuel price estimate
        self._fuel_price = 450.0  # reasonable current estimate
        return self._fuel_price

    def _match_route(self, origin: str, destination: str) -> dict[str, Any]:
        """Match origin/destination to a route profile."""
        origin_lower = origin.lower()
        dest_lower = destination.lower()

        origin_region = self._detect_region(origin_lower)
        dest_region = self._detect_region(dest_lower)

        if origin_region and dest_region and origin_region != dest_region:
            route_key = f"{origin_region}_{dest_region}"
            if route_key in ROUTE_PROFILES:
                profile = ROUTE_PROFILES[route_key].copy()
                profile["name"] = route_key
                return profile
            # Try reverse
            route_key_rev = f"{dest_region}_{origin_region}"
            if route_key_rev in ROUTE_PROFILES:
                profile = ROUTE_PROFILES[route_key_rev].copy()
                profile["name"] = route_key_rev
                return profile

        default = ROUTE_PROFILES["default"].copy()
        default["name"] = "default"
        return default

    def _detect_region(self, text: str) -> Optional[str]:
        """Detect which region a port/location belongs to."""
        for region, keywords in REGION_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return region
        return None

    def _compute_static_rate(self, origin: str, destination: str, weight_kg: float) -> dict[str, Any]:
        """Static fallback rate when no API is available."""
        base_per_ton = 45 + random.uniform(-5, 15)
        fuel_surcharge_pct = 0.12
        insurance_pct = 0.018
        tons = weight_kg / 1000
        base_cost = base_per_ton * tons
        return {
            "origin": origin,
            "destination": destination,
            "weight_kg": weight_kg,
            "base_rate_per_ton": round(base_per_ton, 2),
            "fuel_surcharge_pct": fuel_surcharge_pct,
            "insurance_pct": insurance_pct,
            "estimated_cost": round(base_cost * (1 + fuel_surcharge_pct), 2),
            "insurance_cost": round(base_cost * insurance_pct, 2),
            "currency": "USD",
            "source": "fallback",
            "valid_until": date.today().isoformat(),
        }


freight_feed = FreightRateFeed()
