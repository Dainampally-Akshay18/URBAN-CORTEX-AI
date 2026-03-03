"""
Urban Cortex AI – FastAPI Application Entry Point
===================================================

Phase 2: Full FastAPI bootstrapping with:
  - App factory pattern
  - Lifespan (startup/shutdown) hooks
  - CORS middleware
  - Firebase/Firestore initialization
  - Logging configuration
  - /health endpoint (API status)
  - /firestore-health endpoint (Firestore connectivity)

No business logic. Routers will be added in later phases.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings, validate_settings_on_startup
from app.core.firebase import check_firestore_health, get_firestore_client
from app.core.logging_config import setup_logging
from app.utils.response_formatter import error_response, success_response

logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ──────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler – runs on startup and shutdown."""

    # ── Startup ──────────────────────────────────────────────
    settings = validate_settings_on_startup()
    setup_logging()

    logger.info("🚀  %s backend starting (env=%s)", settings.app_name, settings.app_env.value)

    # Initialize Firebase + Firestore
    try:
        db = get_firestore_client()
        logger.info("✅  Firestore client initialized successfully")
    except Exception as exc:
        logger.error("❌  Failed to initialize Firestore: %s", str(exc))
        # Don't crash – allow the app to start for health diagnostics
        # Firestore health endpoint will report the error

    logger.info("✅  %s backend is READY", settings.app_name)

    yield

    # ── Shutdown ─────────────────────────────────────────────
    logger.info("🛑  %s backend shutting down …", settings.app_name)


# ── Application Factory ───────────────────────────────────────

def create_app() -> FastAPI:
    """
    Application factory.
    Creates and configures the FastAPI instance.
    """
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        description="Smart Urban Waste Intelligence Platform – API",
        version="1.0.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    # ── CORS Middleware ──────────────────────────────────────
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Register health endpoints ────────────────────────────
    _register_health_endpoints(application)

    return application


# ── Health Endpoints ──────────────────────────────────────────

def _register_health_endpoints(app: FastAPI) -> None:
    """Register Phase 2 health check endpoints."""

    settings = get_settings()

    @app.get("/", tags=["root"], summary="Root health probe")
    async def root():
        """Root endpoint – basic API liveness check."""
        return success_response(
            data={
                "environment": settings.app_env.value,
                "version": "1.0.0",
            },
            message=f"{settings.app_name} API is running",
        )

    @app.get(
        "/api/v1/system/health",
        tags=["system"],
        summary="System health check",
    )
    async def health():
        """
        System health endpoint.
        Returns API status, Firestore connectivity, and IoT config.
        PRD Module 10.1: GET /api/v1/system/health (Public)
        """
        firestore_status = await check_firestore_health()
        api_healthy = True
        firestore_healthy = firestore_status.get("status") == "healthy"
        overall_healthy = api_healthy and firestore_healthy

        return success_response(
            data={
                "status": "healthy" if overall_healthy else "degraded",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": "1.0.0",
                "environment": settings.app_env.value,
                "components": {
                    "api": {
                        "status": "healthy",
                    },
                    "firestore": firestore_status,
                    "iot_simulator": {
                        "configured_url": settings.iot_simulator_base_url,
                        "sync_interval_seconds": settings.iot_sync_interval_seconds,
                        "status": "configured",  # Actual check in Phase 9
                    },
                },
            },
            message="System health check",
        )

    @app.get(
        "/api/v1/system/firestore-health",
        tags=["system"],
        summary="Firestore connectivity check",
    )
    async def firestore_health():
        """
        Dedicated Firestore health check endpoint.
        Verifies the backend can read from Firestore.
        """
        firestore_status = await check_firestore_health()
        is_healthy = firestore_status.get("status") == "healthy"

        if is_healthy:
            return success_response(
                data=firestore_status,
                message="Firestore is connected and healthy",
            )
        else:
            return error_response(
                message="Firestore connectivity check failed",
                errors=[firestore_status.get("error", "Unknown error")],
                data=firestore_status,
            )


# ── Module-level app instance (used by uvicorn) ───────────────
app = create_app()
