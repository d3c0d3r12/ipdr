@echo off
REM ============================================================================
REM IPDR TRACKING HUB - INSTALL DEPENDENCIES
REM ============================================================================
REM This is a launcher for the installation script
REM ============================================================================

title IPDR Tracking Hub - Install

echo.
echo ============================================================================
echo           DELHI POLICE IPDR TRACKING HUB - INSTALLATION
echo ============================================================================
echo.
echo Starting installation...
echo.

REM Get the directory where this script is located
set "PROJECT_DIR=%~dp0"

REM Run the actual install script from setup folder
call "%PROJECT_DIR%setup\install.bat"

exit /b %errorlevel%
