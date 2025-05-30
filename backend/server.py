from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import httpx
import json
import uuid
import os
from datetime import datetime
import zipfile
import io
import base64
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError
import asyncio

# Database configuration
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DATABASE_NAME = "stirling_landdev"
PROJECTS_COLLECTION = "projects"

# Global variables for database
client: AsyncIOMotorClient = None
database = None

async def connect_to_mongo():
    """Create database connection"""
    global client, database
    client = AsyncIOMotorClient(MONGO_URL)
    database = client[DATABASE_NAME]
    
    # Create indexes for better performance
    await database[PROJECTS_COLLECTION].create_index("project_id", unique=True)
    await database[PROJECTS_COLLECTION].create_index("created")
    print(f"✅ Connected to MongoDB: {DATABASE_NAME}")

async def close_mongo_connection():
    """Close database connection"""
    global client
    if client:
        client.close()
        print("❌ Disconnected from MongoDB")

# Pydantic models for database
class ProjectCreate(BaseModel):
    name: str
    latitude: float
    longitude: float

class ProjectInDB(BaseModel):
    project_id: str
    name: str
    coordinates: Dict[str, float]
    created: str
    last_modified: str
    data: Optional[Dict[str, Any]] = None
    layers: Optional[Dict[str, Any]] = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    coordinates: Dict[str, float]
    created: str
    lastModified: str
    data: Optional[Dict[str, Any]] = None
    layers: Optional[Dict[str, Any]] = None

app = FastAPI(title="Stirling Bridge LandDev API")

@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class CoordinateInput(BaseModel):
    latitude: float
    longitude: float
    project_name: Optional[str] = "Land Development Project"

class BoundaryLayer(BaseModel):
    layer_name: str
    layer_type: str
    geometry: Dict[str, Any]
    properties: Dict[str, Any]
    source_api: str

class LandDataResponse(BaseModel):
    project_id: str
    coordinates: Dict[str, float]
    boundaries: List[BoundaryLayer]
    files_generated: List[str]
    status: str
    created_at: str

# CSG API Configuration
CSG_BASE_URL = "https://dffeportal.environment.gov.za/hosting/rest/services/CSG_Cadaster/CSG_Cadastral_Data/MapServer"

# SANBI BGIS API Configuration
SANBI_BASE_URL = "https://bgismaps.sanbi.org/server/rest/services"
SANBI_SERVICES = {
    "contours": {
        "url": f"{SANBI_BASE_URL}/BGIS_Projects/Basedata_rivers_contours/MapServer",
        "layers": {
            "contours": 5,
            "rivers": 4
        }
    },
    "conservation_gauteng": {
        "url": f"{SANBI_BASE_URL}/2024_Gauteng_CBA_Map/MapServer",
        "layers": {
            "protected_areas": 0
        }
    },
    "conservation_national": {
        "url": "https://bgismaps.sanbi.org/server/rest/services/2024_Gauteng_CBA_Map/MapServer",
        "layers": {
            "protected_areas": 0  # Use same service for now since it's working
        }
    }
}

# AfriGIS API Configuration (placeholder for when key is available)
AFRIGIS_BASE_URL = "https://ogc.afrigis.co.za/mapservice"
AFRIGIS_AUTH_KEY = os.environ.get('AFRIGIS_API_KEY', None)  # Will be set when key is available

# In-memory storage for project data (in production, use a proper database)
projects_storage = {}

# Available boundary layers to query
BOUNDARY_LAYERS = {
    "farm_portions": {"layer_id": 1, "name": "Farm Portions"},
    "erven": {"layer_id": 2, "name": "Erven"},
    "holdings": {"layer_id": 3, "name": "Holdings"},
    "public_places": {"layer_id": 4, "name": "Public Places"}
}

