"""
External API Service Layer
Provides unified interface for all external API integrations with consistent error handling,
caching, and response formatting.
"""

import httpx
import json
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import os
from abc import ABC, abstractmethod
import logging


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIResponse:
    """Standardized API response wrapper"""
    def __init__(self, success: bool, data: Any = None, error: str = None, source: str = None):
        self.success = success
        self.data = data or {}
        self.error = error
        self.source = source
        self.timestamp = datetime.now().isoformat()

class BaseAPIService(ABC):
    """Base class for all external API services"""
    
    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url
        self.timeout = timeout
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = 300  # 5 minutes default
    
    async def _make_request(self, method: str, endpoint: str, params: Dict = None, 
                          data: Dict = None) -> APIResponse:
        """Make HTTP request with error handling and caching"""
        cache_key = self._get_cache_key(method, endpoint, params, data)
        
        # Check cache first
        if cache_key in self.cache:
            cached_response, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                logger.info(f"Cache hit for {self.__class__.__name__}: {endpoint}")
                return cached_response
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.base_url}/{endpoint.lstrip('/')}"
                
                if method.upper() == 'GET':
                    response = await client.get(url, params=params)
                elif method.upper() == 'POST':
                    response = await client.post(url, json=data, params=params)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                result_data = response.json()
                
                api_response = APIResponse(
                    success=True, 
                    data=result_data, 
                    source=self.__class__.__name__
                )
                
                # Cache successful responses
                self.cache[cache_key] = (api_response, datetime.now())
                
                logger.info(f"API request successful: {self.__class__.__name__} - {endpoint}")
                return api_response
                
        except httpx.TimeoutException:
            error_msg = f"Timeout error for {self.__class__.__name__}: {endpoint}"
            logger.error(error_msg)
            return APIResponse(success=False, error=error_msg, source=self.__class__.__name__)
            
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code} error for {self.__class__.__name__}: {endpoint}"
            logger.error(error_msg)
            return APIResponse(success=False, error=error_msg, source=self.__class__.__name__)
            
        except Exception as e:
            error_msg = f"Unexpected error for {self.__class__.__name__}: {str(e)}"
            logger.error(error_msg)
            return APIResponse(success=False, error=error_msg, source=self.__class__.__name__)
    
    def _get_cache_key(self, method: str, endpoint: str, params: Dict = None, 
                      data: Dict = None) -> str:
        """Generate cache key for request"""
        key_parts = [method, endpoint]
        if params:
            key_parts.append(json.dumps(params, sort_keys=True))
        if data:
            key_parts.append(json.dumps(data, sort_keys=True))
        return "|".join(key_parts)
    
    @abstractmethod
    async def query_by_coordinates(self, latitude: float, longitude: float) -> APIResponse:
        """Query the service by geographic coordinates"""
        pass

class CSGAPIService(BaseAPIService):
    """Chief Surveyor General API Service"""
    
    def __init__(self):
        base_url = "https://dffeportal.environment.gov.za/hosting/rest/services/CSG_Cadaster/CSG_Cadastral_Data/MapServer"
        super().__init__(base_url, timeout=30.0)
        self.cache_ttl = 600  # 10 minutes for CSG data
        
        self.boundary_layers = {
            "farm_portions": {"layer_id": 1, "name": "Farm Portions"},
            "erven": {"layer_id": 2, "name": "Erven"},
            "holdings": {"layer_id": 3, "name": "Holdings"},
            "public_places": {"layer_id": 4, "name": "Public Places"}
        }
    
    async def query_by_coordinates(self, latitude: float, longitude: float) -> APIResponse:
        """Query CSG API for all boundary layers at coordinates"""
        all_boundaries = []
        errors = []
        
        for layer_key, layer_info in self.boundary_layers.items():
            try:
                layer_response = await self._query_layer(latitude, longitude, layer_info["layer_id"])
                if layer_response.success and layer_response.data.get("results"):
                    for result in layer_response.data["results"]:
                        if result.get("geometry") and result.get("attributes"):
                            boundary = {
                                "layer_name": f"{layer_info['name']}_{result['attributes'].get('OBJECTID', 'unknown')}",
                                "layer_type": layer_info["name"],
                                "geometry": result["geometry"],
                                "properties": result["attributes"],
                                "source_api": "CSG"
                            }
                            all_boundaries.append(boundary)
                elif not layer_response.success:
                    errors.append(f"{layer_key}: {layer_response.error}")
                    
            except Exception as e:
                errors.append(f"{layer_key}: {str(e)}")
        
        return APIResponse(
            success=len(all_boundaries) > 0 or len(errors) == 0,
            data={"boundaries": all_boundaries, "errors": errors},
            source="CSGAPIService"
        )
    
    async def _query_layer(self, latitude: float, longitude: float, layer_id: int) -> APIResponse:
        """Query specific CSG layer"""
        endpoint = "identify"
        params = {
            "geometry": json.dumps({"x": longitude, "y": latitude}),
            "geometryType": "esriGeometryPoint",
            "layers": f"visible:{layer_id}",
            "tolerance": 10,
            "mapExtent": f"{longitude-0.01},{latitude-0.01},{longitude+0.01},{latitude+0.01}",
            "imageDisplay": "400,400,96",
            "returnGeometry": "true",
            "f": "json"
        }
        
        return await self._make_request("GET", endpoint, params=params)

