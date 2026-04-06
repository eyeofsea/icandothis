"""News Monitor Agent for the SCM Risk Intelligence Platform.

Uses GDELT DOC API for real-time global news monitoring.
Falls back to pre-built event templates when API is unavailable.
"""

from __future__ import annotations

import logging
import random
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

GDELT_DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

# Supply-chain disruption search queries per category
SCM_QUERIES = [
    "supply chain disruption shipping",
    "port closure maritime trade",
    "sanctions export controls trade",
    "canal blockage shipping route",
    "geopolitical conflict shipping",
    "typhoon hurricane port closure",
    "labor strike port terminal",
]

# Pre-built event templates (fallback when GDELT is unavailable)
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

# Keyword → type classification
TYPE_KEYWORDS: Dict[str, List[str]] = {
    "geopolitical": ["conflict", "war", "military", "attack", "rebel", "houthi", "missile"],
    "sanctions": ["sanction", "tariff", "export control", "ban", "embargo", "regulatory"],
    "canal_blockage": ["canal", "blocked", "grounded", "suez", "panama"],
    "weather": ["typhoon", "hurricane", "storm", "earthquake", "flood", "tsunami"],
    "labor_strike": ["strike", "labor", "union", "workers", "walkout"],
    "port_closure": ["port closure", "port shut", "terminal closed"],
}

# Location → zone mapping
LOCATION_ZONE_MAP: Dict[str, Dict[str, Any]] = {
    "red sea": {"zoneId": "ZONE-REDSEA", "name": "Red Sea", "type": "maritime"},
    "bab el-mandeb": {"zoneId": "ZONE-BABEL", "name": "Bab el-Mandeb Strait", "type": "strait"},
    "suez": {"zoneId": "ZONE-SUEZ", "name": "Suez Canal", "type": "canal"},
    "hormuz": {"zoneId": "ZONE-001", "name": "Strait of Hormuz", "type": "strait"},
    "china": {"zoneId": "ZONE-CHINA", "name": "China Coastal", "type": "maritime"},
    "south china sea": {"zoneId": "ZONE-SCSEA", "name": "South China Sea", "type": "maritime"},
    "pacific": {"zoneId": "ZONE-PACIFIC", "name": "Western Pacific", "type": "maritime"},
    "rotterdam": {"zoneId": "ZONE-EUROPE", "name": "Northern Europe", "type": "port"},
    "hamburg": {"zoneId": "ZONE-EUROPE", "name": "Northern Europe", "type": "port"},
    "antwerp": {"zoneId": "ZONE-EUROPE", "name": "Northern Europe", "type": "port"},
    "mediterranean": {"zoneId": "ZONE-MEDEAST", "name": "Eastern Mediterranean", "type": "maritime"},
    "black sea": {"zoneId": "ZONE-005", "name": "Black Sea / Russia", "type": "maritime"},
    "russia": {"zoneId": "ZONE-005", "name": "Black Sea / Russia", "type": "maritime"},
    "ukraine": {"zoneId": "ZONE-005", "name": "Black Sea / Russia", "type": "maritime"},
    "japan": {"zoneId": "ZONE-003", "name": "East China Sea / Japan", "type": "maritime"},
    "taiwan": {"zoneId": "ZONE-004", "name": "South China Sea", "type": "maritime"},
    "iran": {"zoneId": "ZONE-001", "name": "Strait of Hormuz", "type": "strait"},
    "persian gulf": {"zoneId": "ZONE-001", "name": "Strait of Hormuz", "type": "strait"},
    "panama": {"zoneId": "ZONE-PANAMA", "name": "Panama Canal", "type": "canal"},
    "singapore": {"zoneId": "ZONE-SCSEA", "name": "South China Sea", "type": "port"},
    "malacca": {"zoneId": "ZONE-MALACCA", "name": "Strait of Malacca", "type": "strait"},
}


