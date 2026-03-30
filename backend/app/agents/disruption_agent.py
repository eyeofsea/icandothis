"""Disruption Detection Agent for the SCM Risk Intelligence Platform.

Takes event candidates from the NewsAgent, verifies against the knowledge base,
classifies severity, matches to affected zones, creates DisruptionEvent in Neo4j,
and triggers impact analysis.
"""

from __future__ import annotations

import logging
import uuid
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from app.agents.tools.neo4j_tools import query_neo4j
from app.agents.impact_agent import ImpactAgent

logger = logging.getLogger(__name__)

# Severity classification thresholds
SEVERITY_CRITERIA = {
    5: {
        "keywords": ["blocked", "closed", "all traffic", "category 5", "total shutdown"],
        "min_zones": 2,
        "description": "Critical - Complete disruption of major trade route",
    },
    4: {
        "keywords": ["attacks", "intensify", "forced reroute", "major delay", "surge"],
        "min_zones": 1,
        "description": "Severe - Significant disruption requiring immediate action",
    },
    3: {
        "keywords": ["controls", "restrictions", "reduced capacity", "strike"],
        "min_zones": 1,
        "description": "Moderate - Notable disruption with workaround available",
    },
    2: {
        "keywords": ["temporary", "minor delay", "partial", "localized"],
        "min_zones": 1,
        "description": "Low - Limited disruption, monitoring recommended",
    },
    1: {
        "keywords": ["resolved", "clearing", "resuming", "minimal"],
        "min_zones": 0,
        "description": "Minimal - Negligible impact, awareness only",
    },
}


