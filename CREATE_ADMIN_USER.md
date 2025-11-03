# 🔐 **CREATE ADMIN USER - FIX LOGIN**

## 🎯 **PROBLEM:**

Login fails with "wrong credentials" because no user exists in the database yet.

---

## ✅ **SOLUTION: Run Database Initialization**

### **Step 1: Open Terminal in Backend Directory**
```bash
cd backend
```

### **Step 2: Run Database Initialization Script**
```bash
python init_database.py
```

### **Step 3: Follow Prompts**
```
🔧 Initializing database...
✅ All tables created successfully!

👤 Creating initial admin user...
✅ Admin user created successfully!
   Username: admin
   Password: Admin@123456
   ⚠️  PLEASE CHANGE THIS PASSWORD IMMEDIATELY!

📋 Create sample FIR case for testing? (y/n): n

✅ Database initialization complete!
```

---

## 🔑 **DEFAULT CREDENTIALS:**

After running the script, use these credentials:

```
Username: admin
Password: Admin@123456
```

---

## 🚀 **THEN LOGIN:**

1. Go to: `http://localhost:3000/login`
2. Enter:
   - Username: `admin`
   - Password: `Admin@123456`
3. Click "Login"
4. ✅ Should work!

---

## 📝 **WHAT THE SCRIPT DOES:**

1. **Creates all database tables:**
   - users
   - user_sessions
   - user_activities
   - login_attempts
   - access_logs
   - user_permissions
   - fir_cases
   - fir_ip_lookups
   - fir_evidence
   - fir_suspects
   - fir_timeline

2. **Creates admin user:**
   - Username: `admin`
   - Email: `admin@delhipolice.gov.in`
   - Password: `Admin@123456` (hashed with bcrypt)
   - Role: `admin`
   - Department: `Delhi Police Cyber Cell`
   - Status: Active and verified

3. **Optional: Creates sample FIR case**
   - FIR Number: `FIR/2025/SAMPLE/001`
   - For testing purposes

---

## 🐛 **IF SCRIPT FAILS:**

### **Error: "No module named 'core'"**

**Fix:**
```bash
# Make sure you're in backend directory
cd backend
python init_database.py
```

---

### **Error: "Database connection failed"**

**Fix:**
```bash
# Check if .env file exists with DATABASE_URL
# Should be in backend/.env
```

**Check .env file:**
```
DATABASE_URL=postgresql://...your-neon-db-url...
```

---

### **Error: "Table already exists"**

**This is OK!** The script will skip creating tables and just create the user.

---

## ✅ **VERIFY USER CREATED:**

After running the script, you can verify:

### **Option 1: Try Login**
```
1. Go to: http://localhost:3000/login
2. Username: admin
3. Password: Admin@123456
4. Should work! ✅
```

### **Option 2: Check Database**
```bash
# If you have psql installed
psql <your-database-url>
SELECT username, email, role FROM users;
```

**Expected output:**
```
 username |           email            | role  
----------+----------------------------+-------
 admin    | admin@delhipolice.gov.in   | admin
```

---

## 🔒 **SECURITY NOTE:**

**IMPORTANT:** After first login, change the password!

1. Login with default credentials
2. Go to profile/settings
3. Change password to something secure
4. Use strong password (min 8 chars, uppercase, lowercase, number, special char)

---

## 🎯 **QUICK STEPS:**

```bash
# 1. Open terminal
cd "c:\Users\saheb\Downloads\New FIR\backend"

# 2. Run script
python init_database.py

# 3. When asked about sample FIR, type: n

# 4. Done! Now login with:
#    Username: admin
#    Password: Admin@123456
```

---

## 📊 **COMPLETE WORKFLOW:**

```
1. Run init_database.py
   ↓
2. Admin user created in database
   ↓
3. Go to login page
   ↓
4. Enter: admin / Admin@123456
   ↓
5. ✅ Login successful!
   ↓
6. Redirect to dashboard
   ↓
7. Change password (recommended)
```

---

## 🎉 **RESULT:**

**Before:**
```
❌ Login → Wrong credentials
```

**After:**
```
✅ Login → Success!
✅ Dashboard loads
✅ All features accessible
```

---

**RUN THE SCRIPT NOW TO CREATE ADMIN USER!** 🚀

```bash
cd backend
python init_database.py
```

Then login with: `admin` / `Admin@123456` ✅
