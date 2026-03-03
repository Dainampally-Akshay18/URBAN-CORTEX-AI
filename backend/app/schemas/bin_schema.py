"""
Urban Cortex AI – Bin Schemas
===============================

Pydantic models for bin endpoints.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# ── Create Bin Request ─────────────────────────────────────────

class BinCreateRequest(BaseModel):
    """Request body for POST /api/v1/bins"""
    bin_id: str = Field(..., min_length=1)
    city: str = Field(...)
    latitude: float = Field(...)
    longitude: float = Field(...)
    fill_level: float = Field(..., ge=0, le=100)


# ── Update Bin Request ─────────────────────────────────────────

class BinUpdateRequest(BaseModel):
    """Request body for PUT /api/v1/bins/{bin_id}"""
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    fill_level: Optional[float] = Field(None, ge=0, le=100)
    fill_rate: Optional[float] = Field(None, ge=0)


# ── Bin Response ───────────────────────────────────────────────

class BinResponse(BaseModel):
    """Bin data response"""
    bin_id: str
    city: str
    latitude: float
    longitude: float
    fill_level: float
    fill_rate: float
    status: str
    urgency_score: float
    predicted_overflow_time: str
    time_to_overflow_minutes: float
    created_at: str
    last_updated: str
