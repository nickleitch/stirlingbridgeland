"""
Stirling Bridge LandDev API - Refactored Server
Professional land development platform with clean architecture and service layers.
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
import uuid
import logging
from datetime import datetime
import zipfile
import io

# Import service layers
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.external_api_service import ExternalAPIManager
from services.database_service import db_service
from services.validation_service import (
    CoordinateInput, LandDataResponse, ProjectResponse, ProjectListResponse,
    HealthCheckResponse, ErrorResponse, ValidationUtils, ProjectStatus,
    BoundaryLayer, ProjectInDB, APIStatusResponse, APIConfigurationUpdate,
    UserProfile, UserProfileUpdate, AppStatistics
)
from services.api_management_service import api_management_service
from services.user_profile_service import user_profile_service
from config.settings import settings, LayerConfiguration
from cad_generator import CADFileManager
from arcgis_service import ArcGISAPIService

# Setup logging
logger = logging.getLogger(__name__)

# Initialize services
api_manager = ExternalAPIManager()
cad_manager = CADFileManager()

# Create FastAPI app with configuration
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Professional land development platform for South African SPLUMA compliance",
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

@app.on_event("startup")
async def startup():
    """Application startup initialization"""
    import time
    
    # Set application start time for uptime calculation
    app.state.start_time = time.time()
    
    logger.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    
    # Connect to database
    if not await db_service.connect():
        logger.error("Failed to connect to database")
        raise RuntimeError("Database connection failed")
    
    # Initialize ArcGIS service if credentials are available
    if settings.has_arcgis_credentials:
        arcgis_service = ArcGISAPIService(
            client_id=settings.arcgis_client_id,
            client_secret=settings.arcgis_client_secret
        )
        api_manager.set_arcgis_service(arcgis_service)
        logger.info("✅ ArcGIS service initialized with credentials")
    else:
        logger.warning("⚠️ ArcGIS credentials not configured")
    
    logger.info("✅ Application startup complete")

@app.on_event("shutdown")
async def shutdown():
    """Application shutdown cleanup"""
    await db_service.disconnect()
    logger.info("👋 Application shutdown complete")

@app.get("/api/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint with database status"""
    try:
        db_health = await db_service.health_check()
        
        return HealthCheckResponse(
            status="healthy" if db_health["status"] == "connected" else "degraded",
            service=settings.app_name,
            timestamp=datetime.now().isoformat(),
            version=settings.app_version
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )

@app.get("/api/boundary-types")
async def get_boundary_types():
    """Get available boundary types with color configuration"""
    try:
        boundary_types = []
        
        for layer_type, color in LayerConfiguration.LAYER_COLORS.items():
            weight = LayerConfiguration.LAYER_WEIGHTS.get(layer_type, 0.5)
            boundary_types.append({
                "type": layer_type,
                "color": color,
                "weight": weight,
                "enabled": True
            })
        
        return {
            "boundary_types": boundary_types,
            "total_types": len(boundary_types),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting boundary types: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve boundary types"
        )

