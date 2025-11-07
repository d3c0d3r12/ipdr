# ✅ **HOW TO START BACKEND - CORRECT WAY**

## ❌ **WRONG WAY (ERROR):**

```powershell
# DON'T DO THIS - Will fail!
cd 'c:\Users\saheb\Downloads\New FIR'
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Error:**
```
ERROR: Error loading ASGI app. Could not import module "main".
```

**Why it fails:**
- You're in the wrong directory
- `main.py` is in the `backend` folder
- Uvicorn can't find it from the root folder

---

## ✅ **CORRECT WAY (WORKS):**

### **Option 1: Change to backend directory first**
```powershell
cd 'c:\Users\saheb\Downloads\New FIR\backend'
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### **Option 2: Use cd in one command**
```powershell
cd 'c:\Users\saheb\Downloads\New FIR\backend'; python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### **Option 3: From root directory**
```powershell
cd 'c:\Users\saheb\Downloads\New FIR'
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## ✅ **EXPECTED OUTPUT:**

```
INFO:     Will watch for changes in these directories: ['C:\\Users\\saheb\\Downloads\\New FIR\\backend']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12032] using WatchFiles
INFO:utils.infobyip_cookie_manager: Loaded 6 cookies from file
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Success indicators:**
- ✅ "Uvicorn running on http://0.0.0.0:8000"
- ✅ "Application startup complete"
- ✅ No errors
- ✅ Loaded cookies (if available)

---

## 🔍 **VERIFY IT'S WORKING:**

### **1. Check in browser:**
```
http://localhost:8000/health
```

**Should return:**
```json
{
  "status": "healthy",
  "database": "connected",
  "environment": "development"
}
```

### **2. Check API docs:**
```
http://localhost:8000/docs
```

**Should show:** Swagger UI with all API endpoints

### **3. Run automated tests:**
```powershell
# In a NEW terminal (keep backend running)
cd 'c:\Users\saheb\Downloads\New FIR'
python test_all_features.py
```

**Should show:** All 6 tests passing

---

## 📁 **DIRECTORY STRUCTURE:**

```
c:\Users\saheb\Downloads\New FIR\
├── backend/              ← main.py is HERE
│   ├── main.py          ← This is what uvicorn needs
│   ├── routers/
│   ├── models/
│   ├── core/
│   └── ...
├── frontend/
└── test_all_features.py
```

**Key point:** You MUST be in the `backend` directory to run uvicorn!

---

## 🚀 **COMPLETE STARTUP SEQUENCE:**

### **Terminal 1: Backend**
```powershell
cd 'c:\Users\saheb\Downloads\New FIR\backend'
.\venv\Scripts\Activate.ps1  # If using virtual environment
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### **Terminal 2: Frontend** (Optional)
```powershell
cd 'c:\Users\saheb\Downloads\New FIR\frontend'
npm run dev
```

### **Terminal 3: Tests** (Optional)
```powershell
cd 'c:\Users\saheb\Downloads\New FIR'
python test_all_features.py
```

---

## ⚠️ **COMMON MISTAKES:**

### **Mistake 1: Wrong directory**
```powershell
# ❌ WRONG
cd 'c:\Users\saheb\Downloads\New FIR'
python -m uvicorn main:app --reload
```
**Error:** Could not import module "main"

### **Mistake 2: Typo in command**
```powershell
# ❌ WRONG
cd backend
python -m uvicorn mian:app --reload  # Typo: "mian" instead of "main"
```
**Error:** Could not import module "mian"

### **Mistake 3: Virtual environment not activated**
```powershell
# ❌ WRONG (if using venv)
cd backend
python -m uvicorn main:app --reload
```
**Error:** Module not found errors for dependencies

**Fix:**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload
```

---

## ✅ **QUICK REFERENCE:**

### **Start Backend:**
```powershell
cd 'c:\Users\saheb\Downloads\New FIR\backend'
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### **Stop Backend:**
```
Press CTRL+C in the terminal
```

### **Restart Backend:**
```
Press CTRL+C, then run the command again
OR
Just save a file - auto-reload will restart it
```

### **Check if Running:**
```
http://localhost:8000/health
```

---

## 🎯 **CURRENT STATUS:**

✅ **Backend is NOW RUNNING!**

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [22424] using WatchFiles
INFO:utils.infobyip_cookie_manager: Loaded 6 cookies from file
```

**What you can do now:**
1. ✅ Access API at http://localhost:8000
2. ✅ View docs at http://localhost:8000/docs
3. ✅ Run tests: `python test_all_features.py`
4. ✅ Start frontend: `cd frontend; npm run dev`
5. ✅ Use the application!

---

**🎉 BACKEND IS RUNNING CORRECTLY! 🎉**

**Remember:** Always `cd backend` before running uvicorn!
