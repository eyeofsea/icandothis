"""WebSocket connection manager for the SCM Risk Intelligence Platform.

Tracks active connections and provides broadcast/unicast messaging
for disruption alerts, agent status updates, and impact results.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""

    _instance: Optional[ConnectionManager] = None

    def __init__(self) -> None:
        self._active_connections: Dict[str, WebSocket] = {}
        self._subscriptions: Dict[str, Set[str]] = {}  # topic -> set of connection_ids

    @classmethod
    def get_instance(cls) -> ConnectionManager:
        """Get or create the singleton ConnectionManager."""
        if cls._instance is None:
            cls._instance = ConnectionManager()
        return cls._instance

    async def connect(self, websocket: WebSocket, connection_id: str) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self._active_connections[connection_id] = websocket
        logger.info("WebSocket connected: %s (total: %d)", connection_id, len(self._active_connections))

    def disconnect(self, connection_id: str) -> None:
        """Remove a disconnected WebSocket."""
        self._active_connections.pop(connection_id, None)
        # Remove from all subscriptions
        for topic_subs in self._subscriptions.values():
            topic_subs.discard(connection_id)
        logger.info("WebSocket disconnected: %s (total: %d)", connection_id, len(self._active_connections))

    def subscribe(self, connection_id: str, topic: str) -> None:
        """Subscribe a connection to a topic."""
        if topic not in self._subscriptions:
            self._subscriptions[topic] = set()
        self._subscriptions[topic].add(connection_id)

    def unsubscribe(self, connection_id: str, topic: str) -> None:
        """Unsubscribe a connection from a topic."""
        if topic in self._subscriptions:
            self._subscriptions[topic].discard(connection_id)

    async def send_to_connection(
        self, connection_id: str, message: Dict[str, Any]
    ) -> bool:
        """Send a message to a specific connection. Returns True if successful."""
        websocket = self._active_connections.get(connection_id)
        if websocket is None:
            return False
        try:
            await websocket.send_json(message)
            return True
        except Exception as exc:
            logger.warning("Failed to send to %s: %s", connection_id, exc)
            self.disconnect(connection_id)
            return False

    async def broadcast(self, message: Dict[str, Any]) -> int:
        """
        Broadcast a message to all active connections.
        Returns the number of connections that received the message.
        """
        sent_count = 0
        disconnected: list[str] = []

        for conn_id, websocket in self._active_connections.items():
            try:
                await websocket.send_json(message)
                sent_count += 1
            except Exception as exc:
                logger.warning("Broadcast failed for %s: %s", conn_id, exc)
                disconnected.append(conn_id)

        # Clean up disconnected
        for conn_id in disconnected:
            self.disconnect(conn_id)

        return sent_count

    async def broadcast_to_topic(
        self, topic: str, message: Dict[str, Any]
    ) -> int:
        """
        Broadcast a message to all connections subscribed to a topic.
        Returns the number of connections that received the message.
        """
        subscribers = self._subscriptions.get(topic, set())
        if not subscribers:
            return 0

        sent_count = 0
        disconnected: list[str] = []

        for conn_id in subscribers:
            websocket = self._active_connections.get(conn_id)
            if websocket is None:
                disconnected.append(conn_id)
                continue
            try:
                await websocket.send_json(message)
                sent_count += 1
            except Exception:
                disconnected.append(conn_id)

        for conn_id in disconnected:
            self.disconnect(conn_id)

        return sent_count

    @property
    def active_count(self) -> int:
        """Number of active connections."""
        return len(self._active_connections)

    @property
    def connection_ids(self) -> list[str]:
        """List of active connection IDs."""
        return list(self._active_connections.keys())

    def get_subscriptions(self, connection_id: str) -> list[str]:
        """Get topics a connection is subscribed to."""
        return [
            topic for topic, subs in self._subscriptions.items()
            if connection_id in subs
        ]


def get_connection_manager() -> ConnectionManager:
    """Get the singleton ConnectionManager instance."""
    return ConnectionManager.get_instance()