@app.post("/api/identify-land", response_model=LandDataResponse)
async def identify_land(coordinates: CoordinateInput):
    """Identify land boundaries and create project"""
    try:
        logger.info(f"Processing land identification request for {coordinates.latitude}, {coordinates.longitude}")
        
        # Validate coordinates are in South Africa
        if not ValidationUtils.validate_coordinates_in_south_africa(
            coordinates.latitude, coordinates.longitude
        ):
            logger.warning(f"Coordinates outside South Africa bounds: {coordinates.latitude}, {coordinates.longitude}")
        
        # Generate unique project ID
        project_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Get comprehensive land data from all APIs
        land_data = await api_manager.get_comprehensive_land_data(
            coordinates.latitude, coordinates.longitude
        )
        
        # Convert boundaries to BoundaryLayer models
        boundary_layers = []
        for boundary in land_data["boundaries"]:
            try:
                boundary_layer = BoundaryLayer(
                    layer_name=boundary["layer_name"],
                    layer_type=boundary["layer_type"],
                    geometry=boundary.get("geometry"),
                    properties=boundary.get("properties", {}),
                    source_api=boundary["source_api"]
                )
                boundary_layers.append(boundary_layer)
            except Exception as e:
                logger.warning(f"Failed to create boundary layer: {str(e)}")
                continue
        
        # Generate CAD files
        files_generated = []
        if boundary_layers:
            try:
                # Convert BoundaryLayer models back to dict format for CAD generation
                boundaries_for_cad = [
                    {
                        "layer_name": bl.layer_name,
                        "layer_type": bl.layer_type,
                        "geometry": bl.geometry.dict() if bl.geometry else {},
                        "properties": bl.properties,
                        "source_api": bl.source_api
                    }
                    for bl in boundary_layers
                ]
                
                cad_files = await cad_manager.generate_project_cad_layers(
                    project_id, coordinates.project_name, boundaries_for_cad
                )
                files_generated = list(cad_files.keys())
                logger.info(f"Generated {len(files_generated)} CAD files")
            except Exception as e:
                logger.error(f"CAD generation failed: {str(e)}")
                files_generated = []
        
        # Determine project status
        project_status = ProjectStatus.COMPLETED
        if not boundary_layers:
            project_status = ProjectStatus.NO_DATA_FOUND
        elif land_data.get("errors"):
            project_status = ProjectStatus.PROCESSING  # Partial success
        
        # Create project in database
        project_data = ProjectInDB(
            project_id=project_id,
            name=coordinates.project_name,
            coordinates={"latitude": coordinates.latitude, "longitude": coordinates.longitude},
            created=timestamp,
            last_modified=timestamp,
            data={
                "boundaries": [bl.dict() for bl in boundary_layers],
                "files_generated": files_generated,
                "errors": land_data.get("errors", []),
                "api_response": land_data
            }
        )
        
        db_result = await db_service.create_project(project_data)
        if not db_result["success"]:
            logger.error(f"Failed to save project to database: {db_result.get('error')}")
            # Continue anyway - don't fail the request if database save fails
        
        # Create response
        response_data = {
            "project_id": project_id,
            "coordinates": {"latitude": coordinates.latitude, "longitude": coordinates.longitude},
            "boundaries": boundary_layers,
            "files_generated": files_generated,
            "status": project_status,
            "created_at": timestamp,
            "total_boundaries": len(boundary_layers)
        }
        
        # Add elevation statistics if available
        if land_data.get("elevation_stats"):
            response_data["elevation_stats"] = land_data["elevation_stats"]
        
        response = LandDataResponse(**response_data)
        
        logger.info(f"Land identification complete: {len(boundary_layers)} boundaries found")
        return response
        
    except Exception as e:
        logger.error(f"Land identification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to identify land: {str(e)}"
        )

