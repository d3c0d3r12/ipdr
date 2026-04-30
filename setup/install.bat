@echo off
REM ============================================================================
REM DELHI POLICE IPDR TRACKING HUB - FULLY AUTOMATIC INSTALLATION
REM ============================================================================
REM This script automatically downloads and installs EVERYTHING
REM ============================================================================

title IPDR Tracking Hub - Automatic Installation

color 0B
echo.
echo ============================================================================
echo      DELHI POLICE IPDR TRACKING HUB - FULLY AUTOMATIC INSTALLATION
echo ============================================================================
echo.
echo This script will AUTOMATICALLY:
echo   - Download and install Python (if missing)
echo   - Download and install Node.js (if missing)
echo   - Install all packages
echo.
echo No manual downloads needed!
echo.
echo ============================================================================
echo.

pause

REM Get the directory where this script is located (setup folder)
set "SETUP_DIR=%~dp0"
REM Go up one level to project root
cd /d "%SETUP_DIR%.."
set "PROJECT_DIR=%CD%\"
set "TEMP_DIR=%PROJECT_DIR%temp_installers"

echo.
echo [INFO] Project Directory: %PROJECT_DIR%
echo.

REM ============================================================================
REM STEP 1: CHECK PYTHON
REM ============================================================================

echo ============================================================================
echo STEP 1/4: Checking Python Installation
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
        echo [ERROR] Failed to download Python!
        echo Please check your internet connection.
        echo.
        pause
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
        echo [ERROR] Python installation failed!
        pause
        exit /b 1
    )
    
    echo [SUCCESS] Python installed!
    echo.
    
    REM Refresh environment variables
    call :RefreshEnv
)

echo [OK] Python is installed:
python --version
echo.

REM Check pip
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pip is not installed!
    echo.
    echo Please reinstall Python with pip included.
    echo.
    pause
    exit /b 1
)

echo [OK] pip is installed:
pip --version
echo.

REM ============================================================================
REM STEP 2: CHECK NODE.JS
REM ============================================================================

echo ============================================================================
echo STEP 2/4: Checking Node.js Installation
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
        pause
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
        echo [ERROR] Node.js installation failed!
        pause
        exit /b 1
    )
    
    echo [SUCCESS] Node.js installed!
    echo.
    
    REM Refresh environment variables
    call :RefreshEnv
)

echo [OK] Node.js is installed:
node --version
echo.

REM Check npm
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm is not installed!
    echo.
    echo Please reinstall Node.js with npm included.
    echo.
    pause
    exit /b 1
)

echo [OK] npm is installed:
npm --version
echo.

REM ============================================================================
REM STEP 3: INSTALL BACKEND DEPENDENCIES
REM ============================================================================

echo ============================================================================
echo STEP 3/4: Installing Backend Dependencies (Python)
echo ============================================================================
echo.

if not exist "%PROJECT_DIR%backend" (
    echo [ERROR] Backend directory not found!
    echo Expected: %PROJECT_DIR%backend
    echo.
    pause
    exit /b 1
)

cd /d "%PROJECT_DIR%backend"

if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found in backend directory!
    echo.
    pause
    exit /b 1
)

echo [INFO] Installing Python packages from requirements.txt...
echo.
echo This may take 2-5 minutes depending on your internet speed...
echo.

pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install Python dependencies!
    echo.
    echo Please check your internet connection and try again.
    echo.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Backend dependencies installed successfully!
echo.

REM ============================================================================
REM STEP 4: INSTALL FRONTEND DEPENDENCIES
REM ============================================================================

echo ============================================================================
echo STEP 4/4: Installing Frontend Dependencies (Node.js)
echo ============================================================================
echo.

cd /d "%PROJECT_DIR%frontend"

if not exist "package.json" (
    echo [ERROR] package.json not found in frontend directory!
    echo.
    pause
    exit /b 1
)

echo [INFO] Installing Node.js packages from package.json...
echo.
echo This may take 5-10 minutes depending on your internet speed...
echo.

npm install

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install Node.js dependencies!
    echo.
    echo Please check your internet connection and try again.
    echo.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Frontend dependencies installed successfully!
echo.

REM ============================================================================
REM CLEANUP AND COMPLETE
REM ============================================================================

cd /d "%PROJECT_DIR%"

REM Cleanup temp installers
if exist "%TEMP_DIR%" (
    echo [INFO] Cleaning up temporary files...
    rd /s /q "%TEMP_DIR%" 2>nul
    echo [OK] Cleanup complete!
    echo.
)

echo.
echo ============================================================================
echo                    INSTALLATION COMPLETE!
echo ============================================================================
echo.
echo All dependencies have been installed successfully!
echo.
echo Backend Dependencies:
echo   - FastAPI
echo   - Uvicorn
echo   - Pandas
echo   - SQLAlchemy
echo   - Selenium
echo   - And more...
echo.
echo Frontend Dependencies:
echo   - Nuxt.js
echo   - Vue.js
echo   - And more...
echo.
echo ============================================================================
echo                         NEXT STEPS
echo ============================================================================
echo.
echo 1. Configure your environment:
echo    - Copy .env.example to .env in backend folder
echo    - Update database credentials
echo    - Update API keys if needed
echo.
echo 2. Start the application:
echo    - Double-click: setup.bat
echo    - Or run: start-servers.bat
echo.
echo 3. Access the application:
echo    - Frontend: http://localhost:3000
echo    - Backend API: http://localhost:8000
echo    - API Docs: http://localhost:8000/docs
echo.
echo ============================================================================
echo.
echo Installation completed successfully!
echo.
echo Press any key to exit...
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
