"""Service for loading and activating disruption scenarios from JSON files."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.database.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)

# Path to scenario JSON files relative to the project root
_SCENARIOS_DIR = Path(__file__).resolve().parents[3] / "data" / "scenarios"

# In-memory cache of loaded scenario definitions (populated on first access)
_scenario_cache: Dict[str, Dict[str, Any]] = {}


def _load_scenarios() -> Dict[str, Dict[str, Any]]:
    """Load all scenario JSON files from disk into memory.

    Returns a new dict mapping scenario_id to scenario data.
    """
    scenarios: Dict[str, Dict[str, Any]] = {}

    if not _SCENARIOS_DIR.is_dir():
        logger.warning("Scenarios directory not found: %s", _SCENARIOS_DIR)
        return scenarios

    for filepath in sorted(_SCENARIOS_DIR.glob("*.json")):
        try:
            raw = filepath.read_text(encoding="utf-8")
            data = json.loads(raw)
            scenario_id = filepath.stem  # e.g. "hormuz_blockade"
            data["scenarioId"] = scenario_id
            scenarios[scenario_id] = data
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to load scenario %s: %s", filepath.name, exc)

    logger.info("Loaded %d scenario definitions from %s", len(scenarios), _SCENARIOS_DIR)
    return scenarios


def _get_cache() -> Dict[str, Dict[str, Any]]:
    """Return the scenario cache, populating it on first call."""
    global _scenario_cache
    if not _scenario_cache:
        _scenario_cache = _load_scenarios()
    return _scenario_cache


def list_scenarios() -> List[Dict[str, Any]]:
    """Return summary info for all available scenarios."""
    cache = _get_cache()
    summaries: List[Dict[str, Any]] = []
    for scenario_id, data in cache.items():
        summaries.append({
            "scenarioId": scenario_id,
            "eventId": data.get("eventId"),
            "name": data.get("name"),
            "type": data.get("type"),
            "severity": data.get("severity"),
            "description": data.get("description"),
            "affectedZones": data.get("affectedZones", []),
        })
    return summaries


def get_scenario(scenario_id: str) -> Optional[Dict[str, Any]]:
    """Return full scenario data by ID, or None if not found."""
    return _get_cache().get(scenario_id)


async def activate_scenario(scenario_id: str) -> Dict[str, Any]:
    """Activate a scenario by creating a DisruptionEvent node in Neo4j.

    Creates the DisruptionEvent node with name and description, and
    AFFECTS_ZONE relationships to the referenced GeopoliticalZone nodes.

    Returns the created disruption event data.

    Raises:
        ValueError: If the scenario_id is not found.
        RuntimeError: If the Neo4j write fails.
    """
    scenario = get_scenario(scenario_id)
    if scenario is None:
        raise ValueError(f"Scenario not found: {scenario_id}")

    db = await Neo4jClient.get_instance()

    event_id = scenario["eventId"]
    affected_zones = scenario.get("affectedZones", [])

    # Build the query - create DisruptionEvent and AFFECTS_ZONE relationships
    query = """
    MERGE (d:DisruptionEvent {eventId: $eventId})
    ON CREATE SET
        d.name = $name,
        d.type = $type,
        d.severity = $severity,
        d.description = $description,
        d.startDate = date($startDate),
        d.endDate = CASE WHEN $endDate IS NOT NULL THEN date($endDate) ELSE null END,
        d.source = $source,
        d.verificationStatus = $verificationStatus,
        d.status = 'active',
        d.scenarioId = $scenarioId,
        d.createdAt = datetime()
    ON MATCH SET
        d.name = $name,
        d.type = $type,
        d.severity = $severity,
        d.description = $description,
        d.startDate = date($startDate),
        d.endDate = CASE WHEN $endDate IS NOT NULL THEN date($endDate) ELSE null END,
        d.source = $source,
        d.verificationStatus = $verificationStatus,
        d.status = 'active',
        d.scenarioId = $scenarioId,
        d.updatedAt = datetime()
    WITH d
    OPTIONAL MATCH (d)-[r:AFFECTS_ZONE]->()
    DELETE r
    WITH d
    UNWIND CASE WHEN size($affectedZones) > 0 THEN $affectedZones ELSE [null] END AS zoneId
    OPTIONAL MATCH (z:GeopoliticalZone {zoneId: zoneId})
    FOREACH (_ IN CASE WHEN z IS NOT NULL THEN [1] ELSE [] END |
        CREATE (d)-[:AFFECTS_ZONE]->(z)
    )
    WITH d
    OPTIONAL MATCH (d)-[:AFFECTS_ZONE]->(z:GeopoliticalZone)
    RETURN d {
        .eventId, .name, .type, .severity, .description,
        startDate: toString(d.startDate),
        endDate: toString(d.endDate),
        .source, .verificationStatus, .status, .scenarioId,
        createdAt: toString(d.createdAt),
        affectedZoneIds: collect(z.zoneId)
    } AS disruption
    """

    params = {
        "eventId": event_id,
        "name": scenario.get("name", ""),
        "type": scenario.get("type", ""),
        "severity": scenario.get("severity", 1),
        "description": scenario.get("description", ""),
        "startDate": scenario.get("startDate", "2026-01-01"),
        "endDate": scenario.get("estimatedEndDate"),
        "source": scenario.get("source", ""),
        "verificationStatus": scenario.get("verificationStatus", "Confirmed"),
        "scenarioId": scenario_id,
        "affectedZones": affected_zones,
    }

    records = await db.execute_write(query, params)
    if not records:
        raise RuntimeError(f"Failed to activate scenario {scenario_id}")

    result = records[0]["disruption"]
    logger.info("Activated scenario %s as DisruptionEvent %s", scenario_id, event_id)
    return result


def reload_scenarios() -> int:
    """Force-reload scenarios from disk. Returns number loaded."""
    global _scenario_cache
    _scenario_cache = _load_scenarios()
    return len(_scenario_cache)
