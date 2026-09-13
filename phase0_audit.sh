#!/bin/bash

echo "=========================================="
echo "      PHASE 0: BASELINE INSPECTION        "
echo "=========================================="

echo -e "\n[1] MAPPING REPOSITORY STRUCTURE..."
find . -maxdepth 3 -not -path '*/\.*' -not -path '*/node_modules/*' -not -path '*/__pycache__/*' | sort

echo -e "\n[2] EXPOSING HARDCODED VERIFICATIONS & STUBS..."
echo "-> Searching for hardcoded 'return True' in backend:"
grep -rn "return True" backend/ 2>/dev/null || echo "None found."
echo "-> Searching for test mocks:"
grep -rn "@patch" tests/ 2>/dev/null || echo "None found."

echo -e "\n[3] PINGING CURRENT API (/api/chat)..."
# Boot the backend silently in the background
uvicorn backend.main:app --port 8000 > /dev/null 2>&1 &
BACKEND_PID=$!
sleep 2 # wait for boot
echo "-> Sending request to /api/chat:"
curl -s -X POST http://127.0.0.1:8000/api/chat -H "Content-Type: application/json" -d '{"prompt": "Build a header"}'
echo ""
# Kill the background process
kill $BACKEND_PID

echo -e "\n[4] RUNNING EXISTING TEST SUITE (THE MIRAGE)..."
source .venv/bin/activate
pytest tests/ -v -q

echo -e "\n=========================================="
echo "        BASELINE INSPECTION COMPLETE      "
echo "=========================================="
