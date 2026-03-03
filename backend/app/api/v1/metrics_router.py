"""
Urban Cortex AI – Metrics Router
===================================

PRD Module 8: Metrics – Admin only.
Base path: /api/v1/metrics

All endpoints enforce:
    Depends(require_role(["admin"]))
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, status

from app.core.dependencies import require_role
from app.services.metrics_service import MetricsService
from app.utils.response_formatter import error_response, success_response

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/metrics",
    tags=["Metrics"],
)

metrics_service = MetricsService()


# ── GET /api/v1/metrics/dashboard ─────────────────────────────

@router.get(
    "/dashboard",
    status_code=status.HTTP_200_OK,
    summary="Dashboard KPIs",
)
async def get_dashboard_metrics(
):
    """
    Return aggregated dashboard KPIs computed dynamically from Firestore.

    Includes: total_bins, urgent_bins, total_trucks, active_trucks,
    avg_fill_percentage, efficiency_percentage, trips_avoided.
    """
    try:
        data = await metrics_service.get_dashboard_metrics()
        return success_response(
            data=data,
            message="Dashboard metrics retrieved successfully",
        )
    except Exception as exc:
        logger.error("Dashboard metrics endpoint failed: %s", str(exc))
        return error_response(
            message="Failed to retrieve dashboard metrics",
            errors=[str(exc)],
        )


# ── GET /api/v1/metrics/fleet ─────────────────────────────────

@router.get(
    "/fleet",
    status_code=status.HTTP_200_OK,
    summary="Fleet metrics",
)
async def get_fleet_metrics(
):
    """
    Return fleet & route metrics.

    Includes: total_routes, completed_routes, route_completion_rate,
    avg_route_distance, avg_estimated_time, avg_truck_utilization.
    """
    try:
        data = await metrics_service.get_fleet_metrics()
        return success_response(
            data=data,
            message="Fleet metrics retrieved successfully",
        )
    except Exception as exc:
        logger.error("Fleet metrics endpoint failed: %s", str(exc))
        return error_response(
            message="Failed to retrieve fleet metrics",
            errors=[str(exc)],
        )


# ── GET /api/v1/metrics/bins ──────────────────────────────────

@router.get(
    "/bins",
    status_code=status.HTTP_200_OK,
    summary="Bin metrics",
)
async def get_bin_metrics(
):
    """
    Return bin distribution & prediction metrics.

    Includes: total_bins, normal_bins, urgent_bins, overflow_bins,
    avg_fill_level, bins_predicted_to_overflow_next_2_hours.
    """
    try:
        data = await metrics_service.get_bin_metrics()
        return success_response(
            data=data,
            message="Bin metrics retrieved successfully",
        )
    except Exception as exc:
        logger.error("Bin metrics endpoint failed: %s", str(exc))
        return error_response(
            message="Failed to retrieve bin metrics",
            errors=[str(exc)],
        )


# ── GET /api/v1/metrics/complaints ────────────────────────────

@router.get(
    "/complaints",
    status_code=status.HTTP_200_OK,
    summary="Complaint metrics",
)
async def get_complaint_metrics(
):
    """
    Return complaint resolution metrics.

    Includes: total_complaints, pending_complaints,
    investigating_complaints, resolved_complaints,
    resolution_rate, avg_resolution_time.
    """
    try:
        data = await metrics_service.get_complaint_metrics()
        return success_response(
            data=data,
            message="Complaint metrics retrieved successfully",
        )
    except Exception as exc:
        logger.error("Complaint metrics endpoint failed: %s", str(exc))
        return error_response(
            message="Failed to retrieve complaint metrics",
            errors=[str(exc)],
        )
