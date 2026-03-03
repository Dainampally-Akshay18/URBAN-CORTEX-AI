"""
Urban Cortex AI – Bins Router
===============================

Bin CRUD endpoints (open access).
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Query, status

from app.schemas.bin_schema import BinCreateRequest, BinUpdateRequest
from app.services.bin_service import BinService
from app.utils.response_formatter import success_response

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/bins",
    tags=["Bins"],
)

bin_service = BinService()


# ── POST /api/v1/bins ──────────────────────────────────────────

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create new bin",
)
async def create_bin(request: BinCreateRequest):
    """
    Create new bin.
    
    Calculates status and urgency_score automatically.
    """
    bin_data = await bin_service.create_bin(
        bin_id=request.bin_id,
        city=request.city,
        latitude=request.latitude,
        longitude=request.longitude,
        fill_level=request.fill_level
    )
    
    formatted = bin_service.format_bin_response(bin_data)
    
    return success_response(
        data=formatted,
        message="Bin created successfully",
    )


# ── GET /api/v1/bins ───────────────────────────────────────────

@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="Get all bins",
)
async def get_bins(
    city: Optional[str] = Query(None, description="Filter by city"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(100, ge=1, le=500, description="Max results")
):
    """
    Get all bins with optional filters.
    
    Results ordered by urgency_score (descending).
    """
    bins = await bin_service.get_all_bins(
        city=city,
        status_filter=status_filter,
        limit=limit
    )
    
    formatted_bins = [bin_service.format_bin_response(b) for b in bins]
    
    return success_response(
        data=formatted_bins,
        message=f"Retrieved {len(formatted_bins)} bins",
    )


# ── GET /api/v1/bins/{bin_id} ──────────────────────────────────

@router.get(
    "/{bin_id}",
    status_code=status.HTTP_200_OK,
    summary="Get bin by ID",
)
async def get_bin(bin_id: str):
    """Get single bin by ID."""
    bin_data = await bin_service.get_bin(bin_id)
    
    formatted = bin_service.format_bin_response(bin_data)
    
    return success_response(
        data=formatted,
        message="Bin retrieved successfully",
    )


# ── PUT /api/v1/bins/{bin_id} ──────────────────────────────────

@router.put(
    "/{bin_id}",
    status_code=status.HTTP_200_OK,
    summary="Update bin",
)
async def update_bin(bin_id: str, request: BinUpdateRequest):
    """
    Update bin.
    
    Recomputes status, urgency_score, and overflow prediction.
    """
    bin_data = await bin_service.update_bin(
        bin_id=bin_id,
        city=request.city,
        latitude=request.latitude,
        longitude=request.longitude,
        fill_level=request.fill_level,
        fill_rate=request.fill_rate
    )
    
    formatted = bin_service.format_bin_response(bin_data)
    
    return success_response(
        data=formatted,
        message="Bin updated successfully",
    )


# ── DELETE /api/v1/bins/{bin_id} ───────────────────────────────

@router.delete(
    "/{bin_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete bin",
)
async def delete_bin(bin_id: str):
    """Delete bin by ID."""
    await bin_service.delete_bin(bin_id)
    
    return success_response(
        data={"bin_id": bin_id},
        message="Bin deleted successfully",
    )
