# ftp_relay — Operations Guide

## System Info

| Item | Value |
|---|---|
| Pi hostname | `oreocamftp.lan` |
| Pi IP | `10.0.0.2` |
| Pi user | `mitainesoft` |
| NAS IP | `10.0.0.1` |
| Buffer drive | `/dev/sda1` → `/mnt/oreocamhd1` (1.9 TB, NTFS) |
| Buffer path | `/mnt/oreocamhd1/ftpbuffer` |
| Code path | `/opt/mitainesoft/ftp_relay/` |
| FTP port | `21` |
| Passive ports | `60000–60099` |

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
scp ftprelay/ftp_relay.py mitainesoft@oreocamftp.lan:/opt/mitainesoft/ftp_relay/ftp_relay.py
ssh mitainesoft@oreocamftp.lan "sudo systemctl restart ftprelay"
```

---

## Diagnostics

```bash
# Confirm relay is listening on port 21
sudo ss -tlnp | grep :21

# Check buffer contents (files waiting or stuck)
ls -lh /mnt/oreocamhd1/ftpbuffer/

# Check drive space
df -h /mnt/oreocamhd1

# Test FTP login from another machine
ftp oreocamftp.lan
# user: oreocamftp
```

---

## Notes

- **pyftpdlib version must stay at 1.5.9** — version 2.2.0 crashes at import on this Pi due to a pyOpenSSL incompatibility (`TLS_SERVER_METHOD` missing). Do not upgrade without testing.
- The buffer drive is NTFS (`/dev/sda1`). fstab has `nofail` so a missing drive won't hang boot.
- Files are written to the buffer first, then forwarded to the NAS in a background thread. If the NAS is unreachable, files stay in the buffer — no footage is lost.
- Buffer files are deleted only after a confirmed NAS write.