class DisruptionAgent:
    """Detects and registers disruption events in the knowledge graph."""

    def __init__(self) -> None:
        self.name = "DisruptionAgent"
        self._impact_agent = ImpactAgent()

    async def run(
        self,
        event_candidate: Dict[str, Any],
        matched_zones: Optional[List[Dict[str, Any]]] = None,
        auto_trigger_impact: bool = True,
    ) -> Dict[str, Any]:
        """
        Process an event candidate into a verified disruption event.

        Args:
            event_candidate: Raw event from NewsAgent with headline, type, location, etc.
            matched_zones: Geocoded zone matches from NewsAgent.
            auto_trigger_impact: Whether to automatically run impact analysis.

        Returns:
            Structured disruption detection result with optional impact analysis.
        """
        logger.info(
            "DisruptionAgent.run: processing event '%s'",
            event_candidate.get("headline", "unknown"),
        )

        matched_zones = matched_zones or []
        zone_ids = [z.get("zoneId") for z in matched_zones if z.get("zoneId")]

        # Step 1: Verify against knowledge base
        verification = await self._verify_against_kb(event_candidate, zone_ids)

        # Step 2: Classify severity
        severity = self._classify_severity(event_candidate, verification)

        # Step 3: Match and validate affected zones
        validated_zones = await self._validate_zones(zone_ids)

        # Step 4: Create DisruptionEvent in Neo4j
        disruption_event = await self._create_disruption_event(
            event_candidate, severity, validated_zones
        )

        result: Dict[str, Any] = {
            "disruptionEvent": disruption_event,
            "verification": verification,
            "classifiedSeverity": severity,
            "validatedZones": validated_zones,
            "impactAnalysis": None,
        }

        # Step 5: Trigger impact analysis chain if requested
        if auto_trigger_impact and disruption_event.get("eventId"):
            try:
                impact = await self._impact_agent.run(
                    event=disruption_event,
                    affected_zone_ids=[z.get("zoneId") for z in validated_zones if z.get("zoneId")],
                )
                result["impactAnalysis"] = impact
            except Exception as exc:
                logger.warning("Impact analysis failed: %s", exc)
                result["impactAnalysis"] = {"error": str(exc)}

        result["summary"] = self._generate_summary(result)
        return result

    async def _verify_against_kb(
        self, event_candidate: Dict[str, Any], zone_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Verify the event candidate against existing knowledge base data.
        Checks for duplicate events, validates zones exist, etc.
        """
        verification: Dict[str, Any] = {
            "isDuplicate": False,
            "existingEventId": None,
            "zonesExistInGraph": [],
            "zonesMissing": [],
            "routesAffected": 0,
            "suppliersInZone": 0,
            "status": "new",
        }

        # Check for duplicate/similar events
        event_type = event_candidate.get("rawType") or event_candidate.get("type", "unknown")
        try:
            dup_check = await query_neo4j(
                """
                MATCH (d:DisruptionEvent)
                WHERE d.type = $type
                  AND d.verificationStatus <> 'resolved'
                RETURN d {.eventId, .type, .severity, .description} AS event
                LIMIT 5
                """,
                {"type": event_type},
            )
            if dup_check:
                # Check for similar descriptions
                candidate_desc = (event_candidate.get("description") or "").lower()
                for existing in dup_check:
                    evt = existing.get("event", {})
                    existing_desc = (evt.get("description") or "").lower()
                    # Simple overlap check
                    candidate_words = set(candidate_desc.split())
                    existing_words = set(existing_desc.split())
                    overlap = len(candidate_words & existing_words) / max(len(candidate_words), 1)
                    if overlap > 0.5:
                        verification["isDuplicate"] = True
                        verification["existingEventId"] = evt.get("eventId")
                        verification["status"] = "duplicate"
                        break
        except Exception as exc:
            logger.warning("Duplicate check failed: %s", exc)

        # Validate zones in graph
        if zone_ids:
            try:
                zone_check = await query_neo4j(
                    """
                    UNWIND $zoneIds AS zid
                    OPTIONAL MATCH (z:GeopoliticalZone {zoneId: zid})
                    RETURN zid, z IS NOT NULL AS exists
                    """,
                    {"zoneIds": zone_ids},
                )
                for rec in zone_check:
                    if rec.get("exists"):
                        verification["zonesExistInGraph"].append(rec["zid"])
                    else:
                        verification["zonesMissing"].append(rec["zid"])
            except Exception as exc:
                logger.warning("Zone validation failed: %s", exc)

        # Count potentially affected routes and suppliers
        if zone_ids:
            try:
                count_result = await query_neo4j(
                    """
                    MATCH (r:ShippingRoute)-[:PASSES_THROUGH]->(z:GeopoliticalZone)
                    WHERE z.zoneId IN $zoneIds
                    WITH count(DISTINCT r) AS routeCount
                    OPTIONAL MATCH (s:Supplier)-[:LOCATED_IN]->(z2:GeopoliticalZone)
                    WHERE z2.zoneId IN $zoneIds
                    RETURN routeCount, count(DISTINCT s) AS supplierCount
                    """,
                    {"zoneIds": zone_ids},
                )
                if count_result:
                    verification["routesAffected"] = count_result[0].get("routeCount", 0)
                    verification["suppliersInZone"] = count_result[0].get("supplierCount", 0)
            except Exception as exc:
                logger.warning("Count query failed: %s", exc)

        if not verification["isDuplicate"]:
            verification["status"] = "verified" if verification["zonesExistInGraph"] else "unverified"

        return verification

    def _classify_severity(
        self,
        event_candidate: Dict[str, Any],
        verification: Dict[str, Any],
    ) -> int:
        """Classify event severity on a 1-5 scale."""
        # Start with the raw severity from the event
        raw_severity = event_candidate.get("rawSeverity", 3)
        description = (event_candidate.get("description") or "").lower()

        # Adjust based on keyword analysis
        classified_severity = raw_severity
        for level in sorted(SEVERITY_CRITERIA.keys(), reverse=True):
            criteria = SEVERITY_CRITERIA[level]
            keyword_match = any(kw in description for kw in criteria["keywords"])
            zone_threshold = len(verification.get("zonesExistInGraph", [])) >= criteria["min_zones"]
            if keyword_match and zone_threshold:
                classified_severity = max(classified_severity, level)
                break

        # Adjust based on verification results
        routes_affected = verification.get("routesAffected", 0)
        if routes_affected >= 3:
            classified_severity = min(5, classified_severity + 1)
        elif routes_affected == 0 and classified_severity > 2:
            classified_severity -= 1

        return max(1, min(5, classified_severity))

    async def _validate_zones(
        self, zone_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Validate and enrich zone information from the graph."""
        if not zone_ids:
            return []

        try:
            records = await query_neo4j(
                """
                UNWIND $zoneIds AS zid
                MATCH (z:GeopoliticalZone {zoneId: zid})
                RETURN z {
                    .zoneId, .name, .type, .riskLevel, .currentStatus,
                    .controllingEntity, .description
                } AS zone
                """,
                {"zoneIds": zone_ids},
            )
            return [r["zone"] for r in records if r.get("zone") and r["zone"].get("zoneId")]
        except Exception as exc:
            logger.warning("Zone validation query failed: %s", exc)
            # Return basic zone info if graph query fails
            return [{"zoneId": zid, "name": zid, "validated": False} for zid in zone_ids]

    async def _create_disruption_event(
        self,
        event_candidate: Dict[str, Any],
        severity: int,
        validated_zones: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Create a DisruptionEvent node in Neo4j."""
        event_id = f"DISRUPT-{uuid.uuid4().hex[:8].upper()}"
        event_type = event_candidate.get("rawType") or event_candidate.get("type", "geopolitical")
        description = event_candidate.get("description", event_candidate.get("headline", ""))
        source = event_candidate.get("source", "news_agent")
        today = date.today()
        duration_days = event_candidate.get("estimatedDurationDays", 30)
        end_date = today + timedelta(days=duration_days)
        zone_ids = [z.get("zoneId") for z in validated_zones if z.get("zoneId")]

        try:
            records = await query_neo4j(
                """
                CREATE (d:DisruptionEvent {
                    eventId: $eventId,
                    type: $type,
                    severity: $severity,
                    startDate: date($startDate),
                    endDate: date($endDate),
                    source: $source,
                    verificationStatus: 'confirmed',
                    description: $description,
                    createdAt: datetime()
                })
                WITH d
                UNWIND CASE WHEN size($zoneIds) > 0 THEN $zoneIds ELSE [null] END AS zoneId
                OPTIONAL MATCH (z:GeopoliticalZone {zoneId: zoneId})
                FOREACH (_ IN CASE WHEN z IS NOT NULL THEN [1] ELSE [] END |
                    MERGE (d)-[:AFFECTS_ZONE]->(z)
                )
                WITH d
                OPTIONAL MATCH (d)-[:AFFECTS_ZONE]->(z:GeopoliticalZone)
                RETURN d {
                    .eventId, .type, .severity,
                    startDate: toString(d.startDate),
                    endDate: toString(d.endDate),
                    .source, .verificationStatus, .description,
                    createdAt: toString(d.createdAt),
                    affectedZones: collect(z.zoneId)
                } AS event
                """,
                {
                    "eventId": event_id,
                    "type": event_type,
                    "severity": severity,
                    "startDate": today.isoformat(),
                    "endDate": end_date.isoformat(),
                    "source": source,
                    "description": description,
                    "zoneIds": zone_ids,
                },
            )

            if records and records[0].get("event"):
                logger.info("Created disruption event %s in Neo4j", event_id)
                return records[0]["event"]
        except Exception as exc:
            logger.warning("Failed to create disruption event in Neo4j: %s", exc)

        # Return a local event dict if Neo4j write fails
        return {
            "eventId": event_id,
            "type": event_type,
            "severity": severity,
            "startDate": today.isoformat(),
            "endDate": end_date.isoformat(),
            "source": source,
            "verificationStatus": "unverified",
            "description": description,
            "affectedZones": zone_ids,
            "createdInGraph": False,
        }

    def _generate_summary(self, result: Dict[str, Any]) -> str:
        """Generate human-readable summary of disruption detection."""
        event = result.get("disruptionEvent", {})
        verification = result.get("verification", {})
        zones = result.get("validatedZones", [])

        lines = [
            "DISRUPTION DETECTION REPORT",
            f"Event ID: {event.get('eventId', 'N/A')}",
            f"Type: {event.get('type', 'unknown')}",
            f"Severity: {result.get('classifiedSeverity', 0)}/5",
            f"Status: {verification.get('status', 'unknown')}",
            f"",
            f"Description: {event.get('description', 'N/A')[:200]}",
            f"",
            f"Affected Zones: {len(zones)}",
        ]
        for z in zones:
            lines.append(f"  - {z.get('name', z.get('zoneId', 'Unknown'))}")

        lines.extend([
            f"",
            f"Routes Affected: {verification.get('routesAffected', 0)}",
            f"Suppliers in Zone: {verification.get('suppliersInZone', 0)}",
        ])

        if verification.get("isDuplicate"):
            lines.append(f"NOTE: Duplicate of existing event {verification.get('existingEventId')}")

        impact = result.get("impactAnalysis")
        if impact and not impact.get("error"):
            lines.extend([
                f"",
                f"Impact Analysis:",
                f"  Impact Score: {impact.get('impactScore', 0)}/10",
                f"  Affected Equipment: {impact.get('affectedEquipmentCount', 0)}",
                f"  Critical Path Items: {impact.get('criticalPathItemCount', 0)}",
                f"  Estimated Delay: {impact.get('estimatedDelayDays', 0)} days",
            ])

        return "\n".join(lines)
