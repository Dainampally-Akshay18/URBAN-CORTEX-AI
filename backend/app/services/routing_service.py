"""
Urban Cortex AI – Routing Service
===================================

Route generation and optimization.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List

from fastapi import HTTPException, status

from app.core.collections import Collections
from app.repositories.base_repository import BaseRepository, FirestoreError
from app.utils.haversine import haversine_distance

logger = logging.getLogger(__name__)


class RoutingService:
    """Route generation service."""
    
    # ── Constants ───────────────────────────────────────────────
    
    BIN_WEIGHT = 10.0  # kg
    TRUCK_CAPACITY = 500.0  # kg
    MAX_BINS_PER_TRUCK = 50
    
    def __init__(self):
        self.route_repo = BaseRepository(Collections.ROUTES)
        self.bin_repo = BaseRepository(Collections.BINS)
        self.truck_repo = BaseRepository(Collections.TRUCKS)
    
    # ── Generate Routes ─────────────────────────────────────────
    
    async def generate_routes(self) -> List[Dict]:
        """
        Generate optimized routes for all trucks based on bin priorities.
        
        Steps:
        1. Fetch and classify bins
        2. Fetch available trucks
        3. Assign priority bins (overflow + urgent) to trucks (geo-aware)
        4. Assign normal bins to remaining capacity
        5. Create route documents and update truck statuses
        """
        # STEP 1: Fetch and Classify Bins
        all_bins = self.bin_repo.list(limit=1000)
        if not all_bins:
            logger.info("No bins found for route generation")
            return []
            
        overflow_bins = [b for b in all_bins if b.get("status") == "overflow"]
        urgent_bins = [b for b in all_bins if b.get("status") == "urgent"]
        normal_bins = [b for b in all_bins if b.get("status") == "normal"]
        
        # Combine Priority Bins
        priority_bins = overflow_bins + urgent_bins
        
        logger.info("Classified bins: overflow=%d, urgent=%d, normal=%d", 
                   len(overflow_bins), len(urgent_bins), len(normal_bins))
        
        # STEP 2: Fetch Available Trucks
        # We only assign new routes to idle trucks
        idle_trucks = self.truck_repo.list(filters=[("status", "==", "idle")])
        if not idle_trucks:
            logger.warning("No idle trucks available for route generation")
            return []
            
        logger.info("Found %d idle trucks for assignment", len(idle_trucks))
        
        # Track assignments
        truck_assignments = {t["truck_id"]: [] for t in idle_trucks}
        truck_loads = {t["truck_id"]: 0.0 for t in idle_trucks}
        assigned_bin_ids = set()
        
        # STEP 3: Process Priority Bins (Geo-based Grouping)
        remaining_priority = list(priority_bins)
        
        for truck in idle_trucks:
            t_id = truck["truck_id"]
            
            # Start with a reference point (either truck location or first bin)
            current_lat = truck.get("current_latitude")
            current_lon = truck.get("current_longitude")
            
            # If truck has no location, use the first available priority bin
            if current_lat is None and remaining_priority:
                first_bin = remaining_priority[0]
                current_lat = first_bin.get("latitude")
                current_lon = first_bin.get("longitude")
            
            while truck_loads[t_id] + self.BIN_WEIGHT <= self.TRUCK_CAPACITY and remaining_priority:
                # Find nearest priority bin
                nearest_bin = None
                nearest_dist = float('inf')
                
                for b in remaining_priority:
                    dist = haversine_distance(
                        current_lat, current_lon, 
                        b.get("latitude"), b.get("longitude")
                    )
                    if dist < nearest_dist:
                        nearest_dist = dist
                        nearest_bin = b
                
                if nearest_bin:
                    truck_assignments[t_id].append(nearest_bin)
                    truck_loads[t_id] += self.BIN_WEIGHT
                    assigned_bin_ids.add(nearest_bin.get("bin_id") or nearest_bin.get("id"))
                    
                    # Update current position for next neighbor search
                    current_lat = nearest_bin.get("latitude")
                    current_lon = nearest_bin.get("longitude")
                    remaining_priority.remove(nearest_bin)
                else:
                    break
        
        # STEP 6: Process Normal Bins (Process remaining capacity)
        remaining_normal = list(normal_bins)
        
        for t_id in truck_assignments:
            # Continue from where the truck left off
            if truck_assignments[t_id]:
                last_bin = truck_assignments[t_id][-1]
                current_lat = last_bin.get("latitude")
                current_lon = last_bin.get("longitude")
            else:
                # If truck has no path yet, use its location or first normal bin
                curr_truck = next(t for t in idle_trucks if t["truck_id"] == t_id)
                current_lat = curr_truck.get("current_latitude")
                current_lon = curr_truck.get("current_longitude")
                if current_lat is None and remaining_normal:
                    first_bin = remaining_normal[0]
                    current_lat = first_bin.get("latitude")
                    current_lon = first_bin.get("longitude")

            while truck_loads[t_id] + self.BIN_WEIGHT <= self.TRUCK_CAPACITY and remaining_normal:
                # Find nearest normal bin
                nearest_bin = None
                nearest_dist = float('inf')
                
                for b in remaining_normal:
                    dist = haversine_distance(
                        current_lat, current_lon, 
                        b.get("latitude"), b.get("longitude")
                    )
                    if dist < nearest_dist:
                        nearest_dist = dist
                        nearest_bin = b
                
                if nearest_bin:
                    truck_assignments[t_id].append(nearest_bin)
                    truck_loads[t_id] += self.BIN_WEIGHT
                    assigned_bin_ids.add(nearest_bin.get("bin_id") or nearest_bin.get("id"))
                    
                    # Update current position
                    current_lat = nearest_bin.get("latitude")
                    current_lon = nearest_bin.get("longitude")
                    remaining_normal.remove(nearest_bin)
                else:
                    break

        # STEP 10 & 11: Create Routes and Assign to Trucks
        generated_routes = []
        now = datetime.now(timezone.utc)
        
        for t_id, bins in truck_assignments.items():
            if not bins:
                continue
                
            # Use truck's city
            truck_doc = next(t for t in idle_trucks if t["truck_id"] == t_id)
            city = truck_doc.get("city", "Unknown")
            
            # Nearest Neighbor Optimization (Order the assigned bins)
            ordered_bins = self._nearest_neighbor_route(bins)
            ordered_bin_ids = [b.get("bin_id") or b.get("id") for b in ordered_bins]
            
            # Compute distance and time
            total_distance = self._calculate_total_distance(ordered_bins)
            estimated_time_minutes = (total_distance / 30.0) * 60.0
            
            # Create route document
            route_id = f"ROUTE_{str(uuid.uuid4())[:8].upper()}"
            route_data = {
                "route_id": route_id,
                "city": city,
                "truck_id": t_id,
                "ordered_bin_ids": ordered_bin_ids,
                "total_distance": round(total_distance, 2),
                "estimated_time_minutes": round(estimated_time_minutes, 1),
                "status": "generated",
                "started_at": None,
                "completed_at": None,
                "created_at": now,
            }
            
            try:
                # Store route
                self.route_repo.create(route_id, route_data)
                
                # Update Truck (Step 11 & Step 7)
                remaining_capacity = self.TRUCK_CAPACITY - truck_loads[t_id]
                truck_update = {
                    "assigned_route_id": route_id,
                    "status": "assigned",
                    "current_load": truck_loads[t_id],
                    "remaining_capacity": remaining_capacity  # STEP 7
                }
                self.truck_repo.update(t_id, truck_update)
                
                generated_routes.append(route_data)
                logger.info("Created %s for truck %s (%d bins)", route_id, t_id, len(bins))
                
            except Exception as exc:
                logger.error("Failed to finalize route for truck %s: %s", t_id, str(exc))
        
        return generated_routes

    # ── Handle Dynamic Urgent Bin (Step 8) ──────────────────────
    
    async def handle_new_urgent_bin(self, bin_id: str) -> Dict:
        """
        Handle a new urgent/overflow bin appearing while trucks are assigned.
        Step 8 Implementation.
        """
        bin_data = self.bin_repo.get_by_id(bin_id)
        if not bin_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bin {bin_id} not found")
            
        status_val = bin_data.get("status")
        if status_val not in ["urgent", "overflow"]:
            return {"message": f"Bin {bin_id} is not urgent or overflow (status: {status_val})", "added": False}

        # 1. Check if any assigned truck has remaining capacity
        active_trucks = self.truck_repo.list(
            filters=[("status", "in", ["assigned", "in_transit"])]
        )
        
        for truck in active_trucks:
            remaining = truck.get("remaining_capacity", 0.0)
            if remaining >= self.BIN_WEIGHT:
                # Add bin to that truck's route
                t_id = truck["truck_id"]
                route_id = truck["assigned_route_id"]
                
                route_doc = self.route_repo.get_by_id(route_id)
                if route_doc:
                    ordered_bin_ids = route_doc.get("ordered_bin_ids", [])
                    if bin_id not in ordered_bin_ids:
                        ordered_bin_ids.append(bin_id)
                        
                        # Re-optimize the route with the new bin
                        bin_docs = []
                        for b_id in ordered_bin_ids:
                            b_doc = self.bin_repo.get_by_id(b_id)
                            if b_doc: bin_docs.append(b_doc)
                        
                        optimized_bins = self._nearest_neighbor_route(bin_docs)
                        final_ids = [b.get("bin_id") or b.get("id") for b in optimized_bins]
                        
                        # Update route and distance
                        new_dist = self._calculate_total_distance(optimized_bins)
                        new_time = (new_dist / 30.0) * 60.0
                        
                        self.route_repo.update(route_id, {
                            "ordered_bin_ids": final_ids,
                            "total_distance": round(new_dist, 2),
                            "estimated_time_minutes": round(new_time, 1)
                        })
                        
                        # Update truck capacity
                        new_remaining = remaining - self.BIN_WEIGHT
                        self.truck_repo.update(t_id, {
                            "remaining_capacity": new_remaining,
                            "current_load": truck.get("current_load", 0.0) + self.BIN_WEIGHT
                        })
                        
                        logger.info("Dynamically added bin %s to truck %s route %s", bin_id, t_id, route_id)
                        return {"message": f"Added bin {bin_id} to truck {t_id} route {route_id}", "added": True}

        # 2. Otherwise: Create a new truck route
        new_routes = await self.generate_routes()
        if new_routes:
            return {"message": f"Created new routes to handle bin {bin_id}", "added": True, "new_routes": new_routes}
            
        return {"message": "No capacity and no idle trucks available", "added": False}

    # ── Nearest Neighbor Algorithm ─────────────────────────────
    
    def _nearest_neighbor_route(self, bins: List[Dict]) -> List[Dict]:
        """
        Order bins using nearest neighbor algorithm.
        """
        if not bins:
            return []
        if len(bins) == 1:
            return bins
        
        # Start with the bin having the highest urgency
        sorted_bins = sorted(bins, key=lambda x: x.get("urgency_score", 0), reverse=True)
        ordered = [sorted_bins[0]]
        remaining = sorted_bins[1:]
        
        while remaining:
            current_bin = ordered[-1]
            current_lat = current_bin.get("latitude")
            current_lon = current_bin.get("longitude")
            
            nearest_bin = None
            nearest_distance = float('inf')
            
            for bin_data in remaining:
                bin_lat = bin_data.get("latitude")
                bin_lon = bin_data.get("longitude")
                distance = haversine_distance(current_lat, current_lon, bin_lat, bin_lon)
                
                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest_bin = bin_data
            
            ordered.append(nearest_bin)
            remaining.remove(nearest_bin)
        return ordered
    
    # ── Calculate Total Distance ───────────────────────────────
    
    def _calculate_total_distance(self, ordered_bins: List[Dict]) -> float:
        """Calculate total distance for ordered bins."""
        if len(ordered_bins) < 2:
            return 0.0
        total_distance = 0.0
        for i in range(len(ordered_bins) - 1):
            bin1 = ordered_bins[i]
            bin2 = ordered_bins[i + 1]
            distance = haversine_distance(
                bin1.get("latitude"), bin1.get("longitude"),
                bin2.get("latitude"), bin2.get("longitude")
            )
            total_distance += distance
        return total_distance
    
    # ── Get All Routes ──────────────────────────────────────────
    
    async def get_all_routes(self, city: str = None, limit: int = 100) -> List[Dict]:
        """Get all routes with optional city filter."""
        try:
            filters = []
            if city:
                filters.append(("city", "==", city))
            routes = self.route_repo.list(
                filters=filters if filters else None,
                limit=limit,
                order_by="created_at",
                direction="DESCENDING"
            )
            return routes
        except Exception as exc:
            logger.error("Failed to fetch routes: %s", str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch routes",
            )
    
    # ── Get Route by ID ─────────────────────────────────────────
    
    async def get_route(self, route_id: str) -> Dict:
        """Get route by ID."""
        route = self.route_repo.get_by_id(route_id)
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Route {route_id} not found",
            )
        return route
    
    # ── Delete Route ────────────────────────────────────────────
    
    async def delete_route(self, route_id: str) -> bool:
        """Delete route."""
        try:
            self.route_repo.delete(route_id)
            logger.info("Route deleted: %s", route_id)
            return True
        except FirestoreError as exc:
            if "not found" in str(exc).lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Route {route_id} not found",
                )
            logger.error("Failed to delete route: %s", str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete route",
            )
    
    # ── Format Route Response ───────────────────────────────────
    
    def format_route_response(self, route_data: Dict) -> Dict:
        """Format route data for response."""
        created_at = route_data.get("created_at")
        started_at = route_data.get("started_at")
        completed_at = route_data.get("completed_at")
        
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        if isinstance(started_at, datetime):
            started_at = started_at.isoformat()
        if isinstance(completed_at, datetime):
            completed_at = completed_at.isoformat()
        
        return {
            "route_id": route_data.get("route_id") or route_data.get("id"),
            "city": route_data.get("city"),
            "truck_id": route_data.get("truck_id"),
            "ordered_bin_ids": route_data.get("ordered_bin_ids", []),
            "total_distance": route_data.get("total_distance"),
            "estimated_time_minutes": route_data.get("estimated_time_minutes"),
            "status": route_data.get("status"),
            "started_at": started_at,
            "completed_at": completed_at,
            "created_at": created_at,
        }
