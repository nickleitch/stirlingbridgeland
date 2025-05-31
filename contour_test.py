#!/usr/bin/env python3
"""
Contour Generation System Test Script

This script tests the updated contour generation system with the following specific changes:
1. Default to 10m contour intervals (instead of 2m)
2. Filter contours to only include those within Farm Portions or Erven boundaries
3. Simplified parameters to reduce failure risk
"""

import httpx
import asyncio
import json
import time
import os
import sys
from typing import Dict, Any, List

# Test configuration
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE_URL = f"{BACKEND_URL}/api"
SOUTH_AFRICA_COORDS = {"latitude": -26.0, "longitude": 28.0}  # South African coordinates for testing

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

class ContourTester:
    """Test suite for Contour Generation System"""
    
    def __init__(self, base_url: str = None):
        """Initialize the tester with the backend URL"""
        self.base_url = base_url or API_BASE_URL
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_results = []
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
    
    async def test_contour_generation_minimal_params(self):
        """Test contour generation with minimal parameters (just latitude/longitude)"""
        start_time = time.time()
        try:
            print(f"Testing contour generation with minimal parameters")
            
            # Only provide latitude and longitude
            # Add grid_points=5 to stay within API limits
            payload = {
                "latitude": SOUTH_AFRICA_COORDS["latitude"],
                "longitude": SOUTH_AFRICA_COORDS["longitude"],
                "grid_points": 5  # Reduce grid points to stay within API limits
            }
            
            response = await self.client.post(f"{self.base_url}/contours/generate", json=payload)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if contour data exists
                contour_data = data.get("contour_data", {})
                contour_lines = contour_data.get("contour_lines", [])
                parameters = contour_data.get("parameters", {})
                
                # Verify default parameters
                contour_interval = parameters.get("contour_interval")
                grid_size_km = parameters.get("grid_size_km")
                grid_points = parameters.get("grid_points")
                
                # Check if defaults match expected values (except for grid_points which we overrode)
                interval_correct = contour_interval == 10.0
                grid_size_correct = grid_size_km == 2.0
                
                details = f"Generated {len(contour_lines)} contour lines"
                details += f", Default contour interval: {contour_interval}m (Expected: 10.0m)"
                details += f", Default grid size: {grid_size_km}km (Expected: 2.0km)"
                details += f", Grid points: {grid_points} (Overridden to 5)"
                
                if interval_correct and grid_size_correct:
                    self.log_test("Contour Generation with Minimal Parameters", True, details, response_time)
                    return data
                else:
                    self.log_test("Contour Generation with Minimal Parameters", False, 
                                 f"Default parameters don't match expected values: {details}", 
                                 response_time)
                    return data
            else:
                self.log_test("Contour Generation with Minimal Parameters", False, 
                             f"Unexpected status code: {response.status_code}, Response: {response.text}", response_time)
                return None
        except Exception as e:
            self.log_test("Contour Generation with Minimal Parameters", False, f"Error: {str(e)}")
            return None
    
    async def test_contour_generation_with_property_boundaries(self):
        """Test contour generation with property boundaries parameter"""
        start_time = time.time()
        try:
            print(f"Testing contour generation with property boundaries")
            
            # Sample Farm Portions boundary
            property_boundaries = [
                {
                    "layer_type": "Farm Portions",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [27.99, -26.01],
                            [28.01, -26.01], 
                            [28.01, -25.99],
                            [27.99, -25.99],
                            [27.99, -26.01]
                        ]]
                    }
                }
            ]
            
            payload = {
                "latitude": SOUTH_AFRICA_COORDS["latitude"],
                "longitude": SOUTH_AFRICA_COORDS["longitude"],
                "property_boundaries": property_boundaries,
                "grid_points": 5  # Reduce grid points to stay within API limits
            }
            
            response = await self.client.post(f"{self.base_url}/contours/generate", json=payload)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if contour data exists
                contour_data = data.get("contour_data", {})
                contour_lines = contour_data.get("contour_lines", [])
                boundaries = contour_data.get("boundaries", [])
                
                # Check if we have contour lines and boundaries
                has_contour_lines = len(contour_lines) > 0
                has_boundaries = len(boundaries) > 0
                
                # Check if the response includes a success message about filtering
                message = data.get("message", "")
                has_filtering_message = "Generated" in message and "contour lines" in message
                
                details = f"Generated {len(contour_lines)} contour lines"
                details += f", Boundaries: {len(boundaries)}"
                details += f", Message: {message}"
                
                if has_contour_lines and has_boundaries and has_filtering_message:
                    self.log_test("Contour Generation with Property Boundaries", True, details, response_time)
                    return data
                else:
                    self.log_test("Contour Generation with Property Boundaries", False, 
                                 f"Missing expected data in response: {details}", 
                                 response_time)
                    return data
            else:
                self.log_test("Contour Generation with Property Boundaries", False, 
                             f"Unexpected status code: {response.status_code}, Response: {response.text}", response_time)
                return None
        except Exception as e:
            self.log_test("Contour Generation with Property Boundaries", False, f"Error: {str(e)}")
            return None
    
    async def test_contour_generation_with_erven_boundaries(self):
        """Test contour generation with Erven property boundaries"""
        start_time = time.time()
        try:
            print(f"Testing contour generation with Erven boundaries")
            
            # Sample Erven boundary
            property_boundaries = [
                {
                    "layer_type": "Erven",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [27.995, -26.005],
                            [28.005, -26.005], 
                            [28.005, -25.995],
                            [27.995, -25.995],
                            [27.995, -26.005]
                        ]]
                    }
                }
            ]
            
            payload = {
                "latitude": SOUTH_AFRICA_COORDS["latitude"],
                "longitude": SOUTH_AFRICA_COORDS["longitude"],
                "property_boundaries": property_boundaries,
                "grid_points": 5  # Reduce grid points to stay within API limits
            }
            
            response = await self.client.post(f"{self.base_url}/contours/generate", json=payload)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if contour data exists
                contour_data = data.get("contour_data", {})
                contour_lines = contour_data.get("contour_lines", [])
                boundaries = contour_data.get("boundaries", [])
                
                # Check if we have contour lines and boundaries
                has_contour_lines = len(contour_lines) > 0
                has_boundaries = len(boundaries) > 0
                
                details = f"Generated {len(contour_lines)} contour lines"
                details += f", Boundaries: {len(boundaries)}"
                
                if has_contour_lines and has_boundaries:
                    self.log_test("Contour Generation with Erven Boundaries", True, details, response_time)
                    return data
                else:
                    self.log_test("Contour Generation with Erven Boundaries", False, 
                                 f"Missing expected data in response: {details}", 
                                 response_time)
                    return data
            else:
                self.log_test("Contour Generation with Erven Boundaries", False, 
                             f"Unexpected status code: {response.status_code}, Response: {response.text}", response_time)
                return None
        except Exception as e:
            self.log_test("Contour Generation with Erven Boundaries", False, f"Error: {str(e)}")
            return None
    
    async def test_contour_generation_with_custom_interval(self):
        """Test contour generation with custom contour interval"""
        start_time = time.time()
        try:
            print(f"Testing contour generation with custom contour interval")
            
            # Use custom contour interval
            payload = {
                "latitude": SOUTH_AFRICA_COORDS["latitude"],
                "longitude": SOUTH_AFRICA_COORDS["longitude"],
                "contour_interval": 5.0,  # 5m interval instead of default 10m
                "grid_points": 5  # Reduce grid points to stay within API limits
            }
            
            response = await self.client.post(f"{self.base_url}/contours/generate", json=payload)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if contour data exists
                contour_data = data.get("contour_data", {})
                parameters = contour_data.get("parameters", {})
                
                # Verify custom interval was used
                contour_interval = parameters.get("contour_interval")
                interval_correct = contour_interval == 5.0
                
                details = f"Custom contour interval: {contour_interval}m (Expected: 5.0m)"
                
                if interval_correct:
                    self.log_test("Contour Generation with Custom Interval", True, details, response_time)
                    return data
                else:
                    self.log_test("Contour Generation with Custom Interval", False, 
                                 f"Custom interval not applied: {details}", 
                                 response_time)
                    return data
            else:
                self.log_test("Contour Generation with Custom Interval", False, 
                             f"Unexpected status code: {response.status_code}, Response: {response.text}", response_time)
                return None
        except Exception as e:
            self.log_test("Contour Generation with Custom Interval", False, f"Error: {str(e)}")
            return None
    
    async def test_contour_generation_error_handling(self):
        """Test error handling with invalid parameters"""
        start_time = time.time()
        try:
            print(f"Testing contour generation error handling")
            
            # Invalid parameters (negative contour interval)
            payload = {
                "latitude": SOUTH_AFRICA_COORDS["latitude"],
                "longitude": SOUTH_AFRICA_COORDS["longitude"],
                "contour_interval": -5.0,  # Invalid negative interval
                "grid_points": 5  # Reduce grid points to stay within API limits
            }
            
            response = await self.client.post(f"{self.base_url}/contours/generate", json=payload)
            response_time = time.time() - start_time
            
            # Should return a 400 Bad Request
            if response.status_code == 400:
                error_detail = response.json().get("detail", "")
                
                details = f"Status code: {response.status_code}, Error: {error_detail}"
                
                if "contour interval must be positive" in error_detail.lower():
                    self.log_test("Contour Generation Error Handling", True, details, response_time)
                    return True
                else:
                    self.log_test("Contour Generation Error Handling", False, 
                                 f"Expected error about contour interval, got: {details}", 
                                 response_time)
                    return False
            else:
                self.log_test("Contour Generation Error Handling", False, 
                             f"Expected status code 400, got: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_test("Contour Generation Error Handling", False, f"Error: {str(e)}")
            return False
    
    async def test_contour_generation_invalid_coordinates(self):
        """Test error handling with invalid coordinates"""
        start_time = time.time()
        try:
            print(f"Testing contour generation with invalid coordinates")
            
            # Invalid coordinates (latitude out of range)
            payload = {
                "latitude": 100.0,  # Invalid (>90)
                "longitude": 28.0,
                "grid_points": 5  # Reduce grid points to stay within API limits
            }
            
            response = await self.client.post(f"{self.base_url}/contours/generate", json=payload)
            response_time = time.time() - start_time
            
            # Should return a 400 Bad Request
            if response.status_code == 400:
                error_detail = response.json().get("detail", "")
                
                details = f"Status code: {response.status_code}, Error: {error_detail}"
                
                if "invalid latitude" in error_detail.lower():
                    self.log_test("Contour Generation Invalid Coordinates", True, details, response_time)
                    return True
                else:
                    self.log_test("Contour Generation Invalid Coordinates", False, 
                                 f"Expected error about invalid latitude, got: {details}", 
                                 response_time)
                    return False
            else:
                self.log_test("Contour Generation Invalid Coordinates", False, 
                             f"Expected status code 400, got: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_test("Contour Generation Invalid Coordinates", False, f"Error: {str(e)}")
            return False
    
    async def test_contour_styles_endpoint(self):
        """Test the contour styles endpoint"""
        start_time = time.time()
        try:
            print(f"Testing contour styles endpoint")
            
            response = await self.client.get(f"{self.base_url}/contours/styles")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if contour styles exist
                contour_styles = data.get("contour_styles", {})
                default_interval = data.get("default_interval")
                supported_intervals = data.get("supported_intervals", [])
                
                # Check if we have the expected data
                has_styles = len(contour_styles) > 0
                has_default_interval = default_interval is not None
                has_supported_intervals = len(supported_intervals) > 0
                
                # Check if default interval is 10.0m
                default_interval_correct = default_interval == 10.0
                
                details = f"Contour styles: {list(contour_styles.keys())}"
                details += f", Default interval: {default_interval}m"
                details += f", Supported intervals: {supported_intervals}"
                
                if has_styles and has_default_interval and has_supported_intervals and default_interval_correct:
                    self.log_test("Contour Styles Endpoint", True, details, response_time)
                    return data
                else:
                    self.log_test("Contour Styles Endpoint", False, 
                                 f"Missing expected data in response: {details}", 
                                 response_time)
                    return data
            else:
                self.log_test("Contour Styles Endpoint", False, 
                             f"Unexpected status code: {response.status_code}, Response: {response.text}", response_time)
                return None
        except Exception as e:
            self.log_test("Contour Styles Endpoint", False, f"Error: {str(e)}")
            return None
    
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
    print(f"{Colors.HEADER}Contour Generation System Test Suite{Colors.ENDC}")
    print(f"{Colors.HEADER}Testing updated contour generation system{Colors.ENDC}")
    print("="*80)
    
    # Initialize tester
    tester = ContourTester()
    
    try:
        # Test 1: Contour generation with minimal parameters
        await tester.test_contour_generation_minimal_params()
        
        # Test 2: Contour generation with property boundaries
        await tester.test_contour_generation_with_property_boundaries()
        
        # Test 3: Contour generation with Erven boundaries
        await tester.test_contour_generation_with_erven_boundaries()
        
        # Test 4: Contour generation with custom interval
        await tester.test_contour_generation_with_custom_interval()
        
        # Test 5: Contour generation error handling
        await tester.test_contour_generation_error_handling()
        
        # Test 6: Contour generation with invalid coordinates
        await tester.test_contour_generation_invalid_coordinates()
        
        # Test 7: Contour styles endpoint
        await tester.test_contour_styles_endpoint()
        
    finally:
        # Print summary and close client
        tester.print_summary()
        await tester.close()

if __name__ == "__main__":
    asyncio.run(main())
