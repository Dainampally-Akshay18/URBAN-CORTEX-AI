"""
Urban Cortex AI – Metrics Service
====================================

Business logic for computing all metrics dynamically from Firestore.
PRD Module 8: Dashboard, Fleet, Bins, and Complaints metrics.

All values are computed on-the-fly – no static storage.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.collections import Collections
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class MetricsService:
    """Aggregation service – all metrics computed dynamically from Firestore."""

    def __init__(self) -> None:
        self.bin_repo = BaseRepository(Collections.BINS)
        self.truck_repo = BaseRepository(Collections.TRUCKS)
        self.route_repo = BaseRepository(Collections.ROUTES)
        self.complaint_repo = BaseRepository(Collections.COMPLAINTS)

    # ── Helpers ────────────────────────────────────────────────

    @staticmethod
    def _safe_avg(values: List[float]) -> float:
        """Return average of *values*, or 0.0 if the list is empty."""
        if not values:
            return 0.0
        return round(sum(values) / len(values), 2)

    @staticmethod
    def _pct(numerator: int, denominator: int) -> float:
        """Return percentage (0.0 when denominator is zero)."""
        if denominator == 0:
            return 0.0
        return round((numerator / denominator) * 100, 2)

    # ── 8.1 Dashboard Metrics ─────────────────────────────────

    async def get_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Aggregated KPIs for the admin dashboard.

        Returns:
            Dict containing total_bins, urgent_bins, total_trucks,
            active_trucks, avg_fill_percentage, efficiency_percentage,
            trips_avoided.
        """
        try:
            # Fetch all collections in parallel-ish fashion
            all_bins = self.bin_repo.list(limit=10_000)
            all_trucks = self.truck_repo.list(limit=10_000)
            all_routes = self.route_repo.list(limit=10_000)

            total_bins = len(all_bins)
            urgent_bins = sum(
                1
                for b in all_bins
                if b.get("status") in ("urgent", "overflow")
            )

            total_trucks = len(all_trucks)
            active_trucks = sum(
                1 for t in all_trucks if t.get("status") == "in_transit"
            )

            fill_levels = [
                float(b.get("fill_level", 0)) for b in all_bins
            ]
            avg_fill_percentage = self._safe_avg(fill_levels)

            total_routes = len(all_routes)
            completed_routes = sum(
                1 for r in all_routes if r.get("status") == "completed"
            )
            efficiency_percentage = self._pct(completed_routes, total_routes)

            # trips_avoided: bins that were collected before they hit overflow.
            # Proxy: bins whose fill_level was reset to 0 (collected) and that
            # currently have status == "normal".  Alternatively, count
            # completed routes' ordered_bin_ids length.
            trips_avoided = sum(
                len(r.get("ordered_bin_ids", []))
                for r in all_routes
                if r.get("status") == "completed"
            )

            return {
                "total_bins": total_bins,
                "urgent_bins": urgent_bins,
                "total_trucks": total_trucks,
                "active_trucks": active_trucks,
                "avg_fill_percentage": avg_fill_percentage,
                "efficiency_percentage": efficiency_percentage,
                "trips_avoided": trips_avoided,
            }

        except Exception as exc:
            logger.error("Failed to compute dashboard metrics: %s", str(exc))
            raise

    # ── 8.2 Fleet Metrics ─────────────────────────────────────

    async def get_fleet_metrics(self) -> Dict[str, Any]:
        """
        Fleet & route metrics.

        Returns:
            Dict containing total_routes, completed_routes,
            route_completion_rate, avg_route_distance,
            avg_estimated_time, avg_truck_utilization.
        """
        try:
            all_routes = self.route_repo.list(limit=10_000)
            all_trucks = self.truck_repo.list(limit=10_000)

            total_routes = len(all_routes)
            completed_routes = sum(
                1 for r in all_routes if r.get("status") == "completed"
            )
            route_completion_rate = self._pct(completed_routes, total_routes)

            distances = [
                float(r.get("total_distance", 0))
                for r in all_routes
                if r.get("total_distance") is not None
            ]
            avg_route_distance = self._safe_avg(distances)

            est_times = [
                float(r.get("estimated_time", 0))
                for r in all_routes
                if r.get("estimated_time") is not None
            ]
            avg_estimated_time = self._safe_avg(est_times)

            # Truck utilization: (current_load / max_capacity) * 100
            utilizations: List[float] = []
            for t in all_trucks:
                current_load = t.get("current_load", 0) or 0
                max_capacity = t.get("max_capacity", 0) or 0
                if max_capacity > 0:
                    utilizations.append(
                        (float(current_load) / float(max_capacity)) * 100
                    )
            avg_truck_utilization = self._safe_avg(utilizations)

            return {
                "total_routes": total_routes,
                "completed_routes": completed_routes,
                "route_completion_rate": route_completion_rate,
                "avg_route_distance": avg_route_distance,
                "avg_estimated_time": avg_estimated_time,
                "avg_truck_utilization": avg_truck_utilization,
            }

        except Exception as exc:
            logger.error("Failed to compute fleet metrics: %s", str(exc))
            raise

    # ── 8.3 Bin Metrics ───────────────────────────────────────

    async def get_bin_metrics(self) -> Dict[str, Any]:
        """
        Bin distribution & prediction metrics.

        Returns:
            Dict containing total_bins, normal_bins, urgent_bins,
            overflow_bins, avg_fill_level,
            bins_predicted_to_overflow_next_2_hours.
        """
        try:
            all_bins = self.bin_repo.list(limit=10_000)

            total_bins = len(all_bins)
            normal_bins = sum(
                1 for b in all_bins if b.get("status") == "normal"
            )
            urgent_bins = sum(
                1 for b in all_bins if b.get("status") == "urgent"
            )
            overflow_bins = sum(
                1 for b in all_bins if b.get("status") == "overflow"
            )

            fill_levels = [
                float(b.get("fill_level", 0)) for b in all_bins
            ]
            avg_fill_level = self._safe_avg(fill_levels)

            # Bins with time_to_overflow_minutes <= 120
            bins_predicted_to_overflow_next_2_hours = sum(
                1
                for b in all_bins
                if (b.get("time_to_overflow_minutes") is not None
                    and float(b.get("time_to_overflow_minutes", 999)) <= 120)
            )

            return {
                "total_bins": total_bins,
                "normal_bins": normal_bins,
                "urgent_bins": urgent_bins,
                "overflow_bins": overflow_bins,
                "avg_fill_level": avg_fill_level,
                "bins_predicted_to_overflow_next_2_hours": bins_predicted_to_overflow_next_2_hours,
            }

        except Exception as exc:
            logger.error("Failed to compute bin metrics: %s", str(exc))
            raise

    # ── 8.4 Complaint Metrics ─────────────────────────────────

    async def get_complaint_metrics(self) -> Dict[str, Any]:
        """
        Complaint resolution metrics.

        Returns:
            Dict containing total_complaints, pending_complaints,
            investigating_complaints, resolved_complaints,
            resolution_rate, avg_resolution_time.
        """
        try:
            all_complaints = self.complaint_repo.list(limit=10_000)

            total_complaints = len(all_complaints)

            if total_complaints == 0:
                return {
                    "total_complaints": 0,
                    "pending_complaints": 0,
                    "investigating_complaints": 0,
                    "resolved_complaints": 0,
                    "resolution_rate": 0.0,
                    "avg_resolution_time": None,
                }

            pending_complaints = sum(
                1 for c in all_complaints if c.get("status") == "pending"
            )
            investigating_complaints = sum(
                1
                for c in all_complaints
                if c.get("status") == "investigating"
            )
            resolved_complaints = sum(
                1 for c in all_complaints if c.get("status") == "resolved"
            )
            resolution_rate = self._pct(resolved_complaints, total_complaints)

            # Average resolution time (hours) – only for resolved complaints
            # that have both created_at and resolved_at timestamps.
            resolution_times: List[float] = []
            for c in all_complaints:
                if c.get("status") != "resolved":
                    continue
                created_at = c.get("created_at")
                resolved_at = c.get("resolved_at")
                if created_at and resolved_at:
                    try:
                        # Handle Firestore DatetimeWithNanoseconds or raw datetime
                        if isinstance(created_at, datetime) and isinstance(
                            resolved_at, datetime
                        ):
                            delta = resolved_at - created_at
                            resolution_times.append(
                                delta.total_seconds() / 3600
                            )
                    except Exception:
                        pass  # Skip malformed timestamps

            avg_resolution_time: Optional[float] = None
            if resolution_times:
                avg_resolution_time = round(
                    sum(resolution_times) / len(resolution_times), 2
                )

            return {
                "total_complaints": total_complaints,
                "pending_complaints": pending_complaints,
                "investigating_complaints": investigating_complaints,
                "resolved_complaints": resolved_complaints,
                "resolution_rate": resolution_rate,
                "avg_resolution_time": avg_resolution_time,
            }

        except Exception as exc:
            logger.error("Failed to compute complaint metrics: %s", str(exc))
            raise
