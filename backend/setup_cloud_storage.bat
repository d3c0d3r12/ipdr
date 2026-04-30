@echo off
REM Cloud Storage System - Quick Setup Script
REM Run this from backend directory

echo.
echo ============================================================
echo    CLOUD STORAGE SYSTEM - QUICK SETUP
echo ============================================================
echo.
echo [1/3] Installing required packages...
echo.

pip install sqlalchemy asyncpg pandas python-docx aiosqlite alembic

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Failed to install packages
    echo Please check your Python installation
    pause
    exit /b 1
)

echo.
echo [2/3] Creating database tables...
echo.

python create_cloud_storage_tables.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Failed to create tables
    echo Please check your database connection
    pause
    exit /b 1
)

echo.
echo ============================================================
echo    SETUP COMPLETE!
echo ============================================================
echo.
echo Cloud storage system is ready to use!
echo.
echo Next steps:
echo   1. Start backend: uvicorn main:app --reload --host 0.0.0.0 --port 8000
echo   2. Open http://localhost:8000/docs
echo   3. Look for "Cloud Storage" section
echo   4. Test the endpoints
echo.
echo Press any key to exit...
pause >nul
