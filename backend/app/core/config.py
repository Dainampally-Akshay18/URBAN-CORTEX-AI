"""
Urban Cortex AI – Centralized Configuration Loader
====================================================

Single source of truth for ALL application settings.
Uses pydantic-settings to:
  1. Load from .env file
  2. Override with OS environment variables
  3. Validate types and required fields at startup
  4. Fail fast with clear error messages if anything is missing

Usage:
    from app.core.config import get_settings
    settings = get_settings()
"""

from __future__ import annotations

import sys
from enum import Enum
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ── Enums ──────────────────────────────────────────────────────

class AppEnvironment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(str, Enum):
    JSON = "json"
    TEXT = "text"


# ── Settings Model ────────────────────────────────────────────

class Settings(BaseSettings):
    """
    Centralized settings for Urban Cortex AI backend.
    Every field maps to an environment variable (case-insensitive).
    """

    # ─── Application ───────────────────────────────────────────
    app_name: str = Field(
        default="UrbanCortexAI",
        description="Application display name"
    )
    app_env: AppEnvironment = Field(
        default=AppEnvironment.DEVELOPMENT,
        description="Runtime environment: development | staging | production"
    )
    debug: bool = Field(
        default=True,
        description="Enable debug mode (auto-disabled in production)"
    )

    # ─── Server ────────────────────────────────────────────────
    backend_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Port the backend listens on"
    )
    backend_host: str = Field(
        default="0.0.0.0",
        description="Host the backend binds to"
    )
    backend_cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        description="Comma-separated allowed CORS origins"
    )

    # ─── Firebase Credentials (ENV-BASED, MANDATORY) ───────────
    # These are sourced from the Firebase service account JSON
    # but stored as individual environment variables.
    # No JSON file is used at runtime.
    firebase_project_id: str = Field(
        ...,
        description="Firebase project ID"
    )
    firebase_client_email: str = Field(
        ...,
        description="Firebase service account client email"
    )
    firebase_private_key: str = Field(
        ...,
        description="Firebase service account private key (with escaped \\n)"
    )
    firebase_private_key_id: Optional[str] = Field(
        default=None,
        description="Firebase private key ID (optional)"
    )
    firebase_client_id: Optional[str] = Field(
        default=None,
        description="Firebase client ID (optional)"
    )
    firebase_auth_uri: str = Field(
        default="https://accounts.google.com/o/oauth2/auth",
        description="Firebase auth URI"
    )
    firebase_token_uri: str = Field(
        default="https://oauth2.googleapis.com/token",
        description="Firebase token URI"
    )

    # ─── IoT Simulator ─────────────────────────────────────────
    iot_simulator_base_url: str = Field(
        default="https://urban-simulator.onrender.com",
        description="Base URL of the IoT bin simulator"
    )
    iot_sync_interval_seconds: int = Field(
        default=60,
        ge=10,
        description="Polling interval for IoT simulator (seconds)"
    )
    iot_system_api_key: str = Field(
        ...,
        description="API key for IoT system-level access (POST /bins/update-from-iot)"
    )

    # ─── Rate Limiting ─────────────────────────────────────────
    rate_limit_public: int = Field(
        default=60,
        ge=1,
        description="Rate limit for public endpoints (requests/minute)"
    )
    rate_limit_citizen: int = Field(
        default=100,
        ge=1,
        description="Rate limit for citizen endpoints (requests/minute)"
    )
    rate_limit_admin: int = Field(
        default=200,
        ge=1,
        description="Rate limit for admin endpoints (requests/minute)"
    )
    rate_limit_iot: int = Field(
        default=300,
        ge=1,
        description="Rate limit for IoT ingestion endpoints (requests/minute)"
    )

    # ─── Logging ───────────────────────────────────────────────
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level"
    )
    log_format: LogFormat = Field(
        default=LogFormat.JSON,
        description="Log output format: json | text"
    )

    # ─── Pydantic Settings Config ──────────────────────────────
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",     # Ignore unknown env vars (like VITE_* from root .env)
    )

    # ─── Computed Properties ───────────────────────────────────

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == AppEnvironment.PRODUCTION

    @property
    def is_development(self) -> bool:
        return self.app_env == AppEnvironment.DEVELOPMENT

    @property
    def firebase_private_key_parsed(self) -> str:
        """Replace escaped \\n with real newlines in private key."""
        return self.firebase_private_key.replace("\\n", "\n")

    @property
    def firebase_credentials_dict(self) -> dict:
        """
        Build a Firebase service account credentials dictionary
        from individual environment variables.
        Used by firebase_admin.credentials.Certificate().
        """
        creds = {
            "type": "service_account",
            "project_id": self.firebase_project_id,
            "client_email": self.firebase_client_email,
            "private_key": self.firebase_private_key_parsed,
            "token_uri": self.firebase_token_uri,
            "auth_uri": self.firebase_auth_uri,
        }
        if self.firebase_private_key_id:
            creds["private_key_id"] = self.firebase_private_key_id
        if self.firebase_client_id:
            creds["client_id"] = self.firebase_client_id
        return creds

    # ─── Validators ────────────────────────────────────────────

    @field_validator("debug", mode="before")
    @classmethod
    def coerce_debug(cls, v):
        """Accept string 'true'/'false' in addition to bool."""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes")
        return v


# ── Singleton accessor ─────────────────────────────────────────

@lru_cache()
def get_settings() -> Settings:
    """
    Return a cached Settings instance.
    Call this from anywhere in the application.
    Raises ValidationError at startup if required env vars are missing.
    """
    return Settings()


# ── Startup validation helper ──────────────────────────────────

def validate_settings_on_startup() -> Settings:
    """
    Called once during FastAPI lifespan.
    Forces settings resolution and prints a summary.
    If any MANDATORY variable is missing, pydantic will raise immediately.
    """
    try:
        settings = get_settings()
    except Exception as exc:
        print("=" * 60, file=sys.stderr)
        print("❌  CONFIGURATION ERROR – Cannot start Urban Cortex AI", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print(str(exc), file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        sys.exit(1)

    # Print configuration summary (redact secrets)
    print("=" * 60)
    print(f"🚀  {settings.app_name} – Configuration Loaded")
    print("=" * 60)
    print(f"   Environment         : {settings.app_env.value}")
    print(f"   Debug               : {settings.debug}")
    print(f"   Host:Port           : {settings.backend_host}:{settings.backend_port}")
    print(f"   CORS Origins        : {settings.cors_origins_list}")
    print(f"   Firebase Project    : {settings.firebase_project_id}")
    print(f"   Firebase Client     : {settings.firebase_client_email}")
    print(f"   Firebase Private Key: ****REDACTED****")
    print(f"   IoT Simulator       : {settings.iot_simulator_base_url}")
    print(f"   IoT Sync Every      : {settings.iot_sync_interval_seconds}s")
    print(f"   Log Level           : {settings.log_level.value}")
    print(f"   Log Format          : {settings.log_format.value}")
    print(f"   IoT API Key         : {'*' * min(len(settings.iot_system_api_key), 20)}")
    print("=" * 60)

    return settings
