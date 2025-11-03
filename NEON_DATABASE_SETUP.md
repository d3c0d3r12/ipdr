# 🗄️ **NEON DATABASE SETUP - Complete Guide**

## 🎯 **ISSUE:**

```
ERROR: relation "users" does not exist
```

**Cause:** Database tables haven't been created yet.

---

## ✅ **SOLUTION: Run SQL Script in Neon**

I've created a complete SQL script: `CREATE_TABLES.sql`

This script will:
1. Create all 11 tables
2. Create all indexes
3. Insert admin user
4. Verify setup

---

## 🚀 **STEP-BY-STEP:**

### **Step 1: Open Neon SQL Editor**

```
1. Go to: https://console.neon.tech
2. Login to your account
3. Select your database
4. Click "SQL Editor" tab
```

---

### **Step 2: Copy the SQL Script**

Open the file: `CREATE_TABLES.sql`

Or copy from below (full script):

```sql
-- ============================================
-- IPDR TRACKING HUB - DATABASE SETUP
-- ============================================

-- 1. USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(200) UNIQUE NOT NULL,
    hashed_password VARCHAR(256) NOT NULL,
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

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 2. USER SESSIONS TABLE
CREATE TABLE IF NOT EXISTS user_sessions (
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

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);

-- 3. USER ACTIVITIES TABLE
CREATE TABLE IF NOT EXISTS user_activities (
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

CREATE INDEX IF NOT EXISTS idx_activities_user_id ON user_activities(user_id);
CREATE INDEX IF NOT EXISTS idx_activities_type ON user_activities(activity_type);
CREATE INDEX IF NOT EXISTS idx_activities_created ON user_activities(created_at);

-- 4. LOGIN ATTEMPTS TABLE
CREATE TABLE IF NOT EXISTS login_attempts (
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

CREATE INDEX IF NOT EXISTS idx_login_attempts_username ON login_attempts(username);
CREATE INDEX IF NOT EXISTS idx_login_attempts_ip ON login_attempts(ip_address);
CREATE INDEX IF NOT EXISTS idx_login_attempts_created ON login_attempts(created_at);

-- 5. ACCESS LOGS TABLE
CREATE TABLE IF NOT EXISTS access_logs (
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

CREATE INDEX IF NOT EXISTS idx_access_logs_user_id ON access_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_access_logs_endpoint ON access_logs(endpoint);
CREATE INDEX IF NOT EXISTS idx_access_logs_created ON access_logs(created_at);

-- 6. USER PERMISSIONS TABLE
CREATE TABLE IF NOT EXISTS user_permissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    permission_name VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id INTEGER,
    granted_by VARCHAR(100),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_permissions_user_id ON user_permissions(user_id);

-- 7. FIR CASES TABLE
CREATE TABLE IF NOT EXISTS fir_cases (
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

CREATE INDEX IF NOT EXISTS idx_fir_cases_number ON fir_cases(fir_number);
CREATE INDEX IF NOT EXISTS idx_fir_cases_status ON fir_cases(status);
CREATE INDEX IF NOT EXISTS idx_fir_cases_created ON fir_cases(created_at);

-- 8. FIR IP LOOKUPS TABLE
CREATE TABLE IF NOT EXISTS fir_ip_lookups (
    id SERIAL PRIMARY KEY,
    fir_id INTEGER,
    fir_number VARCHAR(100),
    ip_address VARCHAR(100),
    lookup_date TIMESTAMP WITH TIME ZONE,
    country VARCHAR(100),
    region VARCHAR(100),
    city VARCHAR(100),
    isp VARCHAR(200),
    organization VARCHAR(200),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    timezone VARCHAR(100),
    postal_code VARCHAR(20),
    lookup_source VARCHAR(100),
    raw_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fir_ip_lookups_fir_id ON fir_ip_lookups(fir_id);
CREATE INDEX IF NOT EXISTS idx_fir_ip_lookups_ip ON fir_ip_lookups(ip_address);

-- 9. FIR EVIDENCE TABLE
CREATE TABLE IF NOT EXISTS fir_evidence (
    id SERIAL PRIMARY KEY,
    fir_id INTEGER,
    fir_number VARCHAR(100),
    evidence_type VARCHAR(100),
    evidence_description TEXT,
    file_name VARCHAR(500),
    file_path VARCHAR(1000),
    file_size INTEGER,
    file_hash VARCHAR(256),
    collected_by VARCHAR(200),
    collected_at TIMESTAMP WITH TIME ZONE,
    chain_of_custody TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fir_evidence_fir_id ON fir_evidence(fir_id);

-- 10. FIR SUSPECTS TABLE
CREATE TABLE IF NOT EXISTS fir_suspects (
    id SERIAL PRIMARY KEY,
    fir_id INTEGER,
    fir_number VARCHAR(100),
    suspect_name VARCHAR(200),
    suspect_alias VARCHAR(200),
    age INTEGER,
    gender VARCHAR(20),
    address TEXT,
    phone_number VARCHAR(100),
    email VARCHAR(200),
    identification_marks TEXT,
    criminal_history TEXT,
    status VARCHAR(50),
    arrested BOOLEAN DEFAULT false,
    arrest_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fir_suspects_fir_id ON fir_suspects(fir_id);

-- 11. FIR TIMELINE TABLE
CREATE TABLE IF NOT EXISTS fir_timeline (
    id SERIAL PRIMARY KEY,
    fir_id INTEGER,
    fir_number VARCHAR(100),
    event_type VARCHAR(100),
    event_description TEXT,
    event_date TIMESTAMP WITH TIME ZONE,
    performed_by VARCHAR(200),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fir_timeline_fir_id ON fir_timeline(fir_id);
CREATE INDEX IF NOT EXISTS idx_fir_timeline_date ON fir_timeline(event_date);

-- INSERT DEFAULT ADMIN USER
INSERT INTO users (
    username, 
    email, 
    hashed_password, 
    full_name, 
    role, 
    is_active, 
    is_verified,
    department,
    designation,
    created_at,
    updated_at
) VALUES (
    'admin',
    'admin@delhipolice.gov.in',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEg7Iq',
    'System Administrator',
    'admin',
    true,
    true,
    'Delhi Police Cyber Cell',
    'System Administrator',
    NOW(),
    NOW()
) ON CONFLICT (username) DO NOTHING;

-- VERIFY
SELECT username, email, role, is_active FROM users WHERE username = 'admin';
```

