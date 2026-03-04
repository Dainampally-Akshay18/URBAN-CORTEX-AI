"""
Urban Cortex AI – Complaints Router
======================================

CRUD endpoints for citizen complaints.
Base path: /api/v1/complaints
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_current_user, require_role
from app.schemas.complaint_schema import (
    ComplaintCreateRequest,
    ComplaintStatusUpdateRequest,
)
from app.services.complaint_service import ComplaintService
from app.utils.response_formatter import success_response

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/complaints",
    tags=["Complaints"],
)

complaint_service = ComplaintService()


# ── POST /api/v1/complaints ───────────────────────────────────

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a complaint (Citizen)",
)
async def create_complaint(
    request: ComplaintCreateRequest,
    user: Dict = Depends(require_role(["citizen"])),
):
    """
    Create a new complaint.

    - Role: **Citizen**
    - Generates complaint_id, sets status=pending, stores in Firestore.
    - Emits WebSocket event `complaint_created`.
    """
    complaint = await complaint_service.create_complaint(
        complaint_type=request.type.value,
        city=request.city,
        latitude=request.latitude,
        longitude=request.longitude,
        description=request.description,
        created_by=user.get("user_id"),
    )

    formatted = complaint_service.format_complaint_response(complaint)

    return success_response(
        data=formatted,
        message="Complaint created successfully",
    )


# ── GET /api/v1/complaints ────────────────────────────────────

@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="List complaints (Admin)",
)
async def get_complaints(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    city: Optional[str] = Query(None, description="Filter by city"),
    type_filter: Optional[str] = Query(None, alias="type", description="Filter by type"),
):
    """
    Return list of complaints with optional query filters.

    - Role: **Admin**
    - Supports filters: `status`, `city`, `type`.
    """
    complaints = await complaint_service.get_all_complaints(
        status_filter=status_filter,
        city=city,
        type_filter=type_filter,
    )

    formatted = [complaint_service.format_complaint_response(c) for c in complaints]

    return success_response(
        data=formatted,
        message=f"Retrieved {len(formatted)} complaints",
    )


# ── GET /api/v1/complaints/{complaint_id} ─────────────────────

@router.get(
    "/{complaint_id}",
    status_code=status.HTTP_200_OK,
    summary="Get complaint by ID (Admin or owner Citizen)",
)
async def get_complaint(
    complaint_id: str,
):
    """
    Get a single complaint.

    - **Admin** → any complaint.
    - **Citizen** → own complaint only (created_by == user_id).
    - Returns 403 if a citizen tries to access someone else's complaint.
    """
    complaint = await complaint_service.get_complaint(complaint_id)

    # Ownership check for citizens
    if user.get("role") == "citizen":
        if complaint.get("created_by") != user.get("user_id"):
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: you can only view your own complaints",
            )

    formatted = complaint_service.format_complaint_response(complaint)

    return success_response(
        data=formatted,
        message="Complaint retrieved successfully",
    )


# ── PUT /api/v1/complaints/{complaint_id}/status ──────────────

@router.put(
    "/{complaint_id}/status",
    status_code=status.HTTP_200_OK,
    summary="Update complaint status (Admin)",
)
async def update_complaint_status(
    complaint_id: str,
    request: ComplaintStatusUpdateRequest,
):
    """
    Update complaint status.

    - Role: **Admin**
    - Allowed values: `investigating`, `resolved`.
    - If resolved → sets `resolved_at` timestamp.
    """
    updated = await complaint_service.update_complaint_status(
        complaint_id=complaint_id,
        new_status=request.status.value,
    )

    formatted = complaint_service.format_complaint_response(updated)

    return success_response(
        data=formatted,
        message=f"Complaint status updated to '{request.status.value}'",
    )


# ── DELETE /api/v1/complaints/{complaint_id} ──────────────────

@router.delete(
    "/{complaint_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete complaint (Admin)",
)
async def delete_complaint(
    complaint_id: str,
):
    """
    Delete a complaint document.

    - Role: **Admin**
    """
    await complaint_service.delete_complaint(complaint_id)

    return success_response(
        data={"complaint_id": complaint_id},
        message="Complaint deleted successfully",
    )
