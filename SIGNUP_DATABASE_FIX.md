# 🔧 **SIGNUP DATABASE FIX - Column Mismatch**

## 🎯 **PROBLEM:**

The database table has wrong column names:
- SQL has: `hashed_password` (no salt column)
- Model expects: `password_hash` + `salt`

This causes signup to fail!

---

## ✅ **WHAT I FIXED:**

### **File: `CREATE_TABLES.sql`**

**Changed:**
```sql
-- OLD (Wrong):
hashed_password VARCHAR(256) NOT NULL,

-- NEW (Correct):
password_hash VARCHAR(256) NOT NULL,
salt VARCHAR(64) NOT NULL,
```

---

## 🚀 **FIX THE DATABASE NOW:**

### **Step 1: Drop and Recreate Users Table**

**Run in Neon SQL Editor:**

```sql
-- Drop existing users table
DROP TABLE IF EXISTS users CASCADE;

-- Create users table with correct columns
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
```

---

### **Step 2: Test Signup**

```
1. Go to: https://ipdr-tracking-hub-1.onrender.com/signup
2. Fill form:
   - Username: testuser
   - Email: test@delhipolice.gov.in
   - Full Name: Test User
   - Badge Number: TEST001
   - Department: Cyber Cell
   - Role: Investigator
   - Password: Test@123456
   - Confirm: Test@123456
3. Click: CREATE ACCOUNT
4. ✅ Should work now!
```

---

## 📝 **COMPLETE FIX SCRIPT:**

**Copy and run this entire script in Neon:**

```sql
-- ============================================
-- FIX USERS TABLE - Add salt column
-- ============================================

-- Drop existing table
DROP TABLE IF EXISTS user_permissions CASCADE;
DROP TABLE IF EXISTS access_logs CASCADE;
DROP TABLE IF EXISTS login_attempts CASCADE;
DROP TABLE IF EXISTS user_activities CASCADE;
DROP TABLE IF EXISTS user_sessions CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Create users table with correct schema
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

-- Recreate dependent tables
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

-- Verify
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('password_hash', 'salt', 'hashed_password')
ORDER BY column_name;
```

**Expected result:**
```
column_name   | data_type
--------------|------------------
password_hash | character varying
salt          | character varying
```

Should show `password_hash` and `salt`, NOT `hashed_password`!

---

## 🎯 **THEN TEST SIGNUP:**

After running the fix:

```
1. Go to signup page
2. Fill all fields
3. Click CREATE ACCOUNT
4. ✅ Should work!
5. Login with new credentials
6. ✅ Access dashboard!
```

---

**RUN THE FIX SCRIPT IN NEON NOW!** 🚀

This will fix the column mismatch and signup will work! ✅
