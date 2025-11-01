# ⚡ Quick Deploy Reference Card - IPDR Tracking Hub

## 🎯 Your Mission: Get Live URL for Sir

**Target**: `https://ipdr-tracking-hub.onrender.com`  
**Time**: 20-30 minutes  
**Cost**: FREE  

---

## 📝 Pre-Deployment Checklist

- [ ] Git installed (download from git-scm.com)
- [ ] GitHub account created
- [ ] Render account created (use GitHub login)
- [ ] Neon database connection string ready

---

## 🚀 Quick Commands (Copy-Paste)

### 1. Install Git First!
Download: https://git-scm.com/download/win

### 2. Verify Security
```powershell
cd "C:\Users\saheb\Downloads\New FIR"
powershell -ExecutionPolicy Bypass -File verify_security.ps1
```

### 3. Initialize Git
```powershell
git init
git add .
git status
# ⚠️ VERIFY: .env should NOT appear!
```

### 4. First Commit
```powershell
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
git commit -m "Initial commit - IPDR Tracking Hub"
```

### 5. Push to GitHub
```powershell
# Replace YOUR_USERNAME with your GitHub username
git remote add origin https://github.com/YOUR_USERNAME/ipdr-tracking-hub.git
git push -u origin main
```

---

## 🔑 Environment Variables You'll Need

### For Backend (Render):
```
DATABASE_URL = postgresql://user:pass@ep-xxx.neon.tech/police_data?sslmode=require
JWT_SECRET = any_random_32_character_string_here_12345
ALLOWED_ORIGINS = https://ipdr-tracking-hub.onrender.com
ENVIRONMENT = production
PYTHON_VERSION = 3.11
```

### For Frontend (Render):
```
NUXT_PUBLIC_API_BASE = https://ipdr-tracking-hub-api.onrender.com
NODE_VERSION = 20
```

---

## 🎯 Render Configuration (Quick Copy)

### Backend Service:
- **Name**: `ipdr-tracking-hub-api`
- **Root Directory**: `backend`
- **Build**: `pip install -r requirements.txt`
- **Start**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Frontend Service:
- **Name**: `ipdr-tracking-hub`
- **Root Directory**: `frontend`
- **Build**: `npm install && npm run build`
- **Start**: `npm run preview`

---

## 🔗 Important URLs

### Setup:
- Git Download: https://git-scm.com/download/win
- GitHub New Repo: https://github.com/new
- Render Dashboard: https://dashboard.render.com
- Neon Console: https://console.neon.tech

### After Deployment:
- Backend Health: `https://ipdr-tracking-hub-api.onrender.com/health`
- Frontend App: `https://ipdr-tracking-hub.onrender.com`
- API Docs: `https://ipdr-tracking-hub-api.onrender.com/docs`

---

## 👤 Demo Credentials

**Inspector Account:**
- Username: `inspector`
- Password: `secure@123`

**Analyst Account:**
- Username: `analyst`
- Password: `an@123`

---

## ⚠️ Common Issues & Fixes

### "git: command not found"
→ Install Git first, then restart terminal

### ".env appears in git status"
→ Run: `git rm --cached .env`

### "Authentication failed" on git push
→ Use Personal Access Token (not password)
→ Generate at: https://github.com/settings/tokens

### Backend deploy fails
→ Check `DATABASE_URL` is correct
→ Verify `requirements.txt` exists in backend/

### Frontend deploy fails
→ Check `package.json` exists in frontend/
→ Verify `NUXT_PUBLIC_API_BASE` points to backend

### CORS errors in browser
→ Update backend `ALLOWED_ORIGINS` to match frontend URL
→ Must be exact match with https://

### "Service Unavailable" on first load
→ Free tier sleeps after 15min - wait 30-60 seconds

---

## 🎉 Success Indicators

✅ Backend health check returns: `{"status": "healthy"}`  
✅ Frontend loads dashboard  
✅ Can login with demo credentials  
✅ No console errors in browser  

---

## 📞 Share with Sir

**Live Demo URL:**
```
https://ipdr-tracking-hub.onrender.com
```

**Login:**
- Username: `inspector`
- Password: `secure@123`

**Features to Show:**
1. Dashboard with statistics
2. Upload HTML file functionality
3. IP records list
4. Analytics page
5. Modern dark theme UI

---

## 💡 Pro Tips

1. **First Load**: Takes 30-60 seconds (free tier wakes up)
2. **Demo Mode**: Works without actual data processing
3. **Private Repo**: Code is safe, only you can access
4. **Upgrade Later**: $7/month per service for no sleep time

---

## 🔒 Security Confirmation

✅ `.env` never pushed to GitHub  
✅ 67 processed files stayed local  
✅ Database credentials only in Render  
✅ Private repository  
✅ HTTPS enabled automatically  

---

**Need help? Check DEPLOYMENT_STEPS.md for detailed instructions!**
