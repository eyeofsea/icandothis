"""Service layer for impact analysis - bridges routers with agents."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.agents.impact_agent import ImpactAgent
from app.agents.tools.neo4j_tools import query_neo4j

logger = logging.getLogger(__name__)

# Simple in-memory cache for impact results
_impact_cache: Dict[str, Dict[str, Any]] = {}


class ImpactService:
    """Service that bridges HTTP routers with the ImpactAgent."""

    def __init__(self) -> None:
        self._agent = ImpactAgent()

    async def analyze_disruption_impact(
        self,
        event_id: str,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """
        Run impact analysis for a disruption event by ID.

        Args:
            event_id: The disruption event ID.
            force_refresh: Skip cache and rerun analysis.

        Returns:
            Impact analysis result dict.
        """
        cache_key = f"impact:{event_id}"

        if not force_refresh and cache_key in _impact_cache:
            logger.info("Returning cached impact for %s", event_id)
            return _impact_cache[cache_key]

        # Fetch event from Neo4j
        event = await self._fetch_event(event_id)
        if not event:
            return {"error": f"Disruption event {event_id} not found."}

        zone_ids = event.get("affectedZones", [])
        result = await self._agent.run(event=event, affected_zone_ids=zone_ids)

        # Cache the result
        _impact_cache[cache_key] = result
        return result

    async def analyze_zones_impact(
        self,
        zone_ids: List[str],
        severity: int = 3,
        description: str = "Ad-hoc zone analysis",
    ) -> Dict[str, Any]:
        """Run impact analysis for arbitrary zone IDs without a stored event."""
        synthetic_event = {
            "eventId": "ADHOC",
            "type": "geopolitical",
            "severity": severity,
            "description": description,
            "affectedZones": zone_ids,
        }
        return await self._agent.run(event=synthetic_event, affected_zone_ids=zone_ids)

    async def get_project_impact(
        self, project_id: str
    ) -> Dict[str, Any]:
        """Get impact summary focused on a specific project."""
        # Find disruptions affecting this project's equipment routes
        try:
            records = await query_neo4j(
                """
                MATCH (p:Project {projectId: $projectId})-[:HAS_EQUIPMENT]->(e:Equipment)
                       -[:SHIPPED_VIA]->(r:ShippingRoute)-[:PASSES_THROUGH]->(z:GeopoliticalZone)
                       <-[:AFFECTS_ZONE]-(d:DisruptionEvent)
                WHERE d.verificationStatus <> 'resolved'
                RETURN d {
                    .eventId, .type, .severity, .description,
                    affectedZones: collect(DISTINCT z.zoneId)
                } AS event
                """,
                {"projectId": project_id},
            )
            events = [r["event"] for r in records if r.get("event") and r["event"].get("eventId")]
        except Exception as exc:
            logger.warning("Failed to fetch project disruptions: %s", exc)
            events = []

        if not events:
            return {
                "projectId": project_id,
                "impacted": False,
                "message": "No active disruptions affecting this project.",
            }

        # Run impact for the highest severity event
        events.sort(key=lambda e: e.get("severity", 0), reverse=True)
        primary_event = events[0]
        all_zones = set()
        for evt in events:
            all_zones.update(evt.get("affectedZones", []))

        impact = await self._agent.run(
            event=primary_event,
            affected_zone_ids=list(all_zones),
        )

        # Filter to only this project's data
        project_risk = impact.get("projectRiskMatrix", {}).get(project_id, {})

        return {
            "projectId": project_id,
            "impacted": True,
            "primaryEvent": primary_event,
            "allEvents": events,
            "projectRisk": project_risk,
            "affectedEquipment": [
                e for e in impact.get("affectedEquipment", [])
                if e.get("projectId") == project_id
            ],
            "estimatedDelayDays": project_risk.get("estimatedDelayDays", 0),
            "overallProjectRisk": project_risk.get("overallProjectRisk", 0),
        }

    async def _fetch_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a disruption event from Neo4j."""
        try:
            records = await query_neo4j(
                """
                MATCH (d:DisruptionEvent {eventId: $eventId})
                OPTIONAL MATCH (d)-[:AFFECTS_ZONE]->(z:GeopoliticalZone)
                RETURN d {
                    .eventId, .type, .severity, .description,
                    .verificationStatus, .source,
                    startDate: toString(d.startDate),
                    endDate: toString(d.endDate),
                    affectedZones: collect(z.zoneId)
                } AS event
                """,
                {"eventId": event_id},
            )
            if records and records[0].get("event"):
                return records[0]["event"]
        except Exception as exc:
            logger.warning("Failed to fetch event %s: %s", event_id, exc)
        return None

    def clear_cache(self, event_id: Optional[str] = None) -> None:
        """Clear impact cache, optionally for a specific event."""
        if event_id:
            cache_key = f"impact:{event_id}"
            _impact_cache.pop(cache_key, None)
        else:
            _impact_cache.clear()
