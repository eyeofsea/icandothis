"""News Monitor Agent for the SCM Risk Intelligence Platform (Simulated).

Provides pre-built event templates for common supply chain disruption scenarios.
Designed to be replaced with real news API integration in production.
"""

from __future__ import annotations

import logging
import random
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Pre-built event templates for the 5 primary scenarios
EVENT_TEMPLATES: List[Dict[str, Any]] = [
    {
        "id": "NEWS-REDSEAHOUTHI",
        "headline": "Houthi Rebels Intensify Attacks on Commercial Vessels in Red Sea",
        "source": "Reuters Maritime",
        "type": "geopolitical",
        "severity": 4,
        "location": "Red Sea / Bab el-Mandeb Strait",
        "affectedZones": ["ZONE-REDSEA", "ZONE-BABEL"],
        "description": (
            "Houthi rebel forces have escalated attacks on commercial shipping in the "
            "Red Sea and Bab el-Mandeb strait, forcing major shipping lines to reroute "
            "via the Cape of Good Hope. Insurance premiums for Red Sea transit have surged "
            "300%. Multiple container vessels and tankers targeted."
        ),
        "tags": ["maritime", "conflict", "shipping", "insurance", "rerouting"],
        "estimatedDuration": 90,
    },
    {
        "id": "NEWS-SUEZBLOCK",
        "headline": "Suez Canal Blocked by Grounded Container Vessel",
        "source": "Lloyd's List",
        "type": "canal_blockage",
        "severity": 5,
        "location": "Suez Canal, Egypt",
        "affectedZones": ["ZONE-SUEZ", "ZONE-MEDEAST"],
        "description": (
            "A mega container vessel has run aground in the Suez Canal, blocking all "
            "traffic in both directions. Over 400 vessels are queued at both ends. "
            "Salvage operations estimated to take 5-7 days. Global supply chains are "
            "being rerouted via Cape of Good Hope adding 12-14 days to voyages."
        ),
        "tags": ["canal", "blockage", "shipping", "global-trade"],
        "estimatedDuration": 14,
    },
    {
        "id": "NEWS-CHINASANCTIONS",
        "headline": "New Export Controls Imposed on Critical Industrial Components from China",
        "source": "Financial Times",
        "type": "sanctions",
        "severity": 3,
        "location": "China",
        "affectedZones": ["ZONE-CHINA", "ZONE-SCSEA"],
        "description": (
            "New regulatory controls restrict export of specialized industrial valves, "
            "compressors, and control systems from China. Affects tier-1 suppliers of "
            "rotating and instrumentation equipment. Companies must obtain new export "
            "licenses which may take 60-90 days."
        ),
        "tags": ["sanctions", "regulatory", "china", "export-controls"],
        "estimatedDuration": 120,
    },
    {
        "id": "NEWS-TYPHOONPACIFIC",
        "headline": "Super Typhoon Disrupts Major Pacific Shipping Lanes and Ports",
        "source": "NOAA / Reuters",
        "type": "weather",
        "severity": 4,
        "location": "Western Pacific / South China Sea",
        "affectedZones": ["ZONE-SCSEA", "ZONE-PACIFIC"],
        "description": (
            "Category 5 typhoon tracking across major Pacific shipping lanes has forced "
            "closure of several ports in Southeast Asia. Estimated 2-3 weeks of disruption. "
            "Container terminals in Singapore and Malaysia operating at reduced capacity. "
            "Vessel schedules delayed by 10-21 days."
        ),
        "tags": ["weather", "typhoon", "port-closure", "asia"],
        "estimatedDuration": 21,
    },
    {
        "id": "NEWS-PORTSTRIKE",
        "headline": "Major Port Workers Strike Shuts Down European Container Terminals",
        "source": "BBC News",
        "type": "labor_strike",
        "severity": 3,
        "location": "Rotterdam, Hamburg, Antwerp",
        "affectedZones": ["ZONE-EUROPE", "ZONE-NORTH_SEA"],
        "description": (
            "Port workers across major European container terminals have launched an "
            "indefinite strike over working conditions and automation concerns. "
            "Rotterdam, Hamburg, and Antwerp terminals are operating at 20% capacity. "
            "Equipment deliveries from European suppliers expected to face 2-4 week delays."
        ),
        "tags": ["strike", "labor", "port", "europe"],
        "estimatedDuration": 28,
    },
]


