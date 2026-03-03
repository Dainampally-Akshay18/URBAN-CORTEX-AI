"""
Urban Cortex AI – Bin Service
===============================

Business logic layer for bin operations.
Architecture: Routes → Services → Repositories → Firestore

This service:
  - Validates business rules
  - Coordinates repository calls
  - Prepares data for route responses
  - Contains NO Firestore-specific code
  - Contains NO HTTP/route-specific code

PRD Reference: Section 6.1, 6.2 (Overflow Prediction, Assignment Engine)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.repositories.bin_repository import BinRepository
from app.repositories.base_repository import FirestoreError
from app.schemas.bin_schema import BinCreateRequest, BinUpdateRequest

logger = logging.getLogger(__name__)


class BinService:
    """
    Service layer for bin operations.
    Encapsulates all business logic for bin management.
    """

    def __init__(self):
        self._repo = BinRepository()

    # ─── Create ────────────────────────────────────────────────

    def create_bin(self, request: BinCreateRequest) -> Dict[str, Any]:
        """
        Create a new bin in Firestore.

        Args:
            request: Validated BinCreateRequest

        Returns:
            Created bin data dict.

        Raises:
            FirestoreError: If bin_id already exists.
        """
        # Build document data from validated request
        bin_data = {
            "bin_id": request.bin_id,
            "city": request.city,
            "latitude": request.latitude,
            "longitude": request.longitude,
            "fill_level": request.fill_level,
            "status": request.status.value,
            "urgency_score": 0,               # Calculated in Phase 5
            "predicted_overflow_time": None,   # Calculated in Phase 5
        }

        # Use bin_id as the document ID
        result = self._repo.create(request.bin_id, bin_data)

        logger.info("Bin '%s' created in city '%s'", request.bin_id, request.city)
        return result

    # ─── Read ──────────────────────────────────────────────────

    def get_bin(self, bin_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single bin by ID."""
        return self._repo.get_by_id(bin_id)

    def list_bins(
        self,
        city: Optional[str] = None,
        status: Optional[str] = None,
        min_fill: Optional[int] = None,
        max_fill: Optional[int] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        List bins with optional filtering.
        PRD: GET /api/v1/bins with query params city, status, min_fill, max_fill
        """
        # Build dynamic filters
        filters = []
        if city:
            filters.append(("city", "==", city))
        if status:
            filters.append(("status", "==", status))
        if min_fill is not None:
            filters.append(("fill_level", ">=", min_fill))
        if max_fill is not None:
            filters.append(("fill_level", "<=", max_fill))

        return self._repo.list(limit=limit, filters=filters if filters else None)

    def get_urgent_bins(
        self,
        city: Optional[str] = None,
        threshold: int = 70,
    ) -> List[Dict[str, Any]]:
        """
        Get bins above urgency threshold.
        PRD: GET /api/v1/bins/urgent/list
        """
        return self._repo.get_urgent_bins(city=city, min_fill_level=threshold)

    # ─── Update ────────────────────────────────────────────────

    def update_bin(
        self,
        bin_id: str,
        request: BinUpdateRequest,
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing bin.
        Only non-None fields are updated (partial update).
        """
        update_data = request.to_update_dict()
        if not update_data:
            # Nothing to update
            return self.get_bin(bin_id)

        return self._repo.update(bin_id, update_data)

    # ─── Delete ────────────────────────────────────────────────

    def delete_bin(self, bin_id: str) -> bool:
        """Delete a bin by ID."""
        return self._repo.delete(bin_id)

    # ─── Utility ───────────────────────────────────────────────

    def bin_exists(self, bin_id: str) -> bool:
        """Check if a bin exists without fetching full data."""
        return self._repo.exists(bin_id)

    def count_bins(self, city: Optional[str] = None) -> int:
        """Count bins, optionally filtered by city."""
        filters = [("city", "==", city)] if city else None
        return self._repo.count(filters=filters)
