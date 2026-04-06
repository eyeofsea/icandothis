"""
Sanctions screening feed — checks entities against OpenSanctions API.

Production: Uses OpenSanctions search API (free tier, no key required for basic search).
Optionally uses API key for higher rate limits.
Falls back to keyword-based simulation when API is unavailable.
"""
import logging
from typing import Any, Optional

from app.config import settings
from app.services.external_feeds.base import ExternalFeed

logger = logging.getLogger(__name__)

OPENSANCTIONS_SEARCH_URL = "https://api.opensanctions.org/search/default"

KNOWN_SANCTIONED_COUNTRIES = {"Russia", "Iran", "North Korea", "Syria", "Belarus", "Cuba", "Venezuela"}


class SanctionsFeed(ExternalFeed):
    """Sanctions screening provider using OpenSanctions API."""

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or settings.OPENSANCTIONS_API_KEY or None
        super().__init__(api_key=key, cache_ttl_minutes=1440)  # 24h cache

    async def screen_entity(self, name: str, country: str) -> dict[str, Any]:
        return await self.get(f"sanctions:{name}:{country}", name=name, country=country)

    async def fetch(self, name: str = "", country: str = "", **kwargs: Any) -> dict[str, Any]:
        if not name:
            return self._simulate_screening(name, country)

        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"ApiKey {self.api_key}"

            params: dict[str, Any] = {"q": name, "limit": 5}
            if country:
                params["countries"] = country[:2].upper()  # ISO 2-letter

            resp = await self._client.get(
                OPENSANCTIONS_SEARCH_URL,
                params=params,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

            results = data.get("results", [])

            if not results:
                return {
                    "name": name,
                    "country": country,
                    "sanctioned": False,
                    "lists_matched": [],
                    "confidence": 0.0,
                    "matches": [],
                    "source": "opensanctions",
                }

            # Analyze matches
            matches = []
            highest_score = 0.0
            lists_matched: set = set()

            for result in results:
                score = result.get("score", 0.0)
                if score > highest_score:
                    highest_score = score

                datasets = result.get("datasets", [])
                lists_matched.update(datasets)

                properties = result.get("properties", {})
                match_entry = {
                    "name": " ".join(properties.get("name", [result.get("caption", "")])),
                    "score": round(score, 3),
                    "schema": result.get("schema", ""),
                    "datasets": datasets,
                    "countries": properties.get("country", []),
                    "topics": result.get("topics", []),
                }
                matches.append(match_entry)

            # Consider sanctioned if score > 0.7
            is_sanctioned = highest_score > 0.7

            return {
                "name": name,
                "country": country,
                "sanctioned": is_sanctioned,
                "lists_matched": sorted(lists_matched),
                "confidence": round(min(highest_score, 1.0), 3),
                "matches": matches[:5],
                "total_matches": len(results),
                "source": "opensanctions",
            }

        except Exception as exc:
            logger.warning("OpenSanctions API failed for '%s': %s — using fallback", name, exc)
            return self._simulate_screening(name, country)

    async def screen_bulk(self, entities: list[dict[str, str]]) -> list[dict[str, Any]]:
        """Screen multiple entities."""
        results = []
        for entity in entities:
            result = await self.screen_entity(
                name=entity.get("name", ""),
                country=entity.get("country", ""),
            )
            results.append(result)
        return results

    def fallback(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "name": kwargs.get("name", ""),
            "sanctioned": False,
            "source": "fallback",
        }

    def _simulate_screening(self, name: str, country: str) -> dict[str, Any]:
        """Fallback: keyword-based simulation."""
        is_sanctioned = country in KNOWN_SANCTIONED_COUNTRIES
        return {
            "name": name,
            "country": country,
            "sanctioned": is_sanctioned,
            "lists_matched": ["OFAC-SDN", "EU-CONSOLIDATED"] if is_sanctioned else [],
            "confidence": 0.95 if is_sanctioned else 0.0,
            "source": "simulated",
        }


sanctions_feed = SanctionsFeed()
