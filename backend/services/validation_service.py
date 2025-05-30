"""
Request/Response Validation Service
Provides comprehensive validation schemas and utilities for API endpoints.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from enum import Enum
import re

class CoordinateValidationMixin:
    """Mixin for coordinate validation"""
    
    @validator('latitude')
    def validate_latitude(cls, v):
        if v is None:
            raise ValueError('Latitude is required')
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90 degrees')
        return v
    
    @validator('longitude')
    def validate_longitude(cls, v):
        if v is None:
            raise ValueError('Longitude is required')
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180 degrees')
        return v

class ProjectStatus(str, Enum):
    """Project status enumeration"""
    COMPLETED = "completed"
    PROCESSING = "processing"
    FAILED = "failed"
    NO_DATA_FOUND = "no_data_found"

class SourceAPI(str, Enum):
    """Source API enumeration"""
    CSG = "CSG"
    SANBI_BGIS = "SANBI_BGIS"
    SANBI_BGIS_GAUTENG = "SANBI_BGIS_Gauteng"
    SANBI_BGIS_NATIONAL = "SANBI_BGIS_National"
    ARCGIS_ONLINE = "ArcGIS_Online"
    AFRIGIS = "AfriGIS"
    OPENTOPODATA = "OpenTopoData"

# Input Models
class CoordinateInput(BaseModel, CoordinateValidationMixin):
    """Input model for coordinate-based requests"""
    latitude: float = Field(..., description="Latitude in decimal degrees")
    longitude: float = Field(..., description="Longitude in decimal degrees") 
    project_name: Optional[str] = Field(
        default="Land Development Project",
        min_length=1,
        max_length=200,
        description="Name of the project"
    )
    
    @validator('project_name')
    def validate_project_name(cls, v):
        if v:
            # Remove special characters that might cause issues
            cleaned = re.sub(r'[^\w\s-]', '', v.strip())
            if not cleaned:
                raise ValueError('Project name must contain at least one alphanumeric character')
            return cleaned
        return v

class ProjectCreate(BaseModel, CoordinateValidationMixin):
    """Model for creating new projects"""
    name: str = Field(..., min_length=1, max_length=200)
    latitude: float
    longitude: float

# Response Models
class BoundaryGeometry(BaseModel):
    """Geometry model for boundaries"""
    rings: Optional[List[List[List[float]]]] = None
    paths: Optional[List[List[List[float]]]] = None
    x: Optional[float] = None
    y: Optional[float] = None

class BoundaryLayer(BaseModel):
    """Model for boundary layer data"""
    layer_name: str = Field(..., description="Name of the boundary layer")
    layer_type: str = Field(..., description="Type of boundary layer")
    geometry: Optional[BoundaryGeometry] = Field(None, description="Geometry data")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Boundary properties")
    source_api: SourceAPI = Field(..., description="Source API for the boundary")

class LandDataResponse(BaseModel):
    """Response model for land data queries"""
    project_id: str = Field(..., description="Unique project identifier")
    coordinates: Dict[str, float] = Field(..., description="Query coordinates")
    boundaries: List[BoundaryLayer] = Field(default_factory=list, description="Found boundaries")
    files_generated: List[str] = Field(default_factory=list, description="Generated file names")
    status: ProjectStatus = Field(..., description="Query status")
    created_at: str = Field(..., description="Creation timestamp")
    total_boundaries: Optional[int] = Field(None, description="Total number of boundaries found")
    elevation_stats: Optional[Dict[str, Any]] = Field(None, description="Elevation statistics from Open Topo Data")

class ProjectResponse(BaseModel):
    """Response model for project data"""
    id: str = Field(..., description="Project ID")
    name: str = Field(..., description="Project name")
    coordinates: Dict[str, float] = Field(..., description="Project coordinates")
    created: str = Field(..., description="Creation timestamp")
    lastModified: str = Field(..., description="Last modification timestamp")
    data: Optional[List[BoundaryLayer]] = Field(None, description="Project boundary data")
    layers: Optional[Dict[str, Any]] = Field(None, description="Layer configuration")

class ProjectListResponse(BaseModel):
    """Response model for project lists"""
    projects: List[ProjectResponse] = Field(..., description="List of projects")
    total_count: Optional[int] = Field(None, description="Total number of projects")

class HealthCheckResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    timestamp: str = Field(..., description="Response timestamp")
    version: Optional[str] = Field(None, description="Service version")

class ErrorResponse(BaseModel):
    """Response model for errors"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: str = Field(..., description="Error timestamp")

