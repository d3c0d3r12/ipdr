@echo off
echo Testing PowerShell download command...
echo.

REM Create temp directory
set "TEMP_DIR=%CD%\test_temp"
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

REM Test Python download
set "PYTHON_INSTALLER=%TEMP_DIR%\python-installer.exe"

echo Testing Python download...
echo URL: https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe
echo Output: %PYTHON_INSTALLER%
echo.

powershell -Command "$ProgressPreference = 'SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe' -OutFile '%PYTHON_INSTALLER%'"

if %errorlevel% neq 0 (
    echo [ERROR] Download failed!
    pause
    exit /b 1
) else (
    echo [SUCCESS] Download worked!
    echo.
    echo File size:
    dir "%PYTHON_INSTALLER%"
    echo.
    echo Cleaning up...
    rd /s /q "%TEMP_DIR%"
    echo.
    echo [SUCCESS] Test completed successfully!
)

pause
