#!/usr/bin/env python3
"""
Project Deletion Testing Script

This script tests the project deletion functionality of the Stirling Bridge LandDev API.
It verifies that:
1. Projects can be listed
2. Projects can be deleted
3. Deletion properly removes projects from the database
4. Error handling works for non-existent projects
5. Multiple projects can be deleted in sequence
"""

import requests
import json
import time
import os
import sys
from pprint import pprint
import uuid

# Get backend URL from environment or use default
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE_URL = f"{BACKEND_URL}/api"

# Test coordinates for creating test projects
JOHANNESBURG_COORDS = {"latitude": -26.2041, "longitude": 28.0473}
DURBAN_COORDS = {"latitude": -29.8587, "longitude": 31.0218}
CAPE_TOWN_COORDS = {"latitude": -33.9249, "longitude": 18.4241}

def print_separator(title):
    """Print a separator with a title"""
    print("\n" + "="*80)
    print(f" {title} ".center(80, "="))
    print("="*80 + "\n")

def create_test_project(name, coords):
    """Create a test project with the given name and coordinates"""
    print(f"Creating test project: {name}")
    
    try:
        payload = {
            "latitude": coords["latitude"],
            "longitude": coords["longitude"],
            "project_name": name
        }
        
        response = requests.post(f"{API_BASE_URL}/identify-land", json=payload)
        response.raise_for_status()
        
        data = response.json()
        project_id = data.get("project_id")
        
        print(f"Created project: {name} with ID: {project_id}")
        return project_id
    except Exception as e:
        print(f"Error creating test project: {str(e)}")
        return None

def test_list_projects():
    """Test listing all projects"""
    print_separator("LISTING ALL PROJECTS")
    
    try:
        response = requests.get(f"{API_BASE_URL}/projects")
        response.raise_for_status()
        
        data = response.json()
        print(f"Status Code: {response.status_code}")
        print(f"Total Projects: {data['total_count']}")
        
        if data['projects']:
            print(f"\nProjects ({len(data['projects'])}):")
            for i, project in enumerate(data['projects'], 1):
                print(f"{i}. ID: {project['id']} - Name: {project['name']}")
        else:
            print("\nNo projects found.")
        
        return data
    except Exception as e:
        print(f"Error listing projects: {str(e)}")
        return None

def test_delete_project(project_id):
    """Test deleting a specific project"""
    print_separator(f"DELETING PROJECT: {project_id}")
    
    try:
        response = requests.delete(f"{API_BASE_URL}/projects/{project_id}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Response:")
            pprint(data)
            print(f"\nProject {project_id} deleted successfully!")
            return True
        else:
            print("Response:")
            pprint(response.json())
            print(f"\nFailed to delete project {project_id}")
            return False
    except Exception as e:
        print(f"Error deleting project: {str(e)}")
        return False

def test_delete_nonexistent_project():
    """Test deleting a non-existent project"""
    print_separator("DELETING NON-EXISTENT PROJECT")
    
    non_existent_id = str(uuid.uuid4())
    print(f"Using non-existent project ID: {non_existent_id}")
    
    try:
        response = requests.delete(f"{API_BASE_URL}/projects/{non_existent_id}")
        print(f"Status Code: {response.status_code}")
        print("Response:")
        pprint(response.json())
        
        if response.status_code == 404:
            print("\nCorrectly returned 404 for non-existent project")
            return True
        else:
            print("\nUnexpected response for non-existent project")
            return False
    except Exception as e:
        print(f"Error in non-existent project test: {str(e)}")
        return False

def test_delete_same_project_twice(project_id):
    """Test deleting the same project twice"""
    print_separator(f"DELETING PROJECT TWICE: {project_id}")
    
    # First deletion
    print("First deletion attempt:")
    first_result = test_delete_project(project_id)
    
    # Second deletion (should fail)
    print("\nSecond deletion attempt:")
    try:
        response = requests.delete(f"{API_BASE_URL}/projects/{project_id}")
        print(f"Status Code: {response.status_code}")
        print("Response:")
        pprint(response.json())
        
        if response.status_code == 404:
            print("\nCorrectly returned 404 for already deleted project")
            return True
        else:
            print("\nUnexpected response for second deletion")
            return False
    except Exception as e:
        print(f"Error in second deletion test: {str(e)}")
        return False

