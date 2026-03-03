"""
Urban Cortex AI – Configuration Validation Script
===================================================

Run this script to verify that all environment variables are loaded correctly.

Usage:
    cd backend
    python -m app.core.config_test

This script does NOT start the server. It only validates the config.
"""

from __future__ import annotations

import sys


def main():
    print("=" * 60)
    print("🔍  Urban Cortex AI – Environment Validation")
    print("=" * 60)

    try:
        from app.core.config import Settings

        # Force a fresh load (bypass cache)
        settings = Settings()
        print("✅  All required environment variables are present.")
        print()

        # Print full summary
        print(f"  APP_NAME                         = {settings.app_name}")
        print(f"  APP_ENV                          = {settings.app_env.value}")
        print(f"  DEBUG                            = {settings.debug}")
        print(f"  BACKEND_HOST                     = {settings.backend_host}")
        print(f"  BACKEND_PORT                     = {settings.backend_port}")
        print(f"  BACKEND_CORS_ORIGINS             = {settings.cors_origins_list}")
        print(f"  FIREBASE_PROJECT_ID              = {settings.firebase_project_id}")
        print(f"  FIREBASE_CLIENT_EMAIL            = {settings.firebase_client_email}")
        print(f"  FIREBASE_PRIVATE_KEY             = ****REDACTED****")
        print(f"  FIREBASE_PRIVATE_KEY_ID          = {settings.firebase_private_key_id or '(not set)'}")
        print(f"  FIREBASE_CLIENT_ID               = {settings.firebase_client_id or '(not set)'}")
        print(f"  IOT_SIMULATOR_BASE_URL           = {settings.iot_simulator_base_url}")
        print(f"  IOT_SYNC_INTERVAL_SECONDS        = {settings.iot_sync_interval_seconds}")
        print(f"  IOT_SYSTEM_API_KEY               = {'*' * min(len(settings.iot_system_api_key), 20)}")
        print(f"  RATE_LIMIT_PUBLIC                = {settings.rate_limit_public}")
        print(f"  RATE_LIMIT_CITIZEN               = {settings.rate_limit_citizen}")
        print(f"  RATE_LIMIT_ADMIN                 = {settings.rate_limit_admin}")
        print(f"  RATE_LIMIT_IOT                   = {settings.rate_limit_iot}")
        print(f"  LOG_LEVEL                        = {settings.log_level.value}")
        print(f"  LOG_FORMAT                       = {settings.log_format.value}")
        print()
        print("=" * 60)
        print("✅  Configuration is VALID. Ready to start server.")
        print("=" * 60)

    except Exception as exc:
        print("❌  CONFIGURATION ERROR:", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        print()
        print("Ensure you have copied .env.example → .env and filled in all values.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
