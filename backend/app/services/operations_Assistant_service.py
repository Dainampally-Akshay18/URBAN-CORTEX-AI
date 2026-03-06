"""
Urban Cortex AI – Operations Assistant Service
===============================================

RAG-based logic for understanding admin questions and retrieving insights.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException, status

from app.core.collections import Collections
from app.core.config import get_settings
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class OperationsAssistantService:
    """Service for AI-powered operational insights."""

    def __init__(self):
        self.settings = get_settings()
        self.bin_repo = BaseRepository(Collections.BINS)
        self.truck_repo = BaseRepository(Collections.TRUCKS)
        self.route_repo = BaseRepository(Collections.ROUTES)
        self.complaint_repo = BaseRepository(Collections.COMPLAINTS)
        
        # Switched from Groq to Sarvam AI
        self.sarvam_api_url = "https://api.sarvam.ai/v1/chat/completions"
        self.sarvam_model = "sarvam-m"  # Updated to supported model name

    # ── 1. Intent Detection ───────────────────────────────────
    # ... (existing detection logic remains the same)

    # ── 1. Intent Detection ───────────────────────────────────

    def _detect_intent(self, question: str) -> str:
        """
        Detect the operational intent of the admin question.
        Uses simple keyword matching for speed, but can be scaled to LLM-based detection.
        """
        q = question.lower()
        
        if any(w in q for w in ["overflow", "full", "urgent", "capacity", "level"]):
            return "overflow_monitoring"
        
        if any(w in q for w in ["complaint", "unresolved", "issue", "report", "citizen"]):
            return "complaint_tracking"
        
        if any(w in q for w in ["truck", "route", "fleet", "distance", "longest", "driver"]):
            return "route_analytics"
        
        if any(w in q for w in ["why", "explain", "reason", "prioritize", "prioritization"]):
            return "operational_explanation"
        
        return "general_query"

    # ── 2. Retrieval Layer ─────────────────────────────────────

    async def _retrieve_data(self, intent: str, question: str) -> Dict[str, Any]:
        """Retrieve relevant data from Firestore based on detected intent."""
        data = {}

        if intent == "overflow_monitoring" or intent == "operational_explanation":
            # Fetch bins that are urgent or overflowing
            # Note: Removed order_by to avoid composite index requirement during initial setup
            try:
                urgent_bins = self.bin_repo.list(
                    filters=[("status", "in", ["urgent", "overflow"])],
                    limit=20
                )
                # Sort in memory for better relevance without requiring composite index
                urgent_bins.sort(key=lambda x: x.get("urgency_score", 0), reverse=True)
                data["bins"] = urgent_bins[:10]
            except Exception as exc:
                logger.warning(f"Failed to fetch bins with filters: {str(exc)}. Falling back to all bins.")
                data["bins"] = self.bin_repo.list(limit=5)

        if intent == "complaint_tracking" or intent == "operational_explanation":
            # Fetch unresolved complaints
            try:
                pending_complaints = self.complaint_repo.list(
                    filters=[("status", "==", "pending")],
                    limit=20
                )
                # Sort in memory
                pending_complaints.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
                data["complaints"] = pending_complaints[:10]
            except Exception as exc:
                logger.warning(f"Failed to fetch complaints: {str(exc)}")
                data["complaints"] = []

        if intent == "route_analytics" or intent == "operational_explanation":
            # Fetch active routes and trucks
            routes = self.route_repo.list(limit=5)
            trucks = self.truck_repo.list(limit=10)
            data["routes"] = routes
            data["trucks"] = trucks

        # If a specific bin is mentioned (e.g., "Bin B102"), try to fetch it
        import re
        bin_match = re.search(r'\b[bB][\d]{3}\b', question)
        if bin_match:
            bin_id = bin_match.group(0).upper()
            specific_bin = self.bin_repo.get_by_id(bin_id)
            if specific_bin:
                data["specific_bin"] = specific_bin

        return data

    # ── 3. Context Construction ────────────────────────────────

    def _build_context(self, data: Dict[str, Any]) -> str:
        """Convert retrieved records into structured text for the LLM."""
        context_parts = []

        if "bins" in data and data["bins"]:
            context_parts.append("Bins needing attention:")
            for b in data["bins"]:
                fill = b.get("fill_level", 0)
                status = b.get("status", "unknown")
                wait = b.get("time_to_overflow_minutes")
                wait_str = f"{int(wait)}m" if wait is not None else "unknown"
                context_parts.append(f"- Bin {b.get('bin_id')}: {fill}% full ({status}) – Predicted overflow in {wait_str}")

        if "complaints" in data and data["complaints"]:
            context_parts.append("\nUnresolved complaints:")
            for c in data["complaints"]:
                context_parts.append(f"- [{c.get('type')}] {c.get('description')} (City: {c.get('city')})")

        if "routes" in data and data["routes"]:
            context_parts.append("\nActive Routes:")
            for r in data["routes"]:
                dist = r.get("total_distance", 0)
                bins_count = len(r.get("ordered_bin_ids", []))
                context_parts.append(f"- Route {r.get('route_id')[:8]}: {dist:.1f}km, {bins_count} bins")

        if "trucks" in data and data["trucks"]:
            context_parts.append("\nFleet Status:")
            for t in data["trucks"]:
                context_parts.append(f"- Truck {t.get('truck_id')}: {t.get('status')} (Load: {t.get('current_load')}%)")

        if "specific_bin" in data:
            sb = data["specific_bin"]
            context_parts.append(f"\nDetailed Status for {sb.get('bin_id')}:")
            context_parts.append(f"- Fill Level: {sb.get('fill_level')}%")
            context_parts.append(f"- Current Status: {sb.get('status')}")
            context_parts.append(f"- Urgency Score: {sb.get('urgency_score')}")

        if not context_parts:
            return "No specific operational anomalies found currently."

        return "\n".join(context_parts)

    # ── 4. LLM Integration ────────────────────────────────────

    async def _get_llm_answer(self, question: str, context: str) -> str:
        """Call Sarvam AI API to generate human-readable insights."""
        if not self.settings.sarvam_api_key or self.settings.sarvam_api_key == "sarvam_placeholder":
            logger.warning("Sarvam API key is missing. Returning fallback response.")
            return "I'm sorry, I cannot provide a detailed analysis right now because the Sarvam AI service is not configured (missing SARVAM_API_KEY)."

        system_prompt = (
            "An intelligent municipal waste operations assistant helping administrators "
            "understand operational waste management data. Use the provided context to answer "
            "the user's question clearly and concisely. If the context doesn't contain the answer, "
            "admit it rather than hallucinating. Answer in clear English."
        )

        prompt = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"

        payload = {
            "model": self.sarvam_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 512
        }

        # Sarvam AI specific header: api-subscription-key
        headers = {
            "api-subscription-key": self.settings.sarvam_api_key,
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.sarvam_api_url, headers=headers, json=payload)
                if response.status_code != 200:
                    try:
                        error_data = response.json()
                        logger.error(f"Sarvam AI error ({response.status_code}): {error_data}")
                        return f"AI Service error: {error_data.get('error', {}).get('message', 'Unknown error')}"
                    except:
                        logger.error(f"Sarvam AI error ({response.status_code}): {response.text}")
                        return f"AI Service error ({response.status_code}): {response.text[:200]}"
                
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            logger.error(f"Sarvam AI call failed: {str(exc)}")
            return f"Error communicating with Sarvam AI service: {str(exc)}"
                

    # ── 5. Main Entry Point ───────────────────────────────────

    async def query_assistant(self, question: str) -> Dict[str, Any]:
        """Main RAG flow."""
        # 1. Detect Intent
        intent = self._detect_intent(question)
        
        # 2. Retrieve Data
        retrieved_data = await self._retrieve_data(intent, question)
        
        # 3. Build Context
        context = self._build_context(retrieved_data)
        
        # 4. Get LLM Answer
        answer = await self._get_llm_answer(question, context)
        
        return {
            "answer": answer,
            "retrieved_context": retrieved_data,
            "intent_detected": intent
        }