---

### **Step 3: Paste and Run**

```
1. Paste the entire SQL script into Neon SQL Editor
2. Click "Run" button
3. Wait for execution (takes ~5 seconds)
```

---

### **Step 4: Verify Success**

You should see:

```
✅ 11 tables created
✅ All indexes created
✅ Admin user inserted
✅ Query result shows admin user
```

**Expected output:**
```
username | email                        | role  | is_active
---------|------------------------------|-------|----------
admin    | admin@delhipolice.gov.in     | admin | true
```

---

## 🎯 **AFTER SETUP:**

### **Test Login:**

```
1. Go to: https://ipdr-tracking-hub-1.onrender.com/login
2. Username: admin
3. Password: Admin@123456
4. ✅ Should work!
```

---

## 📊 **WHAT WAS CREATED:**

### **11 Tables:**
1. ✅ users - User accounts
2. ✅ user_sessions - Active sessions
3. ✅ user_activities - Activity logs
4. ✅ login_attempts - Login tracking
5. ✅ access_logs - Access logs
6. ✅ user_permissions - Permissions
7. ✅ fir_cases - FIR cases
8. ✅ fir_ip_lookups - IP lookup results
9. ✅ fir_evidence - Evidence files
10. ✅ fir_suspects - Suspect information
11. ✅ fir_timeline - Case timeline

### **Admin User:**
- Username: admin
- Password: Admin@123456
- Role: admin
- Status: Active & Verified

---

## 🐛 **IF ERRORS OCCUR:**

### **Error: "syntax error"**
- Make sure you copied the entire script
- Check for missing quotes or semicolons

### **Error: "permission denied"**
- Make sure you're using the correct database
- Check if you have admin access to Neon

### **Error: "table already exists"**
- This is OK! Script uses `IF NOT EXISTS`
- Admin user uses `ON CONFLICT DO NOTHING`

---

## ✅ **VERIFICATION CHECKLIST:**

- [ ] Opened Neon SQL Editor
- [ ] Pasted complete SQL script
- [ ] Clicked "Run"
- [ ] Saw success messages
- [ ] Verified admin user exists
- [ ] Tested login on production site
- [ ] Login works!

---

**RUN THE SQL SCRIPT IN NEON NOW!** 🚀

This will create all tables and the admin user! ✅
