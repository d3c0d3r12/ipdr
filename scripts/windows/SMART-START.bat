@echo off
REM ============================================================================
REM DELHI POLICE IPDR TRACKING HUB - SMART START (AUTO-INSTALL & START)
REM ============================================================================
REM This script automatically:
REM 1. Checks for Python, Node.js, pip, npm
REM 2. Installs missing dependencies automatically
REM 3. Installs Python packages (backend)
REM 4. Installs Node.js packages (frontend)
REM 5. Starts both servers
REM ============================================================================

title IPDR Tracking Hub - Smart Start

color 0B
echo.
echo ============================================================================
echo      DELHI POLICE IPDR TRACKING HUB - SMART START (AUTO-INSTALL)
echo ============================================================================
echo.
echo This script will:
echo   1. Check for Python and Node.js
echo   2. Install missing dependencies automatically
echo   3. Start both Backend and Frontend servers
echo.
echo ============================================================================
echo.

set /p CONFIRM="Do you want to proceed? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo.
    echo Cancelled.
    pause
    exit /b 0
)

echo.
echo Starting Smart Setup...
echo.

REM Get the directory where this script is located
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo [INFO] Project Directory: %PROJECT_DIR%
echo.

REM ============================================================================
REM STEP 1: CHECK AND INSTALL PYTHON
REM ============================================================================

echo ============================================================================
echo STEP 1/6: Checking Python Installation
echo ============================================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Python not found!
    echo [INFO] Installing Python automatically...
    echo.
    
    REM Check if auto-install script exists
    if exist "%PROJECT_DIR%setup\auto-install-all.bat" (
        echo [INFO] Running auto-installer for Python...
        call "%PROJECT_DIR%setup\auto-install-all.bat"
        
        REM Refresh environment
        call :RefreshEnv
        
        REM Check again
        python --version >nul 2>&1
        if %errorlevel% neq 0 (
            echo.
            echo [ERROR] Python installation failed or PATH not refreshed!
            echo [SOLUTION] Please restart your computer and run this script again.
            echo.
            pause
            exit /b 1
        )
    ) else (
        echo [ERROR] Auto-installer not found!
        echo [INFO] Please run AUTO-INSTALL.bat first or install Python manually.
        echo.
        pause
        exit /b 1
    )
) else (
    echo [OK] Python is already installed:
    python --version
    echo.
)

REM ============================================================================
REM STEP 2: CHECK AND INSTALL NODE.JS
REM ============================================================================

echo ============================================================================
echo STEP 2/6: Checking Node.js Installation
echo ============================================================================
echo.

node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Node.js not found!
    echo [INFO] Please install Node.js manually or run AUTO-INSTALL.bat
    echo.
    echo Download from: https://nodejs.org/
    echo.
    pause
    exit /b 1
) else (
    echo [OK] Node.js is already installed:
    node --version
    echo.
)

REM ============================================================================
REM STEP 3: CHECK PIP
REM ============================================================================

echo ============================================================================
echo STEP 3/6: Checking pip
echo ============================================================================
echo.

pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pip not found!
    pause
    exit /b 1
)

echo [OK] pip is installed:
pip --version
echo.

REM ============================================================================
REM STEP 4: INSTALL BACKEND DEPENDENCIES
REM ============================================================================

echo ============================================================================
echo STEP 4/6: Installing Backend Dependencies
echo ============================================================================
echo.

if not exist "%PROJECT_DIR%backend\requirements.txt" (
    echo [ERROR] requirements.txt not found!
    pause
    exit /b 1
)

echo [INFO] Installing Python packages...
echo This may take 5-10 minutes...
echo.

cd /d "%PROJECT_DIR%backend"
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python dependencies!
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Backend dependencies installed!
echo.

REM ============================================================================
REM STEP 5: INSTALL FRONTEND DEPENDENCIES
REM ============================================================================

echo ============================================================================
echo STEP 5/6: Installing Frontend Dependencies
echo ============================================================================
echo.

if not exist "%PROJECT_DIR%frontend\package.json" (
    echo [ERROR] package.json not found!
    pause
    exit /b 1
)

echo [INFO] Installing Node.js packages...
echo This may take 5-10 minutes...
echo.

cd /d "%PROJECT_DIR%frontend"
npm install

if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Node.js dependencies!
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Frontend dependencies installed!
echo.

REM ============================================================================
REM STEP 6: START SERVERS
REM ============================================================================

echo ============================================================================
echo STEP 6/6: Starting Servers
echo ============================================================================
echo.

cd /d "%PROJECT_DIR%"

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
echo [INFO] Waiting 10 seconds for frontend to initialize...
timeout /t 10 /nobreak >nul

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
echo   - To stop: Close both windows or run STOP.bat
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
echo To stop servers: Run STOP.bat or close the server windows
echo.
echo ============================================================================
echo.
echo Press any key to close this setup window...
pause >nul

exit /b 0

REM ============================================================================
REM HELPER FUNCTION: Refresh Environment Variables
REM ============================================================================
:RefreshEnv
echo [INFO] Refreshing environment variables...
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "SYS_PATH=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "USER_PATH=%%b"
set "PATH=%SYS_PATH%;%USER_PATH%"
echo [OK] Environment refreshed
goto :eof
