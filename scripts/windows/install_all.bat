@echo off
setlocal ENABLEDELAYEDEXPANSION

REM One-command installer for backend (pip) and frontend (npm)
REM Usage: double-click or run: install_all.bat

where python >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
  echo [ERROR] Python is not installed or not in PATH.
  echo Install Python 3.10+ and re-run this script.
  exit /b 1
)

where npm >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
  echo [ERROR] Node.js/npm is not installed or not in PATH.
  echo Install Node.js 18+ and re-run this script.
  exit /b 1
)

REM Create and activate venv
if not exist .venv (
  echo [INFO] Creating Python virtual environment .venv
  python -m venv .venv
)

call .\.venv\Scripts\activate
IF %ERRORLEVEL% NEQ 0 (
  echo [ERROR] Failed to activate virtual environment.
  exit /b 1
)

echo [INFO] Upgrading pip
python -m pip install --upgrade pip

REM Install backend deps from root requirements.txt
if exist requirements.txt (
  echo [INFO] Installing Python dependencies from requirements.txt
  pip install -r requirements.txt
) else (
  echo [WARN] requirements.txt not found in project root. Skipping Python deps.
)

REM Frontend install
if exist frontend\package.json (
  echo [INFO] Installing frontend dependencies (npm install)
  pushd frontend
  npm install
  popd
) else (
  echo [WARN] frontend/package.json not found. Skipping npm install.
)

echo.
echo [DONE] All dependencies installed.
echo - Backend venv: .\.venv
set ACTIVATE_HINT=.\.venv\Scripts\activate
for /f "delims==" %%A in ('echo %ACTIVATE_HINT%') do set ACTIVATE_HINT=%%A

echo - To start backend: %ACTIVATE_HINT% ^&^& uvicorn backend.main:app --reload

echo - To start frontend: cd frontend ^&^& npm run dev

echo.
endlocal
exit /b 0
