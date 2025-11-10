@echo off
REM ============================================================================
REM IPDR TRACKING HUB - STOP APPLICATION
REM ============================================================================
REM This is a launcher for stopping the application
REM ============================================================================

title IPDR Tracking Hub - Stop

echo.
echo ============================================================================
echo           DELHI POLICE IPDR TRACKING HUB - STOPPING...
echo ============================================================================
echo.

REM Get the directory where this script is located
set "PROJECT_DIR=%~dp0"

REM Run the actual stop script from setup folder
call "%PROJECT_DIR%setup\stop-servers.bat"

exit /b %errorlevel%
