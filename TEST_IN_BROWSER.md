# 🌐 **BROWSER TEST GUIDE**

## 🚀 **Step-by-Step Browser Test:**

### **Step 1: Start Backend**

```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Look for:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### **Step 2: Start Frontend**

```bash
cd frontend
npm run dev
```

**Look for:**
```
✓ Vite server running at http://localhost:3000
```

---

## 🔍 **Browser Tests:**

### **Test 1: Check Backend API**

Open in browser:
```
http://localhost:8000/docs
```

**Expected:** FastAPI documentation page with all endpoints

**Look for these endpoints:**
- `GET /api/lookup/stream`
- `GET /api/lookup/status`
- `POST /api/lookup/start`

**Screenshot this page!** 📸

---

### **Test 2: Check Frontend Upload Page**

Open in browser:
```
http://localhost:3000/upload
```

**Expected:** Upload page with form

**You should see:**
- FIR Number input
- File upload button
- "Bypass Cloudflare" checkbox
- "Upload & Extract" button

**Screenshot this page!** 📸

---

### **Test 3: Check IP Lookup Page**

Open in browser:
```
http://localhost:3000/ip-lookup
```

**Expected:** IP Lookup page with directory selector

**You should see:**
- "Select Processed Run Directory" section
- Input field for run directory path
- "Load Directory" button
- Example paths shown

**Screenshot this page!** 📸

---

### **Test 4: Test with Sample Path**

On the IP Lookup page, enter this path:
```
backend/processed/20251102_104516_205
```

Click "Load Directory"

**Expected:**
- Terminal UI appears
- Shows "Start Lookup" button
- OR shows error if directory doesn't exist

**Screenshot the result!** 📸

---

### **Test 5: Check Browser Console**

1. Press **F12** to open Developer Tools
2. Go to **Console** tab
3. Refresh the page
4. Look for any **red errors**

**Screenshot any errors!** 📸

---

### **Test 6: Check Network Tab**

1. Press **F12**
2. Go to **Network** tab
3. Try uploading a file
4. Watch for API calls

**Look for:**
- `POST /api/upload/` - Should be status 200
- Any failed requests (red)

**Screenshot the network activity!** 📸

---

## 📋 **What to Check:**

### **✅ Backend Checklist:**

- [ ] Backend running on port 8000
- [ ] Can access http://localhost:8000/docs
- [ ] See "IP Lookup" section in API docs
- [ ] See 3 endpoints: stream, status, start

### **✅ Frontend Checklist:**

- [ ] Frontend running on port 3000
- [ ] Can access http://localhost:3000/upload
- [ ] Can access http://localhost:3000/ip-lookup
- [ ] No errors in browser console
- [ ] No 404 errors

---

## 🐛 **Common Issues:**

### **Issue 1: "Cannot GET /ip-lookup"**

**Cause:** Page file doesn't exist or frontend not restarted

**Fix:**
```bash
# Stop frontend (Ctrl+C)
cd frontend
npm run dev
```

### **Issue 2: "404 Not Found" for API**

**Cause:** Backend not running or wrong port

**Fix:**
```bash
cd backend
python -m uvicorn main:app --reload
```

### **Issue 3: "CORS Error"**

**Cause:** Frontend and backend on different origins

**Fix:** Check `backend/core/config.py` - should allow `http://localhost:3000`

### **Issue 4: "Module not found: ip_lookup"**

**Cause:** Backend needs restart after adding new router

**Fix:**
```bash
# Stop backend (Ctrl+C)
cd backend
python -m uvicorn main:app --reload
```

---

## 🎯 **Quick Verification Commands:**

### **Check if files exist:**

```bash
# Check backend router
dir backend\routers\ip_lookup.py

# Check frontend page
dir frontend\pages\ip-lookup.vue

# Check frontend component
dir frontend\components\IPLookupTerminal.vue
```

**All should show file exists!**

---

## 📸 **Screenshots I Need:**

Please take screenshots of:

1. **Backend terminal** - showing "Application startup complete"
2. **Frontend terminal** - showing "Vite server running"
3. **http://localhost:8000/docs** - API documentation
4. **http://localhost:3000/upload** - Upload page
5. **http://localhost:3000/ip-lookup** - IP Lookup page
6. **Browser console (F12)** - Any errors
7. **Upload success** - After uploading a file

---

## 🔥 **Emergency Test:**

If pages don't load, try this:

### **Direct API Test:**

Open in browser:
```
http://localhost:8000/api/lookup/status?run_dir=backend/processed/20251102_104516_205
```

**Expected:** JSON response with IP counts

**If this works:** Backend is fine, frontend issue
**If this fails:** Backend issue

---

## 📝 **Report Back:**

Tell me:

1. **Can you access http://localhost:8000/docs?**
   - [ ] Yes - I see API docs
   - [ ] No - Error: ___________

2. **Can you access http://localhost:3000/upload?**
   - [ ] Yes - I see upload form
   - [ ] No - Error: ___________

3. **Can you access http://localhost:3000/ip-lookup?**
   - [ ] Yes - I see IP lookup page
   - [ ] No - Error: ___________

4. **Any errors in browser console (F12)?**
   ```
   [Paste errors here]
   ```

5. **Backend terminal output:**
   ```
   [Paste last 10 lines]
   ```

6. **Frontend terminal output:**
   ```
   [Paste last 10 lines]
   ```

---

**Test these URLs in your browser and let me know what you see!** 🌐
