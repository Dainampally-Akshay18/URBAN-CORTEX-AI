"""
Urban Cortex AI – Route Schemas
=================================

Pydantic models for route endpoints.
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


# ── Route Response ─────────────────────────────────────────────

class RouteResponse(BaseModel):
    """Route data response"""
    route_id: str
    city: str
    ordered_bin_ids: List[str]
    total_distance: float
    estimated_time_minutes: float
    status: str
    created_at: str
