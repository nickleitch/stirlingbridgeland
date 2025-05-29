
import requests
import sys
import json
from datetime import datetime

class StirlingBridgeAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.project_id = None
        self.test_results = {}

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, params=params)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"Response: {response.text}")
                except:
                    pass
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test the health check endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "api/health",
            200
        )
        self.test_results["health_check"] = {"success": success, "response": response}
        return success, response

    def test_boundary_types(self):
        """Test the boundary types endpoint"""
        success, response = self.run_test(
            "Boundary Types",
            "GET",
            "api/boundary-types",
            200
        )
        self.test_results["boundary_types"] = {"success": success, "response": response}
        return success, response

    def test_identify_land(self, latitude, longitude, project_name="Test Project", architect_email="test@example.com"):
        """Test the identify land endpoint"""
        test_name = f"identify_land_{latitude}_{longitude}"
        
        success, response = self.run_test(
            f"Identify Land at {latitude}, {longitude}",
            "POST",
            "api/identify-land",
            200,
            data={
                "latitude": latitude,
                "longitude": longitude,
                "project_name": project_name,
                "architect_email": architect_email
            }
        )
        
        if success and response.get('project_id'):
            self.project_id = response.get('project_id')
            print(f"  - Project ID: {self.project_id}")
            print(f"  - Status: {response.get('status')}")
            print(f"  - Boundaries found: {len(response.get('boundaries', []))}")
            print(f"  - Files generated: {', '.join(response.get('files_generated', []))}")
            
            # Validate response structure
            self._validate_response_structure(response)
        
        self.test_results[test_name] = {"success": success, "response": response}
        return success, response

    def _validate_response_structure(self, response):
        """Validate the structure of the identify-land response"""
        required_fields = ['project_id', 'coordinates', 'boundaries', 'files_generated', 'status', 'created_at']
        
        for field in required_fields:
            if field not in response:
                print(f"⚠️ Warning: Missing required field '{field}' in response")
                return False
        
        # Validate coordinates
        if not isinstance(response['coordinates'], dict) or 'latitude' not in response['coordinates'] or 'longitude' not in response['coordinates']:
            print("⚠️ Warning: Invalid coordinates format in response")
            return False
            
        # Validate boundaries
        if not isinstance(response['boundaries'], list):
            print("⚠️ Warning: Boundaries should be a list")
            return False
            
        # If we have boundaries, validate the first one
        if response['boundaries']:
            boundary = response['boundaries'][0]
            boundary_fields = ['layer_name', 'layer_type', 'geometry', 'properties', 'source_api']
            
            for field in boundary_fields:
                if field not in boundary:
                    print(f"⚠️ Warning: Missing required field '{field}' in boundary")
                    return False
        
        return True

    def test_get_project(self, project_id):
        """Test the get project endpoint"""
        success, response = self.run_test(
            f"Get Project {project_id}",
            "GET",
            f"api/project/{project_id}",
            200
        )
        self.test_results[f"get_project_{project_id}"] = {"success": success, "response": response}
        return success, response

    def test_send_to_architect(self, project_id, architect_email):
        """Test sending to architect"""
        success, response = self.run_test(
            "Send to Architect",
            "POST",
            "api/send-to-architect",
            200,
            params={
                "project_id": project_id,
                "architect_email": architect_email
            }
        )
        self.test_results[f"send_to_architect_{project_id}"] = {"success": success, "response": response}
        return success, response
        
    def test_invalid_coordinates(self):
        """Test various invalid coordinate inputs"""
        print("\n🔍 Testing Invalid Coordinate Handling...")
        
        # Test with empty coordinates
        success1, response1 = self.run_test(
            "Empty Coordinates",
            "POST",
            "api/identify-land",
            422,  # Expecting validation error
            data={
                "latitude": None,
                "longitude": None
            }
        )
        
        # Test with non-numeric values
        success2, response2 = self.run_test(
            "Non-numeric Coordinates",
            "POST",
            "api/identify-land",
            422,  # Expecting validation error
            data={
                "latitude": "not-a-number",
                "longitude": "not-a-number"
            }
        )
        
        # Test with out-of-range values
        success3, response3 = self.run_test(
            "Out-of-range Coordinates",
            "POST",
            "api/identify-land",
            200,  # Should still accept these but return no boundaries
            data={
                "latitude": 999.999,
                "longitude": 999.999
            }
        )
        
        self.test_results["invalid_coordinates"] = {
            "empty": {"success": success1, "response": response1},
            "non_numeric": {"success": success2, "response": response2},
            "out_of_range": {"success": success3, "response": response3}
        }
        
        return success1 and success2 and success3

    def generate_summary(self):
        """Generate a summary of all test results"""
        print("\n📋 Test Summary:")
        print(f"Total tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed / self.tests_run) * 100:.1f}%")
        
        # Summarize coordinate tests
        coordinate_tests = [k for k in self.test_results.keys() if k.startswith("identify_land_")]
        
        print("\nCoordinate Tests:")
        for test in coordinate_tests:
            result = self.test_results[test]
            lat, lng = test.replace("identify_land_", "").split("_")
            boundaries = len(result["response"].get("boundaries", [])) if result["success"] else 0
            status = "✅ Passed" if result["success"] else "❌ Failed"
            print(f"  - {lat}, {lng}: {status} (Boundaries: {boundaries})")
        
        # Summarize invalid coordinate tests
        if "invalid_coordinates" in self.test_results:
            print("\nInvalid Coordinate Tests:")
            invalid_tests = self.test_results["invalid_coordinates"]
            
            for test_type, result in invalid_tests.items():
                status = "✅ Passed" if result["success"] else "❌ Failed"
                print(f"  - {test_type}: {status}")
        
        return {
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "success_rate": (self.tests_passed / self.tests_run) * 100
        }

def main():
    # Use the public endpoint
    backend_url = "https://583b92f5-4614-4be0-be43-b9dc9f1fbe04.preview.emergentagent.com"
    
    print(f"Testing Stirling Bridge LandDev API at: {backend_url}")
    
    # Setup tester
    tester = StirlingBridgeAPITester(backend_url)
    
    # Test health check
    tester.test_health_check()
    
    # Test boundary types
    tester.test_boundary_types()
    
    # Test identify land with various coordinates
    test_coordinates = [
        # Johannesburg (known working)
        (-26.2041, 28.0473, "Johannesburg Test"),
        # Cape Town
        (-33.9249, 18.4241, "Cape Town Test"),
        # Durban
        (-29.8587, 31.0218, "Durban Test"),
        # Pretoria
        (-25.7479, 28.2293, "Pretoria Test"),
        # Ocean coordinates (should return no boundaries)
        (-30.0000, 0.0000, "Ocean Coordinates Test")
    ]
    
    architect_email = "architect@example.com"
    
    # Test valid coordinates
    for lat, lng, name in test_coordinates:
        success, response = tester.test_identify_land(lat, lng, name, architect_email)
        
        # If we have a project ID, test the project retrieval and send to architect
        if success and tester.project_id:
            tester.test_get_project(tester.project_id)
            tester.test_send_to_architect(tester.project_id, architect_email)
    
    # Test invalid coordinates
    tester.test_invalid_coordinates()
    
    # Generate summary
    summary = tester.generate_summary()
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
      