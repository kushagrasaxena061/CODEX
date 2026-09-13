#!/bin/bash

# Kill any existing processes just to be safe
lsof -ti:8000,5173 | xargs kill -9 2>/dev/null || true

echo "=========================================="
echo " STARTING CODEX (FOREGROUND MODE)         "
echo "=========================================="

# Boot Backend
source .venv/bin/activate
uvicorn backend.main:app --port 8000 &
BACKEND_PID=$!

# Boot Frontend
cd frontend
npm run dev &
FRONTEND_PID=$!

echo -e "\n=========================================="
echo " CODEX IS ONLINE!"
echo " UI: http://localhost:5173"
echo " API: http://localhost:8000"
echo "=========================================="
echo ">>> PRESS CTRL+C HERE TO SHUT DOWN EVERYTHING CLEANLY <<<"
echo "=========================================="

# This traps the Ctrl+C signal and automatically kills both servers
trap "echo -e '\nShutting down Codex safely...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM

wait
