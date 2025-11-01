# Automated Deployment Fix Script
# This script prepares all files for GitHub push

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "IPDR Tracking Hub - Deployment Fix" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

$projectPath = "C:\Users\saheb\Downloads\New FIR"
Set-Location $projectPath

Write-Host "Checking files..." -ForegroundColor Yellow
Write-Host ""

# Check if files exist
$files = @(
    "backend\runtime.txt",
    "backend\.python-version",
    "backend\render.yaml",
    "RENDER_DEPLOYMENT_FIX.md"
)

$allExist = $true
foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "  Found: $file" -ForegroundColor Green
    } else {
        Write-Host "  Missing: $file" -ForegroundColor Red
        $allExist = $false
    }
}

Write-Host ""

if ($allExist) {
    Write-Host "All files ready!" -ForegroundColor Green
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Option 1: Use GitHub Desktop (Recommended)" -ForegroundColor White
    Write-Host "  1. Open GitHub Desktop" -ForegroundColor Gray
    Write-Host "  2. File -> Add Local Repository" -ForegroundColor Gray
    Write-Host "  3. Select: C:\Users\saheb\Downloads\New FIR" -ForegroundColor Gray
    Write-Host "  4. Commit message: Fix Python 3.11.9 compatibility" -ForegroundColor Gray
    Write-Host "  5. Push to GitHub" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Option 2: Use Git Command Line" -ForegroundColor White
    Write-Host "  Run these commands:" -ForegroundColor Gray
    Write-Host '    git add backend/runtime.txt backend/.python-version backend/render.yaml RENDER_DEPLOYMENT_FIX.md' -ForegroundColor Cyan
    Write-Host '    git commit -m "Fix: Force Python 3.11.9 for deployment"' -ForegroundColor Cyan
    Write-Host '    git push origin main' -ForegroundColor Cyan
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "After Pushing:" -ForegroundColor Yellow
    Write-Host "  1. Go to Render Dashboard" -ForegroundColor Gray
    Write-Host "  2. Select ipdr-tracking-hub-api" -ForegroundColor Gray
    Write-Host "  3. Manual Deploy -> Clear build cache & deploy" -ForegroundColor Gray
    Write-Host "  4. Wait 5-10 minutes" -ForegroundColor Gray
    Write-Host "  5. Check logs for: Using Python version 3.11.9" -ForegroundColor Gray
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Files Changed:" -ForegroundColor Yellow
    Write-Host "  - backend/runtime.txt (Python 3.11.9)" -ForegroundColor White
    Write-Host "  - backend/.python-version (3.11.9)" -ForegroundColor White
    Write-Host "  - backend/render.yaml (runtime: python-3.11.9)" -ForegroundColor White
    Write-Host "  - RENDER_DEPLOYMENT_FIX.md (deployment guide)" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "Some files are missing!" -ForegroundColor Red
    Write-Host "Please run the fix script again." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
