# =============================================================================
# ftp_relay.py — FTP relay service for oreocamftp
#
# Accepts camera uploads on port 21, buffers them to /mnt/oreocamhd1/ftpbuffer,
# then forwards each file to the NAS via a background thread.
# Files are deleted from the buffer only after a confirmed NAS write.
# If the NAS upload fails, the file is moved to retry_dir (disk-backed) and
# re-attempted every retry_interval seconds until it succeeds.
# Config and credentials are read from ftp_relay.conf (not in git).
#
# Deploy:  run deploy.sh from the ftprelay/ directory in the repo
# Logs:    /var/log/ftprelay/ftprelay.log  (10 MB × 5 rotation)
# Service: sudo systemctl status ftprelay
# =============================================================================

REVISION = 14

from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from pyftpdlib.authorizers import DummyAuthorizer
import configparser
import ftplib
import logging
import logging.handlers
import re
import shutil
import threading
import time
import os

_cfg = configparser.ConfigParser()
_cfg.read(os.path.join(os.path.dirname(__file__), "ftp_relay.conf"))

NAS_HOST        = _cfg["nas"]["host"]
NAS_PORT        = _cfg["nas"].getint("port")
NAS_USER        = _cfg["nas"]["user"]
NAS_PASS        = _cfg["nas"]["password"]
BUFFER_DIR      = _cfg["relay"]["buffer_dir"]
MAX_CONNECTIONS = _cfg["relay"].getint("max_connections")
RELAY_HOSTNAME  = _cfg["relay"]["hostname"]
PASSIVE_IP      = _cfg["relay"]["passive_ip"]
TRANSFERRED_DIR = _cfg["relay"]["transferred_dir"]
RETRY_DIR       = _cfg["relay"].get("retry_dir", "")
RETRY_INTERVAL  = _cfg["relay"].getint("retry_interval", 30)
NAS_REMOTE_BASE = _cfg["nas"]["remote_base"]
LOG_FILE        = _cfg["relay"]["log_file"]
LOG_MAX_BYTES   = _cfg["relay"].getint("log_max_bytes")
LOG_BACKUP_COUNT= _cfg["relay"].getint("log_backup_count")
CAM_USER        = _cfg["camera"]["user"]
CAMERA_MAP      = dict(_cfg["camera_map"]) if _cfg.has_section("camera_map") else {}
CAM_PASS        = _cfg["camera"]["password"]

# Rotating file logger
_handler = logging.handlers.RotatingFileHandler(
    LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT
)
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
log = logging.getLogger("ftprelay")
log.setLevel(logging.INFO)
log.addHandler(_handler)
log.addHandler(logging.StreamHandler())     # also keep stdout → journald

def normalize_date_path(rel_path):
    """Rewrite YYYY-MM-DD directory component to YYYY/MM/DD for NAS path alignment."""
    return re.sub(r'(\d{4})-(\d{2})-(\d{2})', r'\1/\2/\3', rel_path)

def apply_camera_map(filename):
    """Replace NVR channel prefix (e.g. OREOCAM_08) with the mapped camera name."""
    for channel, name in CAMERA_MAP.items():
        if filename.startswith(channel.upper() + "_"):
            return name.upper() + "_" + filename[len(channel) + 1:]
    return filename

def make_remote_path(rel_path):
    """Build the NAS remote path from a buffer/retry-relative path."""
    mapped_name = apply_camera_map(os.path.basename(rel_path))
    mapped_rel  = os.path.join(os.path.dirname(rel_path), mapped_name)
    return NAS_REMOTE_BASE.rstrip("/") + "/" + normalize_date_path(mapped_rel)

def remove_empty_parents(path, stop_at):
    """Remove empty directories up to (but not including) stop_at."""
    parent = os.path.dirname(path)
    while parent and os.path.abspath(parent) != os.path.abspath(stop_at):
        try:
            os.rmdir(parent)
            parent = os.path.dirname(parent)
        except OSError:
            break   # Not empty or already gone

# Shared NAS connection lock (single outbound connection)
nas_lock = threading.Lock()
nas_conn = None

def get_nas():
    global nas_conn
    try:
        nas_conn.voidcmd("NOOP")    # Test if connection is still alive
    except:
        nas_conn = ftplib.FTP()
        nas_conn.connect(NAS_HOST, NAS_PORT)
        nas_conn.login(NAS_USER, NAS_PASS)
    return nas_conn

