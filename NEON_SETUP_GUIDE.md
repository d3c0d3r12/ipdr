# 🚀 Neon.tech Setup Guide - Quick Start

## Step 1: Create Neon Account & Get Connection String

1. **Go to** https://neon.tech
2. **Sign up** with GitHub or email
3. **Create new project:**
   - Name: `police-intel`
   - Region: `AWS Mumbai (ap-south-1)`
   - PostgreSQL: `16`
4. **Copy connection string** from dashboard

## Step 2: Update Environment Variables

1. **Copy the example file:**
   ```bash
   copy .env.example .env
   ```

2. **Edit `.env` file** and update:
   ```env
   DATABASE_URL=postgresql://your_user:your_password@ep-xxx-xxx.ap-south-1.aws.neon.tech/neondb?sslmode=require
   ```

3. **Generate JWT secrets:**
   ```bash
   # Run these commands to generate secure secrets
   openssl rand -base64 32
   openssl rand -base64 32
   ```

4. **Update JWT secrets in `.env`:**
   ```env
   JWT_SECRET=<paste first generated secret>
   JWT_REFRESH_SECRET=<paste second generated secret>
   ```

## Step 3: Setup Database Tables

**Option A: Using Neon SQL Editor (Recommended)**

1. Go to Neon Dashboard → **SQL Editor**
2. Copy contents from `backend/setup_neon_database.sql`
3. Paste and click **Run**

**Option B: Using psql**

```bash
psql "postgresql://your_user:your_password@ep-xxx-xxx.ap-south-1.aws.neon.tech/neondb?sslmode=require" -f backend/setup_neon_database.sql
```

## Step 4: Test Connection

```bash
cd backend
python test_neon_connection.py
```

**Expected Output:**
```
✅ Test 1: Basic Connection - PASSED
✅ Test 2: PostgreSQL Version
✅ Test 3: Table 'ip_records' - EXISTS
✅ Test 4: Record Count - 0 records
✅ Test 5: Indexes - 5 indexes found
✅ Test 6: Insert Operation - PASSED
✅ Test 7: Database Size - 8192 bytes

🎉 ALL TESTS PASSED!
```

## Step 5: Start Application

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## Step 6: Verify Everything Works

1. **Open browser:** http://localhost:3000
2. **Check backend health:** http://localhost:8000/health
3. **Upload a test file**
4. **Check Neon dashboard** to see data appearing!

---

## 🔧 Troubleshooting

### Connection Failed?

**Check 1: Verify .env file**
```bash
# Make sure DATABASE_URL is correct
cat .env | grep DATABASE_URL
```

**Check 2: Test with psql**
```bash
psql "your_connection_string_here"
```

**Check 3: Neon project active?**
- Go to Neon dashboard
- Check if project status is "Active"
- If suspended, it will wake up on first connection

### Table Not Found?

```bash
# Run the setup SQL script again
psql "your_connection_string" -f backend/setup_neon_database.sql
```

### Import Errors?

```bash
# Reinstall dependencies
cd backend
pip install -r requirements.txt
```

---

## 📊 Monitor Your Database

### Neon Dashboard

1. **Monitoring** → View metrics
2. **Branches** → Create dev/test branches
3. **Query** → Run SQL queries
4. **Settings** → Manage connection

### Check Database Size

```sql
SELECT pg_size_pretty(pg_database_size(current_database()));
```

### Check Table Rows

```sql
SELECT COUNT(*) FROM ip_records;
```

---

## ✅ Success Checklist

- [ ] Neon project created
- [ ] Connection string copied
- [ ] `.env` file updated
- [ ] JWT secrets generated
- [ ] Database tables created
- [ ] Connection test passed
- [ ] Backend starts successfully
- [ ] Frontend connects to backend
- [ ] Test upload works
- [ ] Data visible in Neon dashboard

---

## 🎉 You're Ready!

Your Police Intelligence System is now connected to Neon.tech!

**Next Steps:**
1. Test file upload functionality
2. Implement security features from `SECURITY_CHECKLIST.md`
3. Deploy to production
4. Monitor usage in Neon dashboard

**Need Help?**
- Neon Docs: https://neon.tech/docs
- Discord: https://discord.gg/neon
- Support: support@neon.tech

---

**Status: ✅ NEON SETUP COMPLETE**
