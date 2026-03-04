"""
Urban Cortex AI – Investigation Schemas
==========================================

Pydantic models for investigation endpoints.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────

class InvestigationStatus(str, Enum):
    """Allowed investigation statuses (PRD Section 5.1)."""
    open = "open"
    closed = "closed"


class InvestigationResult(str, Enum):
    """Allowed investigation results (PRD Section 5.1)."""
    valid = "valid"
    invalid = "invalid"
    new_bin_required = "new_bin_required"


# ── Create Investigation Request ──────────────────────────────

class InvestigationCreateRequest(BaseModel):
    """Request body for POST /api/v1/investigations"""
    complaint_id: str = Field(..., min_length=1, description="ID of the linked complaint")
    assigned_admin: str = Field(..., min_length=1, description="Admin user ID assigned to investigate")


# ── Update Investigation Status Request ───────────────────────

class InvestigationStatusUpdateRequest(BaseModel):
    """Request body for PUT /api/v1/investigations/{investigation_id}/status"""
    status: InvestigationStatus = Field(..., description="New status – must be 'closed'")
    result: InvestigationResult = Field(..., description="Investigation result")
    notes: Optional[str] = Field(None, description="Admin notes about the investigation")
