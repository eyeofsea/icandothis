"""WebSocket event handlers for the SCM Risk Intelligence Platform.

Provides handlers for disruption alerts, agent status updates,
and impact result broadcasts.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.websocket.manager import get_connection_manager

logger = logging.getLogger(__name__)


async def on_disruption_event(
    event_data: Dict[str, Any],
    severity: Optional[int] = None,
) -> int:
    """
    Broadcast a disruption alert to all connected clients.

    Args:
        event_data: The disruption event data to broadcast.
        severity: Optional severity override for the alert level.

    Returns:
        Number of clients that received the alert.
    """
    manager = get_connection_manager()

    severity = severity or event_data.get("severity", 3)
    alert_level = "critical" if severity >= 4 else "warning" if severity >= 3 else "info"

    message = {
        "type": "disruption_alert",
        "alertLevel": alert_level,
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "eventId": event_data.get("eventId"),
            "eventType": event_data.get("type"),
            "severity": severity,
            "description": event_data.get("description", ""),
            "affectedZones": event_data.get("affectedZones", []),
        },
    }

    # Broadcast to all connections
    sent = await manager.broadcast(message)

    # Also broadcast to the "disruptions" topic
    await manager.broadcast_to_topic("disruptions", message)

    logger.info(
        "Disruption alert broadcast: %s (severity %d) to %d clients",
        event_data.get("eventId", "unknown"),
        severity,
        sent,
    )
    return sent


async def on_agent_status(
    agent_name: str,
    status: str,
    message: str = "",
    progress: Optional[float] = None,
    details: Optional[Dict[str, Any]] = None,
) -> int:
    """
    Broadcast agent progress/status updates to connected clients.

    Args:
        agent_name: Name of the agent (e.g., "ImpactAgent", "SupplierAgent").
        status: Status string (e.g., "running", "completed", "error").
        message: Human-readable status message.
        progress: Optional progress percentage (0-100).
        details: Optional additional details.

    Returns:
        Number of clients that received the update.
    """
    manager = get_connection_manager()

    payload = {
        "type": "agent_status",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "agentName": agent_name,
            "status": status,
            "message": message,
            "progress": progress,
            "details": details or {},
        },
    }

    sent = await manager.broadcast(payload)

    # Also to agent-specific topic
    await manager.broadcast_to_topic(f"agent:{agent_name}", payload)

    logger.debug("Agent status broadcast: %s [%s] to %d clients", agent_name, status, sent)
    return sent


async def on_impact_update(
    event_id: str,
    impact_data: Dict[str, Any],
    update_type: str = "complete",
) -> int:
    """
    Broadcast impact analysis results to connected clients.

    Args:
        event_id: The disruption event ID.
        impact_data: Impact analysis results.
        update_type: Type of update ("partial", "complete", "error").

    Returns:
        Number of clients that received the update.
    """
    manager = get_connection_manager()

    message = {
        "type": "impact_update",
        "timestamp": datetime.utcnow().isoformat(),
        "updateType": update_type,
        "data": {
            "eventId": event_id,
            "impactScore": impact_data.get("impactScore"),
            "affectedEquipmentCount": impact_data.get("affectedEquipmentCount", 0),
            "criticalPathItemCount": impact_data.get("criticalPathItemCount", 0),
            "affectedRouteCount": impact_data.get("affectedRouteCount", 0),
            "estimatedDelayDays": impact_data.get("estimatedDelayDays", 0),
            "summary": impact_data.get("summary", ""),
            "projectRiskMatrix": impact_data.get("projectRiskMatrix", {}),
        },
    }

    sent = await manager.broadcast(message)

    # Also to impact-specific topic
    await manager.broadcast_to_topic("impact", message)
    await manager.broadcast_to_topic(f"event:{event_id}", message)

    logger.info(
        "Impact update broadcast for event %s (%s) to %d clients",
        event_id, update_type, sent,
    )
    return sent


async def on_cost_update(
    event_id: str,
    cost_data: Dict[str, Any],
) -> int:
    """Broadcast cost analysis results."""
    manager = get_connection_manager()

    no_action = cost_data.get("noActionCost", {})
    best = (cost_data.get("mitigationScenarios") or {}).get("bestScenario", {})

    message = {
        "type": "cost_update",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "eventId": event_id,
            "totalDisruptionCost": no_action.get("totalDisruptionCost", 0),
            "bestMitigation": best.get("name") if best else None,
            "netSavings": best.get("netSavings", 0) if best else 0,
            "summary": cost_data.get("summary", ""),
        },
    }

    sent = await manager.broadcast(message)
    await manager.broadcast_to_topic("costs", message)
    return sent


async def on_route_update(
    route_recommendations: Dict[str, Any],
) -> int:
    """Broadcast route optimization results."""
    manager = get_connection_manager()

    message = {
        "type": "route_update",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "totalBlockedRoutes": route_recommendations.get("totalBlockedRoutes", 0),
            "routesWithAlternatives": route_recommendations.get("routesWithAlternatives", 0),
            "summary": route_recommendations.get("summary", ""),
        },
    }

    sent = await manager.broadcast(message)
    await manager.broadcast_to_topic("routes", message)
    return sent


async def on_supplier_update(
    supplier_recommendations: Dict[str, Any],
) -> int:
    """Broadcast supplier recommendation results."""
    manager = get_connection_manager()

    message = {
        "type": "supplier_update",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "totalEquipmentProcessed": supplier_recommendations.get("totalEquipmentProcessed", 0),
            "equipmentWithAlternatives": supplier_recommendations.get("equipmentWithAlternatives", 0),
            "totalAlternativesFound": supplier_recommendations.get("totalAlternativesFound", 0),
            "summary": supplier_recommendations.get("summary", ""),
        },
    }

    sent = await manager.broadcast(message)
    await manager.broadcast_to_topic("suppliers", message)
    return sent
