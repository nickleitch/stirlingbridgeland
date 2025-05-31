#!/usr/bin/env python3
"""
Contour Generation API Test Script

This script tests the new contour generation functionality to verify:
1. Service Status: Check if the contour service is properly initialized and available
2. Contour Generation: Test the main contour generation endpoint with South African coordinates
3. Contour Styles: Test the contour styling endpoint
4. Error Handling: Test with invalid parameters
"""

import httpx
import asyncio
import json
import time
import sys
from typing import Dict, Any, List

# Test configuration
BACKEND_URL = "http://localhost:8001/api"  # Default local URL
SOUTH_AFRICA_COORDS = {"latitude": -29.4828, "longitude": 31.205}  # Durban area coordinates

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
    """Test suite for Contour Generation API"""
    
    def __init__(self, base_url: str = None):
        """Initialize the tester with the backend URL"""
        self.base_url = base_url or BACKEND_URL
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
    
    async def test_service_status(self):
        """Test if the contour service is properly initialized and available"""
        start_time = time.time()
        try:
            response = await self.client.get(f"{self.base_url}/external-services/status")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                services = data.get("external_services", {})
                contour_service = services.get("contour_service", {})
                
                if contour_service and contour_service.get("status") == "available":
                    details = f"Contour service status: {contour_service.get('status')}"
                    if contour_service.get("description"):
                        details += f", Description: {contour_service.get('description')}"
                    if contour_service.get("algorithms"):
                        details += f", Algorithms: {', '.join(contour_service.get('algorithms'))}"
                    
                    self.log_test("Contour Service Status", True, details, response_time)
                    return True
                else:
                    status = contour_service.get("status", "not found") if contour_service else "not found"
                    self.log_test("Contour Service Status", False, 
                                 f"Contour service not available. Status: {status}", response_time)
                    return False
            else:
                self.log_test("Contour Service Status", False, 
                             f"Unexpected status code: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_test("Contour Service Status", False, f"Error: {str(e)}")
            return False
    
    async def test_contour_generation(self, latitude: float, longitude: float, 
                                    contour_interval: float = 2.0, 
                                    grid_size_km: float = 2.0, 
                                    grid_points: int = 10):
        """Test the contour generation endpoint"""
        start_time = time.time()
        try:
            payload = {
                "latitude": latitude,
                "longitude": longitude,
                "contour_interval": contour_interval,
                "grid_size_km": grid_size_km,
                "grid_points": grid_points
            }
            
            response = await self.client.post(f"{self.base_url}/contours/generate", json=payload)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                contour_data = data.get("contour_data", {})
                contour_lines = contour_data.get("contour_lines", [])
                
                details = f"Generated {len(contour_lines)} contour lines"
                if contour_data.get("statistics"):
                    stats = contour_data.get("statistics")
                    details += f", Elevation range: {stats.get('elevation_range', {}).get('min')}m - {stats.get('elevation_range', {}).get('max')}m"
                    if stats.get("contour_levels"):
                        details += f", Contour levels: {len(stats.get('contour_levels'))} unique elevations"
                
                # Check if we have GeoJSON features with elevation properties
                if contour_lines and all(
                    line.get("type") == "Feature" and 
                    line.get("geometry") and 
                    line.get("properties", {}).get("elevation") is not None
                    for line in contour_lines
                ):
                    self.log_test("Contour Generation", True, details, response_time)
                    return True
                else:
                    self.log_test("Contour Generation", False, 
                                 "Response doesn't contain valid GeoJSON features with elevation properties", response_time)
                    return False
            else:
                self.log_test("Contour Generation", False, 
                             f"Unexpected status code: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_test("Contour Generation", False, f"Error: {str(e)}")
            return False
    
    async def test_contour_styles(self):
        """Test the contour styling endpoint"""
        start_time = time.time()
        try:
            response = await self.client.get(f"{self.base_url}/contours/styles")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                styles = data.get("contour_styles", {})
                
                if styles and isinstance(styles, dict) and len(styles) > 0:
                    style_types = list(styles.keys())
                    details = f"Available styles: {', '.join(style_types)}"
                    if data.get("default_interval"):
                        details += f", Default interval: {data.get('default_interval')}m"
                    if data.get("supported_intervals"):
                        details += f", Supported intervals: {', '.join(map(str, data.get('supported_intervals')))}m"
                    
                    self.log_test("Contour Styles", True, details, response_time)
                    return True
                else:
                    self.log_test("Contour Styles", False, "No contour styles found in response", response_time)
                    return False
            else:
                self.log_test("Contour Styles", False, 
                             f"Unexpected status code: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_test("Contour Styles", False, f"Error: {str(e)}")
            return False
    
    async def test_invalid_coordinates(self):
        """Test error handling with invalid coordinates"""
        start_time = time.time()
        try:
            # Test coordinates outside valid range
            payload = {
                "latitude": 100.0,  # Invalid latitude (>90)
                "longitude": 28.0473,
                "contour_interval": 2.0,
                "grid_size_km": 2.0,
                "grid_points": 10
            }
            
            response = await self.client.post(f"{self.base_url}/contours/generate", json=payload)
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
    
    async def test_negative_contour_interval(self):
        """Test error handling with negative contour interval"""
        start_time = time.time()
        try:
            payload = {
                "latitude": SOUTH_AFRICA_COORDS["latitude"],
                "longitude": SOUTH_AFRICA_COORDS["longitude"],
                "contour_interval": -2.0,  # Negative interval
                "grid_size_km": 2.0,
                "grid_points": 10
            }
            
            response = await self.client.post(f"{self.base_url}/contours/generate", json=payload)
            response_time = time.time() - start_time
            
            if response.status_code in [400, 422]:
                details = f"Status code: {response.status_code}, Error message: {response.json().get('detail')}"
                self.log_test("Error Handling - Negative Contour Interval", True, details, response_time)
                return True
            else:
                self.log_test("Error Handling - Negative Contour Interval", False, 
                             f"Unexpected status code: {response.status_code}, Response: {response.text}", response_time)
                return False
        except Exception as e:
            self.log_test("Error Handling - Negative Contour Interval", False, f"Error: {str(e)}")
            return False
    
    def print_summary(self):
        """Print a summary of all test results"""
        print("\n" + "="*80)
        print(f"{Colors.BOLD}CONTOUR GENERATION TEST SUMMARY{Colors.ENDC}")
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
    print(f"{Colors.HEADER}Contour Generation API Test Suite{Colors.ENDC}")
    print("="*80)
    
    # Initialize tester
    tester = ContourTester()
    
    try:
        # Test 1: Service Status
        print(f"\n{Colors.HEADER}1. Testing Contour Service Status{Colors.ENDC}")
        print("-"*80)
        await tester.test_service_status()
        
        # Test 2: Contour Generation
        print(f"\n{Colors.HEADER}2. Testing Contour Generation{Colors.ENDC}")
        print("-"*80)
        await tester.test_contour_generation(
            SOUTH_AFRICA_COORDS["latitude"], 
            SOUTH_AFRICA_COORDS["longitude"],
            contour_interval=2.0,
            grid_size_km=2.0,
            grid_points=10
        )
        
        # Test 3: Contour Styles
        print(f"\n{Colors.HEADER}3. Testing Contour Styles{Colors.ENDC}")
        print("-"*80)
        await tester.test_contour_styles()
        
        # Test 4: Error Handling
        print(f"\n{Colors.HEADER}4. Testing Error Handling{Colors.ENDC}")
        print("-"*80)
        await tester.test_invalid_coordinates()
        await tester.test_negative_contour_interval()
        
    finally:
        # Print summary and close client
        tester.print_summary()
        await tester.close()

if __name__ == "__main__":
    asyncio.run(main())