# 🚀 **COMPLETE FIX AND DEPLOY GUIDE**

## 📊 **CURRENT STATUS:**

### **✅ Already Committed (Ready to Push):**
1. `backend/requirements.txt` - All dependencies added
2. `backend/routers/auth_secure.py` - Role field added
3. `frontend/pages/signup.vue` - Dropdown styling fixed

### **❌ Main Issues:**
1. **Database schema mismatch** - `hashed_password` vs `password_hash` + `salt`
2. **Changes not pushed to GitHub**
3. **Render not deployed with latest code**

---

## 🔧 **STEP 1: FIX DATABASE SCHEMA**

### **The Root Problem:**

**Backend Model (`backend/models/user_auth.py`):**
```python
password_hash = Column(String(256), nullable=False)
salt = Column(String(64), nullable=False)
```

**Current Database (Wrong):**
```sql
hashed_password VARCHAR(256)  -- Missing salt column!
```

**What We Need:**
```sql
password_hash VARCHAR(256)
salt VARCHAR(64)
```

---

## ✅ **FIX: Update CREATE_TABLES.sql**

I've already updated `CREATE_TABLES.sql` with correct columns.

**Now run this in Neon SQL Editor:**

```sql
-- ============================================
-- COMPLETE DATABASE SETUP - FIXED SCHEMA
-- ============================================

-- Drop all existing tables
DROP TABLE IF EXISTS fir_timeline CASCADE;
DROP TABLE IF EXISTS fir_suspects CASCADE;
DROP TABLE IF EXISTS fir_evidence CASCADE;
DROP TABLE IF EXISTS fir_ip_lookups CASCADE;
DROP TABLE IF EXISTS fir_cases CASCADE;
DROP TABLE IF EXISTS user_permissions CASCADE;
DROP TABLE IF EXISTS access_logs CASCADE;
DROP TABLE IF EXISTS login_attempts CASCADE;
DROP TABLE IF EXISTS user_activities CASCADE;
DROP TABLE IF EXISTS user_sessions CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Create users table with CORRECT schema
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(200) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    salt VARCHAR(64) NOT NULL,
    full_name VARCHAR(200),
    badge_number VARCHAR(50),
    department VARCHAR(200),
    designation VARCHAR(200),
    phone_number VARCHAR(20),
    role VARCHAR(50) DEFAULT 'investigator',
    permissions JSONB,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    is_locked BOOLEAN DEFAULT false,
    failed_login_attempts INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    last_login TIMESTAMP WITH TIME ZONE,
    last_password_change TIMESTAMP WITH TIME ZONE,
    two_factor_enabled BOOLEAN DEFAULT false,
    two_factor_secret VARCHAR(100),
    recovery_email VARCHAR(200),
    created_by VARCHAR(100),
    approved_by VARCHAR(100),
    notes TEXT
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- Create user_sessions table
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    username VARCHAR(100),
    session_token VARCHAR(256) UNIQUE NOT NULL,
    refresh_token VARCHAR(256) UNIQUE,
    ip_address VARCHAR(100),
    user_agent TEXT,
    device_type VARCHAR(50),
    browser VARCHAR(100),
    os VARCHAR(100),
    country VARCHAR(100),
    city VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    last_activity TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_sessions_token ON user_sessions(session_token);

-- Create user_activities table
CREATE TABLE user_activities (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    username VARCHAR(100),
    session_id INTEGER,
    activity_type VARCHAR(100),
    activity_description TEXT,
    endpoint VARCHAR(500),
    method VARCHAR(10),
    status_code INTEGER,
    ip_address VARCHAR(100),
    user_agent TEXT,
    request_data JSONB,
    response_data JSONB,
    duration_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_activities_user_id ON user_activities(user_id);
CREATE INDEX idx_activities_type ON user_activities(activity_type);

-- Create login_attempts table
CREATE TABLE login_attempts (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100),
    email VARCHAR(200),
    ip_address VARCHAR(100),
    user_agent TEXT,
    success BOOLEAN,
    failure_reason VARCHAR(200),
    country VARCHAR(100),
    city VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_login_attempts_username ON login_attempts(username);
CREATE INDEX idx_login_attempts_ip ON login_attempts(ip_address);

-- Create access_logs table
CREATE TABLE access_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    username VARCHAR(100),
    endpoint VARCHAR(500),
    method VARCHAR(10),
    ip_address VARCHAR(100),
    user_agent TEXT,
    status_code INTEGER,
    response_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create FIR tables
CREATE TABLE fir_cases (
    id SERIAL PRIMARY KEY,
    fir_number VARCHAR(100) UNIQUE NOT NULL,
    case_title VARCHAR(500),
    case_description TEXT,
    case_type VARCHAR(100),
    priority VARCHAR(50),
    status VARCHAR(50) DEFAULT 'open',
    investigating_officer VARCHAR(200),
    department VARCHAR(200),
    police_station VARCHAR(200),
    district VARCHAR(100),
    state VARCHAR(100),
    filed_date DATE,
    incident_date DATE,
    incident_location TEXT,
    victim_name VARCHAR(200),
    victim_contact VARCHAR(100),
    suspect_info TEXT,
    evidence_collected TEXT,
    case_notes TEXT,
    created_by VARCHAR(100),
    assigned_to VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    closed_at TIMESTAMP WITH TIME ZONE
);

-- Verify schema
SELECT column_name, data_type, character_maximum_length
FROM information_schema.columns 
WHERE table_name = 'users' 
ORDER BY ordinal_position;
```

**Expected output should show:**
- `password_hash` (character varying, 256)
- `salt` (character varying, 64)

