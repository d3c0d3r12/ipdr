@echo off
REM ============================================================================
REM DELHI POLICE IPDR TRACKING HUB - FULLY AUTOMATIC SETUP
REM ============================================================================
REM This script automatically:
REM 1. Downloads and installs Python (if missing)
REM 2. Downloads and installs Node.js (if missing)
REM 3. Installs all packages automatically
REM 4. Starts both servers
REM ============================================================================

title IPDR Tracking Hub - Automatic Setup

color 0B
cls
echo.
echo ============================================================================
echo      DELHI POLICE IPDR TRACKING HUB - FULLY AUTOMATIC SETUP
echo ============================================================================
echo.
echo This will automatically install everything needed!
echo.
echo Press any key to start...
pause >nul

REM Get the directory where this script is located (setup folder)
set "SETUP_DIR=%~dp0"
REM Go up one level to project root
cd /d "%SETUP_DIR%.."
set "PROJECT_DIR=%CD%\"
set "TEMP_DIR=%PROJECT_DIR%temp_installers"

echo [INFO] Project Directory: %PROJECT_DIR%
echo.

REM ============================================================================
REM STEP 1: CHECK AND INSTALL PYTHON
REM ============================================================================

echo ============================================================================
echo STEP 1/5: Checking Python Installation
echo ============================================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Python not found. Installing automatically...
    echo.
    
    REM Create temp directory
    if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"
    
    REM Download Python installer
    set "PYTHON_INSTALLER=%TEMP_DIR%\python-installer.exe"
    
    echo Downloading Python 3.11.7...
    echo Please wait, this may take 2-3 minutes...
    echo.
    
    powershell -ExecutionPolicy Bypass -Command "$ProgressPreference = 'SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; try { Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe' -OutFile '%PYTHON_INSTALLER%' -UseBasicParsing; Write-Host 'Download complete!' } catch { Write-Host 'Error:' $_.Exception.Message; exit 1 }"
    
    if %errorlevel% neq 0 (
        color 0C
        echo.
        echo [ERROR] Failed to download Python!
        echo Please check your internet connection.
        echo.
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
    
    echo [SUCCESS] Python downloaded!
    echo.
    echo Installing Python (silent mode)...
    echo This will take 2-3 minutes...
    echo.
    
    REM Install Python silently with PATH
    "%PYTHON_INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    
    if %errorlevel% neq 0 (
        color 0C
        echo.
        echo [ERROR] Python installation failed!
        echo.
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
    
    echo [SUCCESS] Python installed!
    echo.
    
    REM Refresh environment variables
    call :RefreshEnv
    
) else (
    echo [OK] Python already installed:
    python --version
)

echo.

REM ============================================================================
REM STEP 2: CHECK AND INSTALL NODE.JS
REM ============================================================================

echo ============================================================================
echo STEP 2/5: Checking Node.js Installation
echo ============================================================================
echo.

node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Node.js not found. Installing automatically...
    echo.
    
    REM Create temp directory
    if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"
    
    REM Download Node.js installer
    set "NODE_INSTALLER=%TEMP_DIR%\nodejs-installer.msi"
    
    echo Downloading Node.js 20.10.0 LTS...
    echo Please wait, this may take 3-5 minutes...
    echo.
    
    powershell -ExecutionPolicy Bypass -Command "$ProgressPreference = 'SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; try { Invoke-WebRequest -Uri 'https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi' -OutFile '%NODE_INSTALLER%' -UseBasicParsing; Write-Host 'Download complete!' } catch { Write-Host 'Error:' $_.Exception.Message; exit 1 }"
    
    if %errorlevel% neq 0 (
        color 0C
        echo [ERROR] Failed to download Node.js!
        echo Please check your internet connection.
        echo.
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
    
    echo [SUCCESS] Node.js downloaded!
    echo.
    echo Installing Node.js (silent mode)...
    echo This will take 3-5 minutes...
    echo.
    
    REM Install Node.js silently
    msiexec /i "%NODE_INSTALLER%" /quiet /norestart
    
    if %errorlevel% neq 0 (
        color 0C
        echo.
        echo [ERROR] Node.js installation failed!
        echo.
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
    
    echo [SUCCESS] Node.js installed!
    echo.
    
    REM Refresh environment variables
    call :RefreshEnv
    
) else (
    echo [OK] Node.js already installed:
    node --version
)

echo.
color 0A

REM ============================================================================
REM STEP 3: CHECK AND INSTALL BACKEND PACKAGES
REM ============================================================================

echo ============================================================================
echo STEP 3/5: Checking Backend Packages
echo ============================================================================
echo.

if not exist "%PROJECT_DIR%backend\requirements.txt" (
    color 0C
    echo [ERROR] Backend requirements.txt not found!
    echo Expected: %PROJECT_DIR%backend\requirements.txt
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

REM Check if packages are installed by trying to import fastapi
python -c "import fastapi" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Backend packages not installed. Installing now...
    echo.
    echo This may take 2-5 minutes...
    echo.
    
    cd /d "%PROJECT_DIR%backend"
    pip install -r requirements.txt
    
    if %errorlevel% neq 0 (
        color 0C
        echo.
        echo [ERROR] Failed to install backend packages!
        echo Please check your internet connection.
        echo.
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
    
    echo.
    echo [SUCCESS] Backend packages installed!
    echo.
) else (
    echo [OK] Backend packages already installed
    echo.
)

REM ============================================================================
REM STEP 4: CHECK AND INSTALL FRONTEND PACKAGES
REM ============================================================================

echo ============================================================================
echo STEP 4/5: Checking Frontend Packages
echo ============================================================================
echo.

if not exist "%PROJECT_DIR%frontend\package.json" (
    color 0C
    echo [ERROR] Frontend package.json not found!
    echo Expected: %PROJECT_DIR%frontend\package.json
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

if not exist "%PROJECT_DIR%frontend\node_modules" (
    echo [INFO] Frontend packages not installed. Installing now...
    echo.
    echo This may take 5-10 minutes...
    echo.
    
    cd /d "%PROJECT_DIR%frontend"
    npm install
    
    if %errorlevel% neq 0 (
        color 0C
        echo.
        echo [ERROR] Failed to install frontend packages!
        echo Please check your internet connection.
        echo.
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
    
    echo.
    echo [SUCCESS] Frontend packages installed!
    echo.
) else (
    echo [OK] Frontend packages already installed
    echo.
)

REM ============================================================================
REM STEP 5: CLEANUP AND START SERVERS
REM ============================================================================

echo ============================================================================
echo STEP 5/5: Starting Servers
echo ============================================================================
echo.

REM Cleanup temp installers
if exist "%TEMP_DIR%" (
    echo [INFO] Cleaning up temporary files...
    rd /s /q "%TEMP_DIR%" 2>nul
    echo [OK] Cleanup complete!
    echo.
)

cd /d "%PROJECT_DIR%"

echo [INFO] Starting Backend Server (Port 8000)...
start "IPDR Backend - FastAPI" cmd /k "cd /d "%PROJECT_DIR%backend" && color 0B && title IPDR Backend Server && echo ============================================================================ && echo                    IPDR BACKEND SERVER && echo ============================================================================ && echo. && echo Starting FastAPI server... && echo. && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo [OK] Backend starting in new window...
echo.

REM Wait for backend to initialize
echo [INFO] Waiting 5 seconds for backend to initialize...
timeout /t 5 /nobreak >nul

echo [INFO] Starting Frontend Server (Port 3000)...
start "IPDR Frontend - Nuxt.js" cmd /k "cd /d "%PROJECT_DIR%frontend" && color 0E && title IPDR Frontend Server && echo ============================================================================ && echo                    IPDR FRONTEND SERVER && echo ============================================================================ && echo. && echo Starting Nuxt.js development server... && echo. && npm run dev"

echo [OK] Frontend starting in new window...
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
echo   - To stop: Run stop-servers.bat or close both windows
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
echo To stop servers: Run stop-servers.bat
echo.
echo ============================================================================
echo.
echo Press any key to close this setup window...
pause >nul

exit /b 0

REM ============================================================================
REM FUNCTION: Refresh Environment Variables
REM ============================================================================
:RefreshEnv
echo [INFO] Refreshing environment variables...
REM Update PATH from registry
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "SYS_PATH=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USER_PATH=%%b"
set "PATH=%SYS_PATH%;%USER_PATH%"
echo [OK] Environment refreshed!
echo.
goto :eof
