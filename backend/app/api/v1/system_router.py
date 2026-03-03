"""
Urban Cortex AI – System Router
=================================

System endpoints (IoT sync, health checks).
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, status

from app.services.iot_service import IoTService
from app.utils.response_formatter import success_response, error_response

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/system",
    tags=["System"],
)

iot_service = IoTService()


# ── POST /api/v1/system/sync-iot ───────────────────────────────

@router.post(
    "/sync-iot",
    status_code=status.HTTP_200_OK,
    summary="Sync bins from IoT simulator",
)
async def sync_iot():
    """
    Fetch bins from IoT simulator and sync to Firestore.
    
    - Creates new bins
    - Updates existing bins
    - Recalculates status and urgency_score
    """
    try:
        result = await iot_service.sync_from_iot()
        
        return success_response(
            data=result,
            message="IoT sync completed successfully",
        )
    
    except Exception as exc:
        logger.error("IoT sync failed: %s", str(exc))
        return error_response(
            message="IoT sync failed",
            errors=[str(exc)],
        )
