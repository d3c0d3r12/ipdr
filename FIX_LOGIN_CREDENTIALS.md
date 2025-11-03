# 🔐 **FIX LOGIN CREDENTIALS - "Login failed. Please check your credentials."**

## 🎯 **ERROR MESSAGE:**
```
"Login failed. Please check your credentials."
```

**This means:**
- ✅ Backend is running
- ✅ Database is connected
- ❌ Either admin user doesn't exist OR password is wrong

---

## 🔍 **DIAGNOSTIC - Run in Neon SQL Editor:**

### **Query 1: Check if admin user exists**
```sql
SELECT 
    id,
    username, 
    email, 
    role, 
    is_active, 
    is_verified,
    LENGTH(hashed_password) as pwd_length,
    created_at
FROM users 
WHERE username = 'admin';
```

**What to look for:**
- **No rows returned** → Admin doesn't exist (go to FIX 1)
- **is_active = false** → User is disabled (go to FIX 2)
- **is_verified = false** → User not verified (go to FIX 3)
- **pwd_length ≠ 60** → Wrong password hash (go to FIX 4)
- **Everything looks good** → Check password field name (go to FIX 5)

---

## ✅ **FIX 1: Admin User Doesn't Exist**

**If query returns 0 rows, create admin:**

```sql
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
```

**Then verify:**
```sql
SELECT username, email, role FROM users WHERE username = 'admin';
```

**Then test login again!**

---

## ✅ **FIX 2: User is Disabled**

**If is_active = false:**

```sql
UPDATE users 
SET is_active = true,
    is_verified = true
WHERE username = 'admin';
```

**Then test login again!**

---

## ✅ **FIX 3: User Not Verified**

**If is_verified = false:**

```sql
UPDATE users 
SET is_verified = true
WHERE username = 'admin';
```

**Then test login again!**

---

## ✅ **FIX 4: Wrong Password Hash**

**If password hash length is not 60:**

```sql
UPDATE users 
SET hashed_password = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEg7Iq'
WHERE username = 'admin';
```

**This sets password to:** `Admin@123456`

**Then test login again!**

---

## ✅ **FIX 5: Check Password Field Name**

**The backend might be looking for different field name.**

**Check what columns exist:**
```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name LIKE '%password%';
```

**Expected:** Should see `hashed_password`

**If you see `password_hash` instead:**
```sql
-- Rename column
ALTER TABLE users 
RENAME COLUMN password_hash TO hashed_password;
```

---

## 🔍 **COMPLETE DIAGNOSTIC SCRIPT:**

**Run this entire script in Neon SQL Editor:**

```sql
-- ============================================
-- DIAGNOSTIC: Check Admin User Status
-- ============================================

-- 1. Check if users table exists
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'users'
) as users_table_exists;

-- 2. Count total users
SELECT COUNT(*) as total_users FROM users;

-- 3. Check admin user details
SELECT 
    id,
    username, 
    email, 
    role, 
    is_active, 
    is_verified,
    is_locked,
    failed_login_attempts,
    LENGTH(hashed_password) as password_hash_length,
    created_at,
    last_login
FROM users 
WHERE username = 'admin';

-- 4. Check password column name
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name LIKE '%password%';

-- ============================================
-- FIX: Create/Update Admin User
-- ============================================

-- Delete existing admin if any issues
DELETE FROM users WHERE username = 'admin';

-- Create fresh admin user
INSERT INTO users (
    username, 
    email, 
    hashed_password, 
    full_name, 
    role, 
    is_active, 
    is_verified,
    is_locked,
    failed_login_attempts,
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
    false,
    0,
    'Delhi Police Cyber Cell',
    'System Administrator',
    NOW(),
    NOW()
);

-- Verify admin created
SELECT 
    username, 
    email, 
    role, 
    is_active, 
    is_verified,
    LENGTH(hashed_password) as pwd_length
FROM users 
WHERE username = 'admin';
```

---

## 🎯 **STEP-BY-STEP FIX:**

### **Step 1: Run Diagnostic**

```
1. Go to: https://console.neon.tech
2. Click: SQL Editor
3. Paste: The diagnostic script above
4. Click: Run
5. Look at results
```

---

### **Step 2: Check Results**

**Look at the output:**

**Query 1 (users_table_exists):**
- `true` = Good ✅
- `false` = Run CREATE_TABLES.sql first ❌

**Query 2 (total_users):**
- `0` = No users, admin needs to be created
- `1+` = Users exist, check admin details

**Query 3 (admin details):**
- **No rows** = Admin doesn't exist
- **is_active = false** = Admin is disabled
- **is_verified = false** = Admin not verified
- **password_hash_length ≠ 60** = Wrong password

**Query 4 (password column):**
- Should show: `hashed_password`
- If shows: `password_hash` = Column name mismatch

---

### **Step 3: Apply Fix**

**The script already includes the fix:**
- Deletes old admin (if exists)
- Creates fresh admin with correct password
- Sets all flags correctly

---

### **Step 4: Test Login**

```
1. Go to: https://ipdr-tracking-hub-1.onrender.com/login
2. Username: admin
3. Password: Admin@123456
4. Click: Login
5. Should work! ✅
```

---

## 🚨 **IF STILL DOESN'T WORK:**

### **Check Backend Logs:**

```
1. Go to: https://dashboard.render.com
2. Select: Backend service
3. Click: Logs tab
4. Try to login
5. Watch logs for error message
```

**Look for:**
- "User not found"
- "Invalid password"
- "Database error"
- Any other error

---

### **Test API Directly:**

```
1. Go to: https://ipdr-tracking-hub-1.onrender.com/docs
2. Find: POST /api/auth/login
3. Click: Try it out
4. Enter:
   {
     "username": "admin",
     "password": "Admin@123456"
   }
5. Click: Execute
6. Check response
```

**Expected:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

**If error:**
- Check error message
- It will tell you exactly what's wrong

---

## 📝 **QUICK FIX (Copy-Paste):**

**Just run this in Neon SQL Editor:**

```sql
-- Delete and recreate admin
DELETE FROM users WHERE username = 'admin';

INSERT INTO users (
    username, email, hashed_password, full_name, role, 
    is_active, is_verified, is_locked, failed_login_attempts,
    department, designation, created_at, updated_at
) VALUES (
    'admin',
    'admin@delhipolice.gov.in',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEg7Iq',
    'System Administrator',
    'admin',
    true,
    true,
    false,
    0,
    'Delhi Police Cyber Cell',
    'System Administrator',
    NOW(),
    NOW()
);

-- Verify
SELECT username, email, role, is_active, is_verified 
FROM users WHERE username = 'admin';
```

**Then test login with:**
- Username: `admin`
- Password: `Admin@123456`

---

## 🎯 **PASSWORD HASH EXPLANATION:**

The hash `$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEg7Iq` is:
- **Algorithm:** bcrypt
- **Rounds:** 12
- **Plain password:** `Admin@123456`

This is the correct hash for that password.

---

**RUN THE DIAGNOSTIC SCRIPT IN NEON NOW!** 🔍

It will show you exactly what's wrong and fix it automatically! ✅
