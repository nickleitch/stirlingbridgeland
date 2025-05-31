#!/usr/bin/env python3
"""
Contour Persistence Test Script

This script tests if contour boundaries are being properly persisted to the backend database
when generated through the frontend.
"""

import requests
import json
import os
import uuid
import time
import zipfile
import io
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get backend URL from environment variable or use default
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_URL = f"{BACKEND_URL}/api" if not BACKEND_URL.endswith('/api') else BACKEND_URL

logger.info(f"Using API URL: {API_URL}")

def create_test_project():
    """Create a test project for contour generation testing"""
    project_data = {
        "name": f"Contour Test Project {uuid.uuid4().hex[:8]}",
        "description": "Test project for contour persistence testing",
        "coordinates": {
            "latitude": -25.7461,  # Pretoria, South Africa
            "longitude": 28.1881
        },
        "project_type": "land_development"
    }
    
    logger.info(f"Creating test project: {project_data['name']}")
    
    response = requests.post(f"{API_URL}/projects", json=project_data)
    
    if response.status_code != 200:
        logger.error(f"Failed to create project: {response.status_code} - {response.text}")
        return None
    
    project = response.json()
    logger.info(f"Created project with ID: {project['project_id']}")
    return project

def generate_contours(latitude, longitude):
    """Generate contours for the given coordinates"""
    contour_params = {
        "latitude": latitude,
        "longitude": longitude,
        "contour_interval": 2.0,
        "grid_size_km": 3.0,
        "grid_points": 10,
        "dataset": "srtm30m"
    }
    
    logger.info(f"Generating contours for coordinates: {latitude}, {longitude}")
    
    response = requests.post(f"{API_URL}/contours/generate", json=contour_params)
    
    if response.status_code != 200:
        logger.error(f"Failed to generate contours: {response.status_code} - {response.text}")
        return None
    
    contour_data = response.json()
    logger.info(f"Generated {len(contour_data.get('contour_data', {}).get('contour_lines', []))} contour lines")
    return contour_data

def get_project(project_id):
    """Get project data from the backend"""
    logger.info(f"Fetching project with ID: {project_id}")
    
    response = requests.get(f"{API_URL}/projects/{project_id}")
    
    if response.status_code != 200:
        logger.error(f"Failed to get project: {response.status_code} - {response.text}")
        return None
    
    project = response.json()
    return project

def update_project_with_contours(project_id, contour_data):
    """Update project with contour boundaries"""
    # First, get the current project data
    project = get_project(project_id)
    
    if not project:
        logger.error("Cannot update project: project not found")
        return False
    
    # Convert contour data to boundaries format
    boundaries = []
    
    if 'contour_data' in contour_data and 'boundaries' in contour_data['contour_data']:
        boundaries = contour_data['contour_data']['boundaries']
    else:
        logger.error("No boundaries found in contour data")
        return False
    
    # Add boundaries to project data
    current_boundaries = project.get('data', [])
    updated_boundaries = current_boundaries + boundaries
    
    # Update project with new boundaries
    update_data = {
        "project_id": project_id,
        "data": updated_boundaries
    }
    
    logger.info(f"Updating project {project_id} with {len(boundaries)} contour boundaries")
    
    response = requests.put(f"{API_URL}/projects/{project_id}", json=update_data)
    
    if response.status_code != 200:
        logger.error(f"Failed to update project: {response.status_code} - {response.text}")
        return False
    
    logger.info(f"Successfully updated project with contour boundaries")
    return True

def download_cad_export(project_id):
    """Download CAD export for the project"""
    logger.info(f"Downloading CAD export for project: {project_id}")
    
    response = requests.get(f"{API_URL}/projects/{project_id}/export/cad")
    
    if response.status_code != 200:
        logger.error(f"Failed to download CAD export: {response.status_code} - {response.text}")
        return None
    
    logger.info(f"Successfully downloaded CAD export")
    return response.content

def check_contours_in_cad_export(zip_content):
    """Check if contours are included in the CAD export"""
    if not zip_content:
        logger.error("No CAD export content to check")
        return False
    
    try:
        zip_file = zipfile.ZipFile(io.BytesIO(zip_content))
        file_list = zip_file.namelist()
        
        logger.info(f"CAD export contains {len(file_list)} files")
        logger.info(f"Files in CAD export: {file_list}")
        
        # Check if there's a contour file in the export
        contour_files = [f for f in file_list if 'contour' in f.lower() or 'cont_gen' in f.lower()]
        
        if contour_files:
            logger.info(f"Found contour files in CAD export: {contour_files}")
            return True
        else:
            logger.error("No contour files found in CAD export")
            return False
    
    except Exception as e:
        logger.error(f"Error checking CAD export: {str(e)}")
        return False