async def query_csg_api(latitude: float, longitude: float, layer_id: int):
    """Query the Chief Surveyor General API for boundary data"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Use identify endpoint to find features at the given coordinates
            url = f"{CSG_BASE_URL}/identify"
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
            
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Error querying CSG API for layer {layer_id}: {str(e)}")
        return {"results": []}

async def query_sanbi_bgis(latitude: float, longitude: float, service_name: str, layer_id: int):
    """Query SANBI BGIS API for environmental and topographic data"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            service_config = SANBI_SERVICES.get(service_name)
            if not service_config:
                print(f"Unknown SANBI service: {service_name}")
                return {"results": []}
            
            # Use identify endpoint to find features at the given coordinates
            url = f"{service_config['url']}/identify"
            params = {
                "geometry": json.dumps({"x": longitude, "y": latitude}),
                "geometryType": "esriGeometryPoint",
                "layers": f"visible:{layer_id}",
                "tolerance": 50,  # Larger tolerance for environmental features
                "mapExtent": f"{longitude-0.02},{latitude-0.02},{longitude+0.02},{latitude+0.02}",
                "imageDisplay": "400,400,96",
                "returnGeometry": "true",
                "f": "json"
            }
            
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Error querying SANBI BGIS for {service_name}, layer {layer_id}: {str(e)}")
        return {"results": []}

async def query_afrigis_wfs(latitude: float, longitude: float, layer_name: str):
    """Query AfriGIS WFS for roads and infrastructure data (placeholder for when API key is available)"""
    if not AFRIGIS_AUTH_KEY:
        print("AfriGIS API key not available - skipping AfriGIS data")
        return {"features": []}
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create a bounding box around the coordinates
            bbox = f"{longitude-0.01},{latitude-0.01},{longitude+0.01},{latitude+0.01}"
            
            url = f"{AFRIGIS_BASE_URL}/wfs"
            params = {
                "authkey": AFRIGIS_AUTH_KEY,
                "service": "WFS",
                "version": "1.1.0",
                "request": "GetFeature",
                "typeName": layer_name,
                "bbox": bbox,
                "outputFormat": "application/json"
            }
            
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Error querying AfriGIS WFS for {layer_name}: {str(e)}")
        return {"features": []}

