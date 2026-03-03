"""
Urban Cortex AI – Truck Simulation Service
============================================

Async truck route simulation with real-time updates.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict

from app.core.collections import Collections
from app.repositories.base_repository import BaseRepository
from app.websocket.connection_manager import manager

logger = logging.getLogger(__name__)


class TruckSimulationService:
    """
    Truck simulation service.
    Simulates truck movement along routes with real-time updates.
    """
    
    def __init__(self):
        self.truck_repo = BaseRepository(Collections.TRUCKS)
        self.route_repo = BaseRepository(Collections.ROUTES)
        self.bin_repo = BaseRepository(Collections.BINS)
    
    # ── Start Trip Simulation ───────────────────────────────────
    
    async def start_trip(self, truck_id: str) -> Dict:
        """
        Start trip simulation for a truck.
        
        PRD Section 6.4: Truck Simulation Engine (Async)
        
        Args:
            truck_id: Truck identifier
            
        Returns:
            Trip start confirmation
            
        Raises:
            ValueError: If truck or route not found, or route not in "generated" status
        """
        # Fetch truck
        truck = self.truck_repo.get_by_id(truck_id)
        if not truck:
            raise ValueError(f"Truck {truck_id} not found")
        
        # Get assigned route
        route_id = truck.get("assigned_route_id")
        if not route_id:
            raise ValueError(f"Truck {truck_id} has no assigned route")
        
        # Fetch route
        route = self.route_repo.get_by_id(route_id)
        if not route:
            raise ValueError(f"Route {route_id} not found")
        
        # Validate route status
        if route.get("status") != "generated":
            raise ValueError(f"Route {route_id} status is not 'generated' (current: {route.get('status')})")
        
        # Update route status
        now = datetime.now(timezone.utc)
        route_update = {
            "status": "in_progress",
            "started_at": now
        }
        self.route_repo.update(route_id, route_update)
        
        # Update truck status
        truck_update = {
            "status": "in_transit"
        }
        self.truck_repo.update(truck_id, truck_update)
        
        logger.info("Trip started: truck=%s, route=%s", truck_id, route_id)
        
        # Start async simulation (non-blocking)
        asyncio.create_task(self._simulate_route(truck_id, route_id))
        
        return {
            "truck_id": truck_id,
            "route_id": route_id,
            "status": "in_transit",
            "message": "Trip started successfully"
        }
    
    # ── Simulate Route Execution ────────────────────────────────
    
    async def _simulate_route(self, truck_id: str, route_id: str):
        """
        Simulate truck movement along route.
        
        PRD Section 6.4: For each bin:
        1. Simulate travel delay
        2. Update truck location
        3. Set bin fill_level = 0
        4. Update truck current_load
        5. Broadcast WebSocket events
        
        Args:
            truck_id: Truck identifier
            route_id: Route identifier
        """
        try:
            logger.info("Starting route simulation: truck=%s, route=%s", truck_id, route_id)
            
            # Fetch route
            route = self.route_repo.get_by_id(route_id)
            if not route:
                logger.error("Route %s not found during simulation", route_id)
                return
            
            ordered_bin_ids = route.get("ordered_bin_ids", [])
            total_bins = len(ordered_bin_ids)
            
            if total_bins == 0:
                logger.warning("Route %s has no bins", route_id)
                await self._complete_route(truck_id, route_id)
                return
            
            logger.info("Simulating %d bins for route %s", total_bins, route_id)
            
            # Process each bin
            for index, bin_id in enumerate(ordered_bin_ids):
                bins_completed = index + 1
                
                # Step 1: Move truck to bin location
                await self._move_truck_to_bin(truck_id, bin_id)
                
                # Step 2: Collect bin
                await self._collect_bin(bin_id)
                
                # Step 3: Update progress
                progress_percent = (bins_completed / total_bins) * 100
                await self._broadcast_progress(route_id, progress_percent)
                
                logger.info(
                    "Bin collected: %s (%d/%d, %.1f%%)",
                    bin_id, bins_completed, total_bins, progress_percent
                )
            
            # Step 4: Complete route
            await self._complete_route(truck_id, route_id)
            
            logger.info("Route simulation completed: truck=%s, route=%s", truck_id, route_id)
        
        except Exception as exc:
            logger.error("Route simulation failed: %s", str(exc), exc_info=True)
            # Attempt to reset truck status
            try:
                self.truck_repo.update(truck_id, {"status": "idle"})
                self.route_repo.update(route_id, {"status": "generated"})
            except Exception:
                pass
    
    # ── Move Truck to Bin ───────────────────────────────────────
    
    async def _move_truck_to_bin(self, truck_id: str, bin_id: str):
        """
        Simulate truck movement to bin location.
        
        Args:
            truck_id: Truck identifier
            bin_id: Bin identifier
        """
        # Fetch bin coordinates
        bin_data = self.bin_repo.get_by_id(bin_id)
        if not bin_data:
            logger.warning("Bin %s not found during simulation", bin_id)
            return
        
        latitude = bin_data.get("latitude")
        longitude = bin_data.get("longitude")
        
        # Update truck location
        truck_update = {
            "current_latitude": latitude,
            "current_longitude": longitude
        }
        self.truck_repo.update(truck_id, truck_update)
        
        # Broadcast truck location update
        await manager.broadcast(
            event="truck_location_update",
            data={
                "truck_id": truck_id,
                "latitude": latitude,
                "longitude": longitude
            }
        )
        
        # Simulate travel time (2-3 seconds)
        await asyncio.sleep(2.5)
    
    # ── Collect Bin ─────────────────────────────────────────────
    
    async def _collect_bin(self, bin_id: str):
        """
        Collect bin - reset fill level and recalculate predictions.
        
        PRD: When truck arrives at bin:
        - fill_level = 0
        - status = "normal"
        - urgency_score = 0
        - Recalculate predictions
        
        Args:
            bin_id: Bin identifier
        """
        # Fetch current bin data
        bin_data = self.bin_repo.get_by_id(bin_id)
        if not bin_data:
            logger.warning("Bin %s not found during collection", bin_id)
            return
        
        # Reset bin data
        now = datetime.now(timezone.utc)
        fill_rate = bin_data.get("fill_rate", 0.0)
        
        # Recalculate predictions with fill_level = 0
        if fill_rate > 0:
            time_to_overflow_minutes = 100.0 / fill_rate
            predicted_overflow_time = datetime.fromtimestamp(
                now.timestamp() + (time_to_overflow_minutes * 60),
                tz=timezone.utc
            )
        else:
            time_to_overflow_minutes = 0.0
            predicted_overflow_time = now
        
        bin_update = {
            "fill_level": 0.0,
            "status": "normal",
            "urgency_score": 0.0,
            "predicted_overflow_time": predicted_overflow_time,
            "time_to_overflow_minutes": time_to_overflow_minutes,
            "last_updated": now
        }
        
        self.bin_repo.update(bin_id, bin_update)
        
        # Broadcast bin collected event
        await manager.broadcast(
            event="bin_collected",
            data={
                "bin_id": bin_id,
                "collected_at": now.isoformat()
            }
        )
        
        logger.info("Bin collected and reset: %s", bin_id)
    
    # ── Broadcast Progress ──────────────────────────────────────
    
    async def _broadcast_progress(self, route_id: str, progress_percent: float):
        """
        Broadcast route progress update.
        
        Args:
            route_id: Route identifier
            progress_percent: Progress percentage (0-100)
        """
        await manager.broadcast(
            event="route_progress",
            data={
                "route_id": route_id,
                "progress_percent": round(progress_percent, 1)
            }
        )
    
    # ── Complete Route ──────────────────────────────────────────
    
    async def _complete_route(self, truck_id: str, route_id: str):
        """
        Mark route as completed and reset truck.
        
        Args:
            truck_id: Truck identifier
            route_id: Route identifier
        """
        now = datetime.now(timezone.utc)
        
        # Update route
        route_update = {
            "status": "completed",
            "completed_at": now
        }
        self.route_repo.update(route_id, route_update)
        
        # Update truck
        truck_update = {
            "status": "idle",
            "assigned_route_id": None,
            "current_load": 0.0
        }
        self.truck_repo.update(truck_id, truck_update)
        
        # Broadcast route completed event
        await manager.broadcast(
            event="route_completed",
            data={
                "route_id": route_id,
                "completed_at": now.isoformat()
            }
        )
        
        logger.info("Route completed: %s", route_id)
