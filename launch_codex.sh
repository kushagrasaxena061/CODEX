#!/bin/bash

echo "=========================================="
echo " SYSTEM CLEANUP & FINAL LAUNCH            "
echo "=========================================="

echo "[1] Cleaning up temporary test files..."
rm -f script.py memory_test.txt architecture.md

echo "[2] Killing old background processes..."
pkill -f uvicorn
pkill -f vite
sleep 2

echo "[3] Booting FastAPI Backend..."
source .venv/bin/activate
uvicorn backend.main:app --port 8000 > /dev/null 2>&1 &
BACKEND_PID=$!

echo "[4] Booting React Frontend..."
cd frontend
npm run dev > /dev/null 2>&1 &
FRONTEND_PID=$!

echo -e "\n=========================================="
echo " CODEX IS ONLINE!"
echo " UI running on: http://localhost:5173"
echo " Backend running on: http://127.0.0.1:8000"
echo "=========================================="
echo "Press Ctrl+C to shut down servers when finished."

wait