@app.get("/api/project/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """Get project details by ID"""
    try:
        # Validate project ID format
        if not ValidationUtils.validate_project_id(project_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid project ID format"
            )
        
        # Get project from database
        project = await db_service.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )
        
        # Convert to response format
        boundaries = []
        if project.data and project.data.get("boundaries"):
            boundaries = project.data["boundaries"]
        
        response = ProjectResponse(
            id=project.project_id,
            name=project.name,
            coordinates=project.coordinates,
            created=project.created,
            lastModified=project.last_modified,
            data=boundaries,
            layers=project.layers
        )
        
        logger.info(f"Retrieved project: {project_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve project"
        )

@app.get("/api/projects", response_model=ProjectListResponse)
async def list_projects(limit: int = 100, skip: int = 0, search: Optional[str] = None):
    """List projects with optional search and pagination"""
    try:
        # Validate pagination parameters
        if limit < 1 or limit > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 1000"
            )
        
        if skip < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Skip must be non-negative"
            )
        
        # Get projects from database
        result = await db_service.list_projects(limit=limit, skip=skip, search_term=search)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to retrieve projects")
            )
        
        response = ProjectListResponse(
            projects=result["projects"],
            total_count=result["total_count"]
        )
        
        logger.info(f"Listed {len(result['projects'])} projects")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list projects: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve projects"
        )

@app.get("/api/download-files/{project_id}")
async def download_files(project_id: str):
    """Download CAD files for a project as ZIP package"""
    try:
        # Validate project ID
        if not ValidationUtils.validate_project_id(project_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid project ID format"
            )
        
        # Get project from database
        project = await db_service.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )
        
        # Get project boundaries for CAD generation
        boundaries = []
        if project.data and project.data.get("boundaries"):
            boundaries = project.data["boundaries"]
        
        if not boundaries:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No boundary data available for this project"
            )
        
        # Generate CAD files
        cad_files = await cad_manager.generate_project_cad_layers(
            project.project_id, project.name, boundaries
        )
        
        if not cad_files:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate CAD files"
            )
        
        # Create ZIP package
        zip_bytes = cad_manager.create_cad_package_zip(cad_files, project.name)
        
        # Sanitize filename
        safe_project_name = ValidationUtils.sanitize_filename(project.name)
        filename = f"{safe_project_name}_CAD_Package.zip"
        
        logger.info(f"Generated CAD package for project {project_id}: {filename}")
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(zip_bytes),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download files for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download files"
        )

@app.get("/api/statistics")
async def get_statistics():
    """Get application statistics"""
    try:
        db_stats = await db_service.get_project_statistics()
        
        return {
            "application": {
                "name": settings.app_name,
                "version": settings.app_version,
                "environment": settings.environment
            },
            "database": db_stats,
            "configuration": {
                "arcgis_configured": settings.has_arcgis_credentials,
                "afrigis_configured": settings.has_afrigis_credentials,
                "cache_ttl_seconds": settings.cache_ttl_seconds
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )

@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a specific project by ID"""
    try:
        result = await db_service.delete_project(project_id)
        
        if result.get("success"):
            logger.info(f"Project deleted: {project_id}")
            return {
                "message": f"Successfully deleted project {project_id}",
                "project_id": project_id,
                "success": True
            }
        else:
            error_type = result.get("error_type", "unknown")
            if error_type == "not_found":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Project {project_id} not found"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.get("error", "Failed to delete project")
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}"
        )

@app.delete("/api/projects/delete-all")
async def delete_all_projects():
    """Delete all projects from the database"""
    try:
        result = await db_service.delete_all_projects()
        
        if result.get("success"):
            logger.info(f"All projects deleted: {result.get('deleted_count', 0)} projects removed")
            return {
                "message": f"Successfully deleted {result.get('deleted_count', 0)} projects",
                "deleted_count": result.get("deleted_count", 0),
                "success": True
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to delete projects")
            )
            
    except Exception as e:
        logger.error(f"Error deleting all projects: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete all projects: {str(e)}"
        )

# ================================
# Open Topo Data API Endpoints  
# ================================

@app.get("/api/elevation/{latitude}/{longitude}")
async def get_elevation_point(latitude: float, longitude: float, dataset: Optional[str] = "srtm30m"):
    """Get elevation data for a specific coordinate point"""
    try:
        if not api_manager.open_topo_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Open Topo Data service not available"
            )
        
        # Validate coordinates
        if not ValidationUtils.validate_coordinates_in_south_africa(latitude, longitude):
            logger.warning(f"Coordinates outside South Africa bounds: {latitude}, {longitude}")
        
        # Query elevation data
        elevation_response = await api_manager.open_topo_service.query_by_coordinates(
            latitude, longitude, dataset=dataset
        )
        
        if elevation_response.success:
            return {
                "success": True,
                "coordinates": {"latitude": latitude, "longitude": longitude},
                "elevation_data": elevation_response.data,
                "dataset": dataset,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Elevation query failed: {elevation_response.error}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get elevation data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve elevation data"
        )

