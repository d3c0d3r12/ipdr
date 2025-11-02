# 🚀 Quick Deployment Script
# Deploy all amazing features to production

Write-Host ""
Write-Host "🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥" -ForegroundColor Red
Write-Host "   DEPLOYING AMAZING FEATURES" -ForegroundColor Cyan
Write-Host "   Status Tracking • Cloudflare Bypass • Downloads" -ForegroundColor Yellow
Write-Host "🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥" -ForegroundColor Red
Write-Host ""

# Step 1: Backup old upload page
Write-Host "📦 Step 1: Backing up old upload page..." -ForegroundColor Yellow
Copy-Item "frontend\pages\upload.vue" "frontend\pages\upload-old-backup.vue" -Force
Write-Host "✅ Backup created: upload-old-backup.vue" -ForegroundColor Green

# Step 2: Replace with enhanced version
Write-Host ""
Write-Host "🔄 Step 2: Replacing with enhanced version..." -ForegroundColor Yellow
Copy-Item "frontend\pages\upload-enhanced.vue" "frontend\pages\upload.vue" -Force
Write-Host "✅ Enhanced upload page activated!" -ForegroundColor Green

# Step 3: Check git status
Write-Host ""
Write-Host "📊 Step 3: Checking git status..." -ForegroundColor Yellow
git status --short

# Step 4: Add files
Write-Host ""
Write-Host "➕ Step 4: Adding files to git..." -ForegroundColor Yellow
git add frontend/pages/upload.vue
git add frontend/pages/index.vue
git add frontend/package.json
git add frontend/nuxt.config.ts
git add backend/routers/upload.py
git add backend/utils/enhanced_cloudflare_bypass.py
git add backend/requirements.txt
git add DEPLOY_AMAZING_FEATURES.md
git add CLOUDFLARE_BYPASS_INTEGRATION.md
git add ENHANCED_BYPASS_GUIDE.md
Write-Host "✅ Files added to git" -ForegroundColor Green

# Step 5: Show what will be committed
Write-Host ""
Write-Host "📝 Step 5: Files to be committed:" -ForegroundColor Yellow
git status --short

# Step 6: Commit
Write-Host ""
Write-Host "💾 Step 6: Creating commit..." -ForegroundColor Yellow
$commitMessage = "feat: Add amazing features - Real-time status tracking, Cloudflare bypass, and download options"
git commit -m $commitMessage
Write-Host "✅ Commit created!" -ForegroundColor Green

# Step 7: Push
Write-Host ""
Write-Host "🚀 Step 7: Pushing to GitHub..." -ForegroundColor Yellow
Write-Host "⚠️  This will trigger auto-deployment on Render.com" -ForegroundColor Yellow
Write-Host ""
$confirm = Read-Host "Push to production? (y/n)"

if ($confirm -eq "y") {
    git push origin main
    Write-Host ""
    Write-Host "✅ Pushed to GitHub!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🎉 DEPLOYMENT STARTED!" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "⏱️  Expected deployment time:" -ForegroundColor Yellow
    Write-Host "   - Backend: 5-10 minutes" -ForegroundColor White
    Write-Host "   - Frontend: 10-15 minutes" -ForegroundColor White
    Write-Host ""
    Write-Host "🌐 Your sites:" -ForegroundColor Yellow
    Write-Host "   - Backend:  https://ipdr-tracking-hub.onrender.com" -ForegroundColor Cyan
    Write-Host "   - Frontend: https://ipdr-tracking-hub-1.onrender.com" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📊 Monitor deployment:" -ForegroundColor Yellow
    Write-Host "   - https://dashboard.render.com/" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "✅ After deployment, test at:" -ForegroundColor Green
    Write-Host "   https://ipdr-tracking-hub-1.onrender.com/upload" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "❌ Deployment cancelled" -ForegroundColor Red
    Write-Host "💡 Run this script again when ready to deploy" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥" -ForegroundColor Red
Write-Host ""
