"""
Urban Cortex AI – Common Response Schemas
===========================================

Pydantic models for the unified API response envelope.
PRD Section: All responses MUST follow unified response format.
"""

from __future__ import annotations

from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """
    Unified API response envelope.
    Every endpoint MUST return this format.
    """
    success: bool = Field(..., description="Whether the request succeeded")
    message: Optional[str] = Field(None, description="Human-readable message")
    data: Optional[T] = Field(None, description="Response payload")
    errors: Optional[List[str]] = Field(None, description="Error details")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed",
                "data": {},
                "errors": None,
            }
        }
