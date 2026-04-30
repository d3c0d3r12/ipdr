@echo off
REM ============================================================================
REM IPDR TRACKING HUB - START APPLICATION (WITH AUTO-INSTALL)
REM ============================================================================
REM This script checks dependencies and installs if missing, then starts servers
REM ============================================================================

title IPDR Tracking Hub - Start

color 0B
echo.
echo ============================================================================
echo      DELHI POLICE IPDR TRACKING HUB - SMART START
echo ============================================================================
echo.

REM Get the directory where this script is located
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

REM ============================================================================
REM CHECK DEPENDENCIES
REM ============================================================================

echo [STEP 1/3] Checking Dependencies...
echo.

set "MISSING_DEPS=0"

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Python not found!
    set "MISSING_DEPS=1"
) else (
    echo [OK] Python installed: 
    python --version
)

REM Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Node.js not found!
    set "MISSING_DEPS=1"
) else (
    echo [OK] Node.js installed:
    node --version
)

echo.

REM If dependencies are missing, install them
if "%MISSING_DEPS%"=="1" (
    echo [INFO] Some dependencies are missing!
    echo [INFO] Installing dependencies automatically...
    echo.
    
    if exist "%PROJECT_DIR%INSTALL.bat" (
        call "%PROJECT_DIR%INSTALL.bat"
    ) else (
        echo [ERROR] INSTALL.bat not found!
        echo [INFO] Please run AUTO-INSTALL.bat first.
        pause
        exit /b 1
    )
)

REM ============================================================================
REM CHECK AND INSTALL PACKAGES
REM ============================================================================

echo [STEP 2/3] Checking Python/Node Packages...
echo.

REM Check if backend packages are installed
if not exist "%PROJECT_DIR%backend\venv" (
    if not exist "%PROJECT_DIR%backend\requirements.txt" (
        echo [ERROR] Backend requirements.txt not found!
        pause
        exit /b 1
    )
    
    echo [INFO] Installing backend packages...
    cd /d "%PROJECT_DIR%backend"
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install backend packages!
        pause
        exit /b 1
    )
)

REM Check if frontend packages are installed
if not exist "%PROJECT_DIR%frontend\node_modules" (
    if not exist "%PROJECT_DIR%frontend\package.json" (
        echo [ERROR] Frontend package.json not found!
        pause
        exit /b 1
    )
    
    echo [INFO] Installing frontend packages...
    cd /d "%PROJECT_DIR%frontend"
    npm install
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install frontend packages!
        pause
        exit /b 1
    )
)

echo [OK] All packages installed!
echo.

REM ============================================================================
REM START SERVERS
REM ============================================================================

echo [STEP 3/3] Starting Servers...
echo.

cd /d "%PROJECT_DIR%"

echo [INFO] Starting Backend Server (Port 8000)...
start "IPDR Backend" cmd /k "cd /d "%PROJECT_DIR%backend" && color 0B && title IPDR Backend Server && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo [OK] Backend starting...
timeout /t 5 /nobreak >nul

echo [INFO] Starting Frontend Server (Port 3000)...
start "IPDR Frontend" cmd /k "cd /d "%PROJECT_DIR%frontend" && color 0E && title IPDR Frontend Server && npm run dev"

echo [OK] Frontend starting...
timeout /t 10 /nobreak >nul

echo.
echo ============================================================================
echo                    SERVERS STARTED SUCCESSFULLY!
echo ============================================================================
echo.
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo   API Docs: http://localhost:8000/docs
echo.
echo ============================================================================
echo.

REM Open browser
timeout /t 3 /nobreak >nul
start http://localhost:3000

echo [SUCCESS] Application is running!
echo.
echo Press any key to close this window (servers will keep running)...
pause >nul

exit /b 0
