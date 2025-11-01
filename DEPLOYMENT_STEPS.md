# 🚀 Deployment Steps - IPDR Tracking Hub (Private GitHub + Render)

## ✅ Step 1: Install Git (Required)

### Download and Install Git:
1. Go to: https://git-scm.com/download/win
2. Download "64-bit Git for Windows Setup"
3. Run installer with default settings
4. **IMPORTANT**: Select "Git from the command line and also from 3rd-party software"
5. After installation, close and reopen your terminal

### Verify Installation:
```powershell
git --version
# Should show: git version 2.x.x
```

---

## ✅ Step 2: Verify Security (CRITICAL)

Before pushing anything, verify sensitive files are protected:

```powershell
cd "C:\Users\saheb\Downloads\New FIR"

# Check .gitignore exists
type .gitignore

# Initialize git (safe to run)
git init

# Check what will be tracked
git status

# VERIFY these are NOT listed:
# ❌ .env
# ❌ backend/processed/ (your 67 case files)
# ❌ backend/uploads/
# ❌ backend/venv/
# ❌ frontend/node_modules/

# If .env shows up, STOP and tell me!
```

---

## ✅ Step 3: Create Private GitHub Repository

1. **Go to GitHub**: https://github.com/new
2. **Repository name**: `ipdr-tracking-hub`
3. **Description**: "IPDR Tracking Hub - IP Data Record Intelligence System for Delhi Police"
4. **Visibility**: ⭐ **PRIVATE** (Very Important!)
5. **DON'T** check any boxes (no README, no .gitignore, no license)
6. Click **"Create repository"**

7. **Copy the repository URL** (will look like):
   ```
   https://github.com/YOUR_USERNAME/ipdr-tracking-hub.git
   ```

---

## ✅ Step 4: Push Code to GitHub (Safely)

```powershell
cd "C:\Users\saheb\Downloads\New FIR"

# Configure git (first time only)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Add all files (protected by .gitignore)
git add .

# Verify again - .env should NOT appear
git status

# Commit
git commit -m "Initial commit - IPDR Tracking Hub"

# Connect to your GitHub repo
git remote add origin https://github.com/YOUR_USERNAME/ipdr-tracking-hub.git

# Push to GitHub
git push -u origin main
# OR if it asks for 'master':
git push -u origin master
```

**GitHub will ask for authentication:**
- Use Personal Access Token (not password)
- Generate at: https://github.com/settings/tokens
- Select: `repo` scope
- Copy token and paste when prompted

---

## ✅ Step 5: Get Your Database Connection String

You need your Neon database URL. It looks like:
```
postgresql://username:password@ep-xxx-xxx.ap-south-1.aws.neon.tech/police_data?sslmode=require
```

**Where to find it:**
1. Go to: https://console.neon.tech
2. Select your project
3. Click "Connection Details"
4. Copy the connection string
5. **Keep this safe - we'll use it in Render**

---

## ✅ Step 6: Deploy Backend to Render

1. **Go to Render**: https://dashboard.render.com/register
2. Sign up with GitHub account
3. Click **"New +"** → **"Web Service"**
4. Click **"Connect GitHub"** → Authorize Render
5. Select your repository: `ipdr-tracking-hub`
6. Click **"Connect"**

### Backend Configuration:
- **Name**: `ipdr-tracking-hub-api`
- **Region**: Singapore (closest to India)
- **Branch**: `main` (or `master`)
- **Root Directory**: `backend`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Instance Type**: Free

### Environment Variables (Click "Add Environment Variable"):
```
DATABASE_URL = (paste your Neon connection string)
JWT_SECRET = (generate random: use any 32+ character random string)
ALLOWED_ORIGINS = https://ipdr-tracking-hub.onrender.com
ENVIRONMENT = production
PYTHON_VERSION = 3.11
```

**Generate JWT_SECRET:**
- Use: https://www.random.org/strings/
- Or type any random 32+ characters

7. Click **"Create Web Service"**
8. **Wait 5-10 minutes** for deployment
9. **Copy your backend URL**: `https://ipdr-tracking-hub-api.onrender.com`

---

## ✅ Step 7: Deploy Frontend to Render

1. In Render Dashboard, click **"New +"** → **"Web Service"**
2. Select same repository: `ipdr-tracking-hub`
3. Click **"Connect"**

### Frontend Configuration:
- **Name**: `ipdr-tracking-hub`
- **Region**: Singapore
- **Branch**: `main` (or `master`)
- **Root Directory**: `frontend`
- **Environment**: `Node`
- **Build Command**: `npm install && npm run build`
- **Start Command**: `npm run preview`
- **Instance Type**: Free

### Environment Variables:
```
NUXT_PUBLIC_API_BASE = https://ipdr-tracking-hub-api.onrender.com
NODE_VERSION = 20
```

4. Click **"Create Web Service"**
5. **Wait 5-10 minutes** for deployment
6. **Your app is live!** 🎉

---

## ✅ Step 8: Update Backend CORS

After frontend deploys:
1. Go to **Backend Service** → **Environment** tab
2. Edit `ALLOWED_ORIGINS` variable
3. Change to: `https://ipdr-tracking-hub.onrender.com`
4. Click **"Save Changes"**
5. Backend will auto-redeploy (2-3 minutes)

---

## ✅ Step 9: Test Your Deployment

### Test Backend:
```
https://ipdr-tracking-hub-api.onrender.com/health
```
Should show: `{"status": "healthy", "database": "connected"}`

### Test Frontend:
```
https://ipdr-tracking-hub.onrender.com
```
Should show your dashboard!

### Login:
- Username: `inspector`
- Password: `secure@123`

---

## 🎉 Success! Share with Your Sir:

**Live URL**: `https://ipdr-tracking-hub.onrender.com`

**Demo Credentials:**
- Inspector: `inspector` / `secure@123`
- Analyst: `analyst` / `an@123`

---

## ⚠️ Important Notes:

1. **Free Tier Limitation**: Services sleep after 15 minutes of inactivity
   - First load after sleep takes 30-60 seconds
   - Subsequent loads are instant

2. **Private Repository**: Only you can see the code on GitHub

3. **Secrets are Safe**: 
   - Not in GitHub ✅
   - Encrypted in Render ✅
   - Your 67 processed files stayed local ✅

4. **Upgrade Later**: If needed, upgrade to paid tier ($7/month per service) for:
   - No sleep time
   - Faster performance
   - More resources

---

## 🐛 Troubleshooting:

### Backend won't deploy?
- Check build logs in Render dashboard
- Verify `requirements.txt` is in `backend/` folder
- Ensure `DATABASE_URL` is correct

### Frontend won't deploy?
- Check build logs
- Verify `package.json` is in `frontend/` folder
- Ensure `NUXT_PUBLIC_API_BASE` points to backend URL

### CORS errors?
- Verify `ALLOWED_ORIGINS` in backend matches frontend URL exactly
- Must include `https://` (no trailing slash)

### Database connection failed?
- Test Neon connection string locally first
- Ensure Neon database is active (not suspended)
- Check for typos in connection string

---

## 📞 Need Help?

If you get stuck at any step, let me know which step number and what error you're seeing!

---

**Ready to start? Begin with Step 1: Install Git!** 🚀
