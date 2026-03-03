"""
Urban Cortex AI – Firebase Initialization
===========================================

Initializes Firebase Admin SDK using environment-based credentials.
Provides a Firestore client singleton.

Architecture decisions:
  - NO file-based JSON credentials
  - NO Firebase Storage
  - Credentials are constructed dynamically from env vars
  - Private key \\n escapes are resolved at load time
  - Firestore is the ONLY Firebase service used

Usage:
    from app.core.firebase import get_firestore_client
    db = get_firestore_client()
    doc = db.collection("bins").document("BIN_001").get()
"""

from __future__ import annotations

import logging
from functools import lru_cache

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.client import Client as FirestoreClient

from app.core.collections import Collections
from app.core.config import get_settings

logger = logging.getLogger(__name__)


# ── Firebase App Initialization ────────────────────────────────

def _initialize_firebase_app() -> firebase_admin.App:
    """
    Initialize the Firebase Admin SDK using environment-based credentials.
    This is called ONCE at startup – subsequent calls return the existing app.
    """
    # Check if already initialized
    try:
        return firebase_admin.get_app()
    except ValueError:
        pass  # Not initialized yet

    settings = get_settings()

    # Build credential from env vars (no JSON file)
    cred_dict = settings.firebase_credentials_dict
    cred = credentials.Certificate(cred_dict)

    app = firebase_admin.initialize_app(cred, {
        "projectId": settings.firebase_project_id,
    })

    logger.info(
        "✅  Firebase Admin SDK initialized (project: %s)",
        settings.firebase_project_id,
    )

    return app


# ── Firestore Client Singleton ─────────────────────────────────

@lru_cache()
def get_firestore_client() -> FirestoreClient:
    """
    Return a cached Firestore client instance.
    Initializes Firebase if not already done.
    """
    _initialize_firebase_app()
    client = firestore.client()
    logger.info("✅  Firestore client ready")
    return client


# ── Health Check Helper ────────────────────────────────────────

async def check_firestore_health() -> dict:
    """
    Verify Firestore connectivity by attempting a lightweight read.
    Returns a status dict for the health endpoint.
    """
    try:
        db = get_firestore_client()
        # Attempt to list 1 document from any collection (lightweight)
        # Using the _system_health_check collection which won't interfere
        # with real data
        db.collection(Collections.SYSTEM_HEALTH_CHECK).limit(1).get()

        return {
            "firestore": "connected",
            "project_id": get_settings().firebase_project_id,
            "status": "healthy",
        }
    except Exception as exc:
        logger.error("❌  Firestore health check failed: %s", str(exc))
        return {
            "firestore": "disconnected",
            "project_id": get_settings().firebase_project_id,
            "status": "unhealthy",
            "error": str(exc),
        }
