#!/usr/bin/env python3
"""
Stirling Bridge LandDev Backend Test Suite

This script tests the refactored backend service layer architecture to verify
that all improvements are working correctly.
"""

import httpx
import asyncio
import json
import time
import os
from typing import Dict, Any, List
import uuid
import sys

# Test configuration
BACKEND_URL = "http://localhost:8001/api"  # Default local URL
JOHANNESBURG_COORDS = {"latitude": -26.2041, "longitude": 28.0473}
TEST_PROJECT_NAME = "Johannesburg Test Project"

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class BackendTester:
    """Test suite for Stirling Bridge LandDev Backend"""
    
    def __init__(self, base_url: str = None):
        """Initialize the tester with the backend URL"""
        self.base_url = base_url or BACKEND_URL
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_results = []
        self.created_project_id = None
        self.test_stats = {"passed": 0, "failed": 0, "total": 0}
        
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
        
    def log_test(self, test_name: str, passed: bool, details: str = None, response_time: float = None):
        """Log test results with formatting"""
        self.test_stats["total"] += 1
        if passed:
            self.test_stats["passed"] += 1
            status = f"{Colors.OKGREEN}✅ PASSED{Colors.ENDC}"
        else:
            self.test_stats["failed"] += 1
            status = f"{Colors.FAIL}❌ FAILED{Colors.ENDC}"
            
        # Format response time if provided
        time_info = f" ({response_time:.2f}s)" if response_time is not None else ""
        
        # Print test result
        print(f"{Colors.BOLD}{test_name}{Colors.ENDC}: {status}{time_info}")
        if details:
            print(f"  {details}")
            
        # Store result for summary
        self.test_results.append({
            "name": test_name,
            "passed": passed,
            "details": details,
            "response_time": response_time
        })
        
    async def test_health_check(self):
        """Test the health check endpoint"""
        start_time = time.time()
        try:
            response = await self.client.get(f"{self.base_url}/health")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                details = f"Status: {data.get('status')}, Service: {data.get('service')}, Version: {data.get('version')}"
                self.log_test("Health Check Endpoint", True, details, response_time)
                return True
            else:
                self.log_test("Health Check Endpoint", False, 
                             f"Unexpected status code: {response.status_code}", response_time)
                return False
        except Exception as e:
            self.log_test("Health Check Endpoint", False, f"Error: {str(e)}")
            return False
            
    async def test_boundary_types(self):
        """Test the boundary types endpoint"""
        start_time = time.time()
        try:
            response = await self.client.get(f"{self.base_url}/boundary-types")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                boundary_types = data.get("boundary_types", [])
                details = f"Found {len(boundary_types)} boundary types"
                self.log_test("Boundary Types Endpoint", True, details, response_time)
                return True
            else:
                self.log_test("Boundary Types Endpoint", False, 
                             f"Unexpected status code: {response.status_code}", response_time)
                return False
        except Exception as e:
            self.log_test("Boundary Types Endpoint", False, f"Error: {str(e)}")
            return False
            
    async def test_land_identification(self, latitude: float, longitude: float, project_name: str):
        """Test the land identification endpoint with coordinates"""
        start_time = time.time()
        try:
            payload = {
                "latitude": latitude,
                "longitude": longitude,
                "project_name": project_name
            }
            
            response = await self.client.post(f"{self.base_url}/identify-land", json=payload)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.created_project_id = data.get("project_id")
                boundaries = data.get("boundaries", [])
                files = data.get("files_generated", [])
                
                details = f"Project ID: {self.created_project_id}, Found {len(boundaries)} boundaries, Generated {len(files)} files"
                self.log_test("Land Identification Endpoint", True, details, response_time)
                return True
            else:
                self.log_test("Land Identification Endpoint", False, 
                             f"Unexpected status code: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_test("Land Identification Endpoint", False, f"Error: {str(e)}")
            return False
            
    async def test_project_retrieval(self, project_id: str = None):
        """Test retrieving a project by ID"""
        if not project_id and not self.created_project_id:
            self.log_test("Project Retrieval Endpoint", False, "No project ID available for testing")
            return False
            
        project_id = project_id or self.created_project_id
        start_time = time.time()
        
        try:
            response = await self.client.get(f"{self.base_url}/project/{project_id}")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                details = f"Project Name: {data.get('name')}, Created: {data.get('created')}"
                self.log_test("Project Retrieval Endpoint", True, details, response_time)
                return True
            else:
                self.log_test("Project Retrieval Endpoint", False, 
                             f"Unexpected status code: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_test("Project Retrieval Endpoint", False, f"Error: {str(e)}")
            return False
            
    async def test_project_listing(self):
        """Test listing all projects"""
        start_time = time.time()
        try:
            response = await self.client.get(f"{self.base_url}/projects")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                projects = data.get("projects", [])
                details = f"Found {len(projects)} projects, Total count: {data.get('total_count')}"
                self.log_test("Project Listing Endpoint", True, details, response_time)
                return True
            else:
                self.log_test("Project Listing Endpoint", False, 
                             f"Unexpected status code: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_test("Project Listing Endpoint", False, f"Error: {str(e)}")
            return False
            
    async def test_file_download(self, project_id: str = None):
        """Test downloading CAD files for a project"""
        if not project_id and not self.created_project_id:
            self.log_test("File Download Endpoint", False, "No project ID available for testing")
            return False
            
        project_id = project_id or self.created_project_id
        start_time = time.time()
        
        try:
            response = await self.client.get(f"{self.base_url}/download-files/{project_id}")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                content_type = response.headers.get("content-type")
                content_disposition = response.headers.get("content-disposition")
                content_length = len(response.content)
                
                details = f"Content-Type: {content_type}, Size: {content_length} bytes"
                if content_disposition:
                    filename = content_disposition.split('filename=')[1].replace('"', '')
                    details += f", Filename: {filename}"
                    
                self.log_test("File Download Endpoint", True, details, response_time)
                return True
            else:
                self.log_test("File Download Endpoint", False, 
                             f"Unexpected status code: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_test("File Download Endpoint", False, f"Error: {str(e)}")
            return False
            
    async def test_statistics_endpoint(self):
        """Test the statistics endpoint"""
        start_time = time.time()
        try:
            response = await self.client.get(f"{self.base_url}/statistics")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                app_info = data.get("application", {})
                db_info = data.get("database", {})
                
                details = f"App: {app_info.get('name')} v{app_info.get('version')}, Environment: {app_info.get('environment')}"
                if db_info:
                    details += f", Total Projects: {db_info.get('total_projects')}"
                    
                self.log_test("Statistics Endpoint", True, details, response_time)
                return True
            else:
                self.log_test("Statistics Endpoint", False, 
                             f"Unexpected status code: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_test("Statistics Endpoint", False, f"Error: {str(e)}")
            return False
            
    async def test_error_handling(self):
        """Test error handling with invalid inputs"""
        # Test invalid project ID format
        start_time = time.time()
        try:
            invalid_id = "not-a-valid-uuid"
            response = await self.client.get(f"{self.base_url}/project/{invalid_id}")
            response_time = time.time() - start_time
            
            if response.status_code in [400, 404, 422]:
                details = f"Status code: {response.status_code}, Error message: {response.json().get('detail')}"
                self.log_test("Error Handling - Invalid Project ID", True, details, response_time)
                return True
            else:
                self.log_test("Error Handling - Invalid Project ID", False, 
                             f"Unexpected status code: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_test("Error Handling - Invalid Project ID", False, f"Error: {str(e)}")
            return False
            
    async def test_invalid_coordinates(self):
        """Test validation with invalid coordinates"""
        start_time = time.time()
        try:
            # Test coordinates outside valid range
            payload = {
                "latitude": 100.0,  # Invalid latitude (>90)
                "longitude": 28.0473,
                "project_name": "Invalid Coordinates Test"
            }
            
            response = await self.client.post(f"{self.base_url}/identify-land", json=payload)
            response_time = time.time() - start_time
            
            if response.status_code in [400, 422]:
                details = f"Status code: {response.status_code}, Error message: {response.json().get('detail')}"
                self.log_test("Error Handling - Invalid Coordinates", True, details, response_time)
                return True
            else:
                self.log_test("Error Handling - Invalid Coordinates", False, 
                             f"Unexpected status code: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_test("Error Handling - Invalid Coordinates", False, f"Error: {str(e)}")
            return False
            
    async def test_caching(self):
        """Test caching by making multiple requests to the same endpoint"""
        # First request to boundary types (should be uncached)
        start_time_1 = time.time()
        await self.client.get(f"{self.base_url}/boundary-types")
        response_time_1 = time.time() - start_time_1
        
        # Second request to boundary types (should be cached)
        start_time_2 = time.time()
        await self.client.get(f"{self.base_url}/boundary-types")
        response_time_2 = time.time() - start_time_2
        
        # Check if second request was faster (indicating caching)
        if response_time_2 < response_time_1:
            details = f"First request: {response_time_1:.4f}s, Second request: {response_time_2:.4f}s, Improvement: {(1 - response_time_2/response_time_1)*100:.2f}%"
            self.log_test("Caching Performance", True, details)
            return True
        else:
            details = f"First request: {response_time_1:.4f}s, Second request: {response_time_2:.4f}s, No improvement detected"
            self.log_test("Caching Performance", False, details)
            return False
            
    async def test_nonexistent_project(self):
        """Test retrieving a non-existent project"""
        start_time = time.time()
        try:
            # Generate a random UUID that doesn't exist
            random_id = str(uuid.uuid4())
            response = await self.client.get(f"{self.base_url}/project/{random_id}")
            response_time = time.time() - start_time
            
            if response.status_code == 404:
                details = f"Status code: {response.status_code}, Error message: {response.json().get('detail')}"
                self.log_test("Error Handling - Non-existent Project", True, details, response_time)
                return True
            else:
                self.log_test("Error Handling - Non-existent Project", False, 
                             f"Unexpected status code: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_test("Error Handling - Non-existent Project", False, f"Error: {str(e)}")
            return False
            
    def print_summary(self):
        """Print a summary of all test results"""
        print("\n" + "="*80)
        print(f"{Colors.BOLD}TEST SUMMARY{Colors.ENDC}")
        print("="*80)
        
        # Calculate pass percentage
        pass_percentage = (self.test_stats["passed"] / self.test_stats["total"]) * 100 if self.test_stats["total"] > 0 else 0
        
        # Print overall stats
        if pass_percentage == 100:
            status = f"{Colors.OKGREEN}ALL TESTS PASSED{Colors.ENDC}"
        elif pass_percentage >= 80:
            status = f"{Colors.WARNING}MOST TESTS PASSED{Colors.ENDC}"
        else:
            status = f"{Colors.FAIL}TESTS FAILING{Colors.ENDC}"
            
        print(f"{status}: {self.test_stats['passed']}/{self.test_stats['total']} tests passed ({pass_percentage:.1f}%)")
        
        # Print failed tests if any
        if self.test_stats["failed"] > 0:
            print("\n" + "-"*80)
            print(f"{Colors.FAIL}FAILED TESTS:{Colors.ENDC}")
            for test in self.test_results:
                if not test["passed"]:
                    print(f"- {test['name']}: {test['details']}")
                    
        print("="*80)

async def main():
    """Main test function"""
    print(f"{Colors.HEADER}Stirling Bridge LandDev Backend Test Suite{Colors.ENDC}")
    print(f"{Colors.HEADER}Testing refactored service layer architecture{Colors.ENDC}")
    print("="*80)
    
    # Initialize tester
    tester = BackendTester()
    
    try:
        # Test health check
        await tester.test_health_check()
        
        # Test boundary types
        await tester.test_boundary_types()
        
        # Test land identification with Johannesburg coordinates
        await tester.test_land_identification(
            JOHANNESBURG_COORDS["latitude"], 
            JOHANNESBURG_COORDS["longitude"],
            TEST_PROJECT_NAME
        )
        
        # Test project retrieval
        await tester.test_project_retrieval()
        
        # Test project listing
        await tester.test_project_listing()
        
        # Test file download
        await tester.test_file_download()
        
        # Test statistics endpoint
        await tester.test_statistics_endpoint()
        
        # Test error handling
        await tester.test_error_handling()
        
        # Test invalid coordinates
        await tester.test_invalid_coordinates()
        
        # Test non-existent project
        await tester.test_nonexistent_project()
        
        # Test caching
        await tester.test_caching()
        
    finally:
        # Print summary and close client
        tester.print_summary()
        await tester.close()

if __name__ == "__main__":
    asyncio.run(main())
