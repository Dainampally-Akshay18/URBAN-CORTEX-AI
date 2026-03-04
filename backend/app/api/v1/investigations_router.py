"""
Urban Cortex AI – Investigations Router
==========================================

CRUD endpoints for investigations linked to complaints.
Base path: /api/v1/investigations

All endpoints are open access (no auth/RBAC) for hackathon simplicity.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Query, status

from app.schemas.investigation_schema import (
    InvestigationCreateRequest,
    InvestigationStatusUpdateRequest,
)
from app.services.investigation_service import InvestigationService
from app.utils.response_formatter import success_response

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/investigations",
    tags=["Investigations"],
)

investigation_service = InvestigationService()


# ── POST /api/v1/investigations ───────────────────────────────

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create an investigation",
)
async def create_investigation(request: InvestigationCreateRequest):
    """
    Create a new investigation linked to a complaint.

    - Verifies the referenced complaint exists.
    - Generates `investigation_id`, sets `status=open`.
    - Stores document in Firestore `investigations` collection.
    """
    investigation = await investigation_service.create_investigation(
        complaint_id=request.complaint_id,
        assigned_admin=request.assigned_admin,
    )

    formatted = investigation_service.format_investigation_response(investigation)

    return success_response(
        data=formatted,
        message="Investigation created successfully",
    )


# ── GET /api/v1/investigations ────────────────────────────────

@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="List investigations",
)
async def get_investigations(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (open / closed)"),
):
    """
    Return all investigations with optional status filter.

    Example: `/api/v1/investigations?status=open`
    """
    investigations = await investigation_service.get_all_investigations(
        status_filter=status_filter,
    )

    formatted = [investigation_service.format_investigation_response(inv) for inv in investigations]

    return success_response(
        data=formatted,
        message=f"Retrieved {len(formatted)} investigations",
    )


# ── GET /api/v1/investigations/{investigation_id} ─────────────

@router.get(
    "/{investigation_id}",
    status_code=status.HTTP_200_OK,
    summary="Get investigation by ID",
)
async def get_investigation(investigation_id: str):
    """
    Return a single investigation document.

    Returns 404 if investigation not found.
    """
    investigation = await investigation_service.get_investigation(investigation_id)

    formatted = investigation_service.format_investigation_response(investigation)

    return success_response(
        data=formatted,
        message="Investigation retrieved successfully",
    )


# ── PUT /api/v1/investigations/{investigation_id}/status ──────

@router.put(
    "/{investigation_id}/status",
    status_code=status.HTTP_200_OK,
    summary="Update investigation status",
)
async def update_investigation_status(
    investigation_id: str,
    request: InvestigationStatusUpdateRequest,
):
    """
    Update investigation result and close it.

    - Saves `result`, `notes`, and sets `closed_at` timestamp.
    - If `result == new_bin_required`, response message advises admin
      to create a bin via the bins module.
    """
    updated = await investigation_service.update_investigation_status(
        investigation_id=investigation_id,
        new_status=request.status.value,
        result=request.result.value,
        notes=request.notes,
    )

    formatted = investigation_service.format_investigation_response(updated)

    # Special business rule: advise admin when a new bin is required
    if request.result.value == "new_bin_required":
        message = "Investigation updated. Admin should create a new bin using the bins module."
    else:
        message = f"Investigation status updated to '{request.status.value}'"

    return success_response(
        data=formatted,
        message=message,
    )
