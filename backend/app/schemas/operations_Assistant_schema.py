"""
Urban Cortex AI – Operations Assistant Schema
==============================================

Request and response models for the RAG-based AI assistant.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class AssistantQueryRequest(BaseModel):
    """Schema for incoming AI assistant questions."""
    question: str = Field(
        ..., 
        description="The natural language question from the administrator.",
        example="Which bins will overflow soon?"
    )


class AssistantQueryResponse(BaseModel):
    """Schema for AI assistant responses."""
    answer: str = Field(..., description="The AI-generated answer based on retrieved context.")
    retrieved_context: Optional[Dict[str, Any]] = Field(
        None, 
        description="The structured data retrieved from the database and used for reasoning."
    )
    intent_detected: Optional[str] = Field(
        None, 
        description="The detected operational intent of the question."
    )
