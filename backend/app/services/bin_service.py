"""
Urban Cortex AI – Bin Service
===============================

Business logic for bin management.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from fastapi import HTTPException, status

from app.core.collections import Collections
from app.repositories.base_repository import BaseRepository, FirestoreError

logger = logging.getLogger(__name__)


class BinService:
    """Bin management service."""
    
    def __init__(self):
        self.bin_repo = BaseRepository(Collections.BINS)
    
    # ── Calculate Status & Urgency ─────────────────────────────
    
    def calculate_bin_metrics(
        self,
        fill_level: float,
        fill_rate: Optional[float] = None,
        time_to_overflow_minutes: Optional[float] = None
    ) -> Dict[str, any]:
        """
        Calculate status and urgency score.
        
        Rules (in priority order):
        1. fill_level >= 90: overflow
        2. time_to_overflow_minutes <= 120: urgent
        3. fill_level >= 70: urgent
        4. otherwise: normal
        
        urgency_score = fill_level
        """
        # Rule 1: Already overflowing
        if fill_level >= 90:
            status = "overflow"
        # Rule 2: Will overflow within 2 hours
        elif time_to_overflow_minutes is not None and time_to_overflow_minutes <= 120:
            status = "urgent"
        # Rule 3: High fill level
        elif fill_level >= 70:
            status = "urgent"
        # Rule 4: Normal
        else:
            status = "normal"
        
        urgency_score = fill_level
        
        return {
            "status": status,
            "urgency_score": urgency_score
        }
    
    # ── Calculate Overflow Prediction ──────────────────────────
    
    def calculate_overflow_prediction(
        self,
        fill_level: float,
        fill_rate: Optional[float]
    ) -> Dict[str, any]:
        """
        Calculate predicted overflow time.
        
        ALWAYS returns values - never null.
        
        Args:
            fill_level: Current fill level (0-100)
            fill_rate: Fill rate (% per minute)
            
        Returns:
            Dict with predicted_overflow_time and time_to_overflow_minutes
        """
        current_time = datetime.now(timezone.utc)
        
        # If no fill_rate or fill_rate is 0, overflow is imminent
        if fill_rate is None or fill_rate <= 0:
            return {
                "predicted_overflow_time": current_time,
                "time_to_overflow_minutes": 0.0
            }
        
        # Calculate time to overflow
        remaining_fill = 100 - fill_level
        
        # If already at or over capacity
        if remaining_fill <= 0:
            return {
                "predicted_overflow_time": current_time,
                "time_to_overflow_minutes": 0.0
            }
        
        time_to_overflow_minutes = remaining_fill / fill_rate
        predicted_overflow_time = current_time + timedelta(minutes=time_to_overflow_minutes)
        
        return {
            "predicted_overflow_time": predicted_overflow_time,
            "time_to_overflow_minutes": time_to_overflow_minutes
        }
    
    # ── Create Bin ──────────────────────────────────────────────
    
    async def create_bin(
        self,
        bin_id: str,
        city: str,
        latitude: float,
        longitude: float,
        fill_level: float,
        fill_rate: float = 0.0
    ) -> Dict:
        """
        Create new bin.
        
        Raises:
            HTTPException: 409 if bin already exists
            HTTPException: 500 if creation fails
        """
        # Check if bin exists
        if self.bin_repo.exists(bin_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Bin {bin_id} already exists",
            )
        
        # Calculate overflow prediction (ALWAYS computed)
        prediction = self.calculate_overflow_prediction(fill_level, fill_rate)
        
        # Calculate metrics
        metrics = self.calculate_bin_metrics(
            fill_level,
            fill_rate,
            prediction["time_to_overflow_minutes"]
        )
        
        # Create bin document
        try:
            now = datetime.now(timezone.utc)
            bin_data = {
                "bin_id": bin_id,
                "city": city,
                "latitude": latitude,
                "longitude": longitude,
                "fill_level": fill_level,
                "fill_rate": fill_rate,
                "status": metrics["status"],
                "urgency_score": metrics["urgency_score"],
                "predicted_overflow_time": prediction["predicted_overflow_time"],
                "time_to_overflow_minutes": prediction["time_to_overflow_minutes"],
                "created_at": now,
                "last_updated": now,
            }
            
            created_bin = self.bin_repo.create(bin_id, bin_data)
            
            logger.info(
                "Bin created: %s (fill: %.1f%%, rate: %.2f, status: %s, overflow in: %.1f min)",
                bin_id, fill_level, fill_rate, metrics["status"], prediction["time_to_overflow_minutes"]
            )
            
            return created_bin
            
        except FirestoreError as exc:
            logger.error("Failed to create bin: %s", str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create bin",
            )
    
    # ── Get All Bins ────────────────────────────────────────────
    
    async def get_all_bins(
        self,
        city: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get all bins with optional filters."""
        try:
            filters = []
            
            if city:
                filters.append(("city", "==", city))
            
            if status_filter:
                filters.append(("status", "==", status_filter))
            
            bins = self.bin_repo.list(
                filters=filters if filters else None,
                limit=limit,
                order_by="urgency_score",
                direction="DESCENDING"
            )
            
            return bins
            
        except Exception as exc:
            logger.error("Failed to fetch bins: %s", str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch bins",
            )
    
    # ── Get Bin by ID ───────────────────────────────────────────
    
    async def get_bin(self, bin_id: str) -> Dict:
        """
        Get bin by ID.
        
        Raises:
            HTTPException: 404 if bin not found
        """
        bin_data = self.bin_repo.get_by_id(bin_id)
        
        if not bin_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bin {bin_id} not found",
            )
        
        return bin_data
    
    # ── Update Bin ──────────────────────────────────────────────
    
    async def update_bin(
        self,
        bin_id: str,
        city: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        fill_level: Optional[float] = None,
        fill_rate: Optional[float] = None
    ) -> Dict:
        """
        Update bin and recompute predictions.
        
        Raises:
            HTTPException: 404 if bin not found
            HTTPException: 500 if update fails
        """
        # Check if bin exists
        existing_bin = self.bin_repo.get_by_id(bin_id)
        if not existing_bin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bin {bin_id} not found",
            )
        
        # Get current values
        current_fill_level = existing_bin.get("fill_level", 0)
        current_fill_rate = existing_bin.get("fill_rate", 0.0)
        
        # Build update data
        update_data = {}
        
        if city is not None:
            update_data["city"] = city
        
        if latitude is not None:
            update_data["latitude"] = latitude
        
        if longitude is not None:
            update_data["longitude"] = longitude
        
        if fill_level is not None:
            update_data["fill_level"] = fill_level
            current_fill_level = fill_level
        
        if fill_rate is not None:
            update_data["fill_rate"] = fill_rate
            current_fill_rate = fill_rate
        
        # ALWAYS recalculate prediction
        prediction = self.calculate_overflow_prediction(current_fill_level, current_fill_rate)
        metrics = self.calculate_bin_metrics(
            current_fill_level,
            current_fill_rate,
            prediction["time_to_overflow_minutes"]
        )
        
        update_data["status"] = metrics["status"]
        update_data["urgency_score"] = metrics["urgency_score"]
        update_data["predicted_overflow_time"] = prediction["predicted_overflow_time"]
        update_data["time_to_overflow_minutes"] = prediction["time_to_overflow_minutes"]
        update_data["last_updated"] = datetime.now(timezone.utc)
        
        # Update bin
        try:
            updated_bin = self.bin_repo.update(bin_id, update_data)
            
            logger.info(
                "Bin updated: %s (fill: %.1f%%, rate: %.2f, status: %s, overflow in: %.1f min)",
                bin_id, current_fill_level, current_fill_rate, metrics["status"], prediction["time_to_overflow_minutes"]
            )
            
            return updated_bin
            
        except FirestoreError as exc:
            logger.error("Failed to update bin: %s", str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update bin",
            )
    
    # ── Delete Bin ──────────────────────────────────────────────
    
    async def delete_bin(self, bin_id: str) -> bool:
        """
        Delete bin.
        
        Raises:
            HTTPException: 404 if bin not found
            HTTPException: 500 if deletion fails
        """
        try:
            self.bin_repo.delete(bin_id)
            
            logger.info("Bin deleted: %s", bin_id)
            
            return True
            
        except FirestoreError as exc:
            if "not found" in str(exc).lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Bin {bin_id} not found",
                )
            logger.error("Failed to delete bin: %s", str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete bin",
            )
    
    # ── Format Bin Response ─────────────────────────────────────
    
    def format_bin_response(self, bin_data: Dict) -> Dict:
        """Format bin data for response."""
        created_at = bin_data.get("created_at")
        last_updated = bin_data.get("last_updated")
        predicted_overflow_time = bin_data.get("predicted_overflow_time")
        
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        
        if isinstance(last_updated, datetime):
            last_updated = last_updated.isoformat()
        
        if isinstance(predicted_overflow_time, datetime):
            predicted_overflow_time = predicted_overflow_time.isoformat()
        
        return {
            "bin_id": bin_data.get("bin_id") or bin_data.get("id"),
            "city": bin_data.get("city"),
            "latitude": bin_data.get("latitude"),
            "longitude": bin_data.get("longitude"),
            "fill_level": bin_data.get("fill_level"),
            "fill_rate": bin_data.get("fill_rate"),
            "status": bin_data.get("status"),
            "urgency_score": bin_data.get("urgency_score"),
            "predicted_overflow_time": predicted_overflow_time,
            "time_to_overflow_minutes": bin_data.get("time_to_overflow_minutes"),
            "created_at": created_at,
            "last_updated": last_updated,
        }
