"""
Urban Cortex AI – WebSocket Router
====================================

WebSocket endpoint for real-time updates.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.websocket.connection_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.
    
    PRD Module 11: WebSocket Contract
    Endpoint: /api/v1/ws/live
    
    Events broadcasted:
    - truck_location_update
    - bin_collected
    - route_progress
    - route_completed
    - complaint_created
    - metrics_updated
    """
    await manager.connect(websocket)
    
    try:
        # Keep connection alive and listen for messages
        while True:
            # Wait for any message from client (ping/pong)
            data = await websocket.receive_text()
            logger.debug("Received WebSocket message: %s", data)
            
            # Echo back for testing (optional)
            # await websocket.send_text(f"Message received: {data}")
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as exc:
        logger.error("WebSocket error: %s", str(exc))
        manager.disconnect(websocket)
