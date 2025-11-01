# ⚡ Quick Start: Render Deployment (5 Steps)

## Step 1: Push Code to GitHub
```powershell
cd "C:\Users\saheb\Downloads\New FIR"
git init
git add .
git commit -m "Ready for deployment"
# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/police-intel.git
git push -u origin main
```

## Step 2: Deploy Backend (Render.com)

1. Go to https://dashboard.render.com
2. **New +** → **Web Service**
3. Connect GitHub repo
4. Settings:
   - **Name**: `police-backend`
   - **Root Directory**: `backend`
   - **Build**: `pip install -r requirements.txt`
   - **Start**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Environment Variables:
   - `DATABASE_URL` = (your Neon connection string)
   - `JWT_SECRET` = (random string)
   - `ALLOWED_ORIGINS` = `https://police-frontend.onrender.com`
6. Click **Create**
7. **Wait for deploy** → Copy URL: `https://police-backend.onrender.com`

## Step 3: Deploy Frontend (Render.com)

1. **New +** → **Web Service** (again)
2. Same GitHub repo
3. Settings:
   - **Name**: `police-frontend`
   - **Root Directory**: `frontend`
   - **Build**: `npm install && npm run build`
   - **Start**: `npm run preview`
4. Environment Variables:
   - `NUXT_PUBLIC_API_BASE` = `https://police-backend.onrender.com`
5. Click **Create**
6. **Wait for deploy** → Your app is live! 🎉

## Step 4: Update Backend CORS

After frontend deploys:
1. Go to **Backend Service** → **Environment**
2. Update `ALLOWED_ORIGINS` = `https://police-frontend.onrender.com`
3. Click **Save** → Auto-redeploys

## Step 5: Test

- Frontend: https://police-frontend.onrender.com
- Backend Health: https://police-backend.onrender.com/health
- API Docs: https://police-backend.onrender.com/docs

✅ Done!

---

## 🔗 URLs You'll Get:

- **Backend**: `https://police-backend.onrender.com`
- **Frontend**: `https://police-frontend.onrender.com`
- **Neon DB**: Already configured ✅

---

## ⚠️ Important Notes:

1. **Free Tier**: Services spin down after 15min inactivity (slow first load)
2. **Database**: Neon free tier is perfect for this
3. **HTTPS**: Automatic on Render
4. **Environment Variables**: Set in Render dashboard, not `.env` file

---

Need help? Check `DEPLOYMENT_GUIDE.md` for detailed troubleshooting!

