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

app = FastAPI(title="Stirling Bridge LandDev API")

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

# In-memory storage for project data (in production, use a proper database)
projects_storage = {}

# Available boundary layers to query
BOUNDARY_LAYERS = {
    "parent_farms": {"layer_id": 0, "name": "Parent Farm Boundaries"},
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

async def query_additional_boundaries(latitude: float, longitude: float):
    """Query additional boundary sources (placeholder for expansion)"""
    # This is where we'll add queries to other South African boundary APIs
    # Municipal boundaries, ward boundaries, conservation areas, etc.
    additional_boundaries = []
    
    # Placeholder for municipal boundaries API
    # municipal_data = await query_municipal_api(latitude, longitude)
    # additional_boundaries.extend(municipal_data)
    
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
        "Parent Farm Boundaries": "#FF0000",  # Red
        "Farm Portions": "#00FF00",           # Green
        "Erven": "#0000FF",                   # Blue
        "Holdings": "#FFFF00",                # Yellow
        "Public Places": "#FF00FF"            # Magenta
    }
    return color_map.get(layer_type, "#000000")

def get_layer_weight(layer_type: str) -> float:
    """Assign line weights to different layer types"""
    weight_map = {
        "Parent Farm Boundaries": 0.8,
        "Farm Portions": 0.6,
        "Erven": 0.4,
        "Holdings": 0.5,
        "Public Places": 0.3
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
        
        # Store project data for download
        projects_storage[project_id] = {
            "response": response,
            "dwg_data": dwg_data,
            "project_name": coordinate_input.project_name,
            "raw_boundaries": boundaries
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing land identification: {str(e)}")

@app.get("/api/download-files/{project_id}")
async def download_files(project_id: str):
    """Generate and download a ZIP file containing all project data"""
    try:
        if project_id not in projects_storage:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project_data = projects_storage[project_id]
        response_data = project_data["response"]
        dwg_data = project_data["dwg_data"]
        project_name = project_data["project_name"]
        
        # Create a ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add project summary JSON
            project_summary = {
                "project_name": project_name,
                "project_id": project_id,
                "coordinates": response_data.coordinates,
                "status": response_data.status,
                "created_at": response_data.created_at,
                "total_boundaries": len(response_data.boundaries)
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
            for boundary in response_data.boundaries:
                boundaries_data.append({
                    "layer_name": boundary.layer_name,
                    "layer_type": boundary.layer_type,
                    "geometry": boundary.geometry,
                    "properties": boundary.properties,
                    "source_api": boundary.source_api
                })
            
            zip_file.writestr(
                f"{project_name.replace(' ', '_')}_boundaries.json",
                json.dumps(boundaries_data, indent=2)
            )
            
            # Add coordinate reference file
            coordinates_text = f"""Land Development Project: {project_name}
Project ID: {project_id}
Search Coordinates: {response_data.coordinates['latitude']}, {response_data.coordinates['longitude']}
Date Generated: {response_data.created_at}
Total Boundary Layers Found: {len(response_data.boundaries)}

Coordinate Reference System: WGS84 (EPSG:4326)
Format: Decimal Degrees

Boundary Types Found:
"""
            for boundary in response_data.boundaries:
                coordinates_text += f"- {boundary.layer_type}: {boundary.layer_name}\n"
            
            zip_file.writestr(
                f"{project_name.replace(' ', '_')}_coordinates.txt",
                coordinates_text
            )
            
            # Add README file
            readme_content = f"""STIRLING BRIDGE LANDDEV - PROJECT FILES
========================================

Project Name: {project_name}
Project ID: {project_id}
Generated: {response_data.created_at}

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
    if project_id not in projects_storage:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return projects_storage[project_id]["response"]

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