def test_contour_persistence():
    """Test if contours are properly persisted to the database"""
    # Step 1: Create a test project
    project = create_test_project()
    
    if not project:
        logger.error("Test failed: Could not create test project")
        return False
    
    project_id = project['project_id']
    
    # Step 2: Generate contours
    contour_data = generate_contours(
        project['coordinates']['latitude'],
        project['coordinates']['longitude']
    )
    
    if not contour_data:
        logger.error("Test failed: Could not generate contours")
        return False
    
    # Step 3: Check if there's a PUT endpoint for updating projects
    try:
        # Check if the PUT endpoint exists by making a test request
        response = requests.options(f"{API_URL}/projects/{project_id}")
        if 'PUT' not in response.headers.get('Allow', ''):
            logger.error("Test failed: PUT endpoint for updating projects does not exist")
            return False
        
        logger.info("PUT endpoint for updating projects exists")
    except Exception as e:
        logger.error(f"Error checking PUT endpoint: {str(e)}")
    
    # Step 4: Update project with contour boundaries
    update_success = update_project_with_contours(project_id, contour_data)
    
    if not update_success:
        logger.error("Test failed: Could not update project with contour boundaries")
        return False
    
    # Step 5: Verify if contours are saved to the database
    updated_project = get_project(project_id)
    
    if not updated_project:
        logger.error("Test failed: Could not get updated project")
        return False
    
    # Check if the project data includes contour boundaries
    project_data = updated_project.get('data', [])
    contour_boundaries = [b for b in project_data if b.get('layer_type') == 'Generated Contours']
    
    if not contour_boundaries:
        logger.error("Test failed: No contour boundaries found in project data")
        return False
    
    logger.info(f"Found {len(contour_boundaries)} contour boundaries in project data")
    
    # Step 6: Test CAD export to see if contours are included
    cad_export = download_cad_export(project_id)
    
    if not cad_export:
        logger.error("Test failed: Could not download CAD export")
        return False
    
    # Check if contours are included in the CAD export
    contours_in_cad = check_contours_in_cad_export(cad_export)
    
    if not contours_in_cad:
        logger.error("Test failed: Contours not found in CAD export")
        return False
    
    logger.info("Test passed: Contours are properly persisted and included in CAD export")
    return True

def test_direct_contour_persistence():
    """Test if contours are directly persisted when generated"""
    # Step 1: Create a test project
    project = create_test_project()
    
    if not project:
        logger.error("Test failed: Could not create test project")
        return False
    
    project_id = project['project_id']
    
    # Step 2: Generate contours
    contour_data = generate_contours(
        project['coordinates']['latitude'],
        project['coordinates']['longitude']
    )
    
    if not contour_data:
        logger.error("Test failed: Could not generate contours")
        return False
    
    # Step 3: Wait a moment to ensure any async operations complete
    time.sleep(2)
    
    # Step 4: Check if contours were automatically saved to the project
    updated_project = get_project(project_id)
    
    if not updated_project:
        logger.error("Test failed: Could not get updated project")
        return False
    
    # Check if the project data includes contour boundaries
    project_data = updated_project.get('data', [])
    contour_boundaries = [b for b in project_data if b.get('layer_type') == 'Generated Contours']
    
    if contour_boundaries:
        logger.info(f"Found {len(contour_boundaries)} contour boundaries automatically saved to project")
        logger.info("Test passed: Contours are automatically persisted when generated")
        return True
    else:
        logger.info("No contour boundaries were automatically saved to the project")
        logger.info("This is expected if the frontend is responsible for saving contours")
        return False

def main():
    """Main test function"""
    logger.info("Starting contour persistence tests")
    
    # Test 1: Check if contours are automatically persisted when generated
    direct_persistence = test_direct_contour_persistence()
    
    # Test 2: Check if contours can be manually persisted and included in CAD export
    manual_persistence = test_contour_persistence()
    
    if direct_persistence:
        logger.info("✅ Contours are automatically persisted when generated")
    else:
        logger.info("❌ Contours are not automatically persisted when generated")
        
        if manual_persistence:
            logger.info("✅ Contours can be manually persisted and included in CAD export")
            logger.info("The issue is that the frontend is not calling the PUT endpoint to save contours")
        else:
            logger.info("❌ Contours cannot be manually persisted")
            logger.info("The issue may be with the backend API or database")

if __name__ == "__main__":
    main()