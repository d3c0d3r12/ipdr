"""
Automated Testing Script for IPDR Tracking Hub
Tests all backend endpoints and features
"""

import requests
import json
import time
from pathlib import Path

# Configuration
API_BASE = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "Admin@123456"  # Default admin password from init_database.py

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}TEST: {name}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

def print_pass(message):
    print(f"{Colors.GREEN}[PASS] {message}{Colors.END}")

def print_fail(message):
    print(f"{Colors.RED}[FAIL] {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.YELLOW}[INFO] {message}{Colors.END}")

# Test Results
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "errors": []
}

def record_result(test_name, passed, error=None):
    test_results["total"] += 1
    if passed:
        test_results["passed"] += 1
        print_pass(test_name)
    else:
        test_results["failed"] += 1
        test_results["errors"].append({"test": test_name, "error": error})
        print_fail(f"{test_name}: {error}")

# Global token storage
auth_token = None

def test_1_login():
    """Test 1: Login & Authentication"""
    global auth_token
    print_test("Login & Authentication")
    
    try:
        # Send JSON data (auth_secure expects JSON, not form data)
        response = requests.post(
            f"{API_BASE}/api/auth/login",
            json={"username": USERNAME, "password": PASSWORD},
            headers={"Content-Type": "application/json"}
        )
        
        print_info(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_info(f"Response data: {json.dumps(data, indent=2)}")
            
            # auth_secure returns access_token, auth returns token
            auth_token = data.get("access_token") or data.get("token")
            
            if auth_token:
                print_info(f"Token: {auth_token[:20]}...")
                record_result("Login successful", True)
                return True
            else:
                record_result("Login failed", False, "No token in response")
                return False
        else:
            error_detail = response.text
            print_info(f"Error response: {error_detail}")
            record_result("Login failed", False, f"Status {response.status_code}: {error_detail}")
            return False
            
    except Exception as e:
        record_result("Login failed", False, str(e))
        return False

def test_2_upload_file():
    """Test 2: Upload HTML File"""
    print_test("Upload HTML File")
    
    if not auth_token:
        record_result("Upload skipped", False, "No auth token")
        return None
    
    try:
        # Create a sample HTML file with IP activity data
        sample_html = """
        <html>
        <body>
        <table>
        <tr><td>2024-11-14 04:40:14 Z</td><td>2401:4900:170a:8799:5211:8ff:5f78:f889</td><td>Login</td></tr>
        <tr><td>2024-11-14 04:45:20 Z</td><td>2401:4900:1708:b927:6afc:6dcb:9cc7:396d</td><td>View</td></tr>
        </table>
        </body>
        </html>
        """
        
        files = {"file": ("test.html", sample_html, "text/html")}
        data = {"fir": "TEST-001"}
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(
            f"{API_BASE}/api/upload",
            files=files,
            data=data,
            headers=headers
        )
        
        print_info(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_info(f"Response: {json.dumps(data, indent=2)}")
            run_dir = data.get("run_dir")
            print_info(f"Run directory: {run_dir}")
            record_result("File upload successful", True)
            return run_dir
        else:
            error_detail = response.text
            print_info(f"Error response: {error_detail}")
            record_result("File upload failed", False, f"Status {response.status_code}: {error_detail}")
            return None
            
    except Exception as e:
        record_result("File upload failed", False, str(e))
        return None

def test_3_lookup_status(run_dir):
    """Test 3: Check Lookup Status"""
    print_test("Check Lookup Status")
    
    if not run_dir:
        record_result("Lookup status skipped", False, "No run directory")
        return False
    
    try:
        response = requests.get(
            f"{API_BASE}/api/lookup/status",
            params={"run_dir": run_dir}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_info(f"Status: {json.dumps(data, indent=2)}")
            record_result("Lookup status check successful", True)
            return True
        else:
            record_result("Lookup status check failed", False, f"Status {response.status_code}")
            return False
            
    except Exception as e:
        record_result("Lookup status check failed", False, str(e))
        return False

def test_4_health_check():
    """Test 4: Health Check"""
    print_test("Health Check")
    
    try:
        response = requests.get(f"{API_BASE}/health")
        
        if response.status_code == 200:
            data = response.json()
            print_info(f"Health: {json.dumps(data, indent=2)}")
            record_result("Health check successful", True)
            return True
        else:
            record_result("Health check failed", False, f"Status {response.status_code}")
            return False
            
    except Exception as e:
        record_result("Health check failed", False, str(e))
        return False

def test_5_cors():
    """Test 5: CORS Headers"""
    print_test("CORS Headers")
    
    try:
        response = requests.options(
            f"{API_BASE}/api/auth/login",
            headers={"Origin": "http://localhost:3000"}
        )
        
        cors_headers = {
            "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
            "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
            "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
        }
        
        print_info(f"CORS Headers: {json.dumps(cors_headers, indent=2)}")
        
        if cors_headers["Access-Control-Allow-Origin"]:
            record_result("CORS configured", True)
            return True
        else:
            record_result("CORS not configured", False, "No CORS headers")
            return False
            
    except Exception as e:
        record_result("CORS check failed", False, str(e))
        return False

def test_6_unauthorized_access():
    """Test 6: Unauthorized Access (401/403)"""
    print_test("Unauthorized Access (401/403)")
    
    try:
        # Try to access protected endpoint without token
        response = requests.post(
            f"{API_BASE}/api/merge-master-file",
            data={"run_dir": "test"}
        )
        
        # FastAPI returns 403 when no Authorization header is provided
        # Returns 401 when invalid/expired token is provided
        if response.status_code in [401, 403]:
            print_info(f"Correctly returned {response.status_code} for unauthorized access")
            record_result("Unauthorized access blocked", True)
            return True
        else:
            record_result("Unauthorized access not blocked", False, f"Expected 401/403, got {response.status_code}")
            return False
            
    except Exception as e:
        record_result("Unauthorized test failed", False, str(e))
        return False

def print_summary():
    """Print test summary"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}TEST SUMMARY{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    print(f"\nTotal Tests: {test_results['total']}")
    print(f"{Colors.GREEN}Passed: {test_results['passed']}{Colors.END}")
    print(f"{Colors.RED}Failed: {test_results['failed']}{Colors.END}")
    
    if test_results['total'] > 0:
        success_rate = (test_results['passed'] / test_results['total']) * 100
        print(f"\nSuccess Rate: {success_rate:.1f}%")
    
    if test_results['errors']:
        print(f"\n{Colors.RED}ERRORS:{Colors.END}")
        for error in test_results['errors']:
            print(f"  - {error['test']}: {error['error']}")
    
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    
    if test_results['failed'] == 0:
        print(f"{Colors.GREEN}*** ALL TESTS PASSED! SYSTEM IS READY! ***{Colors.END}")
    else:
        print(f"{Colors.RED}*** SOME TESTS FAILED. PLEASE FIX ISSUES. ***{Colors.END}")
    
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")

def main():
    """Run all tests"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}IPDR TRACKING HUB - AUTOMATED TESTING{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"\nAPI Base: {API_BASE}")
    print(f"Username: {USERNAME}")
    print(f"\nStarting tests...\n")
    
    # Run tests in order
    test_4_health_check()
    test_5_cors()
    
    if test_1_login():
        run_dir = test_2_upload_file()
        if run_dir:
            test_3_lookup_status(run_dir)
    
    test_6_unauthorized_access()
    
    # Print summary
    print_summary()

if __name__ == "__main__":
    main()
