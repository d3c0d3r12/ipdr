@echo off
REM ============================================================================
REM DELHI POLICE IPDR TRACKING HUB - STOP SERVERS
REM ============================================================================
REM This script stops both Backend and Frontend servers
REM ============================================================================

title IPDR Tracking Hub - Stop Servers

color 0C
echo.
echo ============================================================================
echo           DELHI POLICE IPDR TRACKING HUB - STOP SERVERS
echo ============================================================================
echo.

echo [INFO] Stopping all IPDR servers...
echo.

REM Kill Python processes (Backend)
echo [1/2] Stopping Backend Server (Python/Uvicorn)...
taskkill /FI "WINDOWTITLE eq IPDR Backend*" /F >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Backend server stopped
) else (
    echo [INFO] Backend server was not running
)

REM Kill Node processes (Frontend)
echo [2/2] Stopping Frontend Server (Node.js/Nuxt)...
taskkill /FI "WINDOWTITLE eq IPDR Frontend*" /F >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Frontend server stopped
) else (
    echo [INFO] Frontend server was not running
)

echo.
echo ============================================================================
echo                    SERVERS STOPPED SUCCESSFULLY!
echo ============================================================================
echo.
echo All IPDR Tracking Hub servers have been stopped.
echo.
echo To start servers again, run: setup.bat or start-servers.bat
echo.
echo ============================================================================
echo.
echo Press any key to exit...
pause >nul
