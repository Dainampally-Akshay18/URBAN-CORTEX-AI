"""
Urban Cortex AI – Investigation Service
==========================================

Business logic for investigation management.
All CRUD logic lives here; the router simply delegates.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import HTTPException, status

from app.core.collections import Collections
from app.repositories.base_repository import BaseRepository, FirestoreError

logger = logging.getLogger(__name__)


class InvestigationService:
    """Investigation management service."""

    def __init__(self):
        self.investigation_repo = BaseRepository(Collections.INVESTIGATIONS)
        self.complaint_repo = BaseRepository(Collections.COMPLAINTS)

    # ── Generate Investigation ID ─────────────────────────────

    @staticmethod
    def _generate_investigation_id() -> str:
        """Generate a unique investigation ID in the format INV_XXXXXX."""
        short_uuid = uuid.uuid4().hex[:6].upper()
        return f"INV_{short_uuid}"

    # ── Create Investigation ──────────────────────────────────

    async def create_investigation(
        self,
        complaint_id: str,
        assigned_admin: str,
    ) -> Dict:
        """
        Create a new investigation linked to an existing complaint.

        Raises:
            HTTPException: 404 if complaint doesn't exist
            HTTPException: 500 if creation fails
        """
        # Verify complaint exists
        complaint = self.complaint_repo.get_by_id(complaint_id)
        if not complaint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Complaint {complaint_id} not found",
            )

        investigation_id = self._generate_investigation_id()
        now = datetime.now(timezone.utc)

        investigation_data = {
            "investigation_id": investigation_id,
            "complaint_id": complaint_id,
            "assigned_admin": assigned_admin,
            "result": None,
            "status": "open",
            "notes": None,
            "created_at": now,
            "closed_at": None,
        }

        try:
            created = self.investigation_repo.create(investigation_id, investigation_data)

            logger.info(
                "Investigation created: %s (complaint=%s, admin=%s)",
                investigation_id, complaint_id, assigned_admin,
            )

            return created

        except FirestoreError as exc:
            logger.error("Failed to create investigation: %s", str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create investigation",
            )

    # ── Get All Investigations ────────────────────────────────

    async def get_all_investigations(
        self,
        status_filter: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get all investigations with optional status filter.

        Raises:
            HTTPException: 500 if fetch fails
        """
        try:
            filters = []

            if status_filter:
                filters.append(("status", "==", status_filter))

            investigations = self.investigation_repo.list(
                filters=filters if filters else None,
                limit=500,
            )

            return investigations

        except Exception as exc:
            logger.error("Failed to fetch investigations: %s", str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch investigations",
            )

    # ── Get Investigation by ID ───────────────────────────────

    async def get_investigation(self, investigation_id: str) -> Dict:
        """
        Get a single investigation by ID.

        Raises:
            HTTPException: 404 if not found
        """
        investigation = self.investigation_repo.get_by_id(investigation_id)

        if not investigation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Investigation {investigation_id} not found",
            )

        return investigation

    # ── Update Investigation Status ───────────────────────────

    async def update_investigation_status(
        self,
        investigation_id: str,
        new_status: str,
        result: str,
        notes: Optional[str] = None,
    ) -> Dict:
        """
        Update investigation status, result, and notes.

        If status = closed → set closed_at timestamp.

        Raises:
            HTTPException: 404 if not found
            HTTPException: 500 if update fails
        """
        # Verify investigation exists
        existing = self.investigation_repo.get_by_id(investigation_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Investigation {investigation_id} not found",
            )

        update_data: Dict = {
            "status": new_status,
            "result": result,
            "notes": notes,
        }

        if new_status == "closed":
            update_data["closed_at"] = datetime.now(timezone.utc)

        try:
            updated = self.investigation_repo.update(investigation_id, update_data)

            logger.info(
                "Investigation %s updated: status=%s, result=%s",
                investigation_id, new_status, result,
            )

            return updated

        except FirestoreError as exc:
            logger.error("Failed to update investigation: %s", str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update investigation",
            )

    # ── Format Investigation Response ─────────────────────────

    @staticmethod
    def format_investigation_response(investigation: Dict) -> Dict:
        """Format investigation data for API response (datetime → ISO string)."""
        created_at = investigation.get("created_at")
        closed_at = investigation.get("closed_at")

        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()

        if isinstance(closed_at, datetime):
            closed_at = closed_at.isoformat()

        return {
            "investigation_id": investigation.get("investigation_id") or investigation.get("id"),
            "complaint_id": investigation.get("complaint_id"),
            "assigned_admin": investigation.get("assigned_admin"),
            "result": investigation.get("result"),
            "status": investigation.get("status"),
            "notes": investigation.get("notes"),
            "created_at": created_at,
            "closed_at": closed_at,
        }
