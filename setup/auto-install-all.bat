@echo off
REM ============================================================================
REM DELHI POLICE IPDR TRACKING HUB - FULLY AUTOMATIC INSTALLATION
REM ============================================================================
REM This script automatically downloads and installs ALL dependencies
REM ============================================================================

title IPDR Tracking Hub - Automatic Installation

color 0B
echo.
echo ============================================================================
echo      DELHI POLICE IPDR TRACKING HUB - FULLY AUTOMATIC INSTALLATION
echo ============================================================================
echo.
echo This script will AUTOMATICALLY:
echo   1. Download Python 3.11 (if not installed)
echo   2. Install Python with PATH configuration
echo   3. Download Node.js LTS (if not installed)
echo   4. Install Node.js with PATH configuration
echo   5. Install all Python packages
echo   6. Install all Node.js packages
echo.
echo IMPORTANT: This will download approximately 150 MB
echo.
echo ============================================================================
echo.

set /p CONFIRM="Do you want to proceed with automatic installation? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo.
    echo Installation cancelled.
    pause
    exit /b 0
)

echo.
echo Starting automatic installation...
echo.

REM Get the directory where this script is located
set "PROJECT_DIR=%~dp0"
set "TEMP_DIR=%PROJECT_DIR%temp_installers"

REM Create temp directory for installers
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

REM ============================================================================
REM STEP 1: CHECK AND INSTALL PYTHON
REM ============================================================================

echo ============================================================================
echo STEP 1/6: Checking Python Installation
echo ============================================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Python not found. Downloading Python 3.11...
    echo.
    
    REM Download Python installer
    set "PYTHON_URL=https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe"
    set "PYTHON_INSTALLER=%TEMP_DIR%\python-installer.exe"
    
    echo Downloading from: %PYTHON_URL%
    echo Please wait...
    echo.
    
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_INSTALLER%'}"
    
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to download Python installer!
        echo Please check your internet connection.
        pause
        exit /b 1
    )
    
    echo [SUCCESS] Python installer downloaded!
    echo.
    echo [INFO] Installing Python 3.11...
    echo This may take 2-3 minutes...
    echo.
    
    REM Install Python silently with PATH
    "%PYTHON_INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    
    if %errorlevel% neq 0 (
        echo [ERROR] Python installation failed!
        pause
        exit /b 1
    )
    
    echo [SUCCESS] Python installed successfully!
    echo.
    
    REM Refresh environment variables
    call :RefreshEnv
    
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
    echo [INFO] Node.js not found. Downloading Node.js LTS...
    echo.
    
    REM Download Node.js installer
    set "NODE_URL=https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi"
    set "NODE_INSTALLER=%TEMP_DIR%\nodejs-installer.msi"
    
    echo Downloading from: %NODE_URL%
    echo Please wait...
    echo.
    
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%NODE_URL%' -OutFile '%NODE_INSTALLER%'}"
    
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to download Node.js installer!
        echo Please check your internet connection.
        pause
        exit /b 1
    )
    
    echo [SUCCESS] Node.js installer downloaded!
    echo.
    echo [INFO] Installing Node.js LTS...
    echo This may take 3-5 minutes...
    echo.
    
    REM Install Node.js silently
    msiexec /i "%NODE_INSTALLER%" /quiet /norestart
    
    if %errorlevel% neq 0 (
        echo [ERROR] Node.js installation failed!
        pause
        exit /b 1
    )
    
    echo [SUCCESS] Node.js installed successfully!
    echo.
    
    REM Refresh environment variables
    call :RefreshEnv
    
) else (
    echo [OK] Node.js is already installed:
    node --version
    echo.
)

REM ============================================================================
REM STEP 3: VERIFY INSTALLATIONS
REM ============================================================================

echo ============================================================================
echo STEP 3/6: Verifying Installations
echo ============================================================================
echo.

REM Try to verify Python (may need PATH refresh)
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Python not found in PATH yet.
    echo [INFO] Trying to refresh environment...
    call :RefreshEnv
    
    REM Try again after refresh
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo.
        echo [IMPORTANT] Python installed but PATH not refreshed!
        echo.
        echo SOLUTION: Please restart your computer and run this script again:
        echo    1. Restart computer
        echo    2. Double-click AUTO-INSTALL.bat again
        echo    3. Script will skip Python/Node.js (already installed)
        echo    4. Will install packages only
        echo.
        pause
        exit /b 1
    )
)

echo [OK] Python verified:
python --version
echo.

REM Verify pip
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pip verification failed!
    pause
    exit /b 1
)

echo [OK] pip verified:
pip --version
echo.

REM Verify Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Node.js not found in PATH yet.
    echo [INFO] Trying to refresh environment...
    call :RefreshEnv
    
    REM Try again after refresh
    node --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo.
        echo [IMPORTANT] Node.js installed but PATH not refreshed!
        echo.
        echo SOLUTION: Please restart your computer and run this script again:
        echo    1. Restart computer
        echo    2. Double-click AUTO-INSTALL.bat again
        echo    3. Script will skip installations (already done)
        echo    4. Will install packages only
        echo.
        pause
        exit /b 1
    )
)

echo [OK] Node.js verified:
node --version
echo.

REM Verify npm
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm verification failed!
    pause
    exit /b 1
)

echo [OK] npm verified:
npm --version
echo.

REM ============================================================================
REM STEP 4: INSTALL BACKEND DEPENDENCIES
REM ============================================================================

echo ============================================================================
echo STEP 4/6: Installing Backend Dependencies (Python)
echo ============================================================================
echo.

cd /d "%PROJECT_DIR%..\backend"

if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found!
    pause
    exit /b 1
)

echo [INFO] Installing Python packages...
echo This may take 5-10 minutes...
echo.

pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python dependencies!
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Backend dependencies installed successfully!
echo.

REM ============================================================================
REM STEP 5: INSTALL FRONTEND DEPENDENCIES
REM ============================================================================

echo ============================================================================
echo STEP 5/6: Installing Frontend Dependencies (Node.js)
echo ============================================================================
echo.

cd /d "%PROJECT_DIR%..\frontend"

if not exist "package.json" (
    echo [ERROR] package.json not found!
    pause
    exit /b 1
)

echo [INFO] Installing Node.js packages...
echo This may take 10-15 minutes...
echo.

npm install

if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Node.js dependencies!
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Frontend dependencies installed successfully!
echo.

REM ============================================================================
REM STEP 6: CLEANUP
REM ============================================================================

echo ============================================================================
echo STEP 6/6: Cleaning Up
echo ============================================================================
echo.

cd /d "%PROJECT_DIR%"

REM Delete temp installers
if exist "%TEMP_DIR%" (
    echo [INFO] Removing temporary installers...
    rd /s /q "%TEMP_DIR%"
    echo [OK] Cleanup complete!
    echo.
)

REM ============================================================================
REM INSTALLATION COMPLETE
REM ============================================================================

color 0A
echo.
echo ============================================================================
echo                    INSTALLATION COMPLETE!
echo ============================================================================
echo.
echo All dependencies have been installed successfully!
echo.
echo Installed:
echo   ✅ Python 3.11 (with PATH configured)
echo   ✅ Node.js LTS (with PATH configured)
echo   ✅ 50+ Python packages
echo   ✅ 1200+ Node.js packages
echo.
echo ============================================================================
echo                         NEXT STEPS
echo ============================================================================
echo.
echo 1. RESTART YOUR COMPUTER (recommended)
echo    This ensures all PATH changes take effect
echo.
echo 2. Start the application:
echo    - Double-click: START.bat (in main folder)
echo    - Or run: setup\setup.bat
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