async def query_additional_boundaries(latitude: float, longitude: float):
    """Query additional data sources - SANBI BGIS and AfriGIS"""
    additional_boundaries = []
    
    # Query SANBI BGIS for contours and rivers
    try:
        # Query contours
        contour_data = await query_sanbi_bgis(latitude, longitude, "contours", 5)
        if contour_data.get("results"):
            for result in contour_data["results"]:
                if result.get("geometry") and result.get("attributes"):
                    boundary = BoundaryLayer(
                        layer_name=f"Contour_{result['attributes'].get('OBJECTID', 'unknown')}",
                        layer_type="Contours",
                        geometry=result["geometry"],
                        properties=result["attributes"],
                        source_api="SANBI_BGIS"
                    )
                    additional_boundaries.append(boundary)
        
        # Query rivers/water bodies
        river_data = await query_sanbi_bgis(latitude, longitude, "contours", 4)
        if river_data.get("results"):
            for result in river_data["results"]:
                if result.get("geometry") and result.get("attributes"):
                    boundary = BoundaryLayer(
                        layer_name=f"River_{result['attributes'].get('OBJECTID', 'unknown')}",
                        layer_type="Water Bodies",
                        geometry=result["geometry"],
                        properties=result["attributes"],
                        source_api="SANBI_BGIS"
                    )
                    additional_boundaries.append(boundary)
        
        # Query protected areas from multiple sources
        protected_areas_found = False
        
        # Try Gauteng Conservation Plan
        try:
            gauteng_protected_data = await query_sanbi_bgis(latitude, longitude, "conservation_gauteng", 0)
            if gauteng_protected_data.get("results"):
                for result in gauteng_protected_data["results"]:
                    if result.get("geometry") and result.get("attributes"):
                        # Determine protection level or type
                        attrs = result["attributes"]
                        protection_type = attrs.get("CBA_ESA", attrs.get("CBACat", "Conservation Area"))
                        
                        boundary = BoundaryLayer(
                            layer_name=f"Conservation_{protection_type}_{result['attributes'].get('OBJECTID', 'unknown')}",
                            layer_type="Environmental Constraints",
                            geometry=result["geometry"],
                            properties=result["attributes"],
                            source_api="SANBI_BGIS_Gauteng"
                        )
                        additional_boundaries.append(boundary)
                        protected_areas_found = True
        except Exception as e:
            print(f"Error querying Gauteng conservation areas: {str(e)}")
        
        # Try National Protected Areas if Gauteng didn't find any
        if not protected_areas_found:
            try:
                national_protected_data = await query_sanbi_bgis(latitude, longitude, "conservation_national", 0)
                if national_protected_data.get("results"):
                    for result in national_protected_data["results"]:
                        if result.get("geometry") and result.get("attributes"):
                            attrs = result["attributes"]
                            area_name = attrs.get("NAME", attrs.get("AREA_NAME", "Protected Area"))
                            
                            boundary = BoundaryLayer(
                                layer_name=f"Protected_Area_{area_name}_{result['attributes'].get('OBJECTID', 'unknown')}",
                                layer_type="Environmental Constraints",
                                geometry=result["geometry"],
                                properties=result["attributes"],
                                source_api="SANBI_BGIS_National"
                            )
                            additional_boundaries.append(boundary)
            except Exception as e:
                print(f"Error querying national protected areas: {str(e)}")
    
    except Exception as e:
        print(f"Error querying SANBI BGIS: {str(e)}")
    
    # Query AfriGIS for roads (if API key is available)
    try:
        if AFRIGIS_AUTH_KEY:
            # This is a placeholder structure - actual layer names need to be verified with AfriGIS documentation
            road_data = await query_afrigis_wfs(latitude, longitude, "roads_major")  # Placeholder layer name
            if road_data.get("features"):
                for feature in road_data["features"]:
                    if feature.get("geometry") and feature.get("properties"):
                        boundary = BoundaryLayer(
                            layer_name=f"Road_{feature['properties'].get('id', 'unknown')}",
                            layer_type="Roads",
                            geometry=feature["geometry"],
                            properties=feature["properties"],
                            source_api="AfriGIS"
                        )
                        additional_boundaries.append(boundary)
    except Exception as e:
        print(f"Error querying AfriGIS: {str(e)}")
    
    return additional_boundaries

def convert_to_dwg_layers(boundaries: List[BoundaryLayer]) -> Dict[str, Any]:
    """Convert boundary data to DWG-compatible layer structure"""
    dwg_layers = {
        "layers": [],
        "metadata": {
            "coordinate_system": "WGS84",
            "units": "decimal_degrees",
            "created_at": datetime.now().isoformat()
        }
    }
    
    for boundary in boundaries:
        layer = {
            "name": boundary.layer_name,
            "type": boundary.layer_type,
            "geometry": boundary.geometry,
            "properties": boundary.properties,
            "style": {
                "color": get_layer_color(boundary.layer_type),
                "line_weight": get_layer_weight(boundary.layer_type)
            }
        }
        dwg_layers["layers"].append(layer)
    
    return dwg_layers

def get_layer_color(layer_type: str) -> str:
    """Assign colors to different layer types"""
    color_map = {
        "Farm Portions": "#00FF00",           # Green
        "Erven": "#0000FF",                   # Blue
        "Holdings": "#FFFF00",                # Yellow
        "Public Places": "#FF00FF",           # Magenta
        "Contours": "#8B4513",               # Brown
        "Water Bodies": "#00BFFF",           # Deep Sky Blue
        "Environmental Constraints": "#228B22", # Forest Green
        "Roads": "#FF6347"                   # Tomato Red
    }
    return color_map.get(layer_type, "#000000")

def get_layer_weight(layer_type: str) -> float:
    """Assign line weights to different layer types"""
    weight_map = {
        "Farm Portions": 0.6,
        "Erven": 0.4,
        "Holdings": 0.5,
        "Public Places": 0.3,
        "Contours": 0.2,
        "Water Bodies": 0.8,
        "Environmental Constraints": 0.7,
        "Roads": 0.9
    }
    return weight_map.get(layer_type, 0.5)

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "Stirling Bridge LandDev API"}

