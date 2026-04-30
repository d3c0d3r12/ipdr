#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

BACKEND_HOST="0.0.0.0"
BACKEND_PORT="8000"
FRONTEND_HOST="0.0.0.0"
FRONTEND_PORT="3003"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERROR] python3 not found"
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "[ERROR] node not found"
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "[ERROR] npm not found"
  exit 1
fi

if [[ ! -d "$BACKEND_DIR" ]]; then
  echo "[ERROR] backend directory not found: $BACKEND_DIR"
  exit 1
fi

if [[ ! -d "$FRONTEND_DIR" ]]; then
  echo "[ERROR] frontend directory not found: $FRONTEND_DIR"
  exit 1
fi

if [[ ! -d "$BACKEND_DIR/.venv" ]]; then
  echo "[INFO] Creating backend virtualenv..."
  python3 -m venv "$BACKEND_DIR/.venv"
fi

echo "[INFO] Starting Backend (FastAPI) on http://localhost:$BACKEND_PORT ..."
(
  cd "$BACKEND_DIR"
  source .venv/bin/activate
  "$BACKEND_DIR/.venv/bin/python" -m uvicorn main:app --reload --host "$BACKEND_HOST" --port "$BACKEND_PORT"
) &
BACKEND_PID=$!

cleanup() {
  echo ""
  echo "[INFO] Stopping servers..."
  kill "$BACKEND_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

echo "[INFO] Starting Frontend (Vite/React) on http://localhost:$FRONTEND_PORT ..."
cd "$FRONTEND_DIR"
if [[ ! -d "node_modules" ]]; then
  echo "[INFO] Installing frontend dependencies..."
  npm install
fi
npm run dev -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT"
