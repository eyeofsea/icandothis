"""
Sanctions screening feed — checks entities against sanctions lists.

Production: Integrate with OpenSanctions API or OFAC SDN list.
Development: Returns simulated screening results.
"""
from typing import Any, Optional

from app.services.external_feeds.base import ExternalFeed

KNOWN_SANCTIONED = {"Russia", "Iran", "North Korea", "Syria", "Belarus"}


class SanctionsFeed(ExternalFeed):
    """Sanctions screening provider."""

    OPENSANCTIONS_URL = "https://api.opensanctions.org/v1"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key, cache_ttl_minutes=1440)  # 24h cache

    async def screen_entity(self, name: str, country: str) -> dict[str, Any]:
        return await self.get(f"sanctions:{name}:{country}", name=name, country=country)

    async def fetch(self, name: str = "", country: str = "", **kwargs: Any) -> dict[str, Any]:
        if self.api_key:
            resp = await self._client.get(
                f"{self.OPENSANCTIONS_URL}/match",
                params={"name": name, "country": country},
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            resp.raise_for_status()
            return resp.json()

        return self._simulate_screening(name, country)

    def fallback(self, **kwargs: Any) -> dict[str, Any]:
        return {"name": kwargs.get("name", ""), "sanctioned": False, "source": "fallback"}

    def _simulate_screening(self, name: str, country: str) -> dict[str, Any]:
        is_sanctioned = country in KNOWN_SANCTIONED
        return {
            "name": name,
            "country": country,
            "sanctioned": is_sanctioned,
            "lists_matched": ["OFAC-SDN", "EU-CONSOLIDATED"] if is_sanctioned else [],
            "confidence": 0.95 if is_sanctioned else 0.0,
            "source": "simulated",
        }


sanctions_feed = SanctionsFeed()
