@echo off
REM ============================================================================
REM DELHI POLICE IPDR TRACKING HUB - START SERVERS (ENHANCED)
REM ============================================================================
REM This script starts both Backend and Frontend with dependency checks
REM ============================================================================

title IPDR Tracking Hub - Server Startup

color 0A
echo.
echo ============================================================================
echo           DELHI POLICE IPDR TRACKING HUB - SERVER STARTUP
echo ============================================================================
echo.

REM Get the directory where this script is located
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo [INFO] Project Directory: %PROJECT_DIR%
echo.

REM ============================================================================
REM CHECK DEPENDENCIES
REM ============================================================================

echo [STEP 1/4] Checking Dependencies...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo [INFO] Please install Python 3.8+ from https://www.python.org/
    echo.
    pause
    exit /b 1
)
echo [OK] Python is installed
python --version

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH!
    echo [INFO] Please install Node.js from https://nodejs.org/
    echo.
    pause
    exit /b 1
)
echo [OK] Node.js is installed
node --version

REM Check if npm is installed
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm is not installed or not in PATH!
    echo.
    pause
    exit /b 1
)
echo [OK] npm is installed
npm --version

echo.
echo [SUCCESS] All dependencies are installed!
echo.

REM ============================================================================
REM CHECK BACKEND DIRECTORY
REM ============================================================================

echo [STEP 2/4] Checking Backend...
echo.

if not exist "%PROJECT_DIR%backend" (
    echo [ERROR] Backend directory not found!
    echo [INFO] Expected: %PROJECT_DIR%backend
    echo.
    pause
    exit /b 1
)
echo [OK] Backend directory found

if not exist "%PROJECT_DIR%backend\main.py" (
    echo [ERROR] Backend main.py not found!
    echo.
    pause
    exit /b 1
)
echo [OK] Backend main.py found

echo.

REM ============================================================================
REM CHECK FRONTEND DIRECTORY
REM ============================================================================

echo [STEP 3/4] Checking Frontend...
echo.

if not exist "%PROJECT_DIR%frontend" (
    echo [ERROR] Frontend directory not found!
    echo [INFO] Expected: %PROJECT_DIR%frontend
    echo.
    pause
    exit /b 1
)
echo [OK] Frontend directory found

if not exist "%PROJECT_DIR%frontend\package.json" (
    echo [ERROR] Frontend package.json not found!
    echo.
    pause
    exit /b 1
)
echo [OK] Frontend package.json found

echo.

REM ============================================================================
REM START SERVERS
REM ============================================================================

echo [STEP 4/4] Starting Servers...
echo.

echo [INFO] Starting Backend Server (Port 8000)...
start "IPDR Backend - FastAPI" cmd /k "cd /d "%PROJECT_DIR%backend" && color 0B && title IPDR Backend Server && echo ============================================================================ && echo                    IPDR BACKEND SERVER && echo ============================================================================ && echo. && echo Starting FastAPI server... && echo. && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo [OK] Backend server starting in new window...
echo.

REM Wait for backend to initialize
echo [INFO] Waiting 5 seconds for backend to initialize...
timeout /t 5 /nobreak >nul

echo [INFO] Starting Frontend Server (Port 3000)...
start "IPDR Frontend - Nuxt.js" cmd /k "cd /d "%PROJECT_DIR%frontend" && color 0E && title IPDR Frontend Server && echo ============================================================================ && echo                    IPDR FRONTEND SERVER && echo ============================================================================ && echo. && echo Starting Nuxt.js development server... && echo. && npm run dev"

echo [OK] Frontend server starting in new window...
echo.

REM Wait for frontend to initialize
echo [INFO] Waiting 8 seconds for frontend to initialize...
timeout /t 8 /nobreak >nul

echo.
echo ============================================================================
echo                    SERVERS STARTED SUCCESSFULLY!
echo ============================================================================
echo.
echo   Backend API:     http://localhost:8000
echo   API Docs:        http://localhost:8000/docs
echo   Frontend App:    http://localhost:3000
echo.
echo ============================================================================
echo.
echo [INFO] Two server windows are now running:
echo   1. Backend Server  (Blue)   - FastAPI on port 8000
echo   2. Frontend Server (Yellow) - Nuxt.js on port 3000
echo.
echo [IMPORTANT]
echo   - Keep both windows open while using the application
echo   - To stop: Close both windows or press Ctrl+C in each
echo   - Check server windows for any errors
echo.
echo ============================================================================
echo.

REM Open browser
echo [INFO] Opening browser in 3 seconds...
timeout /t 3 /nobreak >nul

start http://localhost:3000

echo.
echo [SUCCESS] Browser opened to http://localhost:3000
echo.
echo ============================================================================
echo                         SETUP COMPLETE!
echo ============================================================================
echo.
echo You can now:
echo   - Use the application at http://localhost:3000
echo   - View API docs at http://localhost:8000/docs
echo   - Close this window (servers will keep running)
echo.
echo To stop servers: Close the Backend and Frontend windows
echo.
echo ============================================================================
echo.
echo Press any key to close this setup window...
pause >nul

exit /b 0
