"""
Urban Cortex AI – Base Repository (Firestore Data Access Layer)
================================================================

Generic, reusable CRUD repository for Firestore collections.

Architecture:
    Routes → Services → Repositories → Firestore Client

Design principles:
  - Accept collection name dynamically via constructor
  - Handle Firestore errors with structured responses
  - Return plain dicts (Pydantic serialization is the service/route concern)
  - ZERO business logic – data access only
  - Thread-safe via Firestore client singleton

Usage:
    repo = BaseRepository("bins")
    doc = repo.get_by_id("BIN_001")
    repo.create("BIN_002", {"fill_level": 50, "city": "Hyderabad"})
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.firebase import get_firestore_client

logger = logging.getLogger(__name__)


class FirestoreError(Exception):
    """Custom exception for Firestore data access errors."""

    def __init__(self, message: str, collection: str, document_id: str | None = None):
        self.collection = collection
        self.document_id = document_id
        super().__init__(message)


class BaseRepository:
    """
    Generic Firestore repository providing standard CRUD operations.

    Subclass this for domain-specific repositories that need
    custom queries beyond basic CRUD.
    """

    def __init__(self, collection_name: str):
        """
        Args:
            collection_name: Firestore collection name.
                             Use constants from app.core.collections.
        """
        self._collection_name = collection_name
        self._db = get_firestore_client()

    # ─── Properties ────────────────────────────────────────────

    @property
    def collection_name(self) -> str:
        return self._collection_name

    @property
    def collection_ref(self):
        """Return the Firestore collection reference."""
        return self._db.collection(self._collection_name)

    # ─── CREATE ────────────────────────────────────────────────

    def create(self, document_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new document in the collection.

        Args:
            document_id: Unique document ID (e.g. "BIN_001")
            data: Document data as a dict

        Returns:
            The stored document data including metadata fields.

        Raises:
            FirestoreError: If the document already exists or write fails.
        """
        try:
            doc_ref = self.collection_ref.document(document_id)

            # Check if document already exists
            existing = doc_ref.get()
            if existing.exists:
                raise FirestoreError(
                    f"Document '{document_id}' already exists in '{self._collection_name}'",
                    collection=self._collection_name,
                    document_id=document_id,
                )

            # Add metadata timestamps
            now = datetime.now(timezone.utc)
            data_with_meta = {
                **data,
                "created_at": now,
                "last_updated": now,
            }

            doc_ref.set(data_with_meta)

            logger.info(
                "Created document '%s' in '%s'",
                document_id, self._collection_name,
            )

            return {"id": document_id, **data_with_meta}

        except FirestoreError:
            raise
        except Exception as exc:
            logger.error(
                "Failed to create document '%s' in '%s': %s",
                document_id, self._collection_name, str(exc),
            )
            raise FirestoreError(
                f"Failed to create document: {str(exc)}",
                collection=self._collection_name,
                document_id=document_id,
            ) from exc

    # ─── READ BY ID ────────────────────────────────────────────

    def get_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single document by its ID.

        Args:
            document_id: The document ID to fetch.

        Returns:
            Document data dict with 'id' field, or None if not found.
        """
        try:
            doc_ref = self.collection_ref.document(document_id)
            doc = doc_ref.get()

            if not doc.exists:
                logger.debug(
                    "Document '%s' not found in '%s'",
                    document_id, self._collection_name,
                )
                return None

            data = doc.to_dict()
            data["id"] = doc.id
            return data

        except Exception as exc:
            logger.error(
                "Failed to read document '%s' from '%s': %s",
                document_id, self._collection_name, str(exc),
            )
            raise FirestoreError(
                f"Failed to read document: {str(exc)}",
                collection=self._collection_name,
                document_id=document_id,
            ) from exc

    # ─── UPDATE ────────────────────────────────────────────────

    def update(self, document_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing document (merge mode).

        Args:
            document_id: Document ID to update.
            data: Fields to update (partial update supported).

        Returns:
            Updated document data.

        Raises:
            FirestoreError: If document doesn't exist or update fails.
        """
        try:
            doc_ref = self.collection_ref.document(document_id)

            # Verify document exists
            existing = doc_ref.get()
            if not existing.exists:
                raise FirestoreError(
                    f"Document '{document_id}' not found in '{self._collection_name}'",
                    collection=self._collection_name,
                    document_id=document_id,
                )

            # Add update timestamp
            data_with_meta = {
                **data,
                "last_updated": datetime.now(timezone.utc),
            }

            doc_ref.update(data_with_meta)

            logger.info(
                "Updated document '%s' in '%s'",
                document_id, self._collection_name,
            )

            # Return the full updated document
            updated_doc = doc_ref.get()
            result = updated_doc.to_dict()
            result["id"] = updated_doc.id
            return result

        except FirestoreError:
            raise
        except Exception as exc:
            logger.error(
                "Failed to update document '%s' in '%s': %s",
                document_id, self._collection_name, str(exc),
            )
            raise FirestoreError(
                f"Failed to update document: {str(exc)}",
                collection=self._collection_name,
                document_id=document_id,
            ) from exc

    # ─── DELETE ────────────────────────────────────────────────

    def delete(self, document_id: str) -> bool:
        """
        Delete a document by ID.

        Args:
            document_id: Document ID to delete.

        Returns:
            True if deleted successfully.

        Raises:
            FirestoreError: If document doesn't exist or delete fails.
        """
        try:
            doc_ref = self.collection_ref.document(document_id)

            # Verify document exists
            existing = doc_ref.get()
            if not existing.exists:
                raise FirestoreError(
                    f"Document '{document_id}' not found in '{self._collection_name}'",
                    collection=self._collection_name,
                    document_id=document_id,
                )

            doc_ref.delete()

            logger.info(
                "Deleted document '%s' from '%s'",
                document_id, self._collection_name,
            )

            return True

        except FirestoreError:
            raise
        except Exception as exc:
            logger.error(
                "Failed to delete document '%s' from '%s': %s",
                document_id, self._collection_name, str(exc),
            )
            raise FirestoreError(
                f"Failed to delete document: {str(exc)}",
                collection=self._collection_name,
                document_id=document_id,
            ) from exc

    # ─── LIST ──────────────────────────────────────────────────

    def list(
        self,
        limit: int = 100,
        order_by: Optional[str] = None,
        direction: str = "ASCENDING",
        filters: Optional[List[tuple]] = None,
    ) -> List[Dict[str, Any]]:
        """
        List documents from the collection with optional filtering & ordering.

        Args:
            limit: Maximum number of documents to return (default 100).
            order_by: Field name to order by (optional).
            direction: Sort direction – "ASCENDING" or "DESCENDING".
            filters: List of (field, operator, value) tuples for filtering.
                     Example: [("city", "==", "Hyderabad"), ("fill_level", ">=", 70)]

        Returns:
            List of document dicts, each with an 'id' field.
        """
        try:
            query = self.collection_ref

            # Apply filters
            if filters:
                for field, op, value in filters:
                    query = query.where(filter=FieldFilter(field, op, value))

            # Apply ordering
            if order_by:
                from google.cloud.firestore_v1 import query as fquery
                sort_dir = (
                    fquery.Query.DESCENDING
                    if direction.upper() == "DESCENDING"
                    else fquery.Query.ASCENDING
                )
                query = query.order_by(order_by, direction=sort_dir)

            # Apply limit
            query = query.limit(limit)

            # Execute
            docs = query.stream()
            results = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                results.append(data)

            logger.debug(
                "Listed %d documents from '%s'",
                len(results), self._collection_name,
            )

            return results

        except Exception as exc:
            logger.error(
                "Failed to list documents from '%s': %s",
                self._collection_name, str(exc),
            )
            raise FirestoreError(
                f"Failed to list documents: {str(exc)}",
                collection=self._collection_name,
            ) from exc

    # ─── EXISTS ────────────────────────────────────────────────

    def exists(self, document_id: str) -> bool:
        """Check if a document exists without fetching full data."""
        try:
            doc_ref = self.collection_ref.document(document_id)
            return doc_ref.get().exists
        except Exception:
            return False

    # ─── COUNT ─────────────────────────────────────────────────

    def count(self, filters: Optional[List[tuple]] = None) -> int:
        """
        Count documents in the collection, optionally filtered.

        Args:
            filters: Same format as list() filters.

        Returns:
            Number of matching documents.
        """
        try:
            query = self.collection_ref

            if filters:
                for field, op, value in filters:
                    query = query.where(filter=FieldFilter(field, op, value))

            # Use Firestore aggregation query for efficient counting
            count_query = query.count()
            results = count_query.get()

            # results is a list of aggregation results
            for result in results:
                return result[0].value

            return 0

        except Exception as exc:
            logger.error(
                "Failed to count documents in '%s': %s",
                self._collection_name, str(exc),
            )
            raise FirestoreError(
                f"Failed to count documents: {str(exc)}",
                collection=self._collection_name,
            ) from exc
