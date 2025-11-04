# 🧪 **LOCAL TESTING GUIDE**

## 🎯 **TESTING PLAN:**

We'll test all critical features to ensure nothing is broken:

1. ✅ Backend starts without errors
2. ✅ Frontend starts without errors
3. ✅ Upload works
4. ✅ IP lookup completes
5. ✅ **Downloads work (CSV, JSON)**
6. ✅ Master file creation works
7. ✅ Cookie system (optional)

---

## 🚀 **STEP 1: START BACKEND**

### **Open Terminal 1:**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### **Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
🚀 Starting IPDR Tracking Hub...
📍 Environment: development
✅ Database connection successful
INFO:     Application startup complete.
```

### **Check for Errors:**
```
❌ If you see import errors:
   - Cookie manager import error → OK (optional feature)
   
✅ If you see:
   - "Application startup complete" → GOOD!
```

---

## 🚀 **STEP 2: START FRONTEND**

### **Open Terminal 2:**
```bash
cd frontend
npm run dev
```

### **Expected Output:**
```
Nuxt 3.x.x
Local:    http://localhost:3000/
Network:  http://192.168.x.x:3000/

✔ Vite client built in XXXms
✔ Nitro built in XXX ms
```

### **Check for Errors:**
```
❌ If you see component errors:
   - CookieManager not found → Check if file exists
   
✅ If you see:
   - "Local: http://localhost:3000/" → GOOD!
```

---

## 🧪 **STEP 3: TEST UPLOAD**

### **Actions:**
```
1. Open browser: http://localhost:3000
2. Login (if needed): admin / Admin@123456
3. Go to Upload page
4. Enter FIR: "TEST-123"
5. Select HTML file
6. Click Upload
```

### **Expected:**
```
✅ File uploads successfully
✅ Shows: "File uploaded successfully! Rows: X, Unique IPs: Y"
✅ Auto-redirects to IP Lookup page
✅ Shows run directory loaded
```

### **Check Backend Logs:**
```
Look for:
INFO: Upload successful
INFO: Created directory: backend/processed/YYYYMMDD_HHMMSS_TEST-123
```

---

## 🧪 **STEP 4: TEST IP LOOKUP**

### **Actions:**
```
1. Should auto-start after upload
2. Watch terminal output
3. Wait for completion
```

### **Expected Frontend:**
```
🚀 Initializing InfoByIP API...
🌐 Connecting to InfoByIP + Fallback sources...
🔎 Looking up IP 1/X: ...
✅ IP → City, Country | ISP [InfoByIP]
...
🎉 Lookup complete! X/X IPs processed
💾 Saving results...
```

### **Expected Backend Logs:**
```
INFO: Saving CSV to: .../ip_lookup_results.csv
INFO: CSV saved successfully. File exists: True, Size: XXXX bytes
INFO: Saving JSON to: .../ip_lookup_results.json
INFO: JSON saved successfully. File exists: True, Size: XXXX bytes
```

### **Check Results Section:**
```
✅ Shows "Results" section
✅ Shows CSV path
✅ Shows JSON path
✅ Shows download buttons
```

---

## 🧪 **STEP 5: TEST DOWNLOADS (CRITICAL!)**

### **Test CSV Download:**
```
1. Click "💾 Download CSV" button
2. Check browser console (F12)
3. Check Downloads folder
```

### **Expected Console:**
```
Downloading file: /api/files/YYYYMMDD_HHMMSS_TEST-123/ip_lookup_results.csv
Full URL: http://localhost:8000/api/files/YYYYMMDD_HHMMSS_TEST-123/ip_lookup_results.csv
Blob size: XXXX
✅ Download initiated: ip_lookup_results.csv
```

### **Expected Backend Logs:**
```
INFO: 📥 Download request - run_dir: YYYYMMDD_HHMMSS_TEST-123, filename: ip_lookup_results.csv
INFO: 🔍 Looking for file at: .../backend/processed/YYYYMMDD_HHMMSS_TEST-123/ip_lookup_results.csv
INFO: 📁 File exists: True
INFO: ✅ File found, serving: .../backend/processed/YYYYMMDD_HHMMSS_TEST-123/ip_lookup_results.csv
```

### **Expected Result:**
```
✅ File downloads to Downloads folder
✅ File name: ip_lookup_results.csv
✅ File opens in Excel/text editor
✅ Contains IP data
```

### **Test JSON Download:**
```
1. Click "💾 Download JSON" button
2. Check Downloads folder
```

### **Expected:**
```
✅ File downloads: ip_lookup_results.json
✅ File contains JSON data
```

---

## 🧪 **STEP 6: TEST MASTER FILE**

### **Actions:**
```
1. Click "✨ Create Master File.csv"
2. Wait for success message
3. Click "💾 Download Master File.csv"
```

### **Expected:**
```
✅ Shows: "Master file created successfully! X records merged"
✅ Master File section appears
✅ Shows total records
✅ Download button works
✅ File downloads: Master file.csv
```

---

## 🧪 **STEP 7: TEST COOKIE SYSTEM (OPTIONAL)**

### **Check Cookie Manager UI:**
```
1. Look for "🍪 Cookie Management" badge in top-right
2. Should show status (probably "No Cookies" or gray)
3. Click "🍪 Manage" button
```

### **Expected:**
```
✅ Modal opens
✅ Shows cookie status
✅ Shows upload interface
✅ Shows instructions
```

### **If Cookie Manager Not Showing:**
```
⚠️ This is OK! Cookie system is optional.
✅ All other features should still work.
```

---

## 📊 **TESTING CHECKLIST:**

### **Critical Features (Must Work):**
- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] Login works
- [ ] Upload works
- [ ] IP lookup completes
- [ ] **CSV download works (not 404!)**
- [ ] **JSON download works**
- [ ] Master file creation works
- [ ] Master file download works

### **Optional Features:**
- [ ] Cookie manager UI shows
- [ ] Cookie upload works (if you have cookies)

---

## 🐛 **TROUBLESHOOTING:**

### **Issue 1: Backend won't start**
```
Error: "ModuleNotFoundError: No module named 'utils.infobyip_cookie_manager'"

