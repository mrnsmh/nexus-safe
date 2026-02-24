import os
import psutil
import subprocess
import json
import sys
import time
from datetime import datetime
from pathlib import Path

STATE_DIR = Path.home() / ".nexus-safe"
STATE_FILE = STATE_DIR / "state.json"
AUDIT_LOG = STATE_DIR / "audit.log"

ALLOW_RESTARTS = os.getenv("NEXUS_SAFE_ALLOW_RESTARTS", "false").lower() == "true"
ALLOWED_DOCKER = [x.strip() for x in os.getenv("NEXUS_SAFE_ALLOWED_DOCKER", "").split(",") if x.strip()]
ALLOWED_PM2 = [x.strip() for x in os.getenv("NEXUS_SAFE_ALLOWED_PM2", "").split(",") if x.strip()]
MAX_RESTARTS = int(os.getenv("NEXUS_SAFE_MAX_RESTARTS", "3"))
RESTART_WINDOW = int(os.getenv("NEXUS_SAFE_RESTART_WINDOW_SECONDS", "3600"))
LOGS_REQUIRED = os.getenv("NEXUS_SAFE_LOGS_REQUIRED", "true").lower() == "true"
LOGS_FRESH_SEC = int(os.getenv("NEXUS_SAFE_LOGS_FRESH_SECONDS", "300"))

def log_audit(action, target, status, detail=""):
    timestamp = datetime.now().isoformat()
    entry = f"{timestamp} | {action} | {target} | {status} | {detail}\n"
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_LOG, "a") as f:
        f.write(entry)

def load_state():
    if not STATE_FILE.exists():
        return {"restarts": [], "last_logs_view": {}}
    try:
        return json.loads(STATE_FILE.read_text())
    except:
        return {"restarts": [], "last_logs_view": {}}

def save_state(state):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state))
    STATE_FILE.chmod(0o600)

def get_vitals():
    return {
        "cpu": psutil.cpu_percent(interval=0.1),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent,
        "load": os.getloadavg()
    }

def get_logs(target, lines=100):
    try:
        d_check = subprocess.run(['docker', 'inspect', target], capture_output=True)
        if d_check.returncode == 0:
            res = subprocess.run(['docker', 'logs', '--tail', str(lines), target], capture_output=True, text=True)
            return res.stdout + res.stderr
        res = subprocess.run(['pm2', 'logs', target, '--lines', str(lines), '--nostream'], capture_output=True, text=True)
        return res.stdout
    except Exception as e:
        return f"Error: {str(e)}"

def restart_service(target, force=False):
    if not ALLOW_RESTARTS:
        return {"status": "denied", "reason": "NEXUS_SAFE_ALLOW_RESTARTS is false"}
    
    state = load_state()
    # Check Logs Freshness
    if LOGS_REQUIRED and not force:
        last_view = state["last_logs_view"].get(target, 0)
        if (time.time() - last_view) > LOGS_FRESH_SEC:
            return {"status": "denied", "reason": "Logs not reviewed recently. Consult logs before restart."}

    now = time.time()
    state["restarts"] = [t for t in state["restarts"] if (now - t) < RESTART_WINDOW]
    if len(state["restarts"]) >= MAX_RESTARTS:
        return {"status": "denied", "reason": f"Quota exceeded: {MAX_RESTARTS} restarts allowed per hour."}

    # Execute restart based on provider detection
    try:
        d_check = subprocess.run(['docker', 'inspect', target], capture_output=True)
        if d_check.returncode == 0:
            if target not in ALLOWED_DOCKER: return {"status": "denied", "reason": "Not in allowlist"}
            subprocess.run(['docker', 'restart', target], check=True)
        else:
            if target not in ALLOWED_PM2: return {"status": "denied", "reason": "Not in allowlist"}
            subprocess.run(['pm2', 'restart', target], check=True)
        
        state["restarts"].append(now)
        save_state(state)
        log_audit("RESTART", target, "SUCCESS")
        return {"status": "success", "target": target}
    except Exception as e:
        log_audit("RESTART", target, "ERROR", str(e))
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    if action == "status":
        print(json.dumps(get_vitals()))
    elif action == "logs":
        target = sys.argv[2] if len(sys.argv) > 2 else ""
        # Update last view timestamp
        st = load_state()
        st["last_logs_view"][target] = time.time()
        save_state(st)
        print(get_logs(target))
    elif action == "restart":
        target = sys.argv[2] if len(sys.argv) > 2 else ""
        force = "--force" in sys.argv
        print(json.dumps(restart_service(target, force)))
