"""
Contour Generation Service
Generates elevation contour lines from elevation data using marching squares algorithm.
Professional contour generation for land development projects.
"""

import numpy as np
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
from .external_api_service import APIResponse
from .open_topo_data_service import OpenTopoDataService

logger = logging.getLogger(__name__)

class ContourGenerationService:
    """Service for generating elevation contour lines"""
    
    def __init__(self, open_topo_service: OpenTopoDataService):
        self.open_topo_service = open_topo_service
        
        # Default contour generation parameters (simplified for reliability)
        self.default_contour_interval = 10.0  # 10 meter intervals (safer default)
        self.default_grid_size_km = 2.0       # 2km grid for focused coverage  
        self.default_grid_points = 12         # 12x12 grid (144 points, within limits)
        
        # Contour line styling options
        self.contour_styles = {
            "minor": {
                "weight": 1,
                "color": "#8B4513",
                "opacity": 0.6,
                "dashArray": "2,4"
            },
            "major": {
                "weight": 2,
                "color": "#654321",
                "opacity": 0.8,
                "dashArray": None
            },
            "index": {
                "weight": 3,
                "color": "#5D4037",
                "opacity": 1.0,
                "dashArray": None
            }
        }
    
    async def generate_contours(self, 
                              center_lat: float, 
                              center_lng: float,
                              contour_interval: Optional[float] = None,
                              grid_size_km: Optional[float] = None,
                              grid_points: Optional[int] = None,
                              dataset: str = "srtm30m") -> APIResponse:
        """
        Generate contour lines for a given area
        
        Args:
            center_lat: Center latitude
            center_lng: Center longitude  
            contour_interval: Elevation interval between contours (meters)
            grid_size_km: Size of area to analyze (kilometers)
            grid_points: Number of elevation points per side
            dataset: Elevation dataset to use
        """
        try:
            # Use defaults if not provided
            interval = contour_interval or self.default_contour_interval
            grid_size = grid_size_km or self.default_grid_size_km
            points = grid_points or self.default_grid_points
            
            logger.info(f"Generating contours for {center_lat}, {center_lng} with {interval}m intervals")
            
            # Get elevation grid data
            grid_response = await self.open_topo_service.generate_elevation_grid(
                center_lat, center_lng,
                grid_size_km=grid_size,
                grid_points=points,
                dataset=dataset
            )
            
            if not grid_response.success:
                return APIResponse(
                    success=False,
                    error=f"Failed to get elevation grid: {grid_response.error}",
                    source="ContourGenerationService"
                )
            
            # Process elevation data into grid format
            elevation_grid, grid_metadata = self._process_elevation_grid(
                grid_response.data, points, grid_size, center_lat, center_lng
            )
            
            if elevation_grid is None:
                return APIResponse(
                    success=False,
                    error="Invalid elevation grid data",
                    source="ContourGenerationService"
                )
            
            # Generate contour lines
            contour_lines = self._generate_contour_lines(
                elevation_grid, grid_metadata, interval
            )
            
            # Convert to GeoJSON format
            contour_features = self._convert_to_geojson(contour_lines, interval)
            
            # Create response data
            contour_data = {
                "contour_lines": contour_features,
                "parameters": {
                    "center_coordinates": {"latitude": center_lat, "longitude": center_lng},
                    "contour_interval": interval,
                    "grid_size_km": grid_size,
                    "grid_points": points,
                    "dataset": dataset
                },
                "statistics": {
                    "total_contours": len(contour_features),
                    "elevation_range": grid_metadata.get("elevation_range", {}),
                    "contour_levels": list(set([f["properties"]["elevation"] for f in contour_features]))
                },
                "boundaries": self._create_contour_boundaries(contour_features),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Generated {len(contour_features)} contour lines")
            
            return APIResponse(
                success=True,
                data=contour_data,
                source="ContourGenerationService"
            )
            
        except Exception as e:
            logger.error(f"Contour generation failed: {str(e)}")
            return APIResponse(
                success=False,
                error=f"Contour generation failed: {str(e)}",
                source="ContourGenerationService"
            )
    
    def _process_elevation_grid(self, 
                               grid_data: Dict,
                               grid_points: int,
                               grid_size_km: float,
                               center_lat: float,
                               center_lng: float) -> Tuple[Optional[np.ndarray], Dict]:
        """Process elevation grid data into numpy array format"""
        try:
            boundaries = grid_data.get("boundaries", [])
            if not boundaries:
                return None, {}
            
            # Create elevation grid array
            elevation_grid = np.full((grid_points, grid_points), np.nan)
            
            # Calculate grid parameters
            km_to_deg_lat = 1/111.0
            km_to_deg_lng = 1/(111.0 * abs(center_lat * 0.017453))
            
            half_size_lat = (grid_size_km / 2) * km_to_deg_lat
            half_size_lng = (grid_size_km / 2) * km_to_deg_lng
            
            lat_step = (2 * half_size_lat) / (grid_points - 1)
            lng_step = (2 * half_size_lng) / (grid_points - 1)
            
            # Fill elevation grid
            elevations = []
            for boundary in boundaries:
                if boundary.get("elevation") is not None:
                    lat = boundary["properties"]["latitude"]
                    lng = boundary["properties"]["longitude"]
                    elevation = boundary["elevation"]
                    elevations.append(elevation)
                    
                    # Calculate grid indices
                    i = round((lat - (center_lat - half_size_lat)) / lat_step)
                    j = round((lng - (center_lng - half_size_lng)) / lng_step)
                    
                    if 0 <= i < grid_points and 0 <= j < grid_points:
                        elevation_grid[i, j] = elevation
            
            # Create grid metadata
            grid_metadata = {
                "center_lat": center_lat,
                "center_lng": center_lng,
                "lat_step": lat_step,
                "lng_step": lng_step,
                "half_size_lat": half_size_lat,
                "half_size_lng": half_size_lng,
                "elevation_range": {
                    "min": min(elevations) if elevations else 0,
                    "max": max(elevations) if elevations else 0,
                    "mean": sum(elevations) / len(elevations) if elevations else 0
                }
            }
            
            # Interpolate missing values using simple bilinear interpolation
            elevation_grid = self._interpolate_missing_values(elevation_grid)
            
            return elevation_grid, grid_metadata
            
        except Exception as e:
            logger.error(f"Error processing elevation grid: {str(e)}")
            return None, {}
    
    def _interpolate_missing_values(self, grid: np.ndarray) -> np.ndarray:
        """Fill missing values in elevation grid using interpolation"""
        try:
            from scipy import ndimage
            
            # Create mask for valid data
            mask = ~np.isnan(grid)
            
            if not np.any(mask):
                # No valid data, return zeros
                return np.zeros_like(grid)
            
            # Use scipy interpolation if available
            try:
                # Fill NaN values using nearest neighbor interpolation
                from scipy.ndimage import distance_transform_edt
                
                # Get indices of valid points
                ind = distance_transform_edt(~mask, return_distances=False, return_indices=True)
                
                # Interpolate using nearest valid values
                interpolated_grid = grid[tuple(ind)]
                return interpolated_grid
                
            except ImportError:
                # Fallback to simple interpolation
                return self._simple_interpolation(grid, mask)
                
        except Exception as e:
            logger.warning(f"Interpolation failed, using simple fill: {str(e)}")
            # Simple fallback - replace NaN with mean of valid values
            valid_values = grid[~np.isnan(grid)]
            if len(valid_values) > 0:
                fill_value = np.mean(valid_values)
                grid[np.isnan(grid)] = fill_value
            else:
                grid[np.isnan(grid)] = 0
            return grid
    
    def _simple_interpolation(self, grid: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Simple interpolation fallback"""
        filled_grid = grid.copy()
        rows, cols = grid.shape
        
        # Fill missing values with average of surrounding valid values
        for i in range(rows):
            for j in range(cols):
                if not mask[i, j]:  # If value is missing
                    neighbors = []
                    for di in [-1, 0, 1]:
                        for dj in [-1, 0, 1]:
                            ni, nj = i + di, j + dj
                            if (0 <= ni < rows and 0 <= nj < cols and 
                                mask[ni, nj] and not np.isnan(grid[ni, nj])):
                                neighbors.append(grid[ni, nj])
                    
                    if neighbors:
                        filled_grid[i, j] = np.mean(neighbors)
                    else:
                        # Use overall mean if no neighbors
                        valid_values = grid[mask]
                        filled_grid[i, j] = np.mean(valid_values) if len(valid_values) > 0 else 0
        
        return filled_grid
    
    def _generate_contour_lines(self, 
                              elevation_grid: np.ndarray,
                              grid_metadata: Dict,
                              contour_interval: float) -> List[Dict]:
        """Generate contour lines using marching squares algorithm"""
        try:
            # Calculate contour levels
            min_elev = grid_metadata["elevation_range"]["min"]
            max_elev = grid_metadata["elevation_range"]["max"]
            
            # Round to nearest interval
            start_level = np.ceil(min_elev / contour_interval) * contour_interval
            end_level = np.floor(max_elev / contour_interval) * contour_interval
            
            levels = np.arange(start_level, end_level + contour_interval, contour_interval)
            
            contour_lines = []
            
            # Generate contours for each level
            for level in levels:
                lines = self._marching_squares(elevation_grid, level, grid_metadata)
                
                for line in lines:
                    contour_type = self._determine_contour_type(level, contour_interval)
                    
                    contour_lines.append({
                        "elevation": float(level),
                        "coordinates": line,
                        "contour_type": contour_type,
                        "style": self.contour_styles[contour_type]
                    })
            
            return contour_lines
            
        except Exception as e:
            logger.error(f"Error generating contour lines: {str(e)}")
            return []
    
    def _marching_squares(self, 
                         grid: np.ndarray, 
                         level: float,
                         grid_metadata: Dict) -> List[List[Tuple[float, float]]]:
        """Simplified marching squares implementation"""
        try:
            rows, cols = grid.shape
            lines = []
            
            # Grid parameters
            center_lat = grid_metadata["center_lat"]
            center_lng = grid_metadata["center_lng"]
            lat_step = grid_metadata["lat_step"]
            lng_step = grid_metadata["lng_step"]
            half_size_lat = grid_metadata["half_size_lat"]
            half_size_lng = grid_metadata["half_size_lng"]
            
            # Process each grid cell
            for i in range(rows - 1):
                for j in range(cols - 1):
                    # Get the four corner values
                    nw = grid[i, j]         # northwest
                    ne = grid[i, j + 1]     # northeast  
                    sw = grid[i + 1, j]     # southwest
                    se = grid[i + 1, j + 1] # southeast
                    
                    # Check if contour passes through this cell
                    corners = [nw, ne, se, sw]
                    if (min(corners) <= level <= max(corners)):
                        # Calculate line segment through cell
                        line_segment = self._calculate_contour_segment(
                            nw, ne, se, sw, level, i, j, 
                            center_lat, center_lng, lat_step, lng_step,
                            half_size_lat, half_size_lng
                        )
                        
                        if line_segment:
                            lines.append(line_segment)
            
            return lines
            
        except Exception as e:
            logger.error(f"Marching squares error: {str(e)}")
            return []
    
    def _calculate_contour_segment(self, 
                                 nw: float, ne: float, se: float, sw: float,
                                 level: float, i: int, j: int,
                                 center_lat: float, center_lng: float,
                                 lat_step: float, lng_step: float,
                                 half_size_lat: float, half_size_lng: float) -> Optional[List[Tuple[float, float]]]:
        """Calculate contour line segment through a grid cell"""
        try:
            # Convert grid indices to coordinates
            lat_base = center_lat - half_size_lat + (i * lat_step)
            lng_base = center_lng - half_size_lng + (j * lng_step)
            
            # Calculate intersection points on cell edges
            intersections = []
            
            # North edge (between nw and ne)
            if (nw <= level <= ne) or (ne <= level <= nw):
                if ne != nw:
                    t = (level - nw) / (ne - nw)
                    lng = lng_base + (t * lng_step)
                    intersections.append((lat_base, lng))
            
            # East edge (between ne and se)
            if (ne <= level <= se) or (se <= level <= ne):
                if se != ne:
                    t = (level - ne) / (se - ne)
                    lat = lat_base + (t * lat_step)
                    intersections.append((lat, lng_base + lng_step))
            
            # South edge (between se and sw)
            if (se <= level <= sw) or (sw <= level <= se):
                if sw != se:
                    t = (level - se) / (sw - se)
                    lng = lng_base + lng_step - (t * lng_step)
                    intersections.append((lat_base + lat_step, lng))
            
            # West edge (between sw and nw)
            if (sw <= level <= nw) or (nw <= level <= sw):
                if nw != sw:
                    t = (level - sw) / (nw - sw)
                    lat = lat_base + lat_step - (t * lat_step)
                    intersections.append((lat, lng_base))
            
            # Return line segment if we have exactly 2 intersections
            if len(intersections) == 2:
                return intersections
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating contour segment: {str(e)}")
            return None
    
    def _determine_contour_type(self, elevation: float, interval: float) -> str:
        """Determine contour line type (minor, major, or index)"""
        # Index contours every 10 intervals (e.g., every 20m if interval is 2m)
        if elevation % (interval * 10) == 0:
            return "index"
        # Major contours every 5 intervals (e.g., every 10m if interval is 2m)
        elif elevation % (interval * 5) == 0:
            return "major"
        else:
            return "minor"
    
    def _convert_to_geojson(self, contour_lines: List[Dict], interval: float) -> List[Dict]:
        """Convert contour lines to GeoJSON format"""
        features = []
        
        for i, contour in enumerate(contour_lines):
            if contour["coordinates"] and len(contour["coordinates"]) >= 2:
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[coord[1], coord[0]] for coord in contour["coordinates"]]  # [lng, lat]
                    },
                    "properties": {
                        "elevation": contour["elevation"],
                        "contour_type": contour["contour_type"],
                        "contour_id": f"contour_{i}",
                        "interval": interval,
                        "style": contour["style"]
                    }
                }
                features.append(feature)
        
        return features
    
    def _create_contour_boundaries(self, contour_features: List[Dict]) -> List[Dict]:
        """Convert contour features to boundary format for integration with existing system"""
        boundaries = []
        
        for feature in contour_features:
            elevation = feature["properties"]["elevation"]
            contour_type = feature["properties"]["contour_type"]
            
            boundary = {
                "layer_name": f"Contour {elevation}m ({contour_type})",
                "layer_type": "Generated Contours",
                "geometry": feature["geometry"],
                "properties": feature["properties"],
                "source_api": "ContourGenerationService",
                "elevation": elevation,
                "contour_data": True
            }
            boundaries.append(boundary)
        
        return boundaries
    
    def get_contour_styles(self) -> Dict[str, Dict]:
        """Get available contour styling options"""
        return self.contour_styles
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status information"""
        return {
            "service": "ContourGenerationService",
            "status": "active",
            "algorithms": ["marching_squares"],
            "default_interval": self.default_contour_interval,
            "supported_datasets": list(self.open_topo_service.datasets.keys()) if self.open_topo_service else [],
            "contour_types": list(self.contour_styles.keys())
        }