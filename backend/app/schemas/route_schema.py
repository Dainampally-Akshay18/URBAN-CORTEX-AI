"""
Urban Cortex AI – Route Schemas
=================================

Pydantic models for route endpoints.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


# ── Route Response ─────────────────────────────────────────────

class RouteResponse(BaseModel):
    """Route data response"""
    route_id: str
    city: str
    truck_id: Optional[str]
    ordered_bin_ids: List[str]
    total_distance: float
    estimated_time_minutes: float
    status: str  # "generated" | "in_progress" | "completed"
    started_at: Optional[str]
    completed_at: Optional[str]
    created_at: str
