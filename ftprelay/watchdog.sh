#!/usr/bin/env bash
# watchdog.sh — ensure ftprelay systemd service is running
# Intended to run every minute via mitainesoft's crontab:
#   * * * * * /opt/mitainesoft/ftp_relay/watchdog.sh

SERVICE="ftprelay"
LOG="/var/log/ftprelay/watchdog.log"

if ! systemctl is-active --quiet "$SERVICE"; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') [WATCHDOG] $SERVICE not running — restarting" >> "$LOG"
    sudo systemctl start "$SERVICE"
    sleep 2
    if systemctl is-active --quiet "$SERVICE"; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') [WATCHDOG] $SERVICE restarted successfully" >> "$LOG"
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') [WATCHDOG] $SERVICE FAILED to restart" >> "$LOG"
    fi
fi
