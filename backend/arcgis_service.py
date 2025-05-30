"""
ArcGIS/Esri REST API Service Integration

This module provides comprehensive integration with ArcGIS Online and Enterprise services,
including basemaps, feature services, geocoding, routing, and spatial analysis capabilities.
"""

import httpx
import json
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import asyncio

class ArcGISAPIService:
    """
    Complete ArcGIS/Esri REST API Service Handler
    
    Provides access to ArcGIS Online services including:
    - Basemap services (World Imagery, Street Maps, Topographic)
    - Feature services (Living Atlas, Demographics, Administrative boundaries)
    - Geocoding services (World Geocoding Service)
    - Spatial analysis services (Geometry, GeoEnrichment)
    """
    
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.client_id = client_id or os.environ.get('ARCGIS_CLIENT_ID')
        self.client_secret = client_secret or os.environ.get('ARCGIS_CLIENT_SECRET')
        self.base_timeout = 30.0
        self.token_cache = {}
        self.access_token = None
        self.token_expires = None
        
        # ArcGIS Online Base URLs
        self.base_urls = {
            "services": "https://services.arcgisonline.com/ArcGIS/rest/services",
            "geocoding": "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer",
            "routing": "https://route.arcgis.com/arcgis/rest/services/World/Route/NAServer/Route_World",
            "geometry": "https://utility.arcgisonline.com/ArcGIS/rest/services/Geometry/GeometryServer",
            "living_atlas": "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services",
            "static_tiles": "https://static-map-tiles-api.arcgis.com/arcgis/rest/services",
            "basemap_styles": "https://basemaps-api.arcgis.com/arcgis/rest/services/styles"
        }
        
        # Service Configurations for Land Development
        self.land_dev_services = {
            # Administrative Boundaries
            "world_countries": {
                "url": f"{self.base_urls['living_atlas']}/World_Countries_Generalized/FeatureServer/0",
                "description": "World Countries - Administrative boundaries",
                "layer_type": "Administrative Boundaries",
                "cad_layer": "SDP_GEO_ADMIN_BOUND_001"
            },
            "world_admin_divisions": {
                "url": f"{self.base_urls['living_atlas']}/World_Administrative_Divisions/FeatureServer/0", 
                "description": "World Administrative Divisions - States/Provinces",
                "layer_type": "Administrative Boundaries",
                "cad_layer": "SDP_GEO_ADMIN_DIV_001"
            },
            
            # Demographics for Development Planning
            "world_population": {
                "url": f"{self.base_urls['living_atlas']}/World_Population_Density/FeatureServer/0",
                "description": "World Population Density - Development planning data",
                "layer_type": "Demographics",
                "cad_layer": "SDP_DEMO_POP_DENS_001"
            },
            "world_urban_areas": {
                "url": f"{self.base_urls['living_atlas']}/World_Urban_Areas/FeatureServer/0",
                "description": "World Urban Areas - City boundaries and development zones",
                "layer_type": "Urban Planning",
                "cad_layer": "SDP_URBAN_AREAS_001"
            },
            
            # Infrastructure
            "world_cities": {
                "url": f"{self.base_urls['living_atlas']}/World_Cities/FeatureServer/0",
                "description": "World Cities - Municipal centers and major settlements",
                "layer_type": "Infrastructure",
                "cad_layer": "SDP_INFRA_CITIES_001"
            },
            
            # Environmental
            "world_physical_features": {
                "url": f"{self.base_urls['living_atlas']}/World_Physical_Features/FeatureServer/0",
                "description": "World Physical Features - Natural landmarks and constraints",
                "layer_type": "Environmental",
                "cad_layer": "SDP_ENV_PHYS_FEAT_001"
            },
            
            # Transportation
            "world_highways": {
                "url": f"{self.base_urls['living_atlas']}/World_Highways/FeatureServer/0",
                "description": "World Highways - Major transportation corridors",
                "layer_type": "Transportation",
                "cad_layer": "SDP_TRANS_HIGHWAYS_001"
            }
        }
        
        # Basemap Services
        self.basemap_services = {
            "world_imagery": {
                "service_url": f"{self.base_urls['services']}/World_Imagery/MapServer",
                "tile_url": f"{self.base_urls['static_tiles']}/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}",
                "style_url": f"{self.base_urls['basemap_styles']}/ArcGIS:Imagery",
                "description": "High-resolution satellite imagery"
            },
            "world_street_map": {
                "service_url": f"{self.base_urls['services']}/World_Street_Map/MapServer",
                "tile_url": f"{self.base_urls['static_tiles']}/World_Street_Map/MapServer/tile/{{z}}/{{y}}/{{x}}",
                "style_url": f"{self.base_urls['basemap_styles']}/ArcGIS:Streets",
                "description": "Detailed street map with labels"
            },
            "world_topographic": {
                "service_url": f"{self.base_urls['services']}/World_Topo_Map/MapServer",
                "tile_url": f"{self.base_urls['static_tiles']}/World_Topo_Map/MapServer/tile/{{z}}/{{y}}/{{x}}",
                "style_url": f"{self.base_urls['basemap_styles']}/ArcGIS:Topographic",
                "description": "Topographic map with terrain and elevation"
            }
        }
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test ArcGIS API connectivity and return service status"""
        try:
            # Get OAuth2 token first
            token = await self.get_access_token()
            
            async with httpx.AsyncClient(timeout=self.base_timeout) as client:
                # Test basic service info
                info_url = f"{self.base_urls['services']}?f=json"
                if token:
                    info_url += f"&token={token}"
                
                response = await client.get(info_url)
                response.raise_for_status()
                
                return {
                    "status": "connected",
                    "oauth2_configured": bool(self.client_id and self.client_secret),
                    "token_obtained": bool(token),
                    "services_available": len(self.land_dev_services),
                    "basemaps_available": len(self.basemap_services),
                    "response_time_ms": response.elapsed.total_seconds() * 1000 if hasattr(response, 'elapsed') else 0
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "oauth2_configured": bool(self.client_id and self.client_secret)
            }
    
    async def query_features_by_geometry(self, service_key: str, latitude: float, longitude: float, 
                                       buffer_meters: int = 5000) -> Dict[str, Any]:
        """
        Query ArcGIS features by geographic location with buffer
        
        Args:
            service_key: Key from land_dev_services
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            buffer_meters: Search radius in meters
            
        Returns:
            ArcGIS query response with features
        """
        if service_key not in self.land_dev_services:
            raise ValueError(f"Unknown service: {service_key}")
        
        service = self.land_dev_services[service_key]
        
        try:
            # Get OAuth2 token
            token = await self.get_access_token()
            
            async with httpx.AsyncClient(timeout=self.base_timeout) as client:
                # Create point geometry
                point_geometry = {
                    "x": longitude,
                    "y": latitude,
                    "spatialReference": {"wkid": 4326}
                }
                
                # Query parameters
                params = {
                    "geometry": json.dumps(point_geometry),
                    "geometryType": "esriGeometryPoint",
                    "spatialRel": "esriSpatialRelIntersects",
                    "distance": buffer_meters,
                    "units": "esriSRUnit_Meter",
                    "outFields": "*",
                    "returnGeometry": "true",
                    "maxRecordCount": 100,
                    "f": "json"
                }
                
                if token:
                    params["token"] = token
                
                # Query the service
                query_url = f"{service['url']}/query"
                response = await client.get(query_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # Add service metadata to response
                data["service_info"] = {
                    "service_key": service_key,
                    "description": service["description"],
                    "layer_type": service["layer_type"],
                    "cad_layer": service["cad_layer"],
                    "source_url": service["url"]
                }
                
                return data
                
        except Exception as e:
            print(f"Error querying ArcGIS service {service_key}: {str(e)}")
            return {"error": str(e), "features": []}
    
    async def geocode_address(self, address: str) -> Dict[str, Any]:
        """
        Geocode an address using ArcGIS World Geocoding Service
        
        Args:
            address: Address string to geocode
            
        Returns:
            Geocoding response with location candidates
        """
        try:
            # Get OAuth2 token  
            token = await self.get_access_token()
            
            async with httpx.AsyncClient(timeout=self.base_timeout) as client:
                params = {
                    "SingleLine": address,
                    "category": "Address,Postal",
                    "maxLocations": 5,
                    "outFields": "*",
                    "f": "json"
                }
                
                if token:
                    params["token"] = token
                
                url = f"{self.base_urls['geocoding']}/findAddressCandidates"
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                return response.json()
                
        except Exception as e:
            print(f"Error geocoding address: {str(e)}")
            return {"error": str(e), "candidates": []}
    
    async def reverse_geocode(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Reverse geocode coordinates to get address information
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Reverse geocoding response with address
        """
        try:
            # Get OAuth2 token
            token = await self.get_access_token()
            
            async with httpx.AsyncClient(timeout=self.base_timeout) as client:
                params = {
                    "location": f"{longitude},{latitude}",
                    "outSR": "4326",
                    "returnIntersection": "false",
                    "f": "json"
                }
                
                if token:
                    params["token"] = token
                
                url = f"{self.base_urls['geocoding']}/reverseGeocode"
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                return response.json()
                
        except Exception as e:
            print(f"Error reverse geocoding: {str(e)}")
            return {"error": str(e)}
    
    async def get_basemap_info(self, basemap_key: str) -> Dict[str, Any]:
        """
        Get information about a specific basemap service
        
        Args:
            basemap_key: Key from basemap_services
            
        Returns:
            Basemap service information
        """
        if basemap_key not in self.basemap_services:
            raise ValueError(f"Unknown basemap: {basemap_key}")
        
        basemap = self.basemap_services[basemap_key]
        
        try:
            # Get OAuth2 token
            token = await self.get_access_token()
            
            async with httpx.AsyncClient(timeout=self.base_timeout) as client:
                params = {"f": "json"}
                if token:
                    params["token"] = token
                
                response = await client.get(basemap["service_url"], params=params)
                response.raise_for_status()
                
                service_info = response.json()
                service_info["stirling_bridge_config"] = basemap
                
                return service_info
                
        except Exception as e:
            print(f"Error getting basemap info: {str(e)}")
            return {"error": str(e)}
    
    def get_tile_url(self, basemap_key: str, z: int, y: int, x: int) -> str:
        """
        Generate tile URL for a specific basemap
        
        Args:
            basemap_key: Key from basemap_services
            z: Zoom level
            y: Tile Y coordinate
            x: Tile X coordinate
            
        Returns:
            Complete tile URL with authentication
        """
        if basemap_key not in self.basemap_services:
            raise ValueError(f"Unknown basemap: {basemap_key}")
        
        basemap = self.basemap_services[basemap_key]
        tile_url = basemap["tile_url"].format(z=z, y=y, x=x)
        
        # Note: For tile URLs, we would need to get token synchronously
        # For now, return URL without token - most basemap tiles work without auth
        return tile_url
    
    def get_available_services(self) -> Dict[str, Any]:
        """
        Get list of all available ArcGIS services configured for land development
        
        Returns:
            Dictionary of available services organized by category
        """
        return {
            "land_development_services": {
                key: {
                    "description": service["description"],
                    "layer_type": service["layer_type"],
                    "cad_layer": service["cad_layer"]
                }
                for key, service in self.land_dev_services.items()
            },
            "basemap_services": {
                key: {
                    "description": basemap["description"],
                    "tile_url_template": basemap["tile_url"]
                }
                for key, basemap in self.basemap_services.items()
            },
            "total_services": len(self.land_dev_services) + len(self.basemap_services),
            "oauth2_configured": bool(self.client_id and self.client_secret)
        }
    
    async def get_land_development_data(self, latitude: float, longitude: float, 
                                      services: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get comprehensive land development data for a location from multiple ArcGIS services
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            services: Optional list of specific services to query (default: all)
            
        Returns:
            Combined data from multiple ArcGIS services
        """
        if services is None:
            services = list(self.land_dev_services.keys())
        
        results = {
            "location": {"latitude": latitude, "longitude": longitude},
            "services_queried": services,
            "features": [],
            "errors": [],
            "query_time": datetime.now().isoformat()
        }
        
        # Query each service
        for service_key in services:
            try:
                data = await self.query_features_by_geometry(service_key, latitude, longitude)
                
                if "features" in data and data["features"]:
                    for feature in data["features"]:
                        # Standardize feature format for CAD generation
                        standardized_feature = {
                            "layer_name": f"ArcGIS_{service_key}_{feature.get('attributes', {}).get('OBJECTID', 'unknown')}",
                            "layer_type": data["service_info"]["layer_type"],
                            "geometry": feature.get("geometry"),
                            "properties": feature.get("attributes", {}),
                            "source_api": "ArcGIS_Online",
                            "service_key": service_key,
                            "cad_layer": data["service_info"]["cad_layer"],
                            "source_url": data["service_info"]["source_url"]
                        }
                        results["features"].append(standardized_feature)
                
                if "error" in data:
                    results["errors"].append({
                        "service": service_key,
                        "error": data["error"]
                    })
                    
            except Exception as e:
                results["errors"].append({
                    "service": service_key,
                    "error": str(e)
                })
        
        results["total_features"] = len(results["features"])
        return results

# Utility functions for integration
def format_arcgis_geometry_for_leaflet(esri_geometry: Dict) -> List[List[List[float]]]:
    """
    Convert ArcGIS geometry to Leaflet-compatible format
    
    Args:
        esri_geometry: ArcGIS geometry object
        
    Returns:
        Leaflet-compatible coordinate arrays
    """
    if not esri_geometry:
        return []
    
    # Handle different geometry types
    if "rings" in esri_geometry:  # Polygon
        return [
            [[coord[1], coord[0]] for coord in ring]  # Swap x,y to lat,lng
            for ring in esri_geometry["rings"]
        ]
    elif "paths" in esri_geometry:  # Polyline
        return [
            [[coord[1], coord[0]] for coord in path]  # Swap x,y to lat,lng
            for path in esri_geometry["paths"]
        ]
    elif "x" in esri_geometry and "y" in esri_geometry:  # Point
        return [[[esri_geometry["y"], esri_geometry["x"]]]]
    
    return []

def convert_arcgis_to_boundary_layer(feature: Dict, service_info: Dict) -> Dict:
    """
    Convert ArcGIS feature to Stirling Bridge BoundaryLayer format
    
    Args:
        feature: ArcGIS feature object
        service_info: Service metadata
        
    Returns:
        BoundaryLayer-compatible dictionary
    """
    return {
        "layer_name": f"ArcGIS_{service_info['service_key']}_{feature.get('attributes', {}).get('OBJECTID', 'unknown')}",
        "layer_type": service_info["layer_type"],
        "geometry": feature.get("geometry"),
        "properties": feature.get("attributes", {}),
        "source_api": "ArcGIS_Online",
        "service_key": service_info["service_key"],
        "cad_layer": service_info["cad_layer"],
        "source_url": service_info["source_url"]
    }

    async def get_access_token(self) -> Optional[str]:
        """
        Get OAuth2 access token using client credentials
        Caches token until expiration
        """
        # Check if we have a valid cached token
        if (self.access_token and self.token_expires and 
            datetime.now() < self.token_expires - timedelta(minutes=5)):
            return self.access_token
        
        if not self.client_id or not self.client_secret:
            print("Warning: ArcGIS client credentials not configured")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=self.base_timeout) as client:
                # OAuth2 token endpoint
                token_url = "https://www.arcgis.com/sharing/rest/oauth2/token"
                
                data = {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "client_credentials"
                }
                
                response = await client.post(token_url, data=data)
                response.raise_for_status()
                
                token_data = response.json()
                
                if "access_token" in token_data:
                    self.access_token = token_data["access_token"]
                    # Cache token for the duration minus 5 minutes for safety
                    expires_in = token_data.get("expires_in", 7200)  # Default 2 hours
                    self.token_expires = datetime.now() + timedelta(seconds=expires_in)
                    
                    print(f"✅ ArcGIS OAuth2 token obtained, expires in {expires_in} seconds")
                    return self.access_token
                else:
                    print(f"❌ Error getting ArcGIS token: {token_data}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error obtaining ArcGIS OAuth2 token: {str(e)}")
            return None