class CADLayerInfo(BaseModel):
    """Model for CAD layer information"""
    layer_type: str = Field(..., description="Type of CAD layer")
    layer_name: str = Field(..., description="CAD layer name")
    description: str = Field(..., description="Layer description")
    entity_count: int = Field(..., description="Number of entities in layer")
    geometry_type: str = Field(..., description="Geometry type (POLYLINE, POLYGON)")
    color: str = Field(..., description="Layer color")

class CADLayersResponse(BaseModel):
    """Response model for available CAD layers"""
    project_id: str = Field(..., description="Project ID")
    project_name: str = Field(..., description="Project name")
    available_layers: List[CADLayerInfo] = Field(..., description="Available CAD layers")
    total_boundaries: int = Field(..., description="Total boundaries available")
    cad_generation_ready: bool = Field(..., description="Whether CAD generation is ready")

# Database Models
class ProjectInDB(BaseModel):
    """Model for project data in database"""
    project_id: str = Field(..., description="Unique project identifier")
    name: str = Field(..., description="Project name")
    coordinates: Dict[str, float] = Field(..., description="Project coordinates")
    created: str = Field(..., description="Creation timestamp")
    last_modified: str = Field(..., description="Last modification timestamp")
    data: Optional[Dict[str, Any]] = Field(None, description="Project data")
    layers: Optional[Dict[str, Any]] = Field(None, description="Layer data")

# New Models for Navigation Features

class APIStatus(BaseModel):
    """Model for API status information"""
    name: str = Field(..., description="API name")
    is_configured: bool = Field(..., description="Whether API is configured")
    status: str = Field(..., description="API status (connected, error, not_configured)")
    last_check: Optional[str] = Field(None, description="Last status check timestamp")
    error_message: Optional[str] = Field(None, description="Error message if status is error")

class APIConfiguration(BaseModel):
    """Model for API configuration"""
    api_name: str = Field(..., description="API name")
    config_fields: Dict[str, Any] = Field(..., description="Configuration fields")

class APIConfigurationUpdate(BaseModel):
    """Model for updating API configuration"""
    api_name: str = Field(..., description="API name to update")
    config_values: Dict[str, str] = Field(..., description="Configuration values to update")

class UserProfile(BaseModel):
    """Model for user profile"""
    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: Optional[str] = Field(None, description="User email")
    full_name: Optional[str] = Field(None, description="User full name")
    organization: Optional[str] = Field(None, description="User organization")
    created_at: str = Field(..., description="Profile creation timestamp")
    last_login: Optional[str] = Field(None, description="Last login timestamp")

class UserProfileUpdate(BaseModel):
    """Model for updating user profile"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = Field(None, pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    organization: Optional[str] = Field(None, min_length=1, max_length=100)

class APIStatusResponse(BaseModel):
    """Response model for API status"""
    apis: List[APIStatus] = Field(..., description="List of API statuses")
    total_configured: int = Field(..., description="Number of configured APIs")
    total_available: int = Field(..., description="Total number of available APIs")
    timestamp: str = Field(..., description="Response timestamp")

class AppStatistics(BaseModel):
    """Model for application statistics"""
    total_projects: int = Field(..., description="Total number of projects")
    projects_created_today: int = Field(..., description="Projects created today")
    projects_created_this_week: int = Field(..., description="Projects created this week")
    total_boundaries_processed: int = Field(..., description="Total boundaries processed")
    avg_processing_time: Optional[float] = Field(None, description="Average processing time in seconds")
    uptime_hours: float = Field(..., description="Application uptime in hours")

class ValidationUtils:
    """Utility functions for validation"""
    
    @staticmethod
    def validate_project_id(project_id: str) -> bool:
        """Validate project ID format (UUID)"""
        import uuid
        try:
            uuid.UUID(project_id)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_coordinates_in_south_africa(latitude: float, longitude: float) -> bool:
        """Check if coordinates are within South Africa's approximate bounds"""
        # South Africa approximate bounds
        sa_bounds = {
            'min_lat': -35.0,
            'max_lat': -22.0,
            'min_lng': 16.0,
            'max_lng': 33.0
        }
        
        return (sa_bounds['min_lat'] <= latitude <= sa_bounds['max_lat'] and
                sa_bounds['min_lng'] <= longitude <= sa_bounds['max_lng'])
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe file operations"""
        # Remove or replace invalid filename characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove multiple consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remove leading/trailing underscores and spaces
        return sanitized.strip('_ ')
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return bool(re.match(email_pattern, email))
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate username format"""
        # Allow alphanumeric characters, underscores, and hyphens
        username_pattern = r'^[a-zA-Z0-9_-]{3,50}$'
        return bool(re.match(username_pattern, username))
