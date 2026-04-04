"""
Geopolitical risk feed — fetches zone risk levels and active threats.

Production: Integrate with GDELT, ACLED, or ReliefWeb API.
Development: Returns simulated risk data updated daily.
"""
import random
from datetime import datetime
from typing import Any, Optional

from app.services.external_feeds.base import ExternalFeed

ZONE_RISK_PROFILES: dict[str, dict[str, Any]] = {
    "ZONE-001": {"base_risk": 8, "name": "Strait of Hormuz"},
    "ZONE-002": {"base_risk": 5, "name": "Suez Canal"},
    "ZONE-003": {"base_risk": 3, "name": "East China Sea / Japan"},
    "ZONE-004": {"base_risk": 6, "name": "South China Sea"},
    "ZONE-005": {"base_risk": 7, "name": "Black Sea / Russia"},
}


class GeopoliticalRiskFeed(ExternalFeed):
    """Geopolitical risk data provider."""

    GDELT_URL = "https://api.gdeltproject.org/api/v2"  # placeholder

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key, cache_ttl_minutes=360)

    async def get_zone_risk(self, zone_id: str) -> dict[str, Any]:
        return await self.get(f"risk:{zone_id}", zone_id=zone_id)

    async def get_all_zone_risks(self) -> list[dict[str, Any]]:
        results = []
        for zone_id in ZONE_RISK_PROFILES:
            results.append(await self.get_zone_risk(zone_id))
        return results

    async def fetch(self, zone_id: str = "", **kwargs: Any) -> dict[str, Any]:
        if self.api_key:
            resp = await self._client.get(
                f"{self.GDELT_URL}/context",
                params={"zone": zone_id},
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            resp.raise_for_status()
            return resp.json()

        return self._simulate_risk(zone_id)

    def fallback(self, **kwargs: Any) -> dict[str, Any]:
        return self._simulate_risk(kwargs.get("zone_id", "ZONE-001"))

    def _simulate_risk(self, zone_id: str) -> dict[str, Any]:
        profile = ZONE_RISK_PROFILES.get(zone_id, {"base_risk": 5, "name": "Unknown"})
        noise = random.uniform(-1, 1)
        risk_level = max(1, min(10, profile["base_risk"] + noise))
        return {
            "zone_id": zone_id,
            "zone_name": profile["name"],
            "risk_level": round(risk_level, 1),
            "trend": random.choice(["stable", "increasing", "decreasing"]),
            "active_threats": random.randint(0, 3),
            "insurance_multiplier": round(1.0 + (risk_level / 10) * 2, 2),
            "updated_at": datetime.utcnow().isoformat(),
            "source": "simulated",
        }


risk_feed = GeopoliticalRiskFeed()