---

## 🚀 **STEP 2: PUSH TO GITHUB**

### **Check what needs to be pushed:**

```bash
git status
git log --oneline -5
```

### **Push all commits:**

**Option A: Using GitHub Desktop (Easiest)**
```
1. Open GitHub Desktop
2. Should see commits ready to push
3. Click "Push origin"
4. Done!
```

**Option B: Command Line**
```bash
git push origin main
```

**If remote error:**
```bash
# Check remote
git remote -v

# If wrong, fix it
git remote set-url origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Then push
git push origin main
```

---

## ⏰ **STEP 3: WAIT FOR RENDER DEPLOYMENT**

```
1. Go to: https://dashboard.render.com
2. Select backend service
3. Click "Events" tab
4. Watch deployment progress
5. Wait for "Live" status (2-5 minutes)
```

**What to look for:**
```
✅ "Build successful"
✅ "Successfully installed email-validator..."
✅ "Your service is live"
```

---

## 🎯 **STEP 4: TEST SIGNUP**

### **After database is fixed and Render is deployed:**

```
1. Go to: https://ipdr-tracking-hub-1.onrender.com/signup
2. Fill form:
   Username: testuser
   Email: testuser@delhipolice.gov.in
   Full Name: Test User
   Badge Number: TEST001
   Department: Cyber Cell
   Role: Investigator
   Password: Test@123456
   Confirm: Test@123456
3. Click: CREATE ACCOUNT
4. Should see: "Account created successfully!"
5. Redirects to login
6. Login with: testuser / Test@123456
7. ✅ Should work!
```

---

## 🐛 **STEP 5: IF SIGNUP STILL FAILS**

### **Check Browser Console:**

```
1. Press F12
2. Go to Console tab
3. Try signup
4. Look for error message
```

### **Common Errors:**

**Error 1: "relation 'users' does not exist"**
- Database tables not created
- Run the SQL script in Neon

**Error 2: "column 'salt' does not exist"**
- Database has old schema
- Run DROP and CREATE again

**Error 3: "Failed to fetch" or "Network error"**
- Backend not running
- Check Render deployment status

**Error 4: "Password does not meet requirements"**
- Password validation failing
- Use: Test@123456 (meets all requirements)

---

## 📝 **COMPLETE CHECKLIST:**

### **Database (Neon):**
- [ ] Open https://console.neon.tech
- [ ] Go to SQL Editor
- [ ] Run DROP TABLE commands
- [ ] Run CREATE TABLE commands
- [ ] Verify schema shows `password_hash` and `salt`
- [ ] No `hashed_password` column

### **GitHub:**
- [ ] All changes committed locally
- [ ] Push to GitHub successful
- [ ] Check GitHub repo shows latest commits

### **Render:**
- [ ] Deployment triggered automatically
- [ ] Build successful
- [ ] Dependencies installed (email-validator, PyJWT, etc.)
- [ ] Service status: Live (green)
- [ ] No errors in logs

### **Testing:**
- [ ] Signup page loads
- [ ] Dropdowns visible and working
- [ ] Can create account
- [ ] Success message shown
- [ ] Redirects to login
- [ ] Can login with new account
- [ ] Dashboard accessible

---

## 🎯 **VERIFICATION QUERIES:**

### **Run in Neon to verify everything:**

```sql
-- 1. Check if users table exists with correct schema
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('password_hash', 'salt', 'hashed_password')
ORDER BY column_name;

-- Should show ONLY password_hash and salt, NOT hashed_password

-- 2. Check if table is empty (ready for signups)
SELECT COUNT(*) as user_count FROM users;

-- Should return 0 (no users yet)

-- 3. List all tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Should show: access_logs, fir_cases, login_attempts, user_activities, user_sessions, users
```

---

## 🚀 **QUICK COMMANDS:**

### **1. Fix Database:**
```
https://console.neon.tech → SQL Editor → Run the SQL script above
```

### **2. Push to GitHub:**
```
GitHub Desktop → Push origin
```

### **3. Check Render:**
```
https://dashboard.render.com → Events tab → Wait for "Live"
```

### **4. Test Signup:**
```
https://ipdr-tracking-hub-1.onrender.com/signup → Create account
```

---

## 📊 **WHAT EACH STEP DOES:**

```
Step 1: Fix Database Schema
   ↓
   Creates users table with password_hash + salt
   ↓
Step 2: Push to GitHub
   ↓
   Updates remote repository with all fixes
   ↓
Step 3: Render Deploys
   ↓
   Installs dependencies, starts backend
   ↓
Step 4: Test Signup
   ↓
   Backend can now create users properly
   ↓
Step 5: Login Works
   ↓
   ✅ SYSTEM FULLY OPERATIONAL!
```

---

## 🎉 **AFTER EVERYTHING WORKS:**

### **You can:**
1. ✅ Create users via signup
2. ✅ Login with any created user
3. ✅ Upload files
4. ✅ Extract IPs
5. ✅ Run unlimited IP lookups
6. ✅ Download results (CSV, JSON, Master File)
7. ✅ Manage FIR cases
8. ✅ Track investigations

---

## 📝 **SUMMARY:**

**The core issue:** Database schema mismatch
- Model expects: `password_hash` + `salt`
- Database had: `hashed_password` (no salt)

**The fix:**
1. Drop and recreate users table with correct schema
2. Push all code changes to GitHub
3. Wait for Render to deploy
4. Test signup - will work!

---

**START WITH STEP 1: RUN THE SQL SCRIPT IN NEON!** 🚀

This is the most critical fix! ✅
