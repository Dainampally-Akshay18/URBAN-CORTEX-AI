"""
Urban Cortex AI – Truck Schemas
=================================

Pydantic models for truck endpoints.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ── Truck Create Request (with embedded driver info) ───────────

class TruckCreateRequest(BaseModel):
    """Request to create a new truck along with its driver account."""
    truck_id: str = Field(..., description="Unique truck identifier")
    city: str = Field(..., description="City where truck operates")
    max_capacity: float = Field(..., description="Maximum load capacity", gt=0)

    # Driver fields (required for auto-creation)
    name: str = Field(..., min_length=1, max_length=100, description="Driver name")
    email: EmailStr = Field(..., description="Driver email address")
    password: str = Field(..., min_length=6, max_length=100, description="Driver password")


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


# ── Truck + Driver Create Response ─────────────────────────────

class TruckDriverCreateResponse(BaseModel):
    """Response when a truck and driver are created together."""
    truck_id: str
    driver_id: str


# ── Start Trip Response ────────────────────────────────────────

class StartTripResponse(BaseModel):
    """Response when starting a trip"""
    truck_id: str
    route_id: str
    status: str
    message: str
