# 🔧 **DATABASE CONNECTION FIX GUIDE**

## 🎯 **CURRENT PROBLEM:**

### **Error:**
```
ERROR:core.db:❌ Database connection failed: (psycopg2.OperationalError) 
could not translate host name "ep-weathered-paper-ahzmv5qi-pooler.c-3.us-east-1.aws.neon.tech" 
to address: Name or service not known
```

### **What This Means:**
- Your `.env` file HAS a Neon database URL configured
- The database host cannot be reached
- Possible causes:
  1. **Neon project is suspended** (free tier inactivity)
  2. **Wrong credentials** in `.env`
  3. **Network/DNS issue**
  4. **Neon service is down**

---

## ✅ **SOLUTION 1: CHECK NEON PROJECT STATUS**

### **Step 1: Login to Neon Console**
1. Go to: https://console.neon.tech
2. Login with your account
3. Find your project

### **Step 2: Check Project Status**
Look for:
- ❌ **"Suspended"** - Project needs to be reactivated
- ❌ **"Inactive"** - Project was deleted
- ✅ **"Active"** - Project is running

### **Step 3: Reactivate if Suspended**
If suspended:
1. Click on your project
2. Click **"Activate"** or **"Resume"** button
3. Wait 30 seconds for database to start
4. Restart your backend

---

## ✅ **SOLUTION 2: UPDATE DATABASE CREDENTIALS**

### **Step 1: Get Fresh Connection String**
1. Go to: https://console.neon.tech
2. Select your project
3. Click **"Connection Details"** or **"Dashboard"**
4. Copy the **Connection String** (Pooled connection)

### **Step 2: Update `.env` File**
Open `c:\Users\saheb\Downloads\New FIR\.env` and update:

```env
# Replace with your actual Neon connection string
DATABASE_URL=postgresql://username:password@ep-your-project.aws.neon.tech/police_data?sslmode=require
```

**Example (with real values):**
```env
DATABASE_URL=postgresql://neondb_owner:AbCdEf123456@ep-weathered-paper-ahzmv5qi-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require
```

### **Step 3: Restart Backend**
```powershell
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## ✅ **SOLUTION 3: CREATE NEW NEON DATABASE**

If your Neon project was deleted or you don't have one:

### **Step 1: Create Neon Account**
1. Go to: https://neon.tech
2. Click **"Sign Up"** (free)
3. Login with GitHub/Google/Email

### **Step 2: Create New Project**
1. Click **"Create Project"**
2. **Project Name:** `police-intel-system`
3. **Region:** Choose closest to you (e.g., `us-east-1`)
4. **Database Name:** `police_data`
5. Click **"Create Project"**

### **Step 3: Get Connection String**
1. After creation, you'll see **"Connection Details"**
2. Copy the **"Pooled connection"** string
3. It looks like:
```
postgresql://username:password@ep-xxx-xxx.region.aws.neon.tech/police_data?sslmode=require
```

### **Step 4: Update `.env`**
Paste the connection string in your `.env` file:
```env
DATABASE_URL=postgresql://[paste-your-connection-string-here]
```

### **Step 5: Create Database Tables**
Run the SQL setup script:

```powershell
cd backend
python -c "from core.db import Base, engine; Base.metadata.create_all(bind=engine); print('✅ Tables created')"
```

Or manually run the SQL from `CREATE_TABLES.sql`:
```powershell
# Connect to your Neon database and run:
psql "postgresql://your-connection-string" -f CREATE_TABLES.sql
```

---

## ✅ **SOLUTION 4: USE LOCAL POSTGRESQL (Alternative)**

If you don't want to use Neon, use local PostgreSQL:

### **Step 1: Install PostgreSQL**
Download from: https://www.postgresql.org/download/windows/

### **Step 2: Create Database**
```powershell
# Open psql
psql -U postgres

# Create database
CREATE DATABASE police_data;

# Create user
CREATE USER police_admin WITH PASSWORD 'your_password';

# Grant permissions
GRANT ALL PRIVILEGES ON DATABASE police_data TO police_admin;

# Exit
\q
```

### **Step 3: Update `.env`**
```env
DATABASE_URL=postgresql://police_admin:your_password@localhost:5432/police_data
```

### **Step 4: Create Tables**
```powershell
cd backend
python -c "from core.db import Base, engine; Base.metadata.create_all(bind=engine); print('✅ Tables created')"
```

---

## 🔍 **DIAGNOSE THE PROBLEM:**

### **Test 1: Check if Neon is Reachable**
```powershell
# Test DNS resolution
nslookup ep-weathered-paper-ahzmv5qi-pooler.c-3.us-east-1.aws.neon.tech