class SANBIAPIService(BaseAPIService):
    """SANBI BGIS API Service"""
    
    def __init__(self):
        base_url = "https://bgismaps.sanbi.org/server/rest/services"
        super().__init__(base_url, timeout=30.0)
        self.cache_ttl = 900  # 15 minutes for environmental data
        
        self.services = {
            "contours": {
                "url": "BGIS_Projects/Basedata_rivers_contours/MapServer",
                "layers": {
                    "contours_north": 6,
                    "contours_south": 7,
                    "rivers": 4
                }
            },
            "conservation_gauteng": {
                "url": "2024_Gauteng_CBA_Map/MapServer",
                "layers": {
                    "protected_areas": 0
                }
            }
        }
    
    async def query_by_coordinates(self, latitude: float, longitude: float) -> APIResponse:
        """Query SANBI BGIS for environmental and topographic data"""
        all_boundaries = []
        errors = []
        
        # Query contours (both north and south)
        for layer_name, layer_id in [("contours_north", 6), ("contours_south", 7)]:
            try:
                contour_response = await self._query_contours(latitude, longitude, layer_id)
                if contour_response.success and contour_response.data.get("results"):
                    for result in contour_response.data["results"]:
                        if result.get("geometry") and result.get("attributes"):
                            height = result["attributes"].get("HEIGHT", "unknown")
                            boundary = {
                                "layer_name": f"Contour {height}m",
                                "layer_type": "Contours",
                                "geometry": result["geometry"],
                                "properties": result["attributes"],
                                "source_api": "SANBI_BGIS"
                            }
                            all_boundaries.append(boundary)
            except Exception as e:
                errors.append(f"{layer_name}: {str(e)}")
        
        # Query rivers/water bodies
        try:
            river_response = await self._query_layer(latitude, longitude, "contours", 4)
            if river_response.success and river_response.data.get("results"):
                for result in river_response.data["results"]:
                    if result.get("geometry") and result.get("attributes"):
                        # Filter out overly large water body geometries
                        geometry = result["geometry"]
                        if self._is_reasonable_water_body_size(geometry, latitude, longitude):
                            boundary = {
                                "layer_name": f"River_{result['attributes'].get('OBJECTID', 'unknown')}",
                                "layer_type": "Water Bodies",
                                "geometry": geometry,
                                "properties": result["attributes"],
                                "source_api": "SANBI_BGIS"
                            }
                            all_boundaries.append(boundary)
        except Exception as e:
            errors.append(f"rivers: {str(e)}")
        
        # Query protected areas
        try:
            protected_response = await self._query_layer(latitude, longitude, "conservation_gauteng", 0)
            if protected_response.success and protected_response.data.get("results"):
                for result in protected_response.data["results"]:
                    if result.get("geometry") and result.get("attributes"):
                        attrs = result["attributes"]
                        protection_type = attrs.get("CBA_ESA", attrs.get("CBACat", "Conservation Area"))
                        boundary = {
                            "layer_name": f"Conservation_{protection_type}_{attrs.get('OBJECTID', 'unknown')}",
                            "layer_type": "Environmental Constraints",
                            "geometry": result["geometry"],
                            "properties": result["attributes"],
                            "source_api": "SANBI_BGIS_Gauteng"
                        }
                        all_boundaries.append(boundary)
        except Exception as e:
            errors.append(f"protected_areas: {str(e)}")
        
        return APIResponse(
            success=len(all_boundaries) > 0 or len(errors) == 0,
            data={"boundaries": all_boundaries, "errors": errors},
            source="SANBIAPIService"
        )
    
    async def _query_contours(self, latitude: float, longitude: float, layer_id: int) -> APIResponse:
        """Query contour layers using specialized parameters"""
        service_url = f"{self.base_url}/BGIS_Projects/Basedata_rivers_contours/MapServer"
        endpoint = f"{layer_id}/query"
        
        params = {
            "geometry": json.dumps({"x": longitude, "y": latitude}),
            "geometryType": "esriGeometryPoint",
            "spatialRel": "esriSpatialRelIntersects",
            "distance": 500,  # Reduced from 2000m to 500m for more precise results
            "units": "esriSRUnit_Meter",
            "outFields": "HEIGHT,OBJECTID",
            "returnGeometry": "true",
            "f": "json"
        }
        
        # Override base URL for this specific request
        url = f"{service_url}/{endpoint}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Convert query response to identify format
                results = []
                for feature in data.get("features", []):
                    results.append({
                        "layerId": layer_id,
                        "layerName": f"Contours {'north' if layer_id == 6 else 'south'}",
                        "geometry": feature.get("geometry"),
                        "attributes": feature.get("attributes", {})
                    })
                
                return APIResponse(success=True, data={"results": results}, source="SANBIAPIService")
                
        except Exception as e:
            return APIResponse(success=False, error=str(e), source="SANBIAPIService")
    
    async def _query_layer(self, latitude: float, longitude: float, service_name: str, layer_id: int) -> APIResponse:
        """Query regular SANBI layer using identify"""
        service_config = self.services.get(service_name)
        if not service_config:
            return APIResponse(success=False, error=f"Unknown service: {service_name}")
        
        endpoint = f"{service_config['url']}/identify"
        params = {
            "geometry": json.dumps({"x": longitude, "y": latitude}),
            "geometryType": "esriGeometryPoint",
            "layers": f"visible:{layer_id}",
            "tolerance": 10,  # Reduced from 50 to 10 for more precise water body identification
            "mapExtent": f"{longitude-0.005},{latitude-0.005},{longitude+0.005},{latitude+0.005}",  # Reduced from 0.02 to 0.005 degrees (~550m)
            "imageDisplay": "400,400,96",
            "returnGeometry": "true",
            "f": "json"
        }
        
        return await self._make_request("GET", endpoint, params=params)
    
    def _is_reasonable_water_body_size(self, geometry, center_lat: float, center_lng: float) -> bool:
        """Filter out overly large water body geometries (e.g., entire catchments)"""
        if not geometry:
            return False
        
        try:
            # For polygons, check if the area is reasonable for a local water body
            if geometry.get("type") == "polygon":
                rings = geometry.get("rings", [])
                if not rings:
                    return False
                
                # Get the bounding box of the polygon
                all_coords = []
                for ring in rings:
                    all_coords.extend(ring)
                
                if not all_coords:
                    return False
                
                lngs = [coord[0] for coord in all_coords]
                lats = [coord[1] for coord in all_coords]
                
                min_lng, max_lng = min(lngs), max(lngs)
                min_lat, max_lat = min(lats), max(lats)
                
                # Calculate approximate dimensions in degrees
                width = max_lng - min_lng
                height = max_lat - min_lat
                
                # Reject water bodies larger than ~5km x 5km (approximately 0.045 degrees)
                if width > 0.045 or height > 0.045:
                    return False
                
                # Check if the water body is reasonably close to the query point
                center_distance_lng = abs((min_lng + max_lng) / 2 - center_lng)
                center_distance_lat = abs((min_lat + max_lat) / 2 - center_lat)
                
                # Reject if center is more than ~2km away (approximately 0.018 degrees)
                if center_distance_lng > 0.018 or center_distance_lat > 0.018:
                    return False
                
            # For polylines (rivers), check length
            elif geometry.get("type") == "polyline":
                paths = geometry.get("paths", [])
                if not paths:
                    return False
                
                # Calculate total length and check if reasonable for local rivers
                total_length = 0
                for path in paths:
                    for i in range(len(path) - 1):
                        lng1, lat1 = path[i]
                        lng2, lat2 = path[i + 1]
                        # Simple distance approximation
                        segment_length = ((lng2 - lng1) ** 2 + (lat2 - lat1) ** 2) ** 0.5
                        total_length += segment_length
                
                # Reject rivers longer than ~20km (approximately 0.18 degrees total)
                if total_length > 0.18:
                    return False
            
            return True
            
        except Exception as e:
            # If we can't determine size, err on the side of inclusion
            return True

