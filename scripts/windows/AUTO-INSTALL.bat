@echo off
REM ============================================================================
REM IPDR TRACKING HUB - FULLY AUTOMATIC INSTALLATION LAUNCHER
REM ============================================================================
REM This launcher runs the fully automatic installer
REM ============================================================================

title IPDR Tracking Hub - Auto Install

echo.
echo ============================================================================
echo           DELHI POLICE IPDR TRACKING HUB - AUTO INSTALL
echo ============================================================================
echo.
echo This will AUTOMATICALLY download and install:
echo   - Python 3.11
echo   - Node.js LTS
echo   - All project dependencies
echo.
echo No manual steps required!
echo.
echo ============================================================================
echo.

REM Get the directory where this script is located
set "PROJECT_DIR=%~dp0"

REM Run the actual auto-install script from setup folder
call "%PROJECT_DIR%setup\auto-install-all.bat"

exit /b %errorlevel%
