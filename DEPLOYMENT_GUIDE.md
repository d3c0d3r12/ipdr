# 🚀 Complete Deployment Guide - Render.com

This guide will help you deploy both **Backend** (FastAPI) and **Frontend** (Nuxt) to Render.com, connected to your **Neon** database.

---

## 📋 Prerequisites Checklist

- ✅ Neon database set up and connection string ready
- ✅ GitHub account (to connect to Render)
- ✅ Render.com account (free tier available)

---

## 🔧 PART 1: Deploy Backend (FastAPI)

### Step 1: Prepare Backend for Render

1. **Create `.env` file** (or use Render Environment Variables - recommended):
   ```env
   DATABASE_URL=your_neon_connection_string
   JWT_SECRET=generate_a_secure_random_string
   ALLOWED_ORIGINS=https://your-frontend-name.onrender.com
   ENVIRONMENT=production
   ```

2. **Push backend to GitHub** (if not already):
   ```powershell
   cd "C:\Users\saheb\Downloads\New FIR"
   git init
   git add backend/
   git commit -m "Initial backend commit"
   git remote add origin YOUR_GITHUB_REPO_URL
   git push -u origin main
   ```

### Step 2: Deploy Backend on Render

1. **Go to Render Dashboard**: https://dashboard.render.com

2. **Create New Web Service**:
   - Click **"New +"** → **"Web Service"**
   - Connect your GitHub repository
   - Select your repository

3. **Configure Service**:
   - **Name**: `police-intel-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Root Directory**: `backend`

4. **Set Environment Variables** (in Render Dashboard):
   ```
   DATABASE_URL = (your Neon connection string)
   JWT_SECRET = (generate random string)
   ALLOWED_ORIGINS = https://your-frontend-name.onrender.com
   ENVIRONMENT = production
   PYTHON_VERSION = 3.11
   ```

5. **Deploy**:
   - Click **"Create Web Service"**
   - Wait for deployment (5-10 minutes)
   - Copy your backend URL: `https://police-intel-backend.onrender.com`

---

## 🎨 PART 2: Deploy Frontend (Nuxt)

### Step 1: Update Frontend Configuration

1. **Update `frontend/nuxt.config.ts`** (already done ✅):
   - API base URL will use environment variable

2. **Push frontend to GitHub** (same repo or separate):
   ```powershell
   git add frontend/
   git commit -m "Add frontend"
   git push
   ```

### Step 2: Deploy Frontend on Render

1. **Create New Web Service**:
   - Click **"New +"** → **"Web Service"**
   - Select your GitHub repository

2. **Configure Service**:
   - **Name**: `police-intel-frontend`
   - **Environment**: `Node`
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Start Command**: `cd frontend && npm run preview`
   - **Root Directory**: Leave blank (or set to `frontend` if using subdirectory)

3. **Set Environment Variables**:
   ```
   NUXT_PUBLIC_API_BASE = https://police-intel-backend.onrender.com
   NODE_VERSION = 20
   ```

4. **Deploy**:
   - Click **"Create Web Service"**
   - Wait for deployment (5-10 minutes)
   - Your frontend will be live at: `https://police-intel-frontend.onrender.com`

---

## 🔗 PART 3: Update Backend CORS

After frontend is deployed, update backend environment variable:

1. Go to **Backend Service** → **Environment**
2. Update `ALLOWED_ORIGINS`:
   ```
   ALLOWED_ORIGINS = https://police-intel-frontend.onrender.com
   ```
3. **Manual Deploy** to apply changes

---

## ✅ Final Checklist

- [ ] Backend deployed and healthy: `https://your-backend.onrender.com/health`
- [ ] Frontend deployed: `https://your-frontend.onrender.com`
- [ ] Database connected (check backend logs)
- [ ] CORS configured correctly
- [ ] Environment variables set on both services

---

## 🐛 Troubleshooting

### Backend Issues

**Database Connection Failed**:
- Check `DATABASE_URL` in Render environment variables
- Ensure Neon database is active
- Test connection locally first

**Port Error**:
- Render auto-assigns `$PORT` - don't hardcode port 8000

**Build Fails**:
- Check `requirements.txt` has all dependencies
- Ensure Python version matches (`runtime.txt`)

### Frontend Issues

**API Calls Fail (CORS)**:
- Check `NUXT_PUBLIC_API_BASE` is correct backend URL
- Verify `ALLOWED_ORIGINS` in backend includes frontend URL
- Use HTTPS URLs (no http://localhost)

**Build Fails**:
- Ensure Node version is 20+ (`NODE_VERSION=20`)
- Check `package.json` has all dependencies
- Review build logs in Render dashboard

**Blank Page**:
- Check browser console for errors
- Verify API base URL is correct
- Ensure SSR is enabled in `nuxt.config.ts`

---

## 🔒 Security Notes

1. **JWT_SECRET**: Use a strong random string (generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
2. **DATABASE_URL**: Keep secret - only in environment variables
3. **HTTPS Only**: Render provides HTTPS automatically
4. **CORS**: Only allow your frontend domain

---

## 📊 Monitoring

- **Render Dashboard**: View logs, metrics, deployment history
- **Backend Health**: `https://your-backend.onrender.com/health`
- **API Docs**: `https://your-backend.onrender.com/docs` (if enabled)

---

## 🚀 Quick Deploy Commands Summary

```bash
# 1. Backend on Render
# Build: pip install -r requirements.txt
# Start: uvicorn main:app --host 0.0.0.0 --port $PORT

# 2. Frontend on Render  
# Build: cd frontend && npm install && npm run build
# Start: cd frontend && npm run preview
```

---

Your app will be live at: **https://police-intel-frontend.onrender.com** 🎉


