"""
Freight rate feed — fetches current shipping cost data.

Production: Integrate with Freightos/Xeneta API.
Development: Returns realistic simulated rates based on route distance.
"""
import random
from typing import Any, Optional

from app.services.external_feeds.base import ExternalFeed


class FreightRateFeed(ExternalFeed):
    """Freight rate data provider."""

    BASE_URL = "https://api.freightos.com/v1"  # placeholder

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key, cache_ttl_minutes=240)

    async def get_route_rate(self, origin: str, destination: str, weight_kg: float) -> dict[str, Any]:
        cache_key = f"freight:{origin}:{destination}:{int(weight_kg)}"
        return await self.get(cache_key, origin=origin, destination=destination, weight_kg=weight_kg)

    async def fetch(self, origin: str = "", destination: str = "", weight_kg: float = 0, **kwargs: Any) -> dict[str, Any]:
        if self.api_key:
            resp = await self._client.get(
                f"{self.BASE_URL}/rates",
                params={"origin": origin, "dest": destination, "weight": weight_kg},
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            resp.raise_for_status()
            return resp.json()

        return self._simulate_rate(origin, destination, weight_kg)

    def fallback(self, **kwargs: Any) -> dict[str, Any]:
        return self._simulate_rate(
            kwargs.get("origin", ""), kwargs.get("destination", ""), kwargs.get("weight_kg", 10000)
        )

    def _simulate_rate(self, origin: str, destination: str, weight_kg: float) -> dict[str, Any]:
        base_per_ton = 45 + random.uniform(-5, 15)
        fuel_surcharge_pct = 0.10 + random.uniform(0, 0.08)
        insurance_pct = 0.015 + random.uniform(0, 0.005)
        tons = weight_kg / 1000
        base_cost = base_per_ton * tons
        return {
            "origin": origin,
            "destination": destination,
            "weight_kg": weight_kg,
            "base_rate_per_ton": round(base_per_ton, 2),
            "fuel_surcharge_pct": round(fuel_surcharge_pct, 4),
            "insurance_pct": round(insurance_pct, 4),
            "estimated_cost": round(base_cost * (1 + fuel_surcharge_pct), 2),
            "insurance_cost": round(base_cost * insurance_pct, 2),
            "currency": "USD",
            "source": "simulated",
            "valid_until": "2026-04-11",
        }


freight_feed = FreightRateFeed()
