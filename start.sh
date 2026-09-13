#!/bin/bash

echo "=========================================="
echo "   CODEX AI SOFTWARE ENGINEER STARTUP     "
echo "=========================================="

# Ensure we are in the correct directory
cd "$(dirname "$0")"

# 1. Verify dependencies
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is required."
    exit 1
fi
if ! command -v npm &> /dev/null; then
    echo "[ERROR] Node.js (npm) is required."
    exit 1
fi

# 2. Activate Python virtual environment
if [ ! -d ".venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

# 3. Handle Graceful Shutdown
cleanup() {
    echo ""
    echo "[INFO] Shutting down Codex..."
    kill $BACKEND_PID
    kill $FRONTEND_PID
    exit
}
trap cleanup SIGINT SIGTERM

# 4. Start the Backend
echo "[INFO] Starting FastAPI Backend on port 8000..."
uvicorn backend.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# 5. Start the Frontend
echo "[INFO] Starting React Frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo "=========================================="
echo " Codex is running!"
echo " UI: http://localhost:5173"
echo " API: http://127.0.0.1:8000"
echo " Press Ctrl+C to shut down both servers."
echo "=========================================="

# Wait for background processes
wait
