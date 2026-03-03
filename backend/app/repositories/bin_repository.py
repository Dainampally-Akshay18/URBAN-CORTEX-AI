"""
Urban Cortex AI – Bin Repository
==================================

Concrete repository for the 'bins' Firestore collection.
Inherits all CRUD operations from BaseRepository and adds
bin-specific query methods.

PRD Reference: Section 5.1 – bins (Collection)

Firestore Document Structure:
{
    "bin_id": "BIN_001",
    "city": "Hyderabad",
    "latitude": 17.385,
    "longitude": 78.486,
    "fill_level": 72,
    "predicted_overflow_time": timestamp,
    "urgency_score": 81,
    "status": "normal" | "urgent" | "overflow",
    "last_updated": timestamp,
    "created_at": timestamp
}
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional

from app.core.collections import Collections
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class BinRepository(BaseRepository):
    """
    Repository for waste bin data in Firestore.
    Collection: 'bins'
    """

    def __init__(self):
        super().__init__(Collections.BINS)

    # ─── Bin-Specific Queries ──────────────────────────────────

    def get_bins_by_city(
        self,
        city: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Fetch all bins for a specific city."""
        return self.list(
            limit=limit,
            filters=[("city", "==", city)],
        )

    def get_bins_by_status(
        self,
        status: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Fetch bins filtered by status (normal, urgent, overflow)."""
        return self.list(
            limit=limit,
            filters=[("status", "==", status)],
        )

    def get_urgent_bins(
        self,
        city: Optional[str] = None,
        min_fill_level: int = 70,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Fetch bins that are at or above the urgency threshold.

        PRD Section 6.2: Urgent bins have fill_level > threshold (e.g. 70%).
        """
        filters = [("fill_level", ">=", min_fill_level)]
        if city:
            filters.append(("city", "==", city))

        return self.list(
            limit=limit,
            filters=filters,
            order_by="fill_level",
            direction="DESCENDING",
        )

    def get_bins_by_fill_range(
        self,
        min_fill: int = 0,
        max_fill: int = 100,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Fetch bins within a fill level range."""
        filters = [
            ("fill_level", ">=", min_fill),
            ("fill_level", "<=", max_fill),
        ]
        return self.list(limit=limit, filters=filters)

    def update_fill_level(
        self,
        bin_id: str,
        fill_level: int,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update the fill level of a bin.
        Optionally update the status if provided.
        """
        data: Dict[str, Any] = {"fill_level": fill_level}
        if status:
            data["status"] = status
        return self.update(bin_id, data)

    def reset_bin(self, bin_id: str) -> Dict[str, Any]:
        """
        Reset a bin after collection (fill_level → 0, status → normal).
        Called during truck simulation when a bin is collected.
        """
        return self.update(bin_id, {
            "fill_level": 0,
            "status": "normal",
        })
