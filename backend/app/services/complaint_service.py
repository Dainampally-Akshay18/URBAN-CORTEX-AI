"""
Urban Cortex AI – Complaint Service
======================================

Business logic for complaint management.
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
from app.websocket.connection_manager import manager

logger = logging.getLogger(__name__)


class ComplaintService:
    """Complaint management service."""

    def __init__(self):
        self.complaint_repo = BaseRepository(Collections.COMPLAINTS)

    # ── Generate Complaint ID ─────────────────────────────────

    @staticmethod
    def _generate_complaint_id() -> str:
        """Generate a unique complaint ID in the format CMP_XXXXXX."""
        short_uuid = uuid.uuid4().hex[:6].upper()
        return f"CMP_{short_uuid}"

    # ── Create Complaint ──────────────────────────────────────

    async def create_complaint(
        self,
        complaint_type: str,
        city: str,
        latitude: float,
        longitude: float,
        description: str,
        created_by: str,
    ) -> Dict:
        """
        Create a new complaint.

        Raises:
            HTTPException: 500 if creation fails
        """
        complaint_id = self._generate_complaint_id()
        now = datetime.now(timezone.utc)

        complaint_data = {
            "complaint_id": complaint_id,
            "type": complaint_type,
            "city": city,
            "latitude": latitude,
            "longitude": longitude,
            "description": description,
            "status": "pending",
            "created_by": created_by,
            "assigned_admin": None,
            "created_at": now,
            "resolved_at": None,
        }

        try:
            created = self.complaint_repo.create(complaint_id, complaint_data)

            logger.info(
                "Complaint created: %s (type=%s, city=%s, by=%s)",
                complaint_id, complaint_type, city, created_by,
            )

            # Emit WebSocket event
            await manager.broadcast(
                event="complaint_created",
                data={"complaint_id": complaint_id},
            )

            return created

        except FirestoreError as exc:
            logger.error("Failed to create complaint: %s", str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create complaint",
            )

    # ── Get All Complaints (Admin) ────────────────────────────

    async def get_all_complaints(
        self,
        status_filter: Optional[str] = None,
        city: Optional[str] = None,
        type_filter: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get all complaints with optional filters.

        Raises:
            HTTPException: 500 if fetch fails
        """
        try:
            filters = []

            if status_filter:
                filters.append(("status", "==", status_filter))

            if city:
                filters.append(("city", "==", city))

            if type_filter:
                filters.append(("type", "==", type_filter))

            complaints = self.complaint_repo.list(
                filters=filters if filters else None,
                limit=500,
            )

            return complaints

        except Exception as exc:
            logger.error("Failed to fetch complaints: %s", str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch complaints",
            )

    # ── Get Complaint by ID ───────────────────────────────────

    async def get_complaint(self, complaint_id: str) -> Dict:
        """
        Get a single complaint by ID.

        Raises:
            HTTPException: 404 if not found
        """
        complaint = self.complaint_repo.get_by_id(complaint_id)

        if not complaint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Complaint {complaint_id} not found",
            )

        return complaint

    # ── Update Complaint Status (Admin) ───────────────────────

    async def update_complaint_status(
        self,
        complaint_id: str,
        new_status: str,
    ) -> Dict:
        """
        Update complaint status.

        If status = resolved → set resolved_at timestamp.

        Raises:
            HTTPException: 404 if not found
            HTTPException: 500 if update fails
        """
        # Verify complaint exists
        existing = self.complaint_repo.get_by_id(complaint_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Complaint {complaint_id} not found",
            )

        update_data: Dict = {"status": new_status}

        if new_status == "resolved":
            update_data["resolved_at"] = datetime.now(timezone.utc)

        try:
            updated = self.complaint_repo.update(complaint_id, update_data)

            logger.info(
                "Complaint %s status updated to '%s'",
                complaint_id, new_status,
            )

            return updated

        except FirestoreError as exc:
            logger.error("Failed to update complaint status: %s", str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update complaint status",
            )

    # ── Delete Complaint (Admin) ──────────────────────────────

    async def delete_complaint(self, complaint_id: str) -> bool:
        """
        Delete a complaint.

        Raises:
            HTTPException: 404 if not found
            HTTPException: 500 if deletion fails
        """
        try:
            self.complaint_repo.delete(complaint_id)

            logger.info("Complaint deleted: %s", complaint_id)

            return True

        except FirestoreError as exc:
            if "not found" in str(exc).lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Complaint {complaint_id} not found",
                )
            logger.error("Failed to delete complaint: %s", str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete complaint",
            )

    # ── Assign Investigation ──────────────────────────────────────

    async def link_investigation(
        self,
        complaint_id: str,
        assigned_admin: str,
    ) -> Dict:
        """
        Update complaint fields when an investigation is created for it.
        """
        existing = self.complaint_repo.get_by_id(complaint_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Complaint {complaint_id} not found",
            )

        update_data = {
            "assigned_admin": assigned_admin,
            "status": "investigating",
            "last_updated": datetime.now(timezone.utc)
        }

        try:
            updated = self.complaint_repo.update(complaint_id, update_data)
            logger.info(
                "Complaint %s linked to investigation, admin %s",
                complaint_id, assigned_admin
            )
            return updated
        except FirestoreError as exc:
            logger.error("Failed to link complaint investigation info: %s", str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to link complaint investigation info",
            )

    # ── Format Complaint Response ─────────────────────────────

    @staticmethod
    def format_complaint_response(complaint: Dict) -> Dict:
        """Format complaint data for API response (datetime → ISO string)."""
        created_at = complaint.get("created_at")
        resolved_at = complaint.get("resolved_at")
        last_updated = complaint.get("last_updated")

        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()

        if isinstance(resolved_at, datetime):
            resolved_at = resolved_at.isoformat()
            
        if isinstance(last_updated, datetime):
            last_updated = last_updated.isoformat()

        return {
            "complaint_id": complaint.get("complaint_id") or complaint.get("id"),
            "type": complaint.get("type"),
            "city": complaint.get("city"),
            "latitude": complaint.get("latitude"),
            "longitude": complaint.get("longitude"),
            "description": complaint.get("description"),
            "status": complaint.get("status"),
            "created_by": complaint.get("created_by"),
            "assigned_admin": complaint.get("assigned_admin"),
            "created_at": created_at,
            "resolved_at": resolved_at,
            "last_updated": last_updated,
        }
