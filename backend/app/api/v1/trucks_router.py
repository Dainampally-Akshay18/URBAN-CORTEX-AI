"""
Urban Cortex AI – Trucks Router
=================================

Truck management endpoints.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.truck_schema import (
    StartTripResponse,
    TruckCreateRequest,
    TruckResponse,
    TruckUpdateRequest,
)
from app.services.truck_service import TruckService
from app.services.truck_simulation_service import TruckSimulationService
from app.utils.response_formatter import error_response, success_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trucks", tags=["trucks"])

# Service instances
truck_service = TruckService()
simulation_service = TruckSimulationService()


# ── Create Truck + Driver ───────────────────────────────────────

@router.post(
    "",
    summary="Create new truck with driver",
    status_code=status.HTTP_201_CREATED,
)
async def create_truck(request: TruckCreateRequest):
    """
    Create a new truck **and** its driver account in one step.
    
    PRD Module 4.3: POST /trucks
    Role: Admin (hackathon: open access)

    The request body now includes driver info (name, email, password).
    A driver user is automatically created in the 'users' collection.
    """
    try:
        result = await truck_service.create_truck_with_driver(
            truck_id=request.truck_id,
            city=request.city,
            max_capacity=request.max_capacity,
            name=request.name,
            email=request.email,
            password=request.password,
        )
        
        return success_response(
            data=result,
            message="Truck and driver created successfully"
        )
    
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to create truck and driver: %s", str(exc))
        return error_response(
            message="Failed to create truck and driver",
            errors=[str(exc)]
        )


# ── Get All Trucks ──────────────────────────────────────────────

@router.get(
    "",
    summary="Get all trucks",
)
async def get_trucks(
    city: Optional[str] = Query(None, description="Filter by city"),
    limit: int = Query(100, ge=1, le=500)
):
    """
    Get all trucks with optional city filter.
    
    PRD Module 4.1: GET /trucks
    Role: Admin (hackathon: open access)
    """
    try:
        trucks = await truck_service.get_all_trucks(city=city, limit=limit)
        
        formatted_trucks = [
            truck_service.format_truck_response(truck)
            for truck in trucks
        ]
        
        return success_response(
            data=formatted_trucks,
            message=f"Retrieved {len(formatted_trucks)} trucks"
        )
    
    except Exception as exc:
        logger.error("Failed to fetch trucks: %s", str(exc))
        return error_response(
            message="Failed to fetch trucks",
            errors=[str(exc)]
        )


# ── Get Truck by ID ─────────────────────────────────────────────

@router.get(
    "/{truck_id}",
    summary="Get truck by ID",
)
async def get_truck(truck_id: str):
    """
    Get truck by ID.
    
    PRD Module 4.2: GET /trucks/{id}
    Role: Admin, Driver (own only) (hackathon: open access)
    """
    try:
        truck = await truck_service.get_truck(truck_id)
        formatted = truck_service.format_truck_response(truck)
        
        return success_response(
            data=formatted,
            message=f"Truck {truck_id} retrieved"
        )
    
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to fetch truck: %s", str(exc))
        return error_response(
            message="Failed to fetch truck",
            errors=[str(exc)]
        )


# ── Update Truck ────────────────────────────────────────────────

@router.put(
    "/{truck_id}",
    summary="Update truck",
)
async def update_truck(truck_id: str, request: TruckUpdateRequest):
    """
    Update truck information.
    
    PRD Module 4.4: PUT /trucks/{id}
    Role: Admin (hackathon: open access)
    """
    try:
        truck = await truck_service.update_truck(
            truck_id=truck_id,
            max_capacity=request.max_capacity,
            assigned_route_id=request.assigned_route_id,
            driver_id=request.driver_id
        )
        
        formatted = truck_service.format_truck_response(truck)
        
        return success_response(
            data=formatted,
            message=f"Truck {truck_id} updated successfully"
        )
    
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to update truck: %s", str(exc))
        return error_response(
            message="Failed to update truck",
            errors=[str(exc)]
        )


# ── Delete Truck ────────────────────────────────────────────────

@router.delete(
    "/{truck_id}",
    summary="Delete truck",
)
async def delete_truck(truck_id: str):
    """
    Delete truck.
    
    PRD Module 4.5: DELETE /trucks/{id}
    Role: Admin (hackathon: open access)
    """
    try:
        await truck_service.delete_truck(truck_id)
        
        return success_response(
            data={"truck_id": truck_id},
            message=f"Truck {truck_id} deleted successfully"
        )
    
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to delete truck: %s", str(exc))
        return error_response(
            message="Failed to delete truck",
            errors=[str(exc)]
        )


# ── Assign Route to Truck ───────────────────────────────────────

@router.post(
    "/{truck_id}/assign-route/{route_id}",
    summary="Assign route to truck",
)
async def assign_route(truck_id: str, route_id: str):
    """
    Assign a route to a truck.
    
    Custom endpoint for hackathon convenience.
    """
    try:
        truck = await truck_service.assign_route(truck_id, route_id)
        formatted = truck_service.format_truck_response(truck)
        
        return success_response(
            data=formatted,
            message=f"Route {route_id} assigned to truck {truck_id}"
        )
    
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to assign route: %s", str(exc))
        return error_response(
            message="Failed to assign route",
            errors=[str(exc)]
        )


# ── Start Trip ──────────────────────────────────────────────────

@router.post(
    "/{truck_id}/start",
    summary="Start trip simulation",
)
async def start_trip(truck_id: str):
    """
    Start trip simulation for a truck.
    
    PRD Module 4.7: POST /trucks/{id}/start
    Role: Driver (own truck only) (hackathon: open access)
    
    Behavior:
    1. Fetch truck and assigned route
    2. Validate route status == "generated"
    3. Update route.status = "in_progress"
    4. Update truck.status = "in_transit"
    5. Start async simulation process
    6. Return immediately (non-blocking)
    
    Simulation:
    - For each bin in route:
      - Move truck to bin location
      - Update truck coordinates in Firestore
      - Broadcast truck_location_update via WebSocket
      - Collect bin (reset fill_level to 0)
      - Broadcast bin_collected via WebSocket
      - Broadcast route_progress via WebSocket
    - After all bins:
      - Mark route as completed
      - Reset truck to idle
      - Broadcast route_completed via WebSocket
    """
    try:
        result = await simulation_service.start_trip(truck_id)
        
        return success_response(
            data=result,
            message=result["message"]
        )
    
    except ValueError as exc:
        logger.warning("Start trip validation failed: %s", str(exc))
        return error_response(
            message=str(exc),
            errors=[str(exc)]
        )
    except Exception as exc:
        logger.error("Failed to start trip: %s", str(exc))
        return error_response(
            message="Failed to start trip",
            errors=[str(exc)]
        )
