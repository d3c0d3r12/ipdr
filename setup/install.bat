@echo off
REM ============================================================================
REM DELHI POLICE IPDR TRACKING HUB - AUTOMATIC INSTALLATION
REM ============================================================================
REM This script automatically installs all dependencies on a new system
REM ============================================================================

title IPDR Tracking Hub - Installation

color 0B
echo.
echo ============================================================================
echo      DELHI POLICE IPDR TRACKING HUB - AUTOMATIC INSTALLATION
echo ============================================================================
echo.
echo This script will install all required dependencies automatically.
echo.
echo Please ensure you have:
echo   - Python 3.8 or higher installed
echo   - Node.js 16 or higher installed
echo   - Internet connection
echo.
echo ============================================================================
echo.

pause

REM Get the directory where this script is located
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

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
    echo [ERROR] Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.8+ from: https://www.python.org/downloads/
    echo.
    echo IMPORTANT: During installation, check "Add Python to PATH"
    echo.
    pause
    exit /b 1
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
    echo [ERROR] Node.js is not installed or not in PATH!
    echo.
    echo Please install Node.js 16+ from: https://nodejs.org/
    echo.
    echo Recommended: Download LTS version
    echo.
    pause
    exit /b 1
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
REM INSTALLATION COMPLETE
REM ============================================================================

cd /d "%PROJECT_DIR%"

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
