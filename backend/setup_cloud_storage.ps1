# Cloud Storage System - Quick Setup Script (PowerShell)
# Run this from backend directory

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   CLOUD STORAGE SYSTEM - QUICK SETUP" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Install packages
Write-Host "[1/3] Installing required packages..." -ForegroundColor Yellow
Write-Host ""

try {
    pip install sqlalchemy asyncpg pandas python-docx aiosqlite alembic
    
    if ($LASTEXITCODE -ne 0) {
        throw "Package installation failed"
    }
    
    Write-Host ""
    Write-Host "✓ Packages installed successfully" -ForegroundColor Green
}
catch {
    Write-Host ""
    Write-Host "✗ ERROR: Failed to install packages" -ForegroundColor Red
    Write-Host "Please check your Python installation" -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Step 2: Create database tables
Write-Host ""
Write-Host "[2/3] Creating database tables..." -ForegroundColor Yellow
Write-Host ""

try {
    python create_cloud_storage_tables.py
    
    if ($LASTEXITCODE -ne 0) {
        throw "Table creation failed"
    }
    
    Write-Host ""
    Write-Host "✓ Database tables created successfully" -ForegroundColor Green
}
catch {
    Write-Host ""
    Write-Host "✗ ERROR: Failed to create tables" -ForegroundColor Red
    Write-Host "Please check your database connection" -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Success
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "   SETUP COMPLETE!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Cloud storage system is ready to use!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Start backend: uvicorn main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor White
Write-Host "  2. Open http://localhost:8000/docs" -ForegroundColor White
Write-Host "  3. Look for 'Cloud Storage' section" -ForegroundColor White
Write-Host "  4. Test the endpoints" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to exit"
