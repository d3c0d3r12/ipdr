@echo off
REM ============================================================================
REM DELHI POLICE IPDR TRACKING HUB - SETUP & START
REM ============================================================================
REM This script starts both Backend and Frontend servers automatically
REM ============================================================================

title IPDR Tracking Hub - Setup

echo.
echo ============================================================================
echo           DELHI POLICE IPDR TRACKING HUB - SETUP
echo ============================================================================
echo.
echo Starting Backend and Frontend servers...
echo.

REM Get the directory where this script is located
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo [1/2] Starting Backend Server...
echo.

REM Start Backend in a new window
start "IPDR Backend Server" cmd /k "cd /d "%PROJECT_DIR%backend" && echo Starting Backend Server... && echo. && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM Wait 3 seconds for backend to initialize
timeout /t 3 /nobreak >nul

echo [2/2] Starting Frontend Server...
echo.

REM Start Frontend in a new window
start "IPDR Frontend Server" cmd /k "cd /d "%PROJECT_DIR%frontend" && echo Starting Frontend Server... && echo. && npm run dev"

REM Wait 2 seconds
timeout /t 2 /nobreak >nul

echo.
echo ============================================================================
echo                    SERVERS STARTED SUCCESSFULLY!
echo ============================================================================
echo.
echo Backend Server:  http://localhost:8000
echo Frontend Server: http://localhost:3000
echo.
echo Two new windows have been opened:
echo   1. Backend Server (Python/FastAPI)
echo   2. Frontend Server (Nuxt.js)
echo.
echo IMPORTANT:
echo - Keep both windows open while using the application
echo - To stop servers, close both windows or press Ctrl+C in each
echo - Backend API Docs: http://localhost:8000/docs
echo.
echo ============================================================================
echo.
echo Waiting 5 seconds before opening browser...
timeout /t 5 /nobreak >nul

REM Open browser to frontend
start http://localhost:3000

echo.
echo Browser opened to http://localhost:3000
echo.
echo You can now close this window.
echo The servers will continue running in the other windows.
echo.
echo Press any key to exit this setup window...
pause >nul
