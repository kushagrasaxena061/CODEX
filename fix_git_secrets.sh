#!/bin/bash

echo "=========================================="
echo " SECURING REPO & FIXING GIT PUSH          "
echo "=========================================="

echo "[1] Updating remote repository URL to DARWIN..."
git remote set-url origin https://github.com/kushagrasaxena061/DARWIN.git

echo "[2] Unwinding unpushed commits to strip the secret..."
# This keeps your files exactly as they are on your hard drive, 
# but rewinds the Git history back to match GitHub.
git reset --soft origin/main

echo "[3] Removing the token file from the staging area..."
git reset HEAD backend/github_remote.txt 2>/dev/null || true

echo "[4] Adding security rules to .gitignore..."
# This physically prevents DARWIN (or you) from EVER accidentally committing this file again.
if ! grep -q "backend/github_remote.txt" .gitignore; then
    echo "" >> .gitignore
    echo "# Security - Ignore GitHub Tokens" >> .gitignore
    echo "backend/github_remote.txt" >> .gitignore
fi

echo "[5] Recommitting the safe files..."
git add .
git commit -m "Secure update: Removed leaked GitHub token from history"

echo "[6] Pushing safely to GitHub..."
git push origin main

echo "=========================================="
echo " PUSH COMPLETE!                           "
echo "=========================================="
