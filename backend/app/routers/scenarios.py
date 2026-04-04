"""API endpoints for disruption scenario management.

Scenarios are pre-defined disruption event definitions stored as JSON files
in data/scenarios/. They can be listed, inspected, and activated (which
creates a DisruptionEvent node in Neo4j).
"""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.services import scenario_service

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


@router.get("", response_model=List[Dict[str, Any]])
async def list_scenarios() -> List[Dict[str, Any]]:
    """List all available scenario definitions (summaries)."""
    return scenario_service.list_scenarios()


@router.get("/{scenario_id}", response_model=Dict[str, Any])
async def get_scenario(scenario_id: str) -> Dict[str, Any]:
    """Get the full definition of a specific scenario."""
    scenario = scenario_service.get_scenario(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail=f"Scenario not found: {scenario_id}")
    return scenario


@router.post("/{scenario_id}/activate", response_model=Dict[str, Any], status_code=201)
async def activate_scenario(scenario_id: str) -> Dict[str, Any]:
    """Activate a scenario by creating a DisruptionEvent in Neo4j.

    Creates the DisruptionEvent node with proper AFFECTS_ZONE relationships
    to the GeopoliticalZone nodes referenced by the scenario.

    If the event already exists (by eventId), it will be updated.
    """
    try:
        result = await scenario_service.activate_scenario(scenario_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return result


@router.post("/reload", response_model=Dict[str, Any])
async def reload_scenarios() -> Dict[str, Any]:
    """Force-reload scenario definitions from disk."""
    count = scenario_service.reload_scenarios()
    return {"reloaded": count, "message": f"Loaded {count} scenario(s) from disk"}
