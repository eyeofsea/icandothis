"""
Geopolitical risk feed — fetches zone risk levels from GDELT GEO API.

Production: Uses GDELT GEO API v2 (free, no API key required) to get
real-time geopolitical event density and tone for each zone.
Falls back to profile-based simulation when API is unavailable.
"""
import logging
import random
from datetime import datetime
from typing import Any, Optional

from app.services.external_feeds.base import ExternalFeed

logger = logging.getLogger(__name__)

GDELT_GEO_URL = "https://api.gdeltproject.org/api/v2/geo/geo"

# Zone profiles with GDELT search queries
ZONE_RISK_PROFILES: dict[str, dict[str, Any]] = {
    "ZONE-001": {
        "base_risk": 8,
        "name": "Strait of Hormuz",
        "gdelt_query": "hormuz OR iran strait shipping",
    },
    "ZONE-002": {
        "base_risk": 5,
        "name": "Suez Canal",
        "gdelt_query": "suez canal shipping disruption",
    },
    "ZONE-003": {
        "base_risk": 3,
        "name": "East China Sea / Japan",
        "gdelt_query": "east china sea japan maritime tension",
    },
    "ZONE-004": {
        "base_risk": 6,
        "name": "South China Sea",
        "gdelt_query": "south china sea taiwan military",
    },
    "ZONE-005": {
        "base_risk": 7,
        "name": "Black Sea / Russia",
        "gdelt_query": "black sea russia ukraine shipping",
    },
}


class GeopoliticalRiskFeed(ExternalFeed):
    """Geopolitical risk data provider using GDELT GEO API."""

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
        profile = ZONE_RISK_PROFILES.get(zone_id, {"base_risk": 5, "name": "Unknown", "gdelt_query": ""})
        gdelt_query = profile.get("gdelt_query", "")

        if not gdelt_query:
            return self._simulate_risk(zone_id)

        try:
            # GDELT GEO API — returns geojson with event counts and tone
            resp = await self._client.get(
                GDELT_GEO_URL,
                params={
                    "query": gdelt_query,
                    "format": "geojson",
                    "timespan": "14d",
                    "maxpoints": "50",
                },
            )
            resp.raise_for_status()
            data = resp.json()

            features = data.get("features", [])
            if not features:
                logger.info("GDELT GEO returned no features for %s, using profile-based risk", zone_id)
                return self._compute_risk_from_profile(zone_id, profile, event_count=0, avg_tone=0.0)

            # Aggregate: count events and average tone
            event_count = len(features)
            tones = []
            for f in features:
                props = f.get("properties", {})
                # GDELT tone: negative = bad, positive = good
                tone = props.get("urltone", 0.0)
                if isinstance(tone, (int, float)):
                    tones.append(tone)

            avg_tone = sum(tones) / len(tones) if tones else 0.0

            return self._compute_risk_from_gdelt(zone_id, profile, event_count, avg_tone, features[:5])

        except Exception as exc:
            logger.warning("GDELT GEO API failed for zone %s: %s — using simulation", zone_id, exc)
            return self._simulate_risk(zone_id)

    def fallback(self, **kwargs: Any) -> dict[str, Any]:
        return self._simulate_risk(kwargs.get("zone_id", "ZONE-001"))

    def _compute_risk_from_gdelt(
        self,
        zone_id: str,
        profile: dict[str, Any],
        event_count: int,
        avg_tone: float,
        sample_features: list,
    ) -> dict[str, Any]:
        """Compute risk level from real GDELT data."""
        base_risk = profile["base_risk"]

        # Event density factor: more events = higher risk
        # Normalize: 0-5 events = low, 5-20 = medium, 20+ = high
        if event_count > 20:
            density_adjustment = 2.0
        elif event_count > 10:
            density_adjustment = 1.0
        elif event_count > 5:
            density_adjustment = 0.5
        else:
            density_adjustment = -0.5

        # Tone factor: negative tone = higher risk
        # GDELT tone ranges roughly from -10 to +10
        tone_adjustment = 0.0
        if avg_tone < -5:
            tone_adjustment = 2.0
        elif avg_tone < -2:
            tone_adjustment = 1.0
        elif avg_tone < 0:
            tone_adjustment = 0.5
        elif avg_tone > 2:
            tone_adjustment = -0.5

        risk_level = max(1.0, min(10.0, base_risk + density_adjustment + tone_adjustment))

        # Determine trend from tone
        if avg_tone < -3:
            trend = "increasing"
        elif avg_tone > 1:
            trend = "decreasing"
        else:
            trend = "stable"

        # Count active threats (events with strongly negative tone)
        active_threats = sum(
            1 for f in sample_features
            if f.get("properties", {}).get("urltone", 0) < -3
        )

        return {
            "zone_id": zone_id,
            "zone_name": profile["name"],
            "risk_level": round(risk_level, 1),
            "trend": trend,
            "active_threats": active_threats,
            "insurance_multiplier": round(1.0 + (risk_level / 10) * 2, 2),
            "updated_at": datetime.utcnow().isoformat(),
            "source": "gdelt",
            "gdelt_meta": {
                "event_count_14d": event_count,
                "avg_tone": round(avg_tone, 2),
                "query": profile.get("gdelt_query", ""),
            },
        }

    def _compute_risk_from_profile(
        self,
        zone_id: str,
        profile: dict[str, Any],
        event_count: int,
        avg_tone: float,
    ) -> dict[str, Any]:
        """Compute risk using profile defaults when GDELT returns no events."""
        base_risk = profile["base_risk"]
        # No events = slightly lower risk than baseline
        risk_level = max(1.0, base_risk - 0.5)

        return {
            "zone_id": zone_id,
            "zone_name": profile["name"],
            "risk_level": round(risk_level, 1),
            "trend": "stable",
            "active_threats": 0,
            "insurance_multiplier": round(1.0 + (risk_level / 10) * 2, 2),
            "updated_at": datetime.utcnow().isoformat(),
            "source": "gdelt",
            "gdelt_meta": {
                "event_count_14d": 0,
                "avg_tone": 0.0,
                "query": profile.get("gdelt_query", ""),
            },
        }

    def _simulate_risk(self, zone_id: str) -> dict[str, Any]:
        """Fallback: simulated risk data."""
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
