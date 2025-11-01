# Automated GitHub Push Script
# This script helps you push changes to GitHub

Write-Host "IPDR Tracking Hub - GitHub Push Helper" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

# Check if GitHub Desktop is installed
$githubDesktopPath = "$env:LOCALAPPDATA\GitHubDesktop\GitHubDesktop.exe"

if (Test-Path $githubDesktopPath) {
    Write-Host "Opening GitHub Desktop..." -ForegroundColor Green
    Start-Process $githubDesktopPath
    Write-Host ""
    Write-Host "Steps to follow in GitHub Desktop:" -ForegroundColor Yellow
    Write-Host "1. Sign in with your XenoTracer account" -ForegroundColor White
    Write-Host "2. File -> Add Local Repository" -ForegroundColor White
    Write-Host "3. Choose: C:\Users\saheb\Downloads\New FIR" -ForegroundColor White
    Write-Host "4. You'll see 1 changed file: backend/runtime.txt" -ForegroundColor White
    Write-Host "5. Add commit message: Fix Python 3.11.9 compatibility" -ForegroundColor White
    Write-Host "6. Click Commit to main" -ForegroundColor White
    Write-Host "7. Click Publish repository (or Push origin)" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "GitHub Desktop not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Option 1: Install GitHub Desktop" -ForegroundColor Yellow
    Write-Host "Download from: https://desktop.github.com/" -ForegroundColor White
    Write-Host ""
    Write-Host "Option 2: Use Git Bash" -ForegroundColor Yellow
    Write-Host "Download from: https://git-scm.com/download/win" -ForegroundColor White
    Write-Host ""
    Write-Host "Option 3: Manual Commands (if Git is installed)" -ForegroundColor Yellow
    Write-Host "Run these in PowerShell:" -ForegroundColor White
    Write-Host '  cd "C:\Users\saheb\Downloads\New FIR"' -ForegroundColor Cyan
    Write-Host "  git add backend/runtime.txt" -ForegroundColor Cyan
    Write-Host '  git commit -m "Fix: Python 3.11.9 compatibility"' -ForegroundColor Cyan
    Write-Host "  git push -u origin main" -ForegroundColor Cyan
    Write-Host ""
}

Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
