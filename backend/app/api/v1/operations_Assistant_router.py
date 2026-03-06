"""
Urban Cortex AI – Operations Assistant Router
==============================================

API endpoints for the AI Operations Assistant.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.operations_Assistant_schema import AssistantQueryRequest, AssistantQueryResponse
from app.services.operations_Assistant_service import OperationsAssistantService
from app.utils.response_formatter import success_response

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Dependency ───────────────────────────────────────────────

def get_assistant_service() -> OperationsAssistantService:
    """Dependency provider for OperationsAssistantService."""
    return OperationsAssistantService()

# ── Endpoints ────────────────────────────────────────────────

@router.post(
    "/operations-assistant/query",
    response_model=AssistantQueryResponse,
    summary="Ask a question to the AI Operations Assistant",
    description="Processes natural language questions about bins, complaints, routes, and fleet status."
)
async def query_assistant(
    request: AssistantQueryRequest,
    service: OperationsAssistantService = Depends(get_assistant_service)
):
    """
    POST /ai/operations-assistant/query
    
    1. Receives question
    2. Calls RAG service
    3. Returns insights
    """
    try:
        logger.info("AI Assistant query received: '%s'", request.question)
        
        result = await service.query_assistant(request.question)
        
        # We return the AssistantQueryResponse directly as per requirements
        # Note: success_response from utils might wrap it differently, 
        # but the prompt asks for specific schema usage.
        return AssistantQueryResponse(
            answer=result["answer"],
            retrieved_context=result["retrieved_context"],
            intent_detected=result["intent_detected"]
        )

    except Exception as exc:
        logger.error("AI Assistant query failed: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Assistant failed to process query: {str(exc)}"
        )
