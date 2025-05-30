#!/usr/bin/env python3
"""
Focused Backend Test Script for Stirling Bridge LandDev API
Tests the comprehensive land data integration for elevation data.
"""

import requests
import json
import time
import os
from pprint import pprint

# Get backend URL from environment or use default
try:
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.strip().split('=')[1].strip('"\'')
                break
except Exception as e:
    print(f"Warning: Could not read frontend .env file: {e}")
    BACKEND_URL = "http://localhost:8001"  # Default local URL

API_BASE_URL = f"{BACKEND_URL}/api"
print(f"Using Backend URL: {BACKEND_URL}")
print(f"API Base URL: {API_BASE_URL}")

# Test coordinates (Durban area)
DURBAN_COORDS = {"latitude": -29.4828, "longitude": 31.205}

def test_elevation_endpoint():
    """Test the elevation endpoint with South African coordinates"""
    print("\n=== Testing Elevation Endpoint ===")
    
    url = f"{API_BASE_URL}/elevation/{DURBAN_COORDS['latitude']}/{DURBAN_COORDS['longitude']}"
    print(f"Making request to: {url}")
    
    response = requests.get(url)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Elevation Data:")
        pprint(data)
        
        # Verify elevation data is present
        if "elevation_data" in data and "elevation_stats" in data["elevation_data"]:
            print("✅ Elevation data is present")
            print("Elevation Stats:")
            pprint(data["elevation_data"]["elevation_stats"])
            return True
        else:
            print("❌ Elevation data is missing")
            return False
    else:
        print(f"❌ Request failed with status code: {response.status_code}")
        print(response.text)
        return False

def test_identify_land_endpoint():
    """Test the identify-land endpoint with South African coordinates"""
    print("\n=== Testing Identify Land Endpoint ===")
    
    payload = {
        "latitude": DURBAN_COORDS["latitude"],
        "longitude": DURBAN_COORDS["longitude"],
        "project_name": "Test Project"
    }
    
    url = f"{API_BASE_URL}/identify-land"
    print(f"Making POST request to: {url}")
    print(f"Payload: {payload}")
    
    response = requests.post(url, json=payload)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Response Data Keys:")
        pprint(list(data.keys()))
        
        # Check if elevation_stats is in the response
        if "elevation_stats" in data:
            print("✅ Elevation stats are present in the response")
            print("Elevation Stats:")
            pprint(data["elevation_stats"])
            return True
        else:
            print("❌ Elevation stats are missing from the response")
            return False
    else:
        print(f"❌ Request failed with status code: {response.status_code}")
        print(response.text)
        return False

def test_external_services_status():
    """Test the external services status endpoint"""
    print("\n=== Testing External Services Status ===")
    
    url = f"{API_BASE_URL}/external-services/status"
    print(f"Making request to: {url}")
    
    response = requests.get(url)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("External Services Status:")
        
        # Check if Open Topo Data service is listed
        if "external_services" in data:
            services = data["external_services"]
            if "open_topo_service" in services:
                print("✅ Open Topo Data service is listed")
                print("Open Topo Data Service Status:")
                pprint(services["open_topo_service"])
                return True
            else:
                print("❌ Open Topo Data service is not listed")
                return False
        else:
            print("❌ External services data is missing")
            return False
    else:
        print(f"❌ Request failed with status code: {response.status_code}")
        print(response.text)
        return False

def run_all_tests():
    """Run all tests and report results"""
    print("\n======================================")
    print("STARTING BACKEND ELEVATION DATA TESTS")
    print("======================================")
    
    # Run tests
    test_results = {
        "elevation_endpoint": test_elevation_endpoint(),
        "external_services_status": test_external_services_status(),
        "identify_land_endpoint": test_identify_land_endpoint()
    }
    
    # Print summary
    print("\n======================================")
    print("TEST RESULTS SUMMARY")
    print("======================================")
    
    all_passed = True
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n======================================")
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("======================================")
    
    return all_passed

if __name__ == "__main__":
    run_all_tests()