@app.post("/api/identify-land", response_model=LandDataResponse)
async def identify_land(coordinate_input: CoordinateInput):
    """Main endpoint to identify land and retrieve boundary data"""
    try:
        project_id = str(uuid.uuid4())
        boundaries = []
        
        # Query CSG API for all boundary layers
        for layer_key, layer_info in BOUNDARY_LAYERS.items():
            csg_data = await query_csg_api(
                coordinate_input.latitude, 
                coordinate_input.longitude, 
                layer_info["layer_id"]
            )
            
            # Process CSG results
            if csg_data.get("results"):
                for result in csg_data["results"]:
                    if result.get("geometry") and result.get("attributes"):
                        boundary = BoundaryLayer(
                            layer_name=f"{layer_info['name']}_{result['attributes'].get('OBJECTID', 'unknown')}",
                            layer_type=layer_info["name"],
                            geometry=result["geometry"],
                            properties=result["attributes"],
                            source_api="CSG"
                        )
                        boundaries.append(boundary)
        
        # Query additional boundary sources
        additional_boundaries = await query_additional_boundaries(
            coordinate_input.latitude, 
            coordinate_input.longitude
        )
        boundaries.extend(additional_boundaries)
        
        # Convert to DWG format
        dwg_data = convert_to_dwg_layers(boundaries)
        
        # Generate files for architect
        files_generated = []
        
        # Create JSON file with all boundary data
        json_filename = f"land_boundaries_{project_id}.json"
        files_generated.append(json_filename)
        
        # Create DWG-ready file
        dwg_filename = f"boundaries_for_cad_{project_id}.json"
        files_generated.append(dwg_filename)
        
        # Prepare response
        response = LandDataResponse(
            project_id=project_id,
            coordinates={
                "latitude": coordinate_input.latitude,
                "longitude": coordinate_input.longitude
            },
            boundaries=boundaries,
            files_generated=files_generated,
            status="completed" if boundaries else "no_data_found",
            created_at=datetime.now().isoformat()
        )
        
        # Store project data in MongoDB
        project_data = ProjectInDB(
            project_id=project_id,
            name=coordinate_input.project_name,
            coordinates={
                "latitude": coordinate_input.latitude,
                "longitude": coordinate_input.longitude
            },
            created=datetime.now().isoformat(),
            last_modified=datetime.now().isoformat(),
            data={
                "response": response.dict(),
                "dwg_data": dwg_data,
                "raw_boundaries": [b.dict() for b in boundaries]
            }
        )
        
        try:
            await database[PROJECTS_COLLECTION].insert_one(project_data.dict())
        except DuplicateKeyError:
            raise HTTPException(status_code=400, detail="Project ID already exists")
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing land identification: {str(e)}")