# Test connection
Test-NetConnection -ComputerName ep-weathered-paper-ahzmv5qi-pooler.c-3.us-east-1.aws.neon.tech -Port 5432
```

**Expected:**
- ✅ DNS resolves to an IP address
- ✅ Port 5432 is reachable

**If fails:**
- ❌ Neon project is suspended/deleted
- ❌ Network/firewall issue

### **Test 2: Check `.env` File**
```powershell
# View your DATABASE_URL (without showing password)
cd "C:\Users\saheb\Downloads\New FIR"
Get-Content .env | Select-String "DATABASE_URL"
```

### **Test 3: Test Connection from Python**
```powershell
cd backend
python -c "from core.db import test_connection; test_connection()"
```

**Expected:**
```
✅ Connected to Neon PostgreSQL: PostgreSQL 15.x...
```

**If fails:**
```
❌ Database connection failed: could not translate host name...
```

---

## 📊 **WHAT FEATURES NEED DATABASE:**

### **✅ Features That Work WITHOUT Database:**
1. Upload HTML files
2. Extract IPs
3. IP Lookup (Unlimited)
4. Create Master File
5. Fix to Start
6. Fix Final Report
7. Download files
8. Cookie Management

### **❌ Features That NEED Database:**
1. **User Authentication** (Login/Signup)
2. **FIR Management** (Store FIR data)
3. **Tracking** (Activity logs)
4. **User Data Storage** (User profiles)
5. **Session Management** (Secure sessions)

---

## 🎯 **RECOMMENDED SOLUTION:**

### **Option A: Fix Neon Connection (Recommended)**
**Best for:** Production use, cloud deployment
**Steps:**
1. Login to Neon Console
2. Check if project is suspended
3. Reactivate project
4. Get fresh connection string
5. Update `.env`
6. Restart backend

**Time:** 5 minutes

### **Option B: Create New Neon Project**
**Best for:** Fresh start, lost credentials
**Steps:**
1. Create new Neon account (free)
2. Create new project
3. Get connection string
4. Update `.env`
5. Create tables
6. Restart backend

**Time:** 10 minutes

### **Option C: Use Local PostgreSQL**
**Best for:** Offline development, no internet
**Steps:**
1. Install PostgreSQL locally
2. Create database
3. Update `.env`
4. Create tables
5. Restart backend

**Time:** 15 minutes

---

## 🚀 **QUICK FIX (Most Common):**

### **If Neon Project is Suspended:**

```powershell
# 1. Go to Neon Console
Start-Process "https://console.neon.tech"

# 2. Reactivate your project (click Activate button)

# 3. Wait 30 seconds

# 4. Restart backend
cd "C:\Users\saheb\Downloads\New FIR\backend"
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:main:📍 Environment: development
✅ Database engine created successfully
✅ Connected to Neon PostgreSQL: PostgreSQL 15.x...
✅ Database connection successful
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## ✅ **VERIFY IT'S WORKING:**

### **Test 1: Check Backend Logs**
Look for:
```
✅ Database engine created successfully
✅ Connected to Neon PostgreSQL: PostgreSQL 15.x...
✅ Database connection successful
```

### **Test 2: Test Health Endpoint**
```powershell
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

### **Test 3: Try to Login**
1. Go to: http://localhost:3000/login
2. Try to login
3. Should work without errors

### **Test 4: Check Features**
All these should now work:
- ✅ User Authentication
- ✅ FIR Management
- ✅ Tracking
- ✅ User Data Storage

---

## 📝 **COMMON ERRORS & FIXES:**

### **Error 1: "could not translate host name"**
**Cause:** DNS can't resolve Neon hostname
**Fix:** 
- Check internet connection
- Reactivate Neon project
- Use fresh connection string

### **Error 2: "password authentication failed"**
**Cause:** Wrong credentials in `.env`
**Fix:**
- Get fresh connection string from Neon
- Update `.env` with correct password
- Restart backend

### **Error 3: "database does not exist"**
**Cause:** Database name is wrong
**Fix:**
- Check database name in Neon Console
- Update DATABASE_URL in `.env`
- Or create the database

### **Error 4: "SSL connection required"**
**Cause:** Missing `?sslmode=require` in URL
**Fix:**
- Add `?sslmode=require` to end of DATABASE_URL
- Example: `postgresql://user:pass@host/db?sslmode=require`

---

## 🎉 **AFTER FIXING:**

### **You'll Have:**
- ✅ Database connected
- ✅ All features enabled
- ✅ User authentication working
- ✅ FIR management working
- ✅ Tracking working
- ✅ Complete system functional

### **Test Everything:**
1. **Login** - Should work
2. **Signup** - Should work
3. **Upload** - Should work
4. **IP Lookup** - Should work
5. **FIR Management** - Should work
6. **All features** - Should work

---

**🔧 DATABASE CONNECTION - READY TO FIX! 🔧**

**Choose your solution and follow the steps above!**