class NewsAgent:
    """Monitors news sources for supply chain disruption events (simulated)."""

    def __init__(self) -> None:
        self.name = "NewsAgent"
        self._templates = EVENT_TEMPLATES

    async def run(
        self,
        scenario_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run the news monitoring agent.

        Args:
            scenario_id: Specific scenario template ID to simulate, or None for random.

        Returns:
            Detected event candidate with classification.
        """
        logger.info("NewsAgent.run: simulating news detection")

        # Detect event
        event_candidate = await self.simulate_news_detection(scenario_id)

        # Classify it
        classification = self.classify_event(event_candidate)

        # Geocode to zones
        zone_matches = self.geocode_to_zones(event_candidate)

        return {
            "eventCandidate": event_candidate,
            "classification": classification,
            "matchedZones": zone_matches,
            "confidence": classification.get("confidence", 0.8),
            "requiresVerification": classification.get("severity", 0) >= 4,
            "summary": (
                f"Detected: {event_candidate.get('headline', 'Unknown event')}. "
                f"Type: {classification.get('type', 'unknown')}, "
                f"Severity: {classification.get('severity', 0)}/5. "
                f"Matched {len(zone_matches)} zone(s)."
            ),
        }

    async def simulate_news_detection(
        self, scenario_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Simulate detection of a news event.
        Returns a structured event candidate.
        """
        if scenario_id:
            template = next(
                (t for t in self._templates if t["id"] == scenario_id),
                None,
            )
            if not template:
                template = self._templates[0]
        else:
            template = random.choice(self._templates)

        today = date.today()
        return {
            "id": template["id"],
            "headline": template["headline"],
            "source": template["source"],
            "publishedDate": today.isoformat(),
            "location": template["location"],
            "description": template["description"],
            "tags": template["tags"],
            "rawType": template["type"],
            "rawSeverity": template["severity"],
            "affectedZones": template["affectedZones"],
            "estimatedDurationDays": template.get("estimatedDuration", 30),
            "estimatedEndDate": (today + timedelta(days=template.get("estimatedDuration", 30))).isoformat(),
        }

    def classify_event(self, event_candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify event type and severity based on content analysis.
        In production, this would use NLP/LLM classification.
        """
        event_type = event_candidate.get("rawType", "unknown")
        raw_severity = event_candidate.get("rawSeverity", 3)
        description = (event_candidate.get("description") or "").lower()
        tags = event_candidate.get("tags", [])

        # Rule-based severity adjustment
        severity = raw_severity

        # Escalate severity for certain keywords
        escalation_keywords = ["blocked", "closed", "category 5", "indefinite", "all traffic"]
        if any(kw in description for kw in escalation_keywords):
            severity = min(5, severity + 1)

        # Reduce severity for minor/temporary events
        deescalation_keywords = ["minor", "temporary", "localized", "partial"]
        if any(kw in description for kw in deescalation_keywords):
            severity = max(1, severity - 1)

        # Confidence based on source quality and detail level
        high_confidence_sources = ["reuters", "lloyd's", "financial times", "bbc", "noaa"]
        source = (event_candidate.get("source") or "").lower()
        confidence = 0.9 if any(s in source for s in high_confidence_sources) else 0.6

        # Impact scope
        scope_keywords = {
            "global": ["global", "worldwide", "international"],
            "regional": ["regional", "multiple countries", "several ports"],
            "local": ["local", "single port", "localized"],
        }
        scope = "regional"
        for scope_level, keywords in scope_keywords.items():
            if any(kw in description for kw in keywords):
                scope = scope_level
                break

        return {
            "type": event_type,
            "severity": severity,
            "confidence": confidence,
            "scope": scope,
            "impactCategories": self._determine_impact_categories(tags, description),
            "urgency": "immediate" if severity >= 4 else "high" if severity >= 3 else "standard",
        }

    def geocode_to_zones(self, event_candidate: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Match event location to GeopoliticalZones in the knowledge graph.
        In production, this would do actual geocoding + spatial matching.
        """
        affected_zones = event_candidate.get("affectedZones", [])
        location = event_candidate.get("location", "")

        # Map location strings to zone data
        location_zone_map: Dict[str, Dict[str, Any]] = {
            "red sea": {"zoneId": "ZONE-REDSEA", "name": "Red Sea", "type": "maritime"},
            "bab el-mandeb": {"zoneId": "ZONE-BABEL", "name": "Bab el-Mandeb Strait", "type": "strait"},
            "suez": {"zoneId": "ZONE-SUEZ", "name": "Suez Canal", "type": "canal"},
            "china": {"zoneId": "ZONE-CHINA", "name": "China Coastal", "type": "maritime"},
            "south china sea": {"zoneId": "ZONE-SCSEA", "name": "South China Sea", "type": "maritime"},
            "pacific": {"zoneId": "ZONE-PACIFIC", "name": "Western Pacific", "type": "maritime"},
            "rotterdam": {"zoneId": "ZONE-EUROPE", "name": "Northern Europe", "type": "port"},
            "hamburg": {"zoneId": "ZONE-EUROPE", "name": "Northern Europe", "type": "port"},
            "antwerp": {"zoneId": "ZONE-EUROPE", "name": "Northern Europe", "type": "port"},
            "mediterranean": {"zoneId": "ZONE-MEDEAST", "name": "Eastern Mediterranean", "type": "maritime"},
        }

        matched_zones: List[Dict[str, Any]] = []
        seen_zone_ids: set = set()

        # Match from predefined zone IDs
        for zone_id in affected_zones:
            if zone_id not in seen_zone_ids:
                seen_zone_ids.add(zone_id)
                matched_zones.append({
                    "zoneId": zone_id,
                    "matchedBy": "predefined",
                    "confidence": 0.95,
                })

        # Match from location string
        location_lower = location.lower()
        for keyword, zone_data in location_zone_map.items():
            if keyword in location_lower and zone_data["zoneId"] not in seen_zone_ids:
                seen_zone_ids.add(zone_data["zoneId"])
                matched_zones.append({
                    **zone_data,
                    "matchedBy": "geocoding",
                    "confidence": 0.80,
                })

        return matched_zones

    def _determine_impact_categories(
        self, tags: List[str], description: str
    ) -> List[str]:
        """Determine which supply chain categories are impacted."""
        categories = []
        tag_set = set(t.lower() for t in tags)
        desc = description.lower()

        if any(kw in tag_set or kw in desc for kw in ["shipping", "maritime", "vessel", "port"]):
            categories.append("maritime_logistics")
        if any(kw in tag_set or kw in desc for kw in ["supplier", "manufacturer", "factory"]):
            categories.append("supplier_operations")
        if any(kw in tag_set or kw in desc for kw in ["insurance", "premium"]):
            categories.append("insurance_costs")
        if any(kw in tag_set or kw in desc for kw in ["sanctions", "regulatory", "export"]):
            categories.append("regulatory_compliance")
        if any(kw in tag_set or kw in desc for kw in ["labor", "strike", "workforce"]):
            categories.append("labor_relations")
        if any(kw in tag_set or kw in desc for kw in ["weather", "typhoon", "storm", "flood"]):
            categories.append("weather_climate")

        return categories or ["general"]


def get_available_scenarios() -> List[Dict[str, str]]:
    """Return list of available simulation scenarios."""
    return [
        {
            "id": t["id"],
            "headline": t["headline"],
            "type": t["type"],
            "severity": t["severity"],
            "location": t["location"],
        }
        for t in EVENT_TEMPLATES
    ]
