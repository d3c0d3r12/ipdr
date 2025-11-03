# 🌐 **TEST ON WEBSITE - Complete Workflow**

## 🚀 **Step-by-Step Testing Guide**

### **Prerequisites:**
- ✅ Backend running: http://localhost:8000
- ✅ Database initialized
- ✅ Admin user created
- ✅ FIR case created: FIR/2025/CC/001

---

## **Step 1: Start Frontend**

Open a **NEW terminal**:

```bash
cd "c:\Users\saheb\Downloads\New FIR\frontend"
npm run dev
```

**Wait for:**
```
✓ Vite server running at http://localhost:3000
```

---

## **Step 2: Open Website**

Open browser and go to:
```
http://localhost:3000
```

---

## **Step 3: Test Upload & Extract**

1. **Go to:** http://localhost:3000/upload

2. **Fill in the form:**
   - **FIR Number:** `FIR/2025/CC/001`
   - **HTML File:** Select your subscriber HTML file
   - **✅ Check "Bypass Cloudflare"** checkbox
   - **Click** "Upload & Extract"

3. **You should see:**
   ```
   ✓ File uploaded successfully! Rows: 67, Unique IPs: 57
   Run Directory: /opt/render/project/src/backend/processed/20251102_104516_205
   
   [🔍 Start Unlimited IP Lookup] ← Click this button!
   ```

---

## **Step 4: Test IP Lookup Terminal**

### **Option A: Auto-redirect (if Cloudflare checked)**

After 2 seconds, it should automatically redirect to:
```
http://localhost:3000/ip-lookup?run_dir=...&auto_start=true
```

### **Option B: Manual click**

Click the **"Start Unlimited IP Lookup"** button

### **What You'll See:**

```
╔═══════════════════════════════════════════════════════╗
║ 🔍 UNLIMITED IP LOOKUP SYSTEM            ⚡ PROCESSING ║
╚═══════════════════════════════════════════════════════╝

[Matrix rain animation in background]

ℹ 📄 Loaded 57 IPs from original_log.csv
ℹ ✅ Ready to lookup 57 IPs
ℹ ⚠️  This will take approximately 4.8 minutes

> 🚀 Initializing Cloudflare bypass system...
> 🌐 Starting browser session...

→ 🔎 Looking up IP 1/57: 2409:40c1:2a:9bc0...
✓ ✅ 2409:40c1:2a:9bc0 → Ahmedabad, India (IN)

[████████░░░░░░░░░░░░] 40%

📊 Total: 57  ✅ Success: 23  ❌ Errors: 0  ⏱️ 1:55
```

---

## **Step 5: Store Results in Database**

After IP lookup completes:

### **Option A: Via API (Manual)**

1. Go to: http://localhost:8000/docs
2. Authorize with your token
3. Use `POST /api/fir/store-ip-results/FIR/2025/CC/001`
4. Upload the generated `ip_lookup_results.csv`

### **Option B: Automatic (Need to implement)**

We can add an automatic storage feature after lookup completes.

---

## **Step 6: View Results**

### **Via API:**

Go to: http://localhost:8000/docs

Test these endpoints:

1. **Get IP Lookups:**
   ```
   GET /api/fir/FIR/2025/CC/001/ip-lookups
   ```

2. **Get Statistics:**
   ```
   GET /api/fir/FIR/2025/CC/001/statistics
   ```

3. **Get Timeline:**
   ```
   GET /api/fir/FIR/2025/CC/001/timeline
   ```

### **Via Frontend (Need to create):**

We'll create pages to display:
- FIR details
- IP lookup results table
- Map visualization
- Statistics dashboard

---

## 🎯 **CURRENT WORKFLOW:**

```
1. Upload HTML ✅
   ↓
2. Extract IPs ✅
   ↓
3. Click "Start IP Lookup" ✅
   ↓
4. Terminal UI shows progress ✅
   ↓
5. Results saved to CSV/JSON ✅
   ↓
6. Manual: Store in database via API ⚠️
   ↓
7. View data via API ✅
```

---

## 🔧 **WHAT'S WORKING:**

✅ **Upload page** - Form with FIR number  
✅ **IP extraction** - From HTML file  
✅ **Auto-redirect** - To IP lookup page  
✅ **Terminal UI** - Real-time progress  
✅ **IP lookup** - Unlimited with Cloudflare bypass  
✅ **Results export** - CSV and JSON  
✅ **Database storage** - Via API  

---

## 🎨 **WHAT'S MISSING (Need to Create):**

### **1. Login Page**
- Dark CyberForensics theme
- Username/Password fields
- JWT authentication
- Redirect to dashboard after login

### **2. Dashboard**
- FIR cases overview
- Statistics cards
- Recent activity
- Quick actions

### **3. FIR Details Page**
- View FIR information
- IP lookup results table
- Map visualization
- Timeline
- Export options

### **4. Auto-store Results**
- After IP lookup completes
- Automatically call API to store in database
- Show success message

### **5. User Tracking Display**
- Active sessions
- Activity logs
- Login history

---

## 🚀 **NEXT STEPS:**

### **Immediate (Test Now):**

1. ✅ Start frontend: `npm run dev`
2. ✅ Go to: http://localhost:3000/upload
3. ✅ Upload HTML with FIR number
4. ✅ Check "Bypass Cloudflare"
5. ✅ Click "Upload & Extract"
6. ✅ Watch terminal UI in action!
7. ⚠️ Manually store results via API

### **Next Phase (Create UI):**

1. **Login Page** - Secure authentication
2. **Dashboard** - Overview and statistics
3. **FIR Management** - Complete CRUD
4. **Data Visualization** - Charts, maps, tables
5. **Auto-storage** - After IP lookup

---

## 📋 **TEST CHECKLIST:**

- [ ] Frontend running (http://localhost:3000)
- [ ] Backend running (http://localhost:8000)
- [ ] Can access upload page
- [ ] Can upload HTML file
- [ ] "Start IP Lookup" button appears
- [ ] Terminal UI loads
- [ ] IP lookup starts automatically
- [ ] Progress bar updates
- [ ] Results saved to CSV/JSON
- [ ] Can store results via API
- [ ] Can view data via API

---

## 🎉 **READY TO TEST!**

```bash
# Terminal 1 (Backend - Already running)
cd backend
python -m uvicorn main:app --reload

# Terminal 2 (Frontend - Start now)
cd frontend
npm run dev

# Browser
http://localhost:3000/upload
```

---

**Start the frontend and test the complete workflow!** 🚀

After testing, let me know what works and I'll create the missing UI components! 🎨