def test_multiple_deletions(project_ids, count=3):
    """Test deleting multiple projects in sequence"""
    print_separator("MULTIPLE PROJECT DELETIONS")
    
    if len(project_ids) < count:
        print(f"Not enough projects to delete {count} projects. Only {len(project_ids)} available.")
        count = len(project_ids)
    
    success_count = 0
    for i in range(count):
        if i < len(project_ids):
            project_id = project_ids[i]
            print(f"\nDeleting project {i+1}/{count}: {project_id}")
            if test_delete_project(project_id):
                success_count += 1
    
    print(f"\nSuccessfully deleted {success_count}/{count} projects")
    return success_count == count

def verify_deletion(project_id):
    """Verify a project was actually removed by trying to retrieve it"""
    print_separator(f"VERIFYING DELETION: {project_id}")
    
    try:
        response = requests.get(f"{API_BASE_URL}/project/{project_id}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 404:
            print(f"Project {project_id} was successfully deleted (404 Not Found)")
            return True
        else:
            print(f"Project {project_id} still exists! Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print("Project data:")
                pprint(data)
            return False
    except Exception as e:
        print(f"Error verifying deletion: {str(e)}")
        return False

def run_all_tests():
    """Run all project deletion tests"""
    print_separator("PROJECT DELETION TESTING")
    
    # Get initial project list
    initial_data = test_list_projects()
    if not initial_data:
        print("Failed to get initial project list. Aborting tests.")
        return False
    
    initial_count = initial_data['total_count']
    print(f"\nInitial project count: {initial_count}")
    
    # Create test projects if needed
    test_projects = []
    if initial_count < 3:
        print("\nCreating test projects for deletion testing...")
        project1 = create_test_project("Deletion Test Project 1", JOHANNESBURG_COORDS)
        project2 = create_test_project("Deletion Test Project 2", DURBAN_COORDS)
        project3 = create_test_project("Deletion Test Project 3", CAPE_TOWN_COORDS)
        
        if project1 and project2 and project3:
            test_projects = [project1, project2, project3]
            print(f"Created {len(test_projects)} test projects")
        else:
            print("Failed to create all test projects")
    
    # Get updated project list
    updated_data = test_list_projects()
    if not updated_data:
        print("Failed to get updated project list. Aborting tests.")
        return False
    
    # Get project IDs for testing
    project_ids = [project['id'] for project in updated_data['projects']]
    
    # Test deleting a non-existent project
    test_delete_nonexistent_project()
    
    # If we have at least 1 project, test deleting the same project twice
    if project_ids:
        test_delete_same_project_twice(project_ids[0])
        # First project is now deleted, remove it from the list
        project_ids.pop(0)
    
    # If we have at least 2 more projects, test multiple deletions
    if len(project_ids) >= 2:
        test_multiple_deletions(project_ids[:2], 2)
    
    # Get final project list
    print("\nChecking final project list after deletions:")
    final_data = test_list_projects()
    if final_data:
        final_count = final_data['total_count']
        print(f"\nFinal project count: {final_count}")
        print(f"Projects deleted: {initial_count + len(test_projects) - final_count}")
    
    print_separator("TESTING COMPLETE")
    return True

if __name__ == "__main__":
    # Get the backend URL from frontend/.env
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    BACKEND_URL = line.strip().split('=')[1].strip('"\'')
                    API_BASE_URL = f"{BACKEND_URL}/api"
                    break
    except Exception as e:
        print(f"Warning: Could not read REACT_APP_BACKEND_URL from frontend/.env: {e}")
        print(f"Using default API base URL: {API_BASE_URL}")
    
    print(f"Using API base URL: {API_BASE_URL}")
    run_all_tests()