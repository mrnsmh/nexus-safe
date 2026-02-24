import os
import psutil
import subprocess
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# --- CONFIGURATION & PATHS ---
STATE_DIR = Path.home() / ".nexus-safe"
STATE_FILE = STATE_DIR / "state.json"
AUDIT_LOG = STATE_DIR / "audit.log"

# Env vars mapping
ALLOW_RESTARTS = os.getenv("NEXUS_SAFE_ALLOW_RESTARTS", "false").lower() == "true"
ALLOWED_DOCKER = [x.strip() for x in os.getenv("NEXUS_SAFE_ALLOWED_DOCKER", "").split(",") if x.strip()]
ALLOWED_PM2 = [x.strip() for x in os.getenv("NEXUS_SAFE_ALLOWED_PM2", "").split(",") if x.strip()]
MAX_RESTARTS = int(os.getenv("NEXUS_SAFE_MAX_RESTARTS", "3"))
RESTART_WINDOW = int(os.getenv("NEXUS_SAFE_RESTART_WINDOW_SECONDS", "3600"))
LOGS_REQUIRED = os.getenv("NEXUS_SAFE_LOGS_REQUIRED", "true").lower() == "true"
LOGS_FRESH_SEC = int(os.getenv("NEXUS_SAFE_LOGS_FRESH_SECONDS", "300"))

TIMEOUT_STATUS = int(os.getenv("NEXUS_SAFE_TIMEOUT_STATUS", "5"))
TIMEOUT_LOGS = int(os.getenv("NEXUS_SAFE_TIMEOUT_LOGS", "10"))
TIMEOUT_RESTART = int(os.getenv("NEXUS_SAFE_TIMEOUT_RESTART", "15"))

def log_audit(action, target, status, detail=""):
    timestamp = datetime.now().isoformat()
    entry = f"{timestamp} | {action} | {target} | {status} | {detail}\n"
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
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "ram_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "load": os.getloadavg()
    }

def get_docker_list():
    try:
        res = subprocess.run(['docker', 'ps', '-a', '--format', '{{.Names}}|{{.Status}}|{{.State}}'], 
                             capture_output=True, text=True, timeout=TIMEOUT_STATUS)
        if res.returncode != 0: return []
        return [line.split('|') for line in res.stdout.strip().split('\n') if line]
    except Exception: return []

def get_pm2_list():
    try:
        res = subprocess.run(['pm2', 'jlist'], capture_output=True, text=True, timeout=TIMEOUT_STATUS)
        if res.returncode != 0: return []
        data = json.loads(res.stdout)
        return [{"name": p['name'], "status": p['pm2_env']['status']} for p in data]
    except Exception: return []

def fetch_logs(target, lines=50):
    state = load_state()
    output = ""
    provider = None
    
    # Try Docker
    d_check = subprocess.run(['docker', 'inspect', target], capture_output=True)
    if d_check.returncode == 0:
        provider = "docker"
        res = subprocess.run(['docker', 'logs', '--tail', str(lines), target], 
                             capture_output=True, text=True, timeout=TIMEOUT_LOGS)
        output = res.stdout + res.stderr
    else:
        # Try PM2
        p_check = subprocess.run(['pm2', 'describe', target], capture_output=True)
        if p_check.returncode == 0:
            provider = "pm2"
            res = subprocess.run(['pm2', 'logs', target, '--lines', str(lines), '--nostream'], 
                                 capture_output=True, text=True, timeout=TIMEOUT_LOGS)
            output = res.stdout
            
    if provider:
        state["last_logs_view"][target] = time.time()
        save_state(state)
        log_audit("LOGS", target, "SUCCESS")
        return output
    
    log_audit("LOGS", target, "FAILED", "Target not found")
    print(f"Error: Target {target} not found in Docker or PM2", file=sys.stderr)
    sys.exit(2)

def restart_service(target, force=False, dry_run=False):
    if not ALLOW_RESTARTS:
        print("Policy Error: Restarts are disabled (NEXUS_SAFE_ALLOW_RESTARTS=false)", file=sys.stderr)
        sys.exit(3)

    state = load_state()
    
    # 1. Check Allowlist
    is_docker = any(target == c[0] for c in get_docker_list())
    is_pm2 = any(target == p['name'] for p in get_pm2_list())
    
    if is_docker:
        if target not in ALLOWED_DOCKER:
            print(f"Policy Error: {target} not in NEXUS_SAFE_ALLOWED_DOCKER", file=sys.stderr)
            sys.exit(3)
        cmd = ['docker', 'restart', target]
    elif is_pm2:
        if target not in ALLOWED_PM2:
            print(f"Policy Error: {target} not in NEXUS_SAFE_ALLOWED_PM2", file=sys.stderr)
            sys.exit(3)
        cmd = ['pm2', 'restart', target]
    else:
        print(f"Error: Service {target} not found", file=sys.stderr)
        sys.exit(2)

    # 2. Check Logs Freshness
    if LOGS_REQUIRED and not force:
        last_view = state["last_logs_view"].get(target, 0)
        if (time.time() - last_view) > LOGS_FRESH_SEC:
            print(f"Policy Error: Logs for {target} not consulted recently. Use 'logs' first or --force.", file=sys.stderr)
            sys.exit(3)

    # 3. Check Max Restarts (Sliding Window)
    now = time.time()
    state["restarts"] = [t for t in state["restarts"] if (now - t) < RESTART_WINDOW]
    if len(state["restarts"]) >= MAX_RESTARTS:
        print(f"Policy Error: Quota exceeded ({MAX_RESTARTS} restarts per {RESTART_WINDOW}s)", file=sys.stderr)
        sys.exit(3)

    if dry_run:
        print(f"Dry-run: Would execute {' '.join(cmd)}")
        return

    # 4. Execute
    try:
        subprocess.run(cmd, check=True, timeout=TIMEOUT_RESTART, capture_output=True)
        state["restarts"].append(now)
        save_state(state)
        log_audit("RESTART", target, "SUCCESS")
        print(json.dumps({"status": "success", "target": target}))
    except Exception as e:
        log_audit("RESTART", target, "ERROR", str(e))
        print(f"Runtime Error: {str(e)}", file=sys.stderr)
        sys.exit(5)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    
    subparsers.add_parser("status").add_argument("--json", action="store_true")
    
    log_p = subparsers.add_parser("logs")
    log_p.add_argument("target")
    log_p.add_argument("--lines", type=int, default=50)
    
    res_p = subparsers.add_parser("restart")
    res_p.add_argument("target")
    res_p.add_argument("--force", action="store_true")
    res_p.add_argument("--dry-run", action="store_true")
    
    args = parser.parse_args()

    if args.command == "status":
        report = {"timestamp": datetime.now().isoformat(), "vitals": get_vitals(), "docker": get_docker_list(), "pm2": get_pm2_list()}
        print(json.dumps(report, indent=2))
    elif args.command == "logs":
        print(fetch_logs(args.target, args.lines))
    elif args.command == "restart":
        restart_service(args.target, args.force, args.dry_run)
    else:
        parser.print_help()
        sys.exit(2)
