"""
Urban Cortex AI – Complaint Schemas
=====================================

Pydantic models for complaint endpoints.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────

class ComplaintType(str, Enum):
    """Allowed complaint types (PRD Section 5.1)."""
    overflow = "overflow"
    not_collected = "not_collected"
    new_bin_request = "new_bin_request"


class ComplaintStatus(str, Enum):
    """Allowed complaint statuses (PRD Section 5.1)."""
    pending = "pending"
    investigating = "investigating"
    resolved = "resolved"


# ── Create Complaint Request ──────────────────────────────────

class ComplaintCreateRequest(BaseModel):
    """Request body for POST /api/v1/complaints"""
    type: ComplaintType = Field(..., description="Type of complaint")
    city: str = Field(..., min_length=1, description="City name")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    description: str = Field(..., min_length=1, description="Complaint description")


# ── Update Complaint Status Request ───────────────────────────

class ComplaintStatusUpdateRequest(BaseModel):
    """Request body for PUT /api/v1/complaints/{complaint_id}/status"""
    status: ComplaintStatus = Field(
        ...,
        description="New status – must be 'investigating' or 'resolved'",
    )
