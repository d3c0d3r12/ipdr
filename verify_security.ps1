# Security Verification Script
# Run this BEFORE pushing to GitHub

Write-Host "Security Verification for GitHub Push" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

$projectPath = "C:\Users\saheb\Downloads\New FIR"
Set-Location $projectPath

# Check 1: .gitignore exists
Write-Host "Checking .gitignore..." -ForegroundColor Yellow
if (Test-Path ".gitignore") {
    Write-Host "  .gitignore exists" -ForegroundColor Green
} else {
    Write-Host "  .gitignore NOT FOUND - STOP!" -ForegroundColor Red
    exit 1
}

# Check 2: .env file exists (should stay local)
Write-Host ""
Write-Host "Checking .env file..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "  .env exists locally (will be blocked from GitHub)" -ForegroundColor Green
} else {
    Write-Host "  .env not found - you will need to create it for local testing" -ForegroundColor Yellow
}

# Check 3: Sensitive directories
Write-Host ""
Write-Host "Checking sensitive directories..." -ForegroundColor Yellow

$sensitiveDirs = @(
    "backend\processed",
    "backend\uploads",
    "backend\venv",
    "frontend\node_modules"
)

foreach ($dir in $sensitiveDirs) {
    if (Test-Path $dir) {
        $count = (Get-ChildItem $dir -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
        Write-Host "  $dir exists ($count files) - will be blocked" -ForegroundColor Green
    }
}

# Check 4: Git status (if initialized)
Write-Host ""
Write-Host "Checking Git status..." -ForegroundColor Yellow
if (Test-Path ".git") {
    Write-Host "  Git repository initialized" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Files to be committed:" -ForegroundColor Cyan
    git status --short | ForEach-Object {
        if ($_ -match "\.env$" -or $_ -match "processed/" -or $_ -match "uploads/" -or $_ -match "venv/" -or $_ -match "node_modules/") {
            Write-Host "    DANGER: $_" -ForegroundColor Red
        } else {
            Write-Host "    $_" -ForegroundColor Green
        }
    }
} else {
    Write-Host "  Git not initialized yet - run git init first" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "VERIFICATION COMPLETE" -ForegroundColor Cyan
Write-Host ""
Write-Host "Safe to push if:" -ForegroundColor Green
Write-Host "   - No DANGER items above" -ForegroundColor Green
Write-Host "   - .env is NOT in git status" -ForegroundColor Green
Write-Host "   - processed/ is NOT in git status" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "   1. Review the file list above" -ForegroundColor White
Write-Host "   2. If safe, run: git add ." -ForegroundColor White
Write-Host "   3. Then run: git commit -m Initial-commit" -ForegroundColor White
Write-Host "   4. Follow DEPLOYMENT_STEPS.md" -ForegroundColor White
Write-Host ""
