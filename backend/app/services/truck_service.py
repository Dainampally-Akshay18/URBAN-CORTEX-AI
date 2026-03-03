"""
Urban Cortex AI – Truck Service
=================================

Truck management and CRUD operations.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import HTTPException, status

from app.core.collections import Collections
from app.repositories.base_repository import BaseRepository, FirestoreError

logger = logging.getLogger(__name__)


class TruckService:
    """Truck management service."""
    
    def __init__(self):
        self.truck_repo = BaseRepository(Collections.TRUCKS)
        self.route_repo = BaseRepository(Collections.ROUTES)
    
    # ── Create Truck ────────────────────────────────────────────
    
    async def create_truck(
        self,
        truck_id: str,
        city: str,
        max_capacity: float,
        driver_id: Optional[str] = None
    ) -> Dict:
        """
        Create a new truck.
        
        Args:
            truck_id: Unique truck identifier
            city: City where truck operates
            max_capacity: Maximum load capacity
            driver_id: Optional assigned driver ID
            
        Returns:
            Created truck document
        """
        # Check if truck already exists
        existing = self.truck_repo.get_by_id(truck_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Truck {truck_id} already exists"
            )
        
        now = datetime.now(timezone.utc)
        
        truck_data = {
            "truck_id": truck_id,
            "city": city,
            "max_capacity": max_capacity,
            "current_load": 0.0,
            "status": "idle",
            "assigned_route_id": None,
            "driver_id": driver_id,
            "current_latitude": None,
            "current_longitude": None,
            "created_at": now,
        }
        
        try:
            created = self.truck_repo.create(truck_id, truck_data)
            logger.info("Truck created: %s in %s", truck_id, city)
            return created
        except FirestoreError as exc:
            logger.error("Failed to create truck: %s", str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create truck"
            )
    
    # ── Get All Trucks ──────────────────────────────────────────
    
    async def get_all_trucks(self, city: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get all trucks with optional city filter."""
        try:
            filters = []
            if city:
                filters.append(("city", "==", city))
            
            trucks = self.truck_repo.list(
                filters=filters if filters else None,
                limit=limit,
                order_by="created_at",
                direction="DESCENDING"
            )
            
            return trucks
        except Exception as exc:
            logger.error("Failed to fetch trucks: %s", str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch trucks"
            )
    
    # ── Get Truck by ID ─────────────────────────────────────────
    
    async def get_truck(self, truck_id: str) -> Dict:
        """
        Get truck by ID.
        
        Raises:
            HTTPException: 404 if truck not found
        """
        truck = self.truck_repo.get_by_id(truck_id)
        
        if not truck:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Truck {truck_id} not found"
            )
        
        return truck
    
    # ── Update Truck ────────────────────────────────────────────
    
    async def update_truck(
        self,
        truck_id: str,
        max_capacity: Optional[float] = None,
        assigned_route_id: Optional[str] = None,
        driver_id: Optional[str] = None,
    ) -> Dict:
        """
        Update truck information.
        
        Raises:
            HTTPException: 404 if truck not found
        """
        # Verify truck exists
        truck = await self.get_truck(truck_id)
        
        update_data = {}
        
        if max_capacity is not None:
            update_data["max_capacity"] = max_capacity
        
        if assigned_route_id is not None:
            update_data["assigned_route_id"] = assigned_route_id
            # Update status based on route assignment
            if assigned_route_id:
                update_data["status"] = "assigned"
            else:
                update_data["status"] = "idle"
        
        if driver_id is not None:
            update_data["driver_id"] = driver_id
        
        if not update_data:
            return truck
        
        try:
            updated = self.truck_repo.update(truck_id, update_data)
            logger.info("Truck updated: %s", truck_id)
            return updated
        except FirestoreError as exc:
            logger.error("Failed to update truck: %s", str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update truck"
            )
    
    # ── Delete Truck ────────────────────────────────────────────
    
    async def delete_truck(self, truck_id: str) -> bool:
        """
        Delete truck.
        
        Raises:
            HTTPException: 404 if truck not found
        """
        try:
            self.truck_repo.delete(truck_id)
            logger.info("Truck deleted: %s", truck_id)
            return True
        except FirestoreError as exc:
            if "not found" in str(exc).lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Truck {truck_id} not found"
                )
            logger.error("Failed to delete truck: %s", str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete truck"
            )
    
    # ── Assign Route to Truck ───────────────────────────────────
    
    async def assign_route(self, truck_id: str, route_id: str) -> Dict:
        """
        Assign a route to a truck.
        
        Args:
            truck_id: Truck identifier
            route_id: Route identifier
            
        Returns:
            Updated truck document
        """
        # Verify truck exists
        truck = await self.get_truck(truck_id)
        
        # Verify route exists
        route = self.route_repo.get_by_id(route_id)
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Route {route_id} not found"
            )
        
        # Update truck
        update_data = {
            "assigned_route_id": route_id,
            "status": "assigned"
        }
        
        # Update route with truck_id
        route_update = {
            "truck_id": truck_id
        }
        
        try:
            self.route_repo.update(route_id, route_update)
            updated_truck = self.truck_repo.update(truck_id, update_data)
            logger.info("Route %s assigned to truck %s", route_id, truck_id)
            return updated_truck
        except FirestoreError as exc:
            logger.error("Failed to assign route: %s", str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to assign route"
            )
    
    # ── Format Truck Response ───────────────────────────────────
    
    def format_truck_response(self, truck_data: Dict) -> Dict:
        """Format truck data for response."""
        created_at = truck_data.get("created_at")
        
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        
        return {
            "truck_id": truck_data.get("truck_id") or truck_data.get("id"),
            "city": truck_data.get("city"),
            "max_capacity": truck_data.get("max_capacity"),
            "current_load": truck_data.get("current_load", 0.0),
            "status": truck_data.get("status"),
            "assigned_route_id": truck_data.get("assigned_route_id"),
            "driver_id": truck_data.get("driver_id"),
            "current_latitude": truck_data.get("current_latitude"),
            "current_longitude": truck_data.get("current_longitude"),
            "created_at": created_at,
        }
