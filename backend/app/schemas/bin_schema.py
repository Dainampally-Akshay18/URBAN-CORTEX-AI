"""
Urban Cortex AI – Bin Schemas (Pydantic Models)
=================================================

Request validation and response serialization for the bins module.

PRD Reference:
  - Section 5.1: bins collection structure
  - Section 3.1–3.8: Bins API contract
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ── Enums ──────────────────────────────────────────────────────

class BinStatus(str, Enum):
    """Valid bin statuses per PRD Section 5.1."""
    NORMAL = "normal"
    URGENT = "urgent"
    OVERFLOW = "overflow"


# ── Request Schemas ────────────────────────────────────────────

class BinCreateRequest(BaseModel):
    """
    Schema for creating a new bin.
    PRD: POST /api/v1/bins (Role: Admin)
    """
    bin_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unique bin identifier (e.g. BIN_001)",
        examples=["BIN_001"],
    )
    city: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="City where the bin is located",
        examples=["Hyderabad"],
    )
    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Latitude coordinate",
        examples=[17.385],
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Longitude coordinate",
        examples=[78.486],
    )
    fill_level: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Current fill level percentage (0-100)",
        examples=[0],
    )
    status: BinStatus = Field(
        default=BinStatus.NORMAL,
        description="Current bin status",
        examples=["normal"],
    )

    @field_validator("bin_id")
    @classmethod
    def validate_bin_id_format(cls, v: str) -> str:
        """Ensure bin_id is cleaned up (strip whitespace)."""
        return v.strip().upper()


class BinUpdateRequest(BaseModel):
    """
    Schema for updating a bin.
    PRD: PUT /api/v1/bins/{bin_id} (Role: Admin)
    All fields optional for partial update.
    """
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    fill_level: Optional[int] = Field(None, ge=0, le=100)
    status: Optional[BinStatus] = None
    urgency_score: Optional[int] = Field(None, ge=0, le=100)

    def to_update_dict(self) -> dict:
        """Return only non-None fields for Firestore partial update."""
        return {k: v for k, v in self.model_dump().items() if v is not None}


# ── Response Schemas ───────────────────────────────────────────

class BinResponse(BaseModel):
    """
    Schema for bin data in API responses.
    Matches Firestore document structure from PRD Section 5.1.
    """
    id: str = Field(..., description="Document ID")
    bin_id: str = Field(..., description="Bin identifier")
    city: str = Field(..., description="City name")
    latitude: float = Field(..., description="Latitude")
    longitude: float = Field(..., description="Longitude")
    fill_level: int = Field(..., description="Fill level percentage")
    status: str = Field(..., description="Bin status")
    urgency_score: Optional[int] = Field(None, description="Calculated urgency score")
    predicted_overflow_time: Optional[datetime] = Field(
        None, description="Predicted overflow timestamp"
    )
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    last_updated: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "BIN_001",
                "bin_id": "BIN_001",
                "city": "Hyderabad",
                "latitude": 17.385,
                "longitude": 78.486,
                "fill_level": 72,
                "status": "urgent",
                "urgency_score": 81,
                "predicted_overflow_time": "2025-01-15T14:30:00Z",
                "created_at": "2025-01-15T10:00:00Z",
                "last_updated": "2025-01-15T12:00:00Z",
            }
        }


class BinListResponse(BaseModel):
    """Schema for a list of bins."""
    bins: list[BinResponse] = Field(default_factory=list)
    total: int = Field(..., description="Total number of bins returned")
