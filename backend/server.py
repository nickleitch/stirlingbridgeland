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
from .services.external_api_service import ExternalAPIManager
from .services.database_service import db_service
from .services.validation_service import (
    CoordinateInput, LandDataResponse, ProjectResponse, ProjectListResponse,
    HealthCheckResponse, ErrorResponse, ValidationUtils, ProjectStatus,
    BoundaryLayer, ProjectInDB
)
from .config.settings import settings, LayerConfiguration
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
        response = LandDataResponse(
            project_id=project_id,
            coordinates={"latitude": coordinates.latitude, "longitude": coordinates.longitude},
            boundaries=boundary_layers,
            files_generated=files_generated,
            status=project_status,
            created_at=timestamp,
            total_boundaries=len(boundary_layers)
        )
        
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