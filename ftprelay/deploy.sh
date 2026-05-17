#!/usr/bin/env bash
# deploy.sh — bump revision, deploy ftp_relay.py to oreocamftp, restart service

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RELAY="$SCRIPT_DIR/ftp_relay.py"
WATCHDOG="$SCRIPT_DIR/watchdog.sh"
HOST="mitainesoft@oreocamftp.lan"

# Parse --ip <address> to override hostname
while [[ $# -gt 0 ]]; do
  case "$1" in
    --ip)
      HOST="mitainesoft@$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done
REMOTE="/opt/mitainesoft/ftp_relay/ftp_relay.py"
REMOTE_WATCHDOG="/opt/mitainesoft/ftp_relay/watchdog.sh"

# Read current revision and increment
current=$(grep -o 'REVISION = [0-9]*' "$RELAY" | grep -o '[0-9]*')
next=$((current + 1))
sed -i "s/^REVISION = $current$/REVISION = $next/" "$RELAY"
echo "Revision $current → $next"

# Deploy
echo "Deploying to $HOST ..."
cat "$RELAY" | ssh "$HOST" "sudo tee $REMOTE > /dev/null"

# Deploy watchdog and install cron job in mitainesoft's crontab (every minute)
echo "Deploying watchdog to $HOST ..."
cat "$WATCHDOG" | ssh "$HOST" "sudo tee $REMOTE_WATCHDOG > /dev/null && sudo chmod +x $REMOTE_WATCHDOG"
# Ensure sudoers allows mitainesoft to start ftprelay without a password
SUDOERS_LINE="mitainesoft ALL=(ALL) NOPASSWD: /bin/systemctl start ftprelay, /bin/systemctl restart ftprelay"
ssh "$HOST" "echo '$SUDOERS_LINE' | sudo tee /etc/sudoers.d/ftprelay-watchdog > /dev/null && sudo chmod 440 /etc/sudoers.d/ftprelay-watchdog"
# Add cron entry to mitainesoft's crontab (not root's)
CRON_LINE="* * * * * $REMOTE_WATCHDOG"
ssh "$HOST" "( crontab -l 2>/dev/null | grep -qF '$REMOTE_WATCHDOG' ) || \
    ( crontab -l 2>/dev/null; echo '$CRON_LINE' ) | crontab -"
echo "Watchdog cron job installed."

# Restart — backgrounded so systemd cgroup teardown doesn't kill the SSH session
ssh "$HOST" "sudo systemctl restart ftprelay &>/dev/null &"
sleep 3
ssh "$HOST" "sudo systemctl status ftprelay --no-pager"
