#!/bin/bash

echo "=========================================="
echo " BOOTING DARWIN AI ENGINE                 "
echo "=========================================="

# Kill any zombie processes
lsof -ti:8000,5173 | xargs kill -9 2>/dev/null || true

# Start Backend
source .venv/bin/activate
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &

# Start Frontend
cd frontend
npm run dev &

wait
