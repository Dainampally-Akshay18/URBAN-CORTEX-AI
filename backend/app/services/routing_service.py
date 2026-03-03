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
    
    def __init__(self):
        self.route_repo = BaseRepository(Collections.ROUTES)
        self.bin_repo = BaseRepository(Collections.BINS)
    
    # ── Generate Routes ─────────────────────────────────────────
    
    async def generate_routes(self) -> List[Dict]:
        """
        Generate routes for urgent bins using nearest neighbor algorithm.
        
        Returns:
            List of generated routes
        """
        # Step 1: Fetch urgent bins
        urgent_bins = self.bin_repo.list(
            filters=[("status", "in", ["urgent", "overflow"])],
            limit=500
        )
        
        if not urgent_bins:
            logger.info("No urgent bins found for route generation")
            return []
        
        logger.info("Found %d urgent bins for route generation", len(urgent_bins))
        
        # Step 2: Group by city
        bins_by_city = {}
        for bin_data in urgent_bins:
            city = bin_data.get("city")
            if city:
                if city not in bins_by_city:
                    bins_by_city[city] = []
                bins_by_city[city].append(bin_data)
        
        # Step 3: Generate route for each city
        generated_routes = []
        
        for city, city_bins in bins_by_city.items():
            try:
                route = await self._generate_route_for_city(city, city_bins)
                generated_routes.append(route)
                logger.info("Generated route for %s with %d bins", city, len(city_bins))
            except Exception as exc:
                logger.error("Failed to generate route for %s: %s", city, str(exc))
        
        return generated_routes
    
    # ── Generate Route for City ────────────────────────────────
    
    async def _generate_route_for_city(self, city: str, bins: List[Dict]) -> Dict:
        """
        Generate optimized route for bins in a city using nearest neighbor.
        
        Args:
            city: City name
            bins: List of bin documents
            
        Returns:
            Created route document
        """
        if not bins:
            raise ValueError("No bins provided")
        
        # Step 3: Apply nearest neighbor algorithm
        ordered_bins = self._nearest_neighbor_route(bins)
        ordered_bin_ids = [b.get("bin_id") or b.get("id") for b in ordered_bins]
        
        # Step 4: Compute distance
        total_distance = self._calculate_total_distance(ordered_bins)
        estimated_time_hours = total_distance / 30.0  # 30 km/h average speed
        estimated_time_minutes = estimated_time_hours * 60.0
        
        # Step 5: Create route document
        route_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        route_data = {
            "route_id": route_id,
            "city": city,
            "ordered_bin_ids": ordered_bin_ids,
            "total_distance": total_distance,
            "estimated_time_minutes": estimated_time_minutes,
            "status": "generated",
            "created_at": now,
        }
        
        try:
            created_route = self.route_repo.create(route_id, route_data)
            logger.info(
                "Route created: %s for %s (distance: %.2f km, time: %.1f min, bins: %d)",
                route_id, city, total_distance, estimated_time_minutes, len(ordered_bin_ids)
            )
            return created_route
        except FirestoreError as exc:
            logger.error("Failed to create route: %s", str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create route",
            )
    
    # ── Nearest Neighbor Algorithm ─────────────────────────────
    
    def _nearest_neighbor_route(self, bins: List[Dict]) -> List[Dict]:
        """
        Order bins using nearest neighbor algorithm.
        
        Args:
            bins: List of bin documents
            
        Returns:
            Ordered list of bins
        """
        if not bins:
            return []
        
        if len(bins) == 1:
            return bins
        
        # Start with first bin
        ordered = [bins[0]]
        remaining = bins[1:]
        
        # Find nearest unvisited bin iteratively
        while remaining:
            current_bin = ordered[-1]
            current_lat = current_bin.get("latitude")
            current_lon = current_bin.get("longitude")
            
            # Find nearest bin
            nearest_bin = None
            nearest_distance = float('inf')
            
            for bin_data in remaining:
                bin_lat = bin_data.get("latitude")
                bin_lon = bin_data.get("longitude")
                
                distance = haversine_distance(current_lat, current_lon, bin_lat, bin_lon)
                
                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest_bin = bin_data
            
            # Add nearest bin to route
            ordered.append(nearest_bin)
            remaining.remove(nearest_bin)
        
        return ordered
    
    # ── Calculate Total Distance ───────────────────────────────
    
    def _calculate_total_distance(self, ordered_bins: List[Dict]) -> float:
        """
        Calculate total distance for ordered bins.
        
        Args:
            ordered_bins: Ordered list of bin documents
            
        Returns:
            Total distance in kilometers
        """
        if len(ordered_bins) < 2:
            return 0.0
        
        total_distance = 0.0
        
        for i in range(len(ordered_bins) - 1):
            bin1 = ordered_bins[i]
            bin2 = ordered_bins[i + 1]
            
            lat1 = bin1.get("latitude")
            lon1 = bin1.get("longitude")
            lat2 = bin2.get("latitude")
            lon2 = bin2.get("longitude")
            
            distance = haversine_distance(lat1, lon1, lat2, lon2)
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
        """
        Get route by ID.
        
        Raises:
            HTTPException: 404 if route not found
        """
        route = self.route_repo.get_by_id(route_id)
        
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Route {route_id} not found",
            )
        
        return route
    
    # ── Delete Route ────────────────────────────────────────────
    
    async def delete_route(self, route_id: str) -> bool:
        """
        Delete route.
        
        Raises:
            HTTPException: 404 if route not found
        """
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
        
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        
        return {
            "route_id": route_data.get("route_id") or route_data.get("id"),
            "city": route_data.get("city"),
            "ordered_bin_ids": route_data.get("ordered_bin_ids", []),
            "total_distance": route_data.get("total_distance"),
            "estimated_time_minutes": route_data.get("estimated_time_minutes"),
            "status": route_data.get("status"),
            "created_at": created_at,
        }
