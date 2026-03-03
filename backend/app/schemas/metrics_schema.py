"""
Urban Cortex AI – Metrics Response Schemas
=============================================

Pydantic models for metrics module responses.
PRD Module 8: Metrics – Admin only.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class DashboardMetrics(BaseModel):
    """GET /api/v1/metrics/dashboard response data."""

    total_bins: int = Field(..., description="Total number of bins")
    urgent_bins: int = Field(
        ..., description="Bins with status 'urgent' or 'overflow'"
    )
    total_trucks: int = Field(..., description="Total number of trucks")
    active_trucks: int = Field(
        ..., description="Trucks with status 'in_transit'"
    )
    avg_fill_percentage: float = Field(
        ..., description="Average fill_level across all bins"
    )
    efficiency_percentage: float = Field(
        ...,
        description="(completed_routes / total_routes) * 100",
    )
    trips_avoided: int = Field(
        ...,
        description="Bins collected before overflow (simple calculated metric)",
    )


class FleetMetrics(BaseModel):
    """GET /api/v1/metrics/fleet response data."""

    total_routes: int = Field(..., description="Total number of routes")
    completed_routes: int = Field(
        ..., description="Routes with status 'completed'"
    )
    route_completion_rate: float = Field(
        ..., description="(completed_routes / total_routes) * 100"
    )
    avg_route_distance: float = Field(
        ..., description="Average total_distance across all routes"
    )
    avg_estimated_time: float = Field(
        ..., description="Average estimated_time across all routes (seconds)"
    )
    avg_truck_utilization: float = Field(
        ...,
        description="Average (current_load / max_capacity) * 100 across trucks",
    )


class BinMetrics(BaseModel):
    """GET /api/v1/metrics/bins response data."""

    total_bins: int = Field(..., description="Total number of bins")
    normal_bins: int = Field(
        ..., description="Bins with status 'normal'"
    )
    urgent_bins: int = Field(
        ..., description="Bins with status 'urgent'"
    )
    overflow_bins: int = Field(
        ..., description="Bins with status 'overflow'"
    )
    avg_fill_level: float = Field(
        ..., description="Average fill_level across all bins"
    )
    bins_predicted_to_overflow_next_2_hours: int = Field(
        ...,
        description="Bins with time_to_overflow_minutes <= 120",
    )


class ComplaintMetrics(BaseModel):
    """GET /api/v1/metrics/complaints response data."""

    total_complaints: int = Field(..., description="Total number of complaints")
    pending_complaints: int = Field(
        ..., description="Complaints with status 'pending'"
    )
    investigating_complaints: int = Field(
        ..., description="Complaints with status 'investigating'"
    )
    resolved_complaints: int = Field(
        ..., description="Complaints with status 'resolved'"
    )
    resolution_rate: float = Field(
        ...,
        description="(resolved / total) * 100",
    )
    avg_resolution_time: Optional[float] = Field(
        None,
        description="Average resolution time in hours (null if no resolved complaints)",
    )
