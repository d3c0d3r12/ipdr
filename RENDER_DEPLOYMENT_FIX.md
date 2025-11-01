# 🔧 Render Deployment Fix Guide

## ❌ Problem
Render is using Python 3.13.4 which is incompatible with `psycopg2-binary`, causing deployment failures.

## ✅ Solution
Force Python 3.11.9 using multiple methods to ensure compatibility.

---

## 📦 Files Updated

### 1. `backend/runtime.txt`
```
python-3.11.9
```
**Purpose:** Primary method to specify Python version on Render

### 2. `backend/.python-version`
```
3.11.9
```
**Purpose:** Backup method for Python version specification

### 3. `backend/render.yaml`
```yaml
services:
  - type: web
    name: ipdr-tracking-hub-api
    env: python
    runtime: python-3.11.9  # ← Added this line
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
```
**Purpose:** Explicitly set runtime in Render configuration

---

## 🚀 Deployment Steps

### Step 1: Push Changes to GitHub

**Using GitHub Desktop:**
1. Open GitHub Desktop
2. Sign in with `XenoTracer` account
3. File → Add Local Repository
4. Choose: `C:\Users\saheb\Downloads\New FIR`
5. You'll see 3 changed files:
   - `backend/runtime.txt`
   - `backend/.python-version` (new)
   - `backend/render.yaml`
   - `RENDER_DEPLOYMENT_FIX.md` (new)
6. Commit message: `Fix: Force Python 3.11.9 for deployment compatibility`
7. Click "Publish repository" or "Push origin"

**Using Git Command Line:**
```bash
cd "C:\Users\saheb\Downloads\New FIR"
git add backend/runtime.txt backend/.python-version backend/render.yaml RENDER_DEPLOYMENT_FIX.md
git commit -m "Fix: Force Python 3.11.9 for deployment compatibility"
git push origin main
```

### Step 2: Configure Render Dashboard

1. Go to: https://dashboard.render.com/
2. Select your service: **ipdr-tracking-hub-api**
3. Click **Settings**
4. Scroll to **Build & Deploy**
5. Verify these settings:

```
Name: ipdr-tracking-hub-api
Region: Singapore (or closest to India)
Branch: main
Root Directory: backend
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
Instance Type: Free
```

6. Scroll to **Environment**
7. Add/verify these environment variables:

```
DATABASE_URL = postgresql://your-neon-connection-string
INFOBYIP_API_KEY = your-infobyip-api-key
JWT_SECRET_KEY = your-jwt-secret-key
ENVIRONMENT = production
ALLOWED_ORIGINS = https://ipdr-tracking-hub.onrender.com
PYTHON_VERSION = 3.11.9
```

8. Click **Save Changes**

### Step 3: Trigger Manual Deploy

1. Go to **Manual Deploy** tab
2. Click **"Clear build cache & deploy"**
3. Wait 5-10 minutes

---

## ✅ Expected Success Output

```
==> Using Python version 3.11.9 (from runtime.txt)
==> Installing Python version 3.11.9...
==> Running build command 'pip install -r requirements.txt'
Successfully installed fastapi uvicorn psycopg2-binary ...
==> Build successful 🎉
==> Deploying...
==> Running 'uvicorn main:app --host 0.0.0.0 --port $PORT'
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:10000
==> Your service is live 🎉
```

---

## 🔍 Troubleshooting

### Issue: Still using Python 3.13

**Solution 1: Clear Build Cache**
- Render Dashboard → Manual Deploy → "Clear build cache & deploy"

**Solution 2: Set Environment Variable**
- Add: `PYTHON_VERSION = 3.11.9` in Environment tab

**Solution 3: Use render.yaml**
- Ensure `runtime: python-3.11.9` is in `backend/render.yaml`
- Render Dashboard → Settings → "Use render.yaml"

### Issue: psycopg2 still failing

**Solution: Use psycopg2 (not psycopg2-binary)**

Edit `backend/requirements.txt`:
```
# Change from:
psycopg2-binary==2.9.9

# To:
psycopg2==2.9.9
```

### Issue: Missing environment variables

**Check these are set:**
```bash
DATABASE_URL - PostgreSQL connection string
JWT_SECRET_KEY - Secret for JWT tokens
INFOBYIP_API_KEY - InfoByIP API key
ENVIRONMENT - Set to "production"
ALLOWED_ORIGINS - Frontend URL
```

---

## 📊 Verification

### Test Backend API

1. **Health Check:**
   ```
   https://ipdr-tracking-hub-api.onrender.com/
   ```
   Should return:
   ```json
   {
     "status": "IPDR Tracking Hub API is running",
     "environment": "production",
     "version": "1.0.0"
   }
   ```

2. **API Documentation:**
   ```
   https://ipdr-tracking-hub-api.onrender.com/docs
   ```
   Should show Swagger UI

3. **Database Connection:**
   Check logs for:
   ```
   INFO:     Database connection established
   ```

---

## 🎯 Next Steps After Backend is Live

1. ✅ Backend API deployed successfully
2. 🔄 Deploy Frontend (Nuxt 3 static site)
3. 🔄 Run database migrations
4. 🔄 Test user tracking system
5. 🔄 Configure custom domain (optional)

---

## 📞 Support

If deployment still fails:
1. Check Render logs for specific errors
2. Verify all environment variables are set
3. Ensure GitHub repository is accessible
4. Check Neon database is running

---

**Created:** 2025-11-01  
**Last Updated:** 2025-11-01  
**Status:** Ready to deploy
