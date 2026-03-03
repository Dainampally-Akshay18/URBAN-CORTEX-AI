"""
Urban Cortex AI – Test Router (Phase 3 – Temporary)
=====================================================

Temporary test endpoints to validate the data access architecture:
    Route → Service → Repository → Firestore

These endpoints will be REMOVED after Phase 3 validation.

Endpoints:
  POST /api/v1/test/write        → Write a bin document to Firestore
  GET  /api/v1/test/read/{id}    → Read a bin document from Firestore
  GET  /api/v1/test/list         → List all test bins
  DEL  /api/v1/test/delete/{id}  → Delete a test bin
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from app.repositories.base_repository import FirestoreError
from app.schemas.bin_schema import BinCreateRequest, BinUpdateRequest
from app.services.bin_service import BinService
from app.utils.response_formatter import error_response, success_response

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/test",
    tags=["test (Phase 3 – temporary)"],
)

# ── Service instance ────────────────────────────────────────────
_bin_service = BinService()


# ── POST /test/write ────────────────────────────────────────────

@router.post("/write", summary="Test write – Create a bin document")
async def test_write(request: BinCreateRequest):
    """
    Write a bin document to Firestore.
    Validates the full stack: Route → Service → Repository → Firestore.
    """
    try:
        result = _bin_service.create_bin(request)

        # Serialize datetime objects for JSON
        serialized = _serialize_doc(result)

        return success_response(
            data=serialized,
            message=f"Bin '{request.bin_id}' created successfully",
        )
    except FirestoreError as exc:
        logger.warning("Test write failed: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_response(
                message=str(exc),
                errors=[f"Collection: {exc.collection}", f"Document: {exc.document_id}"],
            ),
        )
    except Exception as exc:
        logger.error("Unexpected error in test write: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                message="Internal server error",
                errors=[str(exc)],
            ),
        )


# ── GET /test/read/{bin_id} ─────────────────────────────────────

@router.get("/read/{bin_id}", summary="Test read – Fetch a bin document by ID")
async def test_read(bin_id: str):
    """
    Read a bin document from Firestore by its ID.
    Validates the full stack: Route → Service → Repository → Firestore.
    """
    try:
        result = _bin_service.get_bin(bin_id.strip().upper())

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    message=f"Bin '{bin_id}' not found",
                    errors=["Document does not exist in Firestore"],
                ),
            )

        serialized = _serialize_doc(result)

        return success_response(
            data=serialized,
            message=f"Bin '{bin_id}' retrieved successfully",
        )
    except HTTPException:
        raise
    except FirestoreError as exc:
        logger.warning("Test read failed: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                message=str(exc),
                errors=[f"Collection: {exc.collection}"],
            ),
        )
    except Exception as exc:
        logger.error("Unexpected error in test read: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                message="Internal server error",
                errors=[str(exc)],
            ),
        )


# ── GET /test/list ──────────────────────────────────────────────

@router.get("/list", summary="Test list – Fetch all bins")
async def test_list(limit: int = 10):
    """
    List bins from Firestore.
    Validates the list operation in the repository layer.
    """
    try:
        results = _bin_service.list_bins(limit=limit)
        serialized = [_serialize_doc(doc) for doc in results]

        return success_response(
            data={
                "bins": serialized,
                "total": len(serialized),
            },
            message=f"Retrieved {len(serialized)} bins",
        )
    except FirestoreError as exc:
        logger.warning("Test list failed: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                message=str(exc),
                errors=[f"Collection: {exc.collection}"],
            ),
        )


# ── DELETE /test/delete/{bin_id} ────────────────────────────────

@router.delete("/delete/{bin_id}", summary="Test delete – Remove a bin document")
async def test_delete(bin_id: str):
    """
    Delete a bin document from Firestore.
    Validates the delete operation in the repository layer.
    """
    try:
        _bin_service.delete_bin(bin_id.strip().upper())

        return success_response(
            data={"deleted_id": bin_id.strip().upper()},
            message=f"Bin '{bin_id}' deleted successfully",
        )
    except FirestoreError as exc:
        logger.warning("Test delete failed: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                message=str(exc),
                errors=[f"Collection: {exc.collection}", f"Document: {exc.document_id}"],
            ),
        )


# ── Serialization Helper ───────────────────────────────────────

def _serialize_doc(doc: dict) -> dict:
    """
    Serialize a Firestore document dict for JSON response.
    Converts datetime objects to ISO format strings.
    """
    serialized = {}
    for key, value in doc.items():
        if hasattr(value, "isoformat"):
            serialized[key] = value.isoformat()
        else:
            serialized[key] = value
    return serialized