def upload_to_nas(local_file, remote_path):
    """Upload local_file to NAS at remote_path. Raises on failure."""
    ftp = get_nas()
    dirs = os.path.dirname(remote_path).split("/")
    for i in range(1, len(dirs) + 1):
        d = "/".join(dirs[:i])
        if d:
            try:
                ftp.mkd(d)
            except ftplib.error_perm:
                pass    # Directory already exists
    with open(local_file, "rb") as f:
        ftp.storbinary(f"STOR {remote_path}", f)

def delete_after_upload(local_file, rel_path):
    """Remove file from buffer/retry after a confirmed NAS upload."""
    try:
        if TRANSFERRED_DIR:
            dest = os.path.join(TRANSFERRED_DIR, rel_path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            try:
                os.rename(local_file, dest)
                log.info(f"[→] Moved to local archive: {dest}")
            except OSError:
                shutil.move(local_file, dest)
                log.info(f"[→] Copied to local archive (cross-fs): {dest}")
        else:
            os.remove(local_file)
            log.debug(f"[✓] Deleted from buffer (NAS copy confirmed): {rel_path}")
    except Exception as e:
        log.error(f"[✗] Post-upload cleanup failed for {rel_path}: {e}")

def move_to_retry(local_file, rel_path):
    """Spill a failed upload from the buffer (tmpfs) to the disk-backed retry dir."""
    if not RETRY_DIR:
        log.error(f"[✗] No retry_dir configured — {rel_path} may be lost on reboot")
        return
    try:
        dest = os.path.join(RETRY_DIR, rel_path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.move(local_file, dest)
        log.warning(f"[!] Moved to retry queue: {rel_path}")
    except Exception as e:
        log.error(f"[✗] Failed to move {rel_path} to retry dir: {e}")

def retry_loop():
    """Background thread: re-attempt NAS uploads for files in retry_dir."""
    if not RETRY_DIR:
        return
    log.info(f"[*] Retry loop started — scanning {RETRY_DIR} every {RETRY_INTERVAL}s")
    while True:
        time.sleep(RETRY_INTERVAL)
        pending = []
        for root, _, files in os.walk(RETRY_DIR):
            for fname in files:
                pending.append(os.path.join(root, fname))
        if not pending:
            continue
        log.info(f"[↺] Retrying {len(pending)} queued file(s)")
        for fpath in pending:
            rel_path    = os.path.relpath(fpath, RETRY_DIR)
            remote_path = make_remote_path(rel_path)
            with nas_lock:
                try:
                    upload_to_nas(fpath, remote_path)
                    log.info(f"[✓] Retry succeeded — uploaded to NAS: {remote_path}")
                    delete_after_upload(fpath, rel_path)
                    remove_empty_parents(fpath, RETRY_DIR)
                except Exception as e:
                    log.warning(f"[!] Retry failed for {rel_path}: {e}")

class RelayHandler(FTPHandler):

    def on_connect(self):
        log.debug(f"[+] Camera connected: {self.remote_ip}")

    def on_disconnect(self):
        log.debug(f"[-] Camera disconnected: {self.remote_ip}")

    def on_file_received(self, file):
        """Forward uploaded file to NAS after it lands on the buffer."""
        rel_path    = os.path.relpath(file, BUFFER_DIR)
        remote_path = make_remote_path(rel_path)
        log.info(f"[→] Queuing for NAS upload: {rel_path}")

        def upload():
            with nas_lock:
                try:
                    upload_to_nas(file, remote_path)
                    log.info(f"[✓] Uploaded to NAS: {remote_path}")
                except Exception as e:
                    log.error(f"[✗] NAS upload failed for {rel_path}: {e}")
                    move_to_retry(file, rel_path)
                    return

                delete_after_upload(file, rel_path)

        threading.Thread(target=upload, daemon=True).start()

    def on_incomplete_file_received(self, file):
        log.warning(f"[!] Incomplete upload discarded: {file}")
        os.remove(file)

def main():
    if RETRY_DIR:
        os.makedirs(RETRY_DIR, exist_ok=True)
        threading.Thread(target=retry_loop, daemon=True).start()

    authorizer = DummyAuthorizer()
    authorizer.add_user(CAM_USER, CAM_PASS, BUFFER_DIR, perm="elradfmwMT")

    handler = RelayHandler
    handler.authorizer = authorizer
    handler.masquerade_address = PASSIVE_IP
    handler.passive_ports = range(60000, 60100)

    server = FTPServer(("0.0.0.0", 21), handler)
    server.max_cons = MAX_CONNECTIONS
    server.max_cons_per_ip = 2

    log.info(f"[*] ftp_relay.py revision {REVISION} starting")
    log.info(f"[*] FTP relay started on {RELAY_HOSTNAME} → NAS at {NAS_HOST}")
    server.serve_forever()

if __name__ == "__main__":
    main()