class NewsAgent:
    """Monitors real news sources for supply chain disruption events via GDELT."""

    def __init__(self) -> None:
        self.name = "NewsAgent"
        self._templates = EVENT_TEMPLATES
        self._client = httpx.AsyncClient(timeout=15.0)

    async def run(
        self,
        scenario_id: Optional[str] = None,
        query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run the news monitoring agent.

        Args:
            scenario_id: Specific scenario template ID (uses template, not live API).
            query: Custom search query for GDELT. If None, uses default SCM queries.

        Returns:
            Detected event candidate with classification.
        """
        # If scenario_id is given, use template-based simulation
        if scenario_id:
            logger.info("NewsAgent.run: using template for scenario %s", scenario_id)
            event_candidate = self._get_template_event(scenario_id)
        else:
            # Try real GDELT API first
            logger.info("NewsAgent.run: fetching live news from GDELT")
            event_candidate = await self._fetch_gdelt_news(query)

        classification = self.classify_event(event_candidate)
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

    async def _fetch_gdelt_news(self, query: Optional[str] = None) -> Dict[str, Any]:
        """Fetch real news articles from GDELT DOC API."""
        search_query = query or random.choice(SCM_QUERIES)

        try:
            resp = await self._client.get(
                GDELT_DOC_URL,
                params={
                    "query": search_query,
                    "mode": "artlist",
                    "maxrecords": "10",
                    "format": "json",
                    "sort": "datedesc",
                    "timespan": "7d",
                },
            )
            resp.raise_for_status()
            data = resp.json()

            articles = data.get("articles", [])
            if not articles:
                logger.warning("GDELT returned no articles, falling back to template")
                return self._get_template_event(None)

            # Pick the most relevant article (first result, sorted by date desc)
            article = articles[0]

            title = article.get("title", "Unknown Event")
            source_name = article.get("domain", article.get("source", "Unknown"))
            url = article.get("url", "")
            seendate = article.get("seendate", "")
            language = article.get("language", "English")
            source_country = article.get("sourcecountry", "")

            # Parse date from GDELT format (YYYYMMDDTHHmmssZ)
            published_date = date.today().isoformat()
            if seendate:
                try:
                    published_date = datetime.strptime(seendate[:8], "%Y%m%d").date().isoformat()
                except (ValueError, IndexError):
                    pass

            # Extract location from title + socialimage context
            location = self._extract_location(title, source_country)

            # Build tags from title keywords
            tags = self._extract_tags(title)

            # Estimate severity from title content
            raw_severity = self._estimate_severity(title)

            return {
                "id": f"GDELT-{hash(url) & 0xFFFFFF:06x}",
                "headline": title,
                "source": source_name,
                "url": url,
                "publishedDate": published_date,
                "location": location,
                "description": title,  # GDELT artlist doesn't include full body
                "tags": tags,
                "rawType": self._classify_type(title),
                "rawSeverity": raw_severity,
                "affectedZones": [],
                "estimatedDurationDays": self._estimate_duration(raw_severity),
                "estimatedEndDate": (
                    date.today() + timedelta(days=self._estimate_duration(raw_severity))
                ).isoformat(),
                "language": language,
                "sourceCountry": source_country,
                "dataSource": "gdelt",
                "relatedArticles": [
                    {
                        "title": a.get("title", ""),
                        "source": a.get("domain", ""),
                        "url": a.get("url", ""),
                    }
                    for a in articles[1:5]
                ],
            }

        except Exception as exc:
            logger.warning("GDELT API request failed: %s — falling back to template", exc)
            return self._get_template_event(None)

    async def fetch_multiple(self, max_results: int = 5) -> List[Dict[str, Any]]:
        """Fetch multiple real news events across different SCM categories."""
        events = []
        seen_titles: set = set()

        for query in SCM_QUERIES[:max_results]:
            try:
                resp = await self._client.get(
                    GDELT_DOC_URL,
                    params={
                        "query": query,
                        "mode": "artlist",
                        "maxrecords": "3",
                        "format": "json",
                        "sort": "datedesc",
                        "timespan": "7d",
                    },
                )
                resp.raise_for_status()
                data = resp.json()

                for article in data.get("articles", []):
                    title = article.get("title", "")
                    if title and title not in seen_titles:
                        seen_titles.add(title)
                        seendate = article.get("seendate", "")
                        published_date = date.today().isoformat()
                        if seendate:
                            try:
                                published_date = datetime.strptime(
                                    seendate[:8], "%Y%m%d"
                                ).date().isoformat()
                            except (ValueError, IndexError):
                                pass

                        events.append({
                            "id": f"GDELT-{hash(article.get('url', '')) & 0xFFFFFF:06x}",
                            "headline": title,
                            "source": article.get("domain", "Unknown"),
                            "url": article.get("url", ""),
                            "publishedDate": published_date,
                            "type": self._classify_type(title),
                            "severity": self._estimate_severity(title),
                            "location": self._extract_location(
                                title, article.get("sourcecountry", "")
                            ),
                            "tags": self._extract_tags(title),
                            "dataSource": "gdelt",
                        })
                        if len(events) >= max_results:
                            break

            except Exception as exc:
                logger.warning("GDELT query '%s' failed: %s", query, exc)
                continue

            if len(events) >= max_results:
                break

        return events

    def _get_template_event(self, scenario_id: Optional[str]) -> Dict[str, Any]:
        """Get a pre-built template event (fallback)."""
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
            "estimatedEndDate": (
                today + timedelta(days=template.get("estimatedDuration", 30))
            ).isoformat(),
            "dataSource": "template",
        }

    def _classify_type(self, text: str) -> str:
        """Classify event type from text using keyword matching."""
        text_lower = text.lower()
        for event_type, keywords in TYPE_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                return event_type
        return "general"

    def _estimate_severity(self, text: str) -> int:
        """Estimate severity (1-5) from text keywords."""
        text_lower = text.lower()
        severity = 2  # default baseline

        high_severity = ["war", "blockade", "blocked", "attack", "missile", "explosion", "collapse"]
        medium_severity = ["disruption", "closure", "strike", "sanctions", "tariff", "earthquake"]
        low_severity = ["delay", "concern", "tension", "minor"]

        if any(kw in text_lower for kw in high_severity):
            severity = 4
        elif any(kw in text_lower for kw in medium_severity):
            severity = 3
        elif any(kw in text_lower for kw in low_severity):
            severity = 2

        # Escalate for global-scale keywords
        if any(kw in text_lower for kw in ["global", "worldwide", "all traffic", "complete"]):
            severity = min(5, severity + 1)

        return severity

    def _estimate_duration(self, severity: int) -> int:
        """Estimate disruption duration in days based on severity."""
        duration_map = {1: 7, 2: 14, 3: 30, 4: 60, 5: 90}
        return duration_map.get(severity, 30)

    def _extract_location(self, title: str, source_country: str) -> str:
        """Extract location from title and metadata."""
        title_lower = title.lower()
        for keyword in LOCATION_ZONE_MAP:
            if keyword in title_lower:
                return LOCATION_ZONE_MAP[keyword]["name"]
        return source_country or "Global"

    def _extract_tags(self, title: str) -> List[str]:
        """Extract relevant tags from title."""
        title_lower = title.lower()
        tag_keywords = [
            "shipping", "maritime", "port", "canal", "sanctions", "tariff",
            "strike", "typhoon", "earthquake", "oil", "gas", "pipeline",
            "container", "freight", "blockade", "conflict", "trade",
        ]
        return [kw for kw in tag_keywords if kw in title_lower] or ["supply-chain"]

    def classify_event(self, event_candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Classify event type and severity based on content analysis."""
        event_type = event_candidate.get("rawType", "unknown")
        raw_severity = event_candidate.get("rawSeverity", 3)
        description = (event_candidate.get("description") or "").lower()
        tags = event_candidate.get("tags", [])

        severity = raw_severity

        escalation_keywords = ["blocked", "closed", "category 5", "indefinite", "all traffic"]
        if any(kw in description for kw in escalation_keywords):
            severity = min(5, severity + 1)

        deescalation_keywords = ["minor", "temporary", "localized", "partial"]
        if any(kw in description for kw in deescalation_keywords):
            severity = max(1, severity - 1)

        high_confidence_sources = ["reuters", "lloyd's", "financial times", "bbc", "noaa", "ap news"]
        source = (event_candidate.get("source") or "").lower()
        confidence = 0.9 if any(s in source for s in high_confidence_sources) else 0.7

        # Higher confidence for live data
        if event_candidate.get("dataSource") == "gdelt":
            confidence = min(1.0, confidence + 0.05)

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
        """Match event location to GeopoliticalZones in the knowledge graph."""
        affected_zones = event_candidate.get("affectedZones", [])
        location = event_candidate.get("location", "")
        headline = event_candidate.get("headline", "")

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

        # Match from location string + headline
        combined_text = f"{location} {headline}".lower()
        for keyword, zone_data in LOCATION_ZONE_MAP.items():
            if keyword in combined_text and zone_data["zoneId"] not in seen_zone_ids:
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

    async def close(self) -> None:
        await self._client.aclose()


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
