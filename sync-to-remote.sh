#!/bin/bash

# Remote sync and restart script for Mitzon
# Usage: ./sync-to-remote.sh [optional-file]

REMOTE_HOST="192.168.6.83"
REMOTE_USER="mitainesoft"
LOCAL_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/"
REMOTE_PATH="/opt/mitainesoft/mitzon/"

echo "================================"
echo "Syncing Mitzon to $REMOTE_HOST"
echo "================================"

# If a specific file is provided, only sync that file
if [ $# -eq 1 ]; then
  FILE_TO_SYNC="$1"
  if [ -f "$FILE_TO_SYNC" ]; then
    echo "Syncing only: $FILE_TO_SYNC"
    # Create remote directory if needed and copy with full path preservation
    ssh "${REMOTE_USER}@${REMOTE_HOST}" "mkdir -p ${REMOTE_PATH}$(dirname "$FILE_TO_SYNC")"
    scp "$FILE_TO_SYNC" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}$FILE_TO_SYNC"
  else
    echo "ERROR: File '$FILE_TO_SYNC' not found!"
    exit 1
  fi
else
  # Full sync using tar and ssh (works on Windows Git Bash)
  echo "Full sync (use './sync-to-remote.sh filename' for single file)"
  tar czf - \
    --exclude='.git' \
    --exclude='.vscode' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='node_modules' \
    --exclude='*.log' \
    -C "$(dirname "$LOCAL_PATH")" "$(basename "${LOCAL_PATH%/}")" | \
    ssh "${REMOTE_USER}@${REMOTE_HOST}" "cd /opt/mitainesoft && tar xzf -"
fi

if [ $? -ne 0 ]; then
  echo "ERROR: Sync failed!"
  exit 1
fi

echo ""
echo "Sync complete. Restarting mitzon on remote..."
echo ""

# Restart the remote service
ssh "${REMOTE_USER}@${REMOTE_HOST}" "bash ${REMOTE_PATH}mitzon.bash"

echo ""
echo "================================"
echo "Done! Debugger waiting on port 5678"
echo "Press F5 in VS Code to attach"
echo "================================"
