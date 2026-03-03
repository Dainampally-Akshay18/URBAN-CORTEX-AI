"""
Urban Cortex AI – Truck Schemas
=================================

Pydantic models for truck endpoints.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# ── Truck Create Request ───────────────────────────────────────

class TruckCreateRequest(BaseModel):
    """Request to create a new truck"""
    truck_id: str = Field(..., description="Unique truck identifier")
    city: str = Field(..., description="City where truck operates")
    max_capacity: float = Field(..., description="Maximum load capacity", gt=0)
    driver_id: Optional[str] = Field(None, description="Assigned driver ID")


# ── Truck Update Request ───────────────────────────────────────

class TruckUpdateRequest(BaseModel):
    """Request to update truck"""
    max_capacity: Optional[float] = Field(None, gt=0)
    assigned_route_id: Optional[str] = None
    driver_id: Optional[str] = None


# ── Truck Response ─────────────────────────────────────────────

class TruckResponse(BaseModel):
    """Truck data response"""
    truck_id: str
    city: str
    max_capacity: float
    current_load: float
    status: str  # "idle" | "assigned" | "in_transit"
    assigned_route_id: Optional[str]
    driver_id: Optional[str]
    current_latitude: Optional[float]
    current_longitude: Optional[float]
    created_at: str


# ── Start Trip Response ────────────────────────────────────────

class StartTripResponse(BaseModel):
    """Response when starting a trip"""
    truck_id: str
    route_id: str
    status: str
    message: str
