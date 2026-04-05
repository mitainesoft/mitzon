#!/usr/bin/env bash
# deploy.sh — bump revision, deploy ftp_relay.py to oreocamftp, restart service

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RELAY="$SCRIPT_DIR/ftp_relay.py"
HOST="mitainesoft@oreocamftp.lan"
REMOTE="/opt/mitainesoft/ftp_relay/ftp_relay.py"

# Read current revision and increment
current=$(grep -o 'REVISION = [0-9]*' "$RELAY" | grep -o '[0-9]*')
next=$((current + 1))
sed -i "s/^REVISION = $current$/REVISION = $next/" "$RELAY"
echo "Revision $current → $next"

# Deploy
echo "Deploying to $HOST ..."
cat "$RELAY" | ssh "$HOST" "sudo tee $REMOTE > /dev/null"

# Restart
ssh "$HOST" "sudo systemctl restart ftprelay && sleep 1 && sudo systemctl status ftprelay --no-pager"
