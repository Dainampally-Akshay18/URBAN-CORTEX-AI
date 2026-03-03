"""
Urban Cortex AI – WebSocket Connection Manager
================================================

Manages WebSocket connections and broadcasts events.
"""

from __future__ import annotations

import json
import logging
from typing import Dict, List

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    WebSocket connection manager.
    Maintains active connections and broadcasts events.
    """
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket connected. Total connections: %d", len(self.active_connections))
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("WebSocket disconnected. Total connections: %d", len(self.active_connections))
    
    async def broadcast(self, event: str, data: Dict):
        """
        Broadcast an event to all connected clients.
        
        Args:
            event: Event type (e.g., "truck_location_update")
            data: Event payload
        """
        message = {
            "event": event,
            "data": data
        }
        
        message_json = json.dumps(message)
        
        # Send to all active connections
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as exc:
                logger.error("Failed to send to WebSocket: %s", str(exc))
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
        
        logger.debug("Broadcast event '%s' to %d clients", event, len(self.active_connections))
    
    async def send_personal(self, websocket: WebSocket, event: str, data: Dict):
        """
        Send event to a specific client.
        
        Args:
            websocket: Target WebSocket connection
            event: Event type
            data: Event payload
        """
        message = {
            "event": event,
            "data": data
        }
        
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as exc:
            logger.error("Failed to send personal message: %s", str(exc))
            self.disconnect(websocket)


# Global connection manager instance
manager = ConnectionManager()
