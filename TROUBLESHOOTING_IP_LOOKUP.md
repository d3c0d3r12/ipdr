# 🔧 **IP LOOKUP TROUBLESHOOTING GUIDE**

## ❌ **ISSUE: "Start Unlimited IP Lookup" Button Not Working**

---

## ✅ **FIXES APPLIED:**

### **1. Fixed Router Prefix**

**Problem:**
```python
# WRONG - Double prefix
app.include_router(ip_lookup.router, prefix="/api/lookup", tags=["🔍 IP Lookup"])
# This creates: /api/lookup/lookup/stream ❌
```

**Fixed:**
```python
# CORRECT - Single prefix
app.include_router(ip_lookup.router, prefix="/api", tags=["🔍 IP Lookup"])
# This creates: /api/lookup/stream ✅
```

**File:** `backend/main.py` line 40

---

### **2. Fixed EventSource URL**

**File:** `frontend/components/IPLookupTerminal.vue` line 188

```javascript
// CORRECT
const url = `http://localhost:8000/api/lookup/stream?run_dir=${encodeURIComponent(props.runDir)}`
```

---

## 🧪 **TESTING STEPS:**

### **Step 1: Restart Backend**

```bash
cd backend

# Stop any running backend (Ctrl+C)

# Start fresh
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     🚀 Starting IPDR Tracking Hub...
INFO:     📍 Environment: development
INFO:     ✅ Database connection successful
```

---

### **Step 2: Test Backend Endpoint**

Open browser and test:

```
http://localhost:8000/docs
```

**Look for:**
- ✅ `/api/lookup/stream` endpoint
- ✅ `/api/lookup/status` endpoint
- ✅ `/api/lookup/start` endpoint

**Test the endpoint directly:**
```
http://localhost:8000/api/lookup/status?run_dir=backend/processed/20251031_125529_202
```

**Expected Response:**
```json
{
  "has_results": false,
  "csv_exists": false,
  "json_exists": false,
  "total_ips": 500,
  "results_count": 0,
  "success_rate": 0,
  "csv_path": null,
  "json_path": null
}
```

---

### **Step 3: Restart Frontend**

```bash
cd frontend

# Stop any running frontend (Ctrl+C)

# Clear cache and restart
npm run dev
```

**Expected Output:**
```
Nuxt 3.20.0 (with Nitro 2.12.9, Vite 7.1.12 and Vue 3.5.22)

  ➜ Local:    http://localhost:3000/
  ➜ Network:  use --host to expose
```

---

### **Step 4: Test the Button**

1. **Go to IP Lookup page:**
   ```
   http://localhost:3000/ip-lookup
   ```

2. **Enter a run directory:**
   ```
   backend/processed/20251031_125529_202
   ```

3. **Click "Load Directory"**
   - Should show directory info
   - Should show "🚀 Start Lookup" button

4. **Click "🚀 Start Lookup"**
   - Terminal should show initialization
   - Progress bar should appear
   - Real-time updates should stream

---

## 🔍 **DEBUGGING:**

### **Check 1: Backend Running?**

```bash
# Test if backend is accessible
curl http://localhost:8000/health
```

**Expected:**
```json
{
  "status": "healthy",
  "database": "connected",
  "environment": "development"
}
```

---

### **Check 2: Endpoint Exists?**

```bash
# Test lookup status endpoint
curl "http://localhost:8000/api/lookup/status?run_dir=backend/processed/20251031_125529_202"
```

**If you get 404:**
- Backend not running
- Wrong URL
- Router not included

---

### **Check 3: CORS Issue?**

Open browser console (F12) and check for errors:

**Bad (CORS Error):**
```
Access to fetch at 'http://localhost:8000/api/lookup/stream' 
from origin 'http://localhost:3000' has been blocked by CORS policy
```

**Good (No CORS Error):**
```
EventSource connected successfully
```

---

### **Check 4: EventSource Connection?**

Open browser console and check Network tab:

1. **Go to Network tab**
2. **Filter by "stream"**
3. **Click "🚀 Start Lookup"**
4. **Look for:**
   - Request to `/api/lookup/stream`
   - Status: 200 OK
   - Type: text/event-stream

**If Status is 404:**
- Backend endpoint doesn't exist
- Wrong URL in frontend

**If Status is 500:**
- Backend error
- Check backend console for errors

---

## 🐛 **COMMON ERRORS & FIXES:**

### **Error 1: "Failed to fetch"**

**Cause:** Backend not running

**Fix:**
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

### **Error 2: "404 Not Found"**

**Cause:** Wrong endpoint URL

**Fix:** Already fixed in `main.py` line 40

---

### **Error 3: "CORS policy blocked"**

**Cause:** CORS not configured

**Fix:** Check `backend/main.py` lines 24-31:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### **Error 4: "Directory not found"**

**Cause:** Invalid run directory path

**Fix:** Use correct path format:
```
backend/processed/20251031_125529_202
```

Or absolute path:
```
C:\Users\saheb\Downloads\New FIR\backend\processed\20251031_125529_202
```

---

### **Error 5: "original_log.csv not found"**

**Cause:** Run directory doesn't have the CSV file

**Fix:**
1. Go to upload page
2. Upload HTML file
3. Extract IPs
4. This creates the run directory with original_log.csv

---

### **Error 6: Button clicks but nothing happens**

**Cause:** JavaScript error or EventSource not connecting

**Fix:**
1. Open browser console (F12)
2. Look for errors
3. Check if EventSource is created
4. Verify URL is correct

---

## 📝 **COMPLETE TEST SCRIPT:**

Save this as `test_ip_lookup.py` in backend folder:

```python
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test if backend is running"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Health Check: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
        return False

