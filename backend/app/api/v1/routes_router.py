"""
Urban Cortex AI – Routes Router
=================================

Route generation and management endpoints.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Query, status

from app.services.routing_service import RoutingService
from app.utils.response_formatter import success_response

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/routes",
    tags=["Routes"],
)

routing_service = RoutingService()


# ── POST /api/v1/routes/generate ──────────────────────────────

@router.post(
    "/generate",
    status_code=status.HTTP_201_CREATED,
    summary="Generate routes for urgent bins",
)
async def generate_routes():
    """
    Generate optimized routes for urgent bins.
    
    - Fetches bins with status 'urgent' or 'overflow'
    - Groups by city
    - Applies nearest neighbor algorithm
    - Calculates distance and time
    - Stores routes in Firestore
    """
    routes = await routing_service.generate_routes()
    
    if not routes:
        return success_response(
            data=[],
            message="No urgent bins found",
        )
    
    formatted_routes = [routing_service.format_route_response(r) for r in routes]
    
    return success_response(
        data=formatted_routes,
        message=f"Generated {len(formatted_routes)} routes",
    )


# ── GET /api/v1/routes ─────────────────────────────────────────

@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="Get all routes",
)
async def get_routes(
    city: Optional[str] = Query(None, description="Filter by city"),
    limit: int = Query(100, ge=1, le=500, description="Max results")
):
    """Get all routes with optional filters."""
    routes = await routing_service.get_all_routes(city=city, limit=limit)
    
    formatted_routes = [routing_service.format_route_response(r) for r in routes]
    
    return success_response(
        data=formatted_routes,
        message=f"Retrieved {len(formatted_routes)} routes",
    )


# ── GET /api/v1/routes/{route_id} ─────────────────────────────

@router.get(
    "/{route_id}",
    status_code=status.HTTP_200_OK,
    summary="Get route by ID",
)
async def get_route(route_id: str):
    """Get single route by ID."""
    route = await routing_service.get_route(route_id)
    
    formatted = routing_service.format_route_response(route)
    
    return success_response(
        data=formatted,
        message="Route retrieved successfully",
    )


# ── POST /api/v1/routes/assign-urgent-bin/{bin_id} ───────────

@router.post(
    "/assign-urgent-bin/{bin_id}",
    status_code=status.HTTP_200_OK,
    summary="Handle new urgent bin dynamically",
)
async def assign_urgent_bin(bin_id: str):
    """
    Handle a new urgent or overflow bin appearing.
    
    - Checks for existing trucks with remaining capacity.
    - Adds bin to route if capacity exists.
    - Otherwise triggers new route generation for idle trucks.
    """
    result = await routing_service.handle_new_urgent_bin(bin_id)
    
    return success_response(
        data=result,
        message=result.get("message", "Processed urgent bin"),
    )


# ── DELETE /api/v1/routes/{route_id} ──────────────────────────


@router.delete(
    "/{route_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete route",
)
async def delete_route(route_id: str):
    """Delete route by ID."""
    await routing_service.delete_route(route_id)
    
    return success_response(
        data={"route_id": route_id},
        message="Route deleted successfully",
    )
