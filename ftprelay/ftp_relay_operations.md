# ftp_relay — Operations Guide

## System Info

| Item | Value |
|---|---|
| Pi hostname | `oreocamftp.lan` |
| Pi IP | `10.0.0.2` |
| Pi user | `mitainesoft` |
| NAS IP | `10.0.0.1` |
| Buffer drive | `/dev/sda1` → `/mnt/oreocamhd1` (1.9 TB, NTFS) |
| Buffer path | `/mnt/oreocamhd1/ftpbuffer` (tmpfs — RAM, see below) |
| Retry path | `/mnt/oreocamhd1/retry` (disk — NAS failure spill) |
| Code path | `/opt/mitainesoft/ftp_relay/` |
| FTP port | `21` |
| Passive ports | `60000–60099` |

---

## File Flow

```
camera upload
     │
     ▼
/mnt/oreocamhd1/ftpbuffer  (tmpfs — RAM, no disk write)
     │
     ▼ background thread
  NAS upload
     │
     ├─ success → delete from tmpfs (silent)
     │
     └─ failure → move to /mnt/oreocamhd1/retry  (disk-backed, survives reboot)
                       │
                       └─ retry thread wakes every 30s, re-attempts until success
```

---

## RAM Buffer (tmpfs)

The FTP buffer is mounted as a tmpfs to avoid constant writes to the physical drive.
Camera files land in RAM, are forwarded to the NAS within seconds, then deleted — the drive
is only written to when a NAS upload fails (retry spill).

Mount entry in `/etc/fstab` on the Pi:
```
tmpfs  /mnt/oreocamhd1/ftpbuffer  tmpfs  defaults,size=1g,uid=root,gid=root,mode=0777  0  0
```

To mount manually after adding the fstab entry:
```bash
sudo mkdir -p /mnt/oreocamhd1/ftpbuffer
sudo mount /mnt/oreocamhd1/ftpbuffer
```

**Note:** if the Pi reboots while files are in the buffer and the NAS is unreachable, those
in-flight files are lost. Files already moved to `/mnt/oreocamhd1/retry` are safe.

---

## Retry Queue

If a NAS upload fails, the file is moved from tmpfs to `/mnt/oreocamhd1/retry` (on the physical
drive). A background thread retries every 30 seconds until the NAS recovers. No manual
intervention is needed — the queue drains automatically.

Configured via `ftp_relay.conf`:
```ini
retry_dir      = /mnt/oreocamhd1/retry
retry_interval = 30
```

To inspect the queue:
```bash
find /mnt/oreocamhd1/retry -ls
```

---

## Files on Pi

| File | Purpose |
|---|---|
| `/opt/mitainesoft/ftp_relay/ftp_relay.py` | Relay script |
| `/opt/mitainesoft/ftp_relay/ftp_relay.conf` | Credentials and config (`chmod 600`) |
| `/etc/systemd/system/ftprelay.service` | systemd unit |

`ftp_relay.conf` is not in git — edit it directly on the Pi. See `ftp_relay.conf.example` in this repo for the format.

---

## Camera FTP Settings

| Setting | Value |
|---|---|
| FTP Server | `oreocamftp.lan` |
| Port | `21` |
| Username | `oreocamftp` |
| Password | see `ftp_relay.conf` → `[camera] password` |
| Mode | Passive |
| Remote path | unique per camera (e.g. `/cam01/`, `/cam02/`) |

Network filtering is handled by the router — all IPs are accepted by the relay itself.

---

## Service Management

```bash
# Status
sudo systemctl status ftprelay

# Start / Stop / Restart
sudo systemctl start ftprelay
sudo systemctl stop ftprelay
sudo systemctl restart ftprelay

# Live logs
sudo journalctl -u ftprelay -f

# Last 50 log lines
sudo journalctl -u ftprelay -n 50 --no-pager
```

---

## Editing Config (credentials, NAS host, etc.)

```bash
ssh mitainesoft@oreocamftp.lan
sudo nano /opt/mitainesoft/ftp_relay/ftp_relay.conf
sudo systemctl restart ftprelay
```

---

## Deploying a Script Update from This Repo

```bash
cd ftprelay && bash deploy.sh
```

`deploy.sh` bumps the revision, copies the script to the Pi, and restarts the service.

---

## Diagnostics

```bash
# Confirm relay is listening on port 21
sudo ss -tlnp | grep :21

# Check buffer contents (files waiting or stuck)
ls -lh /mnt/oreocamhd1/ftpbuffer/

# Check retry queue
find /mnt/oreocamhd1/retry -ls

# Check RAM buffer usage (tmpfs)
df -h /mnt/oreocamhd1/ftpbuffer

# Check drive space (physical disk)
df -h /mnt/oreocamhd1

# Monitor disk I/O (install sysstat first: sudo apt install sysstat)
iostat -x /dev/sda1 2

# Test FTP login from another machine
ftp oreocamftp.lan
# user: oreocamftp
```

---

## Log Levels

The relay logs at INFO by default. Buffer deletions after successful NAS uploads are logged
at DEBUG (silent unless the log level is lowered). To enable debug output, change
`log.setLevel(logging.INFO)` to `log.setLevel(logging.DEBUG)` in `ftp_relay.py`.

---

## Notes

- **pyftpdlib version must stay at 1.5.9** — version 2.2.0 crashes at import on this Pi due to a pyOpenSSL incompatibility (`TLS_SERVER_METHOD` missing). Do not upgrade without testing.
- The buffer drive is NTFS (`/dev/sda1`). fstab has `nofail` so a missing drive won't hang boot.
- `transferred_dir` is intentionally left empty in the config — the NAS is the only persistent copy. There is no local archive of transferred files.
- Buffer files are deleted only after a confirmed NAS write. On failure they spill to the retry dir on disk.