@app.post("/api/elevation/grid")
async def generate_elevation_grid(coordinates: CoordinateInput, 
                                grid_size_km: Optional[float] = 2.0,
                                grid_points: Optional[int] = 10,
                                dataset: Optional[str] = "srtm30m"):
    """Generate elevation grid around coordinates for contour analysis"""
    try:
        if not api_manager.open_topo_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Open Topo Data service not available"
            )
        
        # Validate parameters
        if grid_size_km <= 0 or grid_size_km > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Grid size must be between 0 and 10 kilometers"
            )
        
        if grid_points < 3 or grid_points > 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Grid points must be between 3 and 20"
            )
        
        # Generate elevation grid
        grid_response = await api_manager.open_topo_service.generate_elevation_grid(
            coordinates.latitude, coordinates.longitude,
            grid_size_km=grid_size_km, grid_points=grid_points, dataset=dataset
        )
        
        if grid_response.success:
            return {
                "success": True,
                "center_coordinates": {"latitude": coordinates.latitude, "longitude": coordinates.longitude},
                "grid_parameters": {
                    "size_km": grid_size_km,
                    "points": grid_points,
                    "dataset": dataset
                },
                "elevation_grid": grid_response.data,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Elevation grid generation failed: {grid_response.error}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate elevation grid: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate elevation grid"
        )

@app.get("/api/elevation/datasets")
async def get_available_datasets():
    """Get available elevation datasets"""
    try:
        if not api_manager.open_topo_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Open Topo Data service not available"
            )
        
        return {
            "available_datasets": api_manager.open_topo_service.datasets,
            "default_dataset": "srtm30m",
            "interpolation_methods": ["bilinear", "nearest", "cubic"],
            "service_status": api_manager.open_topo_service.get_service_status(),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dataset information: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dataset information"
        )

# ================================
# Contour Generation API Endpoints  
# ================================

@app.post("/api/contours/generate")
async def generate_contours(request: dict):
    """Generate elevation contour lines for a specified area"""
    try:
        if not api_manager.contour_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Contour generation service not available"
            )
        
        # Extract parameters
        center_lat = request.get("latitude")
        center_lng = request.get("longitude")
        contour_interval = request.get("contour_interval", 2.0)
        grid_size_km = request.get("grid_size_km", 3.0)
        grid_points = request.get("grid_points", 15)
        dataset = request.get("dataset", "srtm30m")
        
        if center_lat is None or center_lng is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Latitude and longitude are required"
            )
        
        # Validate parameters
        if not (-90 <= center_lat <= 90):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid latitude. Must be between -90 and 90"
            )
        
        if not (-180 <= center_lng <= 180):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid longitude. Must be between -180 and 180"
            )
        
        if contour_interval <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contour interval must be positive"
            )
        
        logger.info(f"Generating contours for {center_lat}, {center_lng} with {contour_interval}m intervals")
        
        # Generate contours
        contour_response = await api_manager.contour_service.generate_contours(
            center_lat=center_lat,
            center_lng=center_lng,
            contour_interval=contour_interval,
            grid_size_km=grid_size_km,
            grid_points=grid_points,
            dataset=dataset
        )
        
        if not contour_response.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Contour generation failed: {contour_response.error}"
            )
        
        return {
            "success": True,
            "contour_data": contour_response.data,
            "message": f"Generated {len(contour_response.data.get('contour_lines', []))} contour lines",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Contour generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate contour lines"
        )

@app.get("/api/contours/styles")
async def get_contour_styles():
    """Get available contour line styling options"""
    try:
        if not api_manager.contour_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Contour generation service not available"
            )
        
        return {
            "contour_styles": api_manager.contour_service.get_contour_styles(),
            "default_interval": api_manager.contour_service.default_contour_interval,
            "supported_intervals": [0.5, 1.0, 2.0, 5.0, 10.0, 20.0],
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get contour styles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve contour styling information"
        )

# ================================
# External Services API Endpoints
# ================================