class ExternalAPIManager:
    """Centralized manager for all external API services"""
    
    def __init__(self):
        self.csg_service = CSGAPIService()
        self.sanbi_service = SANBIAPIService()
        # ArcGIS service will be injected separately due to its complexity
        self.arcgis_service = None
        # Initialize Open Topo Data service for enhanced elevation data
        try:
            from .open_topo_data_service import OpenTopoDataService
            self.open_topo_service = OpenTopoDataService()
            logger.info("Open Topo Data service initialized successfully")
        except ImportError as e:
            self.open_topo_service = None
            logger.warning(f"Open Topo Data service not available: {e}")
    
    def set_arcgis_service(self, arcgis_service):
        """Inject ArcGIS service"""
        self.arcgis_service = arcgis_service
    
    async def get_comprehensive_land_data(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Get data from all external APIs and combine results"""
        logger.info(f"Querying comprehensive land data for {latitude}, {longitude}")
        
        # Gather all API responses concurrently
        tasks = [
            self.csg_service.query_by_coordinates(latitude, longitude),
            self.sanbi_service.query_by_coordinates(latitude, longitude)
        ]
        
        # Add ArcGIS if available
        if self.arcgis_service:
            tasks.append(self._get_arcgis_data(latitude, longitude))
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine all boundaries
        all_boundaries = []
        all_errors = []
        
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                all_errors.append(f"Service {i}: {str(response)}")
                continue
                
            if hasattr(response, 'success') and response.success:
                if response.data.get("boundaries"):
                    all_boundaries.extend(response.data["boundaries"])
                if response.data.get("errors"):
                    all_errors.extend(response.data["errors"])
            else:
                if hasattr(response, 'error'):
                    all_errors.append(response.error)
        
        logger.info(f"Comprehensive query complete: {len(all_boundaries)} boundaries, {len(all_errors)} errors")
        
        return {
            "boundaries": all_boundaries,
            "total_boundaries": len(all_boundaries),
            "errors": all_errors,
            "query_timestamp": datetime.now().isoformat()
        }
    
    async def _get_arcgis_data(self, latitude: float, longitude: float) -> APIResponse:
        """Get ArcGIS data and format as APIResponse"""
        try:
            if not self.arcgis_service:
                return APIResponse(success=False, error="ArcGIS service not available")
            
            arcgis_data = await self.arcgis_service.get_land_development_data(
                latitude, longitude,
                services=['world_countries', 'world_admin_divisions', 'world_cities']
            )
            
            boundaries = []
            if arcgis_data.get("features"):
                for feature in arcgis_data["features"]:
                    boundary = {
                        "layer_name": feature.get("layer_name"),
                        "layer_type": feature.get("layer_type"),
                        "geometry": feature.get("geometry"),
                        "properties": feature.get("properties", {}),
                        "source_api": feature.get("source_api", "ArcGIS_Online")
                    }
                    boundaries.append(boundary)
            
            return APIResponse(
                success=True,
                data={"boundaries": boundaries, "errors": arcgis_data.get("errors", [])},
                source="ArcGISAPIService"
            )
            
        except Exception as e:
            return APIResponse(success=False, error=str(e), source="ArcGISAPIService")
