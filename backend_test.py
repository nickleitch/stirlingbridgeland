
import requests
import sys
import json
import zipfile
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

    def test_identify_land(self, latitude, longitude, project_name="Test Project"):
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
                "project_name": project_name
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
            
            # Check for absence of Parent Farm Boundaries
            self._check_parent_farm_boundaries(response)
            
            # Check for farm names and sizes
            self._check_farm_info(response)
        
        self.test_results[test_name] = {"success": success, "response": response}
        return success, response
        
    def _check_parent_farm_boundaries(self, response):
        """Check that Parent Farm Boundaries are not present in the response"""
        print("\n  🔍 Checking for absence of Parent Farm Boundaries...")
        
        if not response.get('boundaries'):
            print("  ⚠️ No boundaries found to check")
            return
            
        parent_farm_found = False
        boundary_types = set()
        
        for boundary in response.get('boundaries', []):
            boundary_type = boundary.get('layer_type')
            boundary_types.add(boundary_type)
            
            if boundary_type == "Parent Farm Boundaries":
                parent_farm_found = True
                print(f"  ❌ Found Parent Farm Boundary: {boundary.get('layer_name')}")
        
        if parent_farm_found:
            print("  ❌ Parent Farm Boundaries are still present in the response")
        else:
            print("  ✅ No Parent Farm Boundaries found in the response")
            
        print(f"  📊 Boundary types found: {', '.join(boundary_types)}")
        
        # Check that only 4 boundary types are present (not 5)
        expected_types = {"Farm Portions", "Erven", "Holdings", "Public Places"}
        unexpected_types = boundary_types - expected_types
        missing_types = expected_types - boundary_types
        
        if unexpected_types:
            print(f"  ⚠️ Unexpected boundary types found: {', '.join(unexpected_types)}")
        
        if missing_types and boundary_types:  # Only report if we found some boundaries
            print(f"  ⚠️ Expected boundary types missing: {', '.join(missing_types)}")
            
    def _check_farm_info(self, response):
        """Check for farm names and sizes in the response"""
        print("\n  🔍 Checking for farm names and sizes...")
        
        if not response.get('boundaries'):
            print("  ⚠️ No boundaries found to check")
            return
            
        farm_names_found = False
        farm_sizes_found = False
        farm_numbers_found = False
        farm_names = set()
        farm_sizes = {}
        
        for boundary in response.get('boundaries', []):
            properties = boundary.get('properties', {})
            
            # Check for farm names in various property fields (enhanced fields)
            farm_name = properties.get('FARMNAME') or properties.get('NAME') or \
                        properties.get('FARM_NAME') or properties.get('PropertyName') or \
                        properties.get('SS_NAME')
                        
            if farm_name and farm_name != 'Unknown Farm':
                farm_names_found = True
                farm_names.add(farm_name)
            
            # Check for farm numbers in various property fields (enhanced fields)
            farm_number = properties.get('FARM_NO') or properties.get('FARM_NUMBER') or \
                          properties.get('PARCEL_NO') or properties.get('PORTION') or \
                          properties.get('DSG_NO')
                          
            if farm_number:
                farm_numbers_found = True
            
            # Check for farm sizes in various property fields (enhanced fields)
            farm_size = properties.get('AREA') or properties.get('HECTARES') or \
                        properties.get('SIZE') or properties.get('EXTENT') or \
                        properties.get('SHAPE_AREA') or properties.get('Shape.STArea()') or \
                        properties.get('GEOM_AREA') or properties.get('Shape_Area')
                        
            if farm_size:
                farm_sizes_found = True
                if farm_name:
                    farm_sizes[farm_name] = farm_size
        
        if farm_names_found:
            print(f"  ✅ Farm names found: {', '.join(list(farm_names)[:5])}")
            if len(farm_names) > 5:
                print(f"     ...and {len(farm_names) - 5} more")
        else:
            print("  ❌ No farm names found in the response")
            
        if farm_numbers_found:
            print("  ✅ Farm numbers/identifiers found in the response")
        else:
            print("  ❌ No farm numbers/identifiers found in the response")
            
        if farm_sizes_found:
            print("  ✅ Farm sizes found in the response")
            for name, size in list(farm_sizes.items())[:3]:
                print(f"     • {name}: {size}")
            if len(farm_sizes) > 3:
                print(f"     ...and {len(farm_sizes) - 3} more")
        else:
            print("  ❌ No farm sizes found in the response")
            
        # Return results for summary
        return {
            "farm_names_found": farm_names_found,
            "farm_numbers_found": farm_numbers_found,
            "farm_sizes_found": farm_sizes_found,
            "farm_names": list(farm_names)[:10],
            "farm_sizes": {k: v for k, v in list(farm_sizes.items())[:5]}
        }

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
        
    def test_download_files(self, project_id):
        """Test downloading files"""
        print(f"\n🔍 Testing Download Files for Project {project_id}...")
        
        try:
            url = f"{self.base_url}/api/download-files/{project_id}"
            headers = {'Content-Type': 'application/json'}
            
            self.tests_run += 1
            
            response = requests.get(url, headers=headers, stream=True)
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                
                # Check content type
                content_type = response.headers.get('Content-Type')
                print(f"  - Content Type: {content_type}")
                
                # Check content disposition
                content_disposition = response.headers.get('Content-Disposition')
                print(f"  - Content Disposition: {content_disposition}")
                
                # Get filename from content disposition
                filename = None
                if content_disposition:
                    filename_match = content_disposition.split('filename=')
                    if len(filename_match) > 1:
                        filename = filename_match[1].strip('"')
                        print(f"  - Filename: {filename}")
                
                # Save the file for inspection
                if filename:
                    test_download_path = f"/tmp/{filename}"
                    with open(test_download_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    print(f"  - Downloaded file to: {test_download_path}")
                    
                    # Check if it's a valid ZIP file
                    try:
                        with zipfile.ZipFile(test_download_path, 'r') as zip_ref:
                            file_list = zip_ref.namelist()
                            print(f"  - ZIP contains {len(file_list)} files:")
                            for file in file_list:
                                print(f"    • {file}")
                    except Exception as e:
                        print(f"  ⚠️ Warning: Could not read ZIP file: {str(e)}")
                
                self.test_results[f"download_files_{project_id}"] = {
                    "success": success, 
                    "content_type": content_type,
                    "filename": filename,
                    "file_saved": test_download_path if filename else None
                }
                
                return success, {"filename": filename}
            else:
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                try:
                    print(f"Response: {response.text}")
                except:
                    pass
                
                self.test_results[f"download_files_{project_id}"] = {"success": False}
                return False, {}
                
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.test_results[f"download_files_{project_id}"] = {"success": False, "error": str(e)}
            return False, {}
        
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
        
        # Summarize enhanced legend functionality tests
        print("\nEnhanced Legend Functionality Tests:")
        
        # Check for absence of Parent Farm Boundaries
        parent_farm_found = False
        for test in coordinate_tests:
            result = self.test_results[test]
            if not result["success"]:
                continue
                
            for boundary in result["response"].get("boundaries", []):
                if boundary.get("layer_type") == "Parent Farm Boundaries":
                    parent_farm_found = True
                    break
                    
            if parent_farm_found:
                break
                
        print(f"  - Parent Farm Boundaries Removed: {'❌ Failed' if parent_farm_found else '✅ Passed'}")
        
        # Check for farm names and sizes
        farm_names_found = False
        farm_sizes_found = False
        
        for test in coordinate_tests:
            result = self.test_results[test]
            if not result["success"] or not result["response"].get("boundaries"):
                continue
                
            for boundary in result["response"].get("boundaries", []):
                properties = boundary.get("properties", {})
                
                # Check for farm names
                farm_name = properties.get('FARMNAME') or properties.get('NAME') or \
                            properties.get('FARM_NAME') or properties.get('PropertyName')
                            
                if farm_name and farm_name != 'Unknown Farm':
                    farm_names_found = True
                
                # Check for farm sizes
                farm_size = properties.get('AREA') or properties.get('HECTARES') or \
                            properties.get('SIZE') or properties.get('EXTENT')
                            
                if farm_size:
                    farm_sizes_found = True
                    
                if farm_names_found and farm_sizes_found:
                    break
                    
            if farm_names_found and farm_sizes_found:
                break
                
        print(f"  - Farm Names in Legend: {'✅ Passed' if farm_names_found else '❌ Failed'}")
        print(f"  - Farm Sizes in Legend: {'✅ Passed' if farm_sizes_found else '❌ Failed'}")
        
        return {
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "success_rate": (self.tests_passed / self.tests_run) * 100,
            "enhanced_legend": {
                "parent_farm_boundaries_removed": not parent_farm_found,
                "farm_names_found": farm_names_found,
                "farm_sizes_found": farm_sizes_found
            }
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
        # Johannesburg (urban farms) - as specified in the test requirements
        (-26.2041, 28.0473, "Johannesburg Test"),
        # Free State (agricultural) - as specified in the test requirements
        (-25.5000, 28.1000, "Free State Agricultural Test"),
        # Cape Town (mixed development) - as specified in the test requirements
        (-33.9249, 18.4241, "Cape Town Test"),
        # Pretoria
        (-25.7479, 28.2293, "Pretoria Test"),
        # Ocean coordinates (should return no boundaries)
        (-30.0000, 0.0000, "Ocean Coordinates Test")
    ]
    
    # Test valid coordinates
    for lat, lng, name in test_coordinates:
        success, response = tester.test_identify_land(lat, lng, name)
        
        # If we have a project ID, test the project retrieval and download files
        if success and tester.project_id:
            tester.test_get_project(tester.project_id)
            tester.test_download_files(tester.project_id)
    
    # Test invalid coordinates
    tester.test_invalid_coordinates()
    
    # Generate summary
    summary = tester.generate_summary()
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
      