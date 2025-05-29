
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
        return self.run_test(
            "Health Check",
            "GET",
            "api/health",
            200
        )

    def test_boundary_types(self):
        """Test the boundary types endpoint"""
        return self.run_test(
            "Boundary Types",
            "GET",
            "api/boundary-types",
            200
        )

    def test_identify_land(self, latitude, longitude, project_name="Test Project", architect_email="test@example.com"):
        """Test the identify land endpoint"""
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
        
        return success, response

    def test_get_project(self, project_id):
        """Test the get project endpoint"""
        return self.run_test(
            f"Get Project {project_id}",
            "GET",
            f"api/project/{project_id}",
            200
        )

    def test_send_to_architect(self, project_id, architect_email):
        """Test sending to architect"""
        return self.run_test(
            "Send to Architect",
            "POST",
            "api/send-to-architect",
            200,
            params={
                "project_id": project_id,
                "architect_email": architect_email
            }
        )

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
        # Invalid/ocean coordinates
        (-30.0000, 0.0000, "Invalid Coordinates Test")
    ]
    
    architect_email = "architect@example.com"
    
    for lat, lng, name in test_coordinates:
        success, response = tester.test_identify_land(lat, lng, name, architect_email)
        
        # If we have a project ID, test the project retrieval and send to architect
        if success and tester.project_id:
            tester.test_get_project(tester.project_id)
            tester.test_send_to_architect(tester.project_id, architect_email)
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
      