@app.get("/api/external-services/status")
async def get_external_services_status():
    """Get status of all external API services including Open Topo Data"""
    try:
        return {
            "external_services": api_manager.get_service_status(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get external services status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve external services status"
        )

# ================================
# Navigation Menu API Endpoints
# ================================

@app.get("/api/menu/api-status", response_model=APIStatusResponse)
async def get_api_status():
    """Get status of all configured APIs for API Management menu"""
    try:
        return await api_management_service.get_api_status()
    except Exception as e:
        logger.error(f"Failed to get API status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API status"
        )

@app.post("/api/menu/api-config")
async def update_api_configuration(update: APIConfigurationUpdate):
    """Update API configuration for API Management menu"""
    try:
        success = await api_management_service.update_api_configuration(update)
        if success:
            return {"message": "API configuration updated successfully", "success": True}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid API name or configuration"
            )
    except Exception as e:
        logger.error(f"Failed to update API config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update API configuration"
        )

@app.get("/api/menu/api-configs")
async def get_api_configurations():
    """Get all API configuration schemas"""
    try:
        return api_management_service.get_all_api_configurations()
    except Exception as e:
        logger.error(f"Failed to get API configurations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API configurations"
        )

@app.get("/api/menu/api-docs/{api_name}")
async def get_api_documentation(api_name: str):
    """Get documentation for a specific API"""
    try:
        docs = api_management_service.get_api_documentation(api_name)
        if docs:
            return docs
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API documentation not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get API documentation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API documentation"
        )

@app.get("/api/menu/user-profile", response_model=UserProfile)
async def get_user_profile(user_id: Optional[str] = None):
    """Get user profile for Profile menu"""
    try:
        return await user_profile_service.get_user_profile(user_id)
    except Exception as e:
        logger.error(f"Failed to get user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )

@app.put("/api/menu/user-profile", response_model=UserProfile)
async def update_user_profile(update_data: UserProfileUpdate, user_id: Optional[str] = None):
    """Update user profile"""
    try:
        return await user_profile_service.update_user_profile(user_id, update_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )

@app.get("/api/menu/user-stats")
async def get_user_statistics(user_id: Optional[str] = None):
    """Get user statistics for Profile menu"""
    try:
        return await user_profile_service.get_user_statistics(user_id)
    except Exception as e:
        logger.error(f"Failed to get user statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )

@app.get("/api/menu/app-statistics", response_model=AppStatistics)
async def get_app_statistics():
    """Get application statistics for Dashboard"""
    try:
        # Get database statistics
        db_stats = await db_service.get_project_statistics()
        
        # Calculate additional metrics
        from datetime import datetime, timedelta
        now = datetime.now()
        today = now.date().isoformat()
        week_ago = (now - timedelta(days=7)).isoformat()
        
        # Get database and count projects
        db = await db_service.get_database()
        projects_collection = db["projects"]
        
        total_projects = await projects_collection.count_documents({})
        projects_today = await projects_collection.count_documents({
            "created": {"$regex": f"^{today}"}
        })
        projects_this_week = await projects_collection.count_documents({
            "created": {"$gte": week_ago}
        })
        
        # Calculate uptime (simplified - from app start)
        import time
        uptime_hours = (time.time() - getattr(app.state, 'start_time', time.time())) / 3600
        
        return AppStatistics(
            total_projects=total_projects,
            projects_created_today=projects_today,
            projects_created_this_week=projects_this_week,
            total_boundaries_processed=db_stats.get("total_projects", 0) * 10,  # Estimate
            avg_processing_time=5.2,  # Estimated average
            uptime_hours=uptime_hours
        )
        
    except Exception as e:
        logger.error(f"Failed to get app statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve application statistics"
        )

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle validation errors"""
    logger.warning(f"Validation error: {str(exc)}")
    return ErrorResponse(
        error="Validation Error",
        detail=str(exc),
        timestamp=datetime.now().isoformat()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return ErrorResponse(
        error="Internal Server Error",
        detail="An unexpected error occurred" if settings.is_production else str(exc),
        timestamp=datetime.now().isoformat()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=settings.is_development
    )