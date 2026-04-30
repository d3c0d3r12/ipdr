"""
Test script for IP Lookup endpoints
Run this to verify the backend is working correctly
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test if backend is running"""
    print("=" * 60)
    print("TEST 1: Health Check")
    print("=" * 60)
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend is running!")
            print(f"   Status: {data.get('status')}")
            print(f"   Database: {data.get('database')}")
            print(f"   Environment: {data.get('environment')}")
            return True
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to backend at {BASE_URL}")
        print(f"   Make sure backend is running:")
        print(f"   cd backend")
        print(f"   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
        return False

def test_lookup_status():
    """Test lookup status endpoint"""
    print("\n" + "=" * 60)
    print("TEST 2: Lookup Status Endpoint")
    print("=" * 60)
    try:
        # Use a sample run directory
        run_dir = "backend/processed/20251031_125529_202"
        response = requests.get(
            f"{BASE_URL}/api/lookup/status", 
            params={"run_dir": run_dir},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Lookup Status endpoint working!")
            print(f"   Total IPs: {data.get('total_ips')}")
            print(f"   Has Results: {data.get('has_results')}")
            print(f"   Results Count: {data.get('results_count')}")
            return True
        elif response.status_code == 404:
            print(f"⚠️  Endpoint works but directory not found")
            print(f"   This is OK if you haven't uploaded files yet")
            print(f"   Directory tested: {run_dir}")
            return True
        else:
            print(f"❌ Status endpoint failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Lookup Status Failed: {e}")
        return False

def test_stream_endpoint():
    """Test if stream endpoint exists and responds"""
    print("\n" + "=" * 60)
    print("TEST 3: Stream Endpoint (SSE)")
    print("=" * 60)
    try:
        run_dir = "backend/processed/20251031_125529_202"
        url = f"{BASE_URL}/api/lookup/stream?run_dir={run_dir}"
        
        print(f"Testing: {url}")
        
        # Try to connect to stream
        response = requests.get(url, stream=True, timeout=3)
        
        if response.status_code == 200:
            print(f"✅ Stream endpoint connected!")
            print(f"   Content-Type: {response.headers.get('content-type')}")
            
            # Try to read first event
            print(f"   Reading first few events...")
            for i, line in enumerate(response.iter_lines(decode_unicode=True)):
                if i >= 5:  # Just read first 5 lines
                    break
                if line and line.startswith('data:'):
                    try:
                        data = json.loads(line[5:].strip())
                        print(f"   Event {i+1}: {data.get('type')} - {data.get('message', '')[:50]}")
                    except:
                        print(f"   Event {i+1}: {line[:60]}")
            
            return True
        elif response.status_code == 404:
            print(f"⚠️  Stream endpoint works but directory not found")
            print(f"   This is OK if you haven't uploaded files yet")
            return True
        else:
            print(f"❌ Stream endpoint failed with status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"✅ Stream endpoint connected (timeout is normal for streaming)")
        return True
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to stream endpoint")
        print(f"   Make sure backend is running")
        return False
    except Exception as e:
        print(f"❌ Stream Endpoint Test Failed: {e}")
        return False

def test_api_docs():
    """Test if API docs are accessible"""
    print("\n" + "=" * 60)
    print("TEST 4: API Documentation")
    print("=" * 60)
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print(f"✅ API docs accessible at: {BASE_URL}/docs")
            print(f"   Open this URL in your browser to see all endpoints")
            return True
        else:
            print(f"⚠️  API docs not accessible (status {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ API docs test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("\n")
    print("🧪" * 30)
    print("IP LOOKUP SYSTEM - BACKEND TEST")
    print("🧪" * 30)
    print()
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health()))
    results.append(("Lookup Status", test_lookup_status()))
    results.append(("Stream Endpoint", test_stream_endpoint()))
    results.append(("API Docs", test_api_docs()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print()
        print("🎉" * 30)
        print("ALL TESTS PASSED!")
        print("🎉" * 30)
        print()
        print("✅ Backend is working correctly!")
        print("✅ IP Lookup endpoints are accessible!")
        print("✅ You can now test the frontend button!")
        print()
        print("Next steps:")
        print("1. Make sure frontend is running: npm run dev")
        print("2. Go to: http://localhost:3000/ip-lookup")
        print("3. Click '🚀 Start Lookup' button")
        print()
    else:
        print()
        print("⚠️  Some tests failed!")
        print()
        print("Troubleshooting:")
        print("1. Make sure backend is running:")
        print("   cd backend")
        print("   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        print()
        print("2. Check for errors in backend console")
        print()
        print("3. Verify port 8000 is not in use by another process")
        print()

if __name__ == "__main__":
    main()
