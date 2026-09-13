#!/bin/bash

echo "=========================================="
echo " RESUMING PHASE 3 & 4 EXECUTION           "
echo "=========================================="

echo -e "\n[1] ENSURING README.md EXISTS..."
cat << 'INNER_EOF' > README.md
# Codex AI Software Engineer

A local, autonomous, repository-aware multi-agent software engineering system powered primarily by Ollama.
INNER_EOF

echo -e "\n[2] VERIFYING OLLAMA MODELS (Checking if deepseek-coder is present)..."
ollama list

echo -e "\n[3] RE-VERIFYING END-TO-END EXECUTION..."
source .venv/bin/activate
# Boot the backend
uvicorn backend.main:app --port 8000 > /dev/null 2>&1 &
BACKEND_PID=$!
sleep 4 # Give it an extra second to boot completely

echo "-> Triggering real LLM pipeline (Wait ~10-20 seconds for the model to think)..."
curl -s -X POST http://127.0.0.1:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Read the README.md file. Find the text \"Codex AI Software Engineer\" and replace it exactly with \"Codex AI Software Engineer (Real Pipeline Active)\"."}' | json_pp

kill $BACKEND_PID

echo -e "\n\n[Checking File System for Actual Changes]"
grep "Real Pipeline Active" README.md && echo "SUCCESS: FILE WAS MODIFIED INDEPENDENTLY." || echo "FAILURE: FILE WAS NOT MODIFIED."
