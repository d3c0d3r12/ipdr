@echo off
REM ============================================================================
REM IPDR TRACKING HUB - START APPLICATION
REM ============================================================================
REM This is a launcher for starting the application
REM ============================================================================

title IPDR Tracking Hub - Start

echo.
echo ============================================================================
echo           DELHI POLICE IPDR TRACKING HUB - STARTING...
echo ============================================================================
echo.

REM Get the directory where this script is located
set "PROJECT_DIR=%~dp0"

REM Run the actual start script from setup folder
call "%PROJECT_DIR%setup\setup.bat"

exit /b %errorlevel%
