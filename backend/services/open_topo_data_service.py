"""
Open Topo Data API Service
High-quality elevation data service for enhanced contour generation and topographic analysis.
Provides access to SRTM and ASTER elevation datasets with proper rate limiting.
"""

import httpx
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
from .external_api_service import BaseAPIService, APIResponse

logger = logging.getLogger(__name__)

class OpenTopoDataService(BaseAPIService):
    """Open Topo Data API Service for elevation data"""
    
    def __init__(self):
        base_url = "https://api.opentopodata.org/v1"
        super().__init__(base_url, timeout=30.0)
        self.cache_ttl = 3600  # 1 hour cache due to daily rate limits
        
        # Rate limiting for API compliance
        self.max_requests_per_second = 1
        self.max_requests_per_day = 1000
        self.max_locations_per_request = 100
        
        # Request tracking for rate limiting
        self.request_times = []
        self.daily_request_count = 0
        self.last_reset_date = datetime.now().date()
        
        # Available datasets
        self.datasets = {
            "srtm30m": {
                "name": "SRTM 30m",
                "resolution": "30 meters",
                "description": "High-resolution SRTM elevation data"
            },
            "srtm90m": {
                "name": "SRTM 90m", 
                "resolution": "90 meters",
                "description": "Standard SRTM elevation data"
            },
            "aster30m": {
                "name": "ASTER 30m",
                "resolution": "30 meters", 
                "description": "ASTER Global DEM elevation data"
            }
        }
    
    async def query_by_coordinates(self, latitude: float, longitude: float, 
                                 dataset: str = "srtm30m") -> APIResponse:
        """Query elevation for a single coordinate point"""
        return await self.query_elevation_points(
            [(latitude, longitude)], 
            dataset=dataset
        )
    
    async def query_elevation_points(self, coordinates: List[Tuple[float, float]], 
                                   dataset: str = "srtm30m",
                                   interpolation: str = "bilinear") -> APIResponse:
        """
        Query elevation for multiple coordinate points
        
        Args:
            coordinates: List of (latitude, longitude) tuples
            dataset: Dataset to use (srtm30m, srtm90m, aster30m)
            interpolation: Interpolation method (bilinear, nearest, cubic)
        """
        if not self._check_rate_limits():
            return APIResponse(
                success=False, 
                error="Rate limit exceeded. Daily limit: 1000 requests, Current rate: 1 request/second",
                source="OpenTopoDataService"
            )
        
        if len(coordinates) > self.max_locations_per_request:
            return APIResponse(
                success=False,
                error=f"Too many coordinates. Maximum {self.max_locations_per_request} per request",
                source="OpenTopoDataService"
            )
        
        if dataset not in self.datasets:
            return APIResponse(
                success=False,
                error=f"Unknown dataset: {dataset}. Available: {list(self.datasets.keys())}",
                source="OpenTopoDataService"
            )
        
        # Format coordinates for API
        locations = "|".join([f"{lat},{lng}" for lat, lng in coordinates])
        
        endpoint = f"{dataset}"
        params = {
            "locations": locations,
            "interpolation": interpolation
        }
        
        # Apply rate limiting
        await self._apply_rate_limiting()
        
        # Make the request
        response = await self._make_request("GET", endpoint, params=params)
        
        if response.success:
            self._update_request_tracking()
            
            # Process and enhance the response
            elevation_data = self._process_elevation_response(response.data, dataset)
            return APIResponse(
                success=True,
                data=elevation_data,
                source="OpenTopoDataService"
            )
        
        return response
    
    async def generate_elevation_grid(self, center_lat: float, center_lng: float,
                                    grid_size_km: float = 2.0, grid_points: int = 10,
                                    dataset: str = "srtm30m") -> APIResponse:
        """
        Generate elevation grid around a center point for contour generation
        
        Args:
            center_lat: Center latitude
            center_lng: Center longitude  
            grid_size_km: Size of grid in kilometers (default 2km)
            grid_points: Number of grid points per side (default 10x10 grid)
            dataset: Elevation dataset to use
        """
        # Calculate grid bounds (approximate degrees for South Africa)
        km_to_deg_lat = 1/111.0  # 1 degree ≈ 111 km latitude
        km_to_deg_lng = 1/(111.0 * abs(center_lat * 0.017453))  # Adjust for longitude at latitude
        
        half_size_lat = (grid_size_km / 2) * km_to_deg_lat
        half_size_lng = (grid_size_km / 2) * km_to_deg_lng
        
        # Generate grid coordinates
        grid_coordinates = []
        lat_step = (2 * half_size_lat) / (grid_points - 1)
        lng_step = (2 * half_size_lng) / (grid_points - 1)
        
        for i in range(grid_points):
            for j in range(grid_points):
                lat = center_lat - half_size_lat + (i * lat_step)
                lng = center_lng - half_size_lng + (j * lng_step)
                grid_coordinates.append((lat, lng))
        
        logger.info(f"Generating {len(grid_coordinates)} elevation points in {grid_size_km}km grid")
        
        # Query elevation data for grid
        return await self.query_elevation_points(grid_coordinates, dataset=dataset)
    
    async def get_boundary_elevations(self, boundaries: List[Dict]) -> APIResponse:
        """
        Get elevation data for boundary features to enhance existing contour data
        
        Args:
            boundaries: List of boundary features from other APIs
        """
        elevation_boundaries = []
        
        for boundary in boundaries:
            if boundary.get('layer_type') == 'Contours':
                # Enhance existing contour data with elevation information
                enhanced_boundary = await self._enhance_contour_boundary(boundary)
                if enhanced_boundary:
                    elevation_boundaries.append(enhanced_boundary)
        
        return APIResponse(
            success=True,
            data={"boundaries": elevation_boundaries},
            source="OpenTopoDataService"
        )
    
    def _check_rate_limits(self) -> bool:
        """Check if we can make a request within rate limits"""
        current_date = datetime.now().date()
        
        # Reset daily counter if new day
        if current_date > self.last_reset_date:
            self.daily_request_count = 0
            self.last_reset_date = current_date
            self.request_times = []
        
        # Check daily limit
        if self.daily_request_count >= self.max_requests_per_day:
            logger.warning(f"Daily rate limit exceeded: {self.daily_request_count}/{self.max_requests_per_day}")
            return False
        
        # Check per-second limit
        now = datetime.now()
        recent_requests = [t for t in self.request_times if now - t < timedelta(seconds=1)]
        
        if len(recent_requests) >= self.max_requests_per_second:
            logger.info("Per-second rate limit reached, will wait")
            return True  # We can wait and retry
        
        return True
    
    async def _apply_rate_limiting(self):
        """Apply rate limiting by waiting if necessary"""
        now = datetime.now()
        
        # Clean old request times
        self.request_times = [t for t in self.request_times if now - t < timedelta(seconds=2)]
        
        # Wait if we've made a request in the last second
        if self.request_times:
            last_request = max(self.request_times)
            time_since_last = (now - last_request).total_seconds()
            if time_since_last < 1.0:
                wait_time = 1.0 - time_since_last
                logger.info(f"Rate limiting: waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
    
    def _update_request_tracking(self):
        """Update request tracking for rate limiting"""
        self.request_times.append(datetime.now())
        self.daily_request_count += 1
        logger.info(f"API request made. Daily count: {self.daily_request_count}/{self.max_requests_per_day}")
    
    def _process_elevation_response(self, data: Dict, dataset: str) -> Dict:
        """Process elevation response and convert to boundary format"""
        boundaries = []
        
        if not data.get("results"):
            return {"boundaries": boundaries, "dataset_info": self.datasets.get(dataset)}
        
        for result in data["results"]:
            if result.get("elevation") is not None:
                elevation = result["elevation"]
                location = result["location"]
                
                # Create elevation point boundary
                boundary = {
                    "layer_name": f"Elevation {elevation}m",
                    "layer_type": "Elevation Data",
                    "elevation": elevation,
                    "geometry": {
                        "type": "point",
                        "coordinates": [location["lng"], location["lat"]]
                    },
                    "properties": {
                        "elevation": elevation,
                        "dataset": dataset,
                        "latitude": location["lat"],
                        "longitude": location["lng"],
                        "source": "Open Topo Data"
                    },
                    "source_api": "OpenTopoData",
                    "dataset": dataset
                }
                boundaries.append(boundary)
        
        return {
            "boundaries": boundaries,
            "dataset_info": self.datasets.get(dataset),
            "elevation_stats": self._calculate_elevation_stats(boundaries)
        }
    
    def _calculate_elevation_stats(self, boundaries: List[Dict]) -> Dict:
        """Calculate elevation statistics"""
        elevations = [b["elevation"] for b in boundaries if b.get("elevation") is not None]
        
        if not elevations:
            return {}
        
        return {
            "min_elevation": min(elevations),
            "max_elevation": max(elevations),
            "avg_elevation": sum(elevations) / len(elevations),
            "elevation_range": max(elevations) - min(elevations),
            "point_count": len(elevations)
        }
    
    async def _enhance_contour_boundary(self, boundary: Dict) -> Optional[Dict]:
        """Enhance existing contour boundary with elevation data"""
        try:
            geometry = boundary.get("geometry")
            if not geometry:
                return None
            
            # For contour lines, sample a few points along the path
            if geometry.get("paths"):
                sample_points = []
                for path in geometry["paths"]:
                    # Sample every 5th point to avoid rate limits
                    for i in range(0, len(path), 5):
                        if len(sample_points) < 10:  # Limit sample size
                            coord = path[i]
                            sample_points.append((coord[1], coord[0]))  # lat, lng
                
                if sample_points:
                    elevation_response = await self.query_elevation_points(sample_points)
                    if elevation_response.success:
                        elevation_data = elevation_response.data.get("elevation_stats", {})
                        
                        # Enhance the boundary with elevation statistics
                        enhanced_boundary = boundary.copy()
                        enhanced_boundary["properties"] = enhanced_boundary.get("properties", {}).copy()
                        enhanced_boundary["properties"].update({
                            "elevation_enhanced": True,
                            "elevation_stats": elevation_data,
                            "enhancement_source": "OpenTopoData"
                        })
                        enhanced_boundary["layer_name"] += f" (Enhanced)"
                        
                        return enhanced_boundary
            
            return None
            
        except Exception as e:
            logger.error(f"Error enhancing contour boundary: {str(e)}")
            return None
    
    def get_service_status(self) -> Dict:
        """Get service status and rate limit information"""
        current_date = datetime.now().date()
        
        if current_date > self.last_reset_date:
            self.daily_request_count = 0
            self.last_reset_date = current_date
        
        return {
            "service": "Open Topo Data API",
            "status": "active",
            "daily_requests_used": self.daily_request_count,
            "daily_requests_remaining": self.max_requests_per_day - self.daily_request_count,
            "requests_per_second_limit": self.max_requests_per_second,
            "max_locations_per_request": self.max_locations_per_request,
            "available_datasets": list(self.datasets.keys()),
            "cache_ttl_seconds": self.cache_ttl
        }