Solution:
Check if file exists: backend/utils/infobyip_cookie_manager.py
If missing, cookie system won't work but other features should.
```

### **Issue 2: Frontend won't start**
```
Error: "Cannot find module 'CookieManager'"

Solution:
Check if file exists: frontend/components/CookieManager.vue
If missing, remove import from ip-lookup.vue
```

### **Issue 3: Download gives 404**
```
Check backend logs for:
❌ File not found: ...
📂 Directory exists: True/False
❌ Available files: [...]

If directory doesn't exist:
- IP lookup didn't complete
- Check if CSV was saved

If file doesn't exist:
- Check "Available files" list
- File might have different name
```

### **Issue 4: Cookie manager error**
```
Error in console about cookies

Solution:
This is OK! Cookie system is optional.
Just ignore the error.
All other features work.
```

---

## ✅ **SUCCESS CRITERIA:**

### **Minimum Required (Must Pass):**
```
✅ Upload works
✅ IP lookup completes
✅ CSV downloads (not 404!)
✅ JSON downloads
✅ Master file works
```

### **Bonus (Nice to Have):**
```
✅ Cookie manager shows
✅ No console errors
```

---

## 📝 **TESTING SCRIPT:**

### **Quick Test (5 minutes):**
```
1. Start backend
2. Start frontend
3. Upload test file
4. Wait for IP lookup to complete
5. Click "Download CSV"
6. ✅ If file downloads → SUCCESS!
7. ✅ If 404 → Check backend logs
```

### **Full Test (10 minutes):**
```
1. All steps above
2. Test JSON download
3. Test Master file creation
4. Test Master file download
5. Check cookie manager UI
6. ✅ All work → READY TO DEPLOY!
```

---

## 🎯 **WHAT TO REPORT:**

### **If Everything Works:**
```
✅ Backend started: OK
✅ Frontend started: OK
✅ Upload: OK
✅ IP Lookup: OK
✅ CSV Download: OK
✅ JSON Download: OK
✅ Master File: OK

Result: READY TO DEPLOY! 🚀
```

### **If Download Fails:**
```
❌ CSV Download: 404

Backend logs show:
[paste the error logs here]

Available files: [paste the list]
```

---

## 🚀 **AFTER TESTING:**

### **If All Tests Pass:**
```bash
# Push to GitHub
git push origin main

# Wait 10 minutes
# Test on production
# ✅ Done!
```

### **If Tests Fail:**
```
Report the issue with:
1. Which test failed
2. Error messages
3. Backend logs
4. Console logs

I'll fix it immediately!
```

---

## 📋 **TESTING COMMANDS SUMMARY:**

```bash
# Terminal 1 - Backend
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev

# Browser
http://localhost:3000

# Test Flow
1. Login
2. Upload HTML file
3. Wait for IP lookup
4. Click "Download CSV"
5. ✅ Check if file downloads!
```

---

**START TESTING NOW!** 🧪

Let me know the results! ✅