@app.get("/api/download-files/{project_id}")
async def download_files(project_id: str):
    """Generate and download a ZIP file containing all project data"""
    try:
        # Get project from MongoDB
        project_doc = await database[PROJECTS_COLLECTION].find_one({"project_id": project_id})
        if not project_doc:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project_data = ProjectInDB(**project_doc)
        response_data = project_data.data["response"]
        dwg_data = project_data.data["dwg_data"]
        project_name = project_data.name
        
        # Create a ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add project summary JSON
            project_summary = {
                "project_name": project_name,
                "project_id": project_id,
                "coordinates": response_data["coordinates"],
                "status": response_data["status"],
                "created_at": response_data["created_at"],
                "total_boundaries": len(response_data["boundaries"])
            }
            zip_file.writestr(
                f"{project_name.replace(' ', '_')}_summary.json",
                json.dumps(project_summary, indent=2)
            )
            
            # Add DWG-ready data
            zip_file.writestr(
                f"{project_name.replace(' ', '_')}_dwg_data.json",
                json.dumps(dwg_data, indent=2)
            )
            
            # Add detailed boundary data
            boundaries_data = []
            for boundary in response_data["boundaries"]:
                boundaries_data.append({
                    "layer_name": boundary["layer_name"],
                    "layer_type": boundary["layer_type"],
                    "geometry": boundary["geometry"],
                    "properties": boundary["properties"],
                    "source_api": boundary["source_api"]
                })
            
            zip_file.writestr(
                f"{project_name.replace(' ', '_')}_boundaries.json",
                json.dumps(boundaries_data, indent=2)
            )
            
            # Add coordinate reference file
            coordinates_text = f"""Land Development Project: {project_name}
Project ID: {project_id}
Search Coordinates: {response_data["coordinates"]["latitude"]}, {response_data["coordinates"]["longitude"]}
Date Generated: {response_data["created_at"]}
Total Boundary Layers Found: {len(response_data["boundaries"])}

Coordinate Reference System: WGS84 (EPSG:4326)
Format: Decimal Degrees

Boundary Types Found:
"""
            for boundary in response_data["boundaries"]:
                coordinates_text += f"- {boundary['layer_type']}: {boundary['layer_name']}\n"
            
            zip_file.writestr(
                f"{project_name.replace(' ', '_')}_coordinates.txt",
                coordinates_text
            )
            
            # Add README file
            readme_content = f"""STIRLING BRIDGE LANDDEV - PROJECT FILES
========================================

Project Name: {project_name}
Project ID: {project_id}
Generated: {response_data["created_at"]}

FILES INCLUDED:
===============

1. {project_name.replace(' ', '_')}_summary.json
   - Project overview and metadata
   - Coordinate information
   - Boundary count summary

2. {project_name.replace(' ', '_')}_dwg_data.json
   - DWG-ready boundary data with layers
   - Formatted for CAD software import
   - Includes color coding and line weights

3. {project_name.replace(' ', '_')}_boundaries.json
   - Detailed boundary geometry data
   - Property information and attributes
   - Source API references

4. {project_name.replace(' ', '_')}_coordinates.txt
   - Human-readable coordinate information
   - Project details and boundary summary
   - Coordinate reference system info

USAGE INSTRUCTIONS:
==================

For Architects & CAD Users:
- Use the *_dwg_data.json file for importing into CAD software
- Color codes and layer information are included
- Coordinate system is WGS84 (EPSG:4326)

For GIS Applications:
- Use the *_boundaries.json file for detailed geometry
- Contains full property attributes and metadata
- Compatible with most GIS software

For Project Management:
- Reference the *_summary.json for project overview
- Use coordinates.txt for quick reference information

SUPPORT:
========
Generated by Stirling Bridge LandDev Platform
For support, contact your development team
"""
            
            zip_file.writestr("README.txt", readme_content)
        
        zip_buffer.seek(0)
        
        # Create filename
        safe_project_name = project_name.replace(' ', '_').replace('/', '_')
        filename = f"stirling_bridge_{safe_project_name}_{project_id[:8]}.zip"
        
        # Return the ZIP file as a streaming response
        return StreamingResponse(
            io.BytesIO(zip_buffer.read()),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating download: {str(e)}")

@app.get("/api/project/{project_id}")
async def get_project_data(project_id: str):
    """Retrieve project data by ID"""
    project_doc = await database[PROJECTS_COLLECTION].find_one({"project_id": project_id})
    if not project_doc:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_data = ProjectInDB(**project_doc)
    return ProjectResponse(
        id=project_data.project_id,
        name=project_data.name,
        coordinates=project_data.coordinates,
        created=project_data.created,
        lastModified=project_data.last_modified,
        data=project_data.data.get("response", {}).get("data"),
        layers=project_data.data.get("response", {}).get("layers")
    )

@app.get("/api/boundary-types")
async def get_available_boundary_types():
    """Get list of available boundary types that can be queried"""
    return {
        "csg_layers": BOUNDARY_LAYERS,
        "additional_sources": [
            "Municipal Boundaries",
            "Ward Boundaries", 
            "Conservation Areas",
            "Agricultural Zones",
            "Environmental Sensitive Areas",
            "Heritage Sites"
        ],
        "note": "Additional sources are planned for future implementation"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
