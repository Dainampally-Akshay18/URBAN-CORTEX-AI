"""
Urban Cortex AI – IoT Service
===============================

IoT simulator integration.
"""

from __future__ import annotations

import logging
from typing import Dict, List

import httpx

from app.services.bin_service import BinService

logger = logging.getLogger(__name__)

IOT_SIMULATOR_URL = "https://urban-cortex-iot-simulator-1.onrender.com/bins"


class IoTService:
    """IoT simulator integration service."""
    
    def __init__(self):
        self.bin_service = BinService()
    
    async def sync_from_iot(self) -> Dict:
        """
        Fetch bins from IoT simulator and sync to Firestore.
        
        Returns:
            Dict with sync statistics
        """
        try:
            # Fetch bins from IoT simulator
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(IOT_SIMULATOR_URL)
                response.raise_for_status()
                iot_bins = response.json()
            
            logger.info("Fetched %d bins from IoT simulator", len(iot_bins))
            
            created_count = 0
            updated_count = 0
            error_count = 0
            
            # Process each bin
            for iot_bin in iot_bins:
                try:
                    bin_id = iot_bin.get("bin_id")
                    city = iot_bin.get("city")
                    latitude = iot_bin.get("latitude")
                    longitude = iot_bin.get("longitude")
                    fill_level = iot_bin.get("fill_level")
                    fill_rate = iot_bin.get("fill_rate", 0.0)  # Default to 0.0 if missing
                    
                    if not all([bin_id, city, latitude is not None, longitude is not None, fill_level is not None]):
                        logger.warning("Skipping bin with missing fields: %s", iot_bin)
                        error_count += 1
                        continue
                    
                    # Check if bin exists
                    existing_bin = self.bin_service.bin_repo.get_by_id(bin_id)
                    
                    if existing_bin:
                        # Update existing bin
                        await self.bin_service.update_bin(
                            bin_id=bin_id,
                            city=city,
                            latitude=latitude,
                            longitude=longitude,
                            fill_level=fill_level,
                            fill_rate=fill_rate
                        )
                        updated_count += 1
                        logger.debug("Updated bin %s: fill=%.1f%%, rate=%.2f", bin_id, fill_level, fill_rate)
                    else:
                        # Create new bin
                        await self.bin_service.create_bin(
                            bin_id=bin_id,
                            city=city,
                            latitude=latitude,
                            longitude=longitude,
                            fill_level=fill_level,
                            fill_rate=fill_rate
                        )
                        created_count += 1
                        logger.debug("Created bin %s: fill=%.1f%%, rate=%.2f", bin_id, fill_level, fill_rate)
                
                except Exception as exc:
                    logger.error("Failed to process bin %s: %s", iot_bin.get("bin_id"), str(exc))
                    error_count += 1
            
            logger.info(
                "IoT sync complete: %d created, %d updated, %d errors",
                created_count,
                updated_count,
                error_count
            )
            
            return {
                "total_fetched": len(iot_bins),
                "created": created_count,
                "updated": updated_count,
                "errors": error_count
            }
            
        except httpx.HTTPError as exc:
            logger.error("Failed to fetch from IoT simulator: %s", str(exc))
            raise Exception(f"IoT simulator connection failed: {str(exc)}")
        except Exception as exc:
            logger.error("IoT sync failed: %s", str(exc))
            raise