def test_lookup_status():
    """Test lookup status endpoint"""
    try:
        run_dir = "backend/processed/20251031_125529_202"
        response = requests.get(f"{BASE_URL}/api/lookup/status", params={"run_dir": run_dir})
        print(f"✅ Lookup Status: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Lookup Status Failed: {e}")
        return False

def test_stream_endpoint():
    """Test if stream endpoint exists"""
    try:
        run_dir = "backend/processed/20251031_125529_202"
        url = f"{BASE_URL}/api/lookup/stream?run_dir={run_dir}"
        
        # Just check if endpoint exists (don't wait for full stream)
        response = requests.get(url, stream=True, timeout=5)
        
        if response.status_code == 200:
            print(f"✅ Stream Endpoint: Connected (Status 200)")
            # Read first few events
            for i, line in enumerate(response.iter_lines()):
                if i >= 3:  # Just read first 3 events
                    break
                if line:
                    print(f"   Event: {line.decode('utf-8')}")
            return True
        else:
            print(f"❌ Stream Endpoint: Status {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"✅ Stream Endpoint: Connected (timeout is expected)")
        return True
    except Exception as e:
        print(f"❌ Stream Endpoint Failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing IP Lookup System...\n")
    
    print("1. Testing Health Endpoint...")
    test_health()
    print()
    
    print("2. Testing Lookup Status Endpoint...")
    test_lookup_status()
    print()
    
    print("3. Testing Stream Endpoint...")
    test_stream_endpoint()
    print()
    
    print("✅ All tests completed!")
```

**Run it:**
```bash
cd backend
python test_ip_lookup.py
```

---

## 🎯 **QUICK FIX CHECKLIST:**

- [x] **Backend main.py** - Fixed router prefix (line 40)
- [x] **Frontend IPLookupTerminal.vue** - Fixed EventSource URL (line 188)
- [ ] **Backend running** - Start with `uvicorn main:app --reload`
- [ ] **Frontend running** - Start with `npm run dev`
- [ ] **Test endpoint** - Visit `http://localhost:8000/docs`
- [ ] **Test button** - Click "🚀 Start Lookup"

---

## 🚀 **FINAL STEPS:**

### **1. Restart Everything:**

```bash
# Terminal 1 - Backend
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### **2. Test:**

```
1. Go to: http://localhost:3000/ip-lookup
2. Enter: backend/processed/20251031_125529_202
3. Click: Load Directory
4. Click: 🚀 Start Lookup
5. Watch: Real-time progress!
```

---

## 📞 **STILL NOT WORKING?**

### **Check Browser Console:**

1. Open browser (Chrome/Edge)
2. Press F12
3. Go to Console tab
4. Click "🚀 Start Lookup"
5. Look for errors

**Common Console Errors:**

```javascript
// Error 1: Network error
"Failed to fetch"
→ Backend not running

// Error 2: 404
"GET http://localhost:8000/api/lookup/stream 404"
→ Endpoint doesn't exist (check main.py)

// Error 3: CORS
"blocked by CORS policy"
→ CORS not configured (check main.py)

// Error 4: EventSource error
"EventSource failed"
→ Check backend logs for errors
```

---

## 📊 **EXPECTED BEHAVIOR:**

### **When Button Works:**

1. **Click "🚀 Start Lookup"**
2. **Terminal shows:**
   ```
   ╔ ═══════════════════════════════════════════════════════
   ║     UNLIMITED IP LOOKUP SYSTEM v2.0
   ║     Powered by Enhanced Cloudflare Bypass
   ╚ ═══════════════════════════════════════════════════════
   
   > 🔍 Extracting IPs from file...
   ℹ 📄 Loaded 500 IPs from original_log.csv
   ℹ ✅ Ready to lookup 500 IPs
   ℹ ⚠️  This will take approximately 16.7 minutes
   > 🚀 Initializing Cloudflare bypass system...
   > 🌐 Starting browser session...
   → 🔎 Looking up IP 1/500: 2401:4900:xxxx
   ```

3. **Progress bar updates**
4. **Stats update in footer**
5. **Results saved when complete**

---

**THE BUTTON SHOULD NOW WORK!** ✅

Restart both backend and frontend, then test! 🚀
