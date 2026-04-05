#!/usr/bin/env bash
# =============================================================================
# cleanup.sh — Daily disk space cleanup for oreocamftp archive
#
# Runs from mitainesoft crontab. Checks disk usage on /mnt/oreocamhd1.
# When usage reaches THRESHOLD%, deletes the oldest daily directories
# (named YYYY-MM-DD) under the archive, one day at a time, until usage
# drops below the threshold. Directories within MIN_AGE_DAYS are never touched.
#
# Logs: /var/log/ftprelay/cleanup.log
# =============================================================================

ARCHIVE_DIR="/mnt/oreocamhd1/nas_transferred/mitainecam"
MOUNT_POINT="/mnt/oreocamhd1"
THRESHOLD=90
MIN_AGE_DAYS=30
LOG="/var/log/ftprelay/cleanup.log"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG"; }

disk_usage() { df "$MOUNT_POINT" | awk 'NR==2 {gsub("%",""); print $5}'; }

usage=$(disk_usage)

if [ "$usage" -lt "$THRESHOLD" ]; then
    log "[OK] Disk at ${usage}% — no cleanup needed"
    exit 0
fi

log "[!] Disk at ${usage}% (threshold ${THRESHOLD}%) — starting cleanup"

cutoff=$(date -d "-${MIN_AGE_DAYS} days" '+%Y-%m-%d')
deleted_dirs=0
freed=0

# Find all YYYY-MM-DD directories, sort oldest first
while IFS= read -r day_dir; do
    dir_name=$(basename "$day_dir")

    # Never delete directories within MIN_AGE_DAYS
    if [[ "$dir_name" > "$cutoff" || "$dir_name" == "$cutoff" ]]; then
        log "[SKIP] $dir_name is within ${MIN_AGE_DAYS}-day retention window — stopping"
        break
    fi

    current=$(disk_usage)
    if [ "$current" -lt "$THRESHOLD" ]; then
        log "[OK] Disk down to ${current}% — stopping cleanup"
        break
    fi

    dir_size=$(du -sb "$day_dir" 2>/dev/null | awk '{print $1}')
    if rm -rf "$day_dir"; then
        freed=$((freed + dir_size))
        deleted_dirs=$((deleted_dirs + 1))
        log "[DEL] $dir_name ($(( dir_size / 1024 / 1024 )) MB)"
    else
        log "[ERR] Failed to delete: $day_dir"
    fi

done < <(find "$ARCHIVE_DIR" -maxdepth 1 -type d -regextype posix-extended \
         -regex '.*/[0-9]{4}-[0-9]{2}-[0-9]{2}$' | sort)

freed_mb=$(( freed / 1024 / 1024 ))
final=$(disk_usage)
log "[✓] Done — deleted $deleted_dirs day(s), freed ~${freed_mb} MB, disk now at ${final}%"
