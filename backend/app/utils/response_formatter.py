"""
Urban Cortex AI – Unified Response Formatter
==============================================

All API responses MUST follow the envelope format defined in the PRD:
{
    "success": true|false,
    "message": "Optional message",
    "data": {},
    "errors": null | [...]
}
"""

from __future__ import annotations

from typing import Any, Optional


def success_response(
    data: Any = None,
    message: Optional[str] = None,
) -> dict:
    """Build a success response envelope."""
    return {
        "success": True,
        "message": message,
        "data": data,
        "errors": None,
    }


def error_response(
    message: str,
    errors: Any = None,
    data: Any = None,
) -> dict:
    """Build an error response envelope."""
    return {
        "success": False,
        "message": message,
        "data": data,
        "errors": errors,
    }
