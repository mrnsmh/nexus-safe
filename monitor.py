import os
import psutil
import subprocess
import json
import sys
from datetime import datetime

# Safety list of allowed services (prevents arbitrary command execution)
# If empty, the agent decides based on docker ps / pm2 list results.
ALLOWED_CONTAINERS = [] 

def get_vitals():
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "ram_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "load": os.getloadavg()
    }

def get_docker():
    try:
        res = subprocess.run(['docker', 'ps', '-a', '--format', '{{.Names}}|{{.Status}}|{{.State}}'], capture_output=True, text=True)
        return [line.split('|') for line in res.stdout.strip().split('\n') if line]
    except:
        return []

def get_pm2():
    try:
        res = subprocess.run(['pm2', 'jlist'], capture_output=True, text=True)
        data = json.loads(res.stdout)
        return [{"name": p['name'], "status": p['pm2_env']['status']} for p in data]
    except:
        return []

def get_logs(service_name, lines=50):
    try:
        # Check docker
        docker_check = subprocess.run(['docker', 'inspect', service_name], capture_output=True)
        if docker_check.returncode == 0:
            res = subprocess.run(['docker', 'logs', '--tail', str(lines), service_name], capture_output=True, text=True)
            return res.stdout + res.stderr
        # Check PM2
        res = subprocess.run(['pm2', 'logs', service_name, '--lines', str(lines), '--nostream'], capture_output=True, text=True)
        return res.stdout
    except Exception as e:
        return f"Error: {str(e)}"

def restart_service(service_name):
    """Explicit restart logic with basic validation."""
    try:
        # 1. Try Docker
        docker_check = subprocess.run(['docker', 'inspect', service_name], capture_output=True)
        if docker_check.returncode == 0:
            subprocess.run(['docker', 'restart', service_name], check=True)
            return {"status": "success", "provider": "docker", "service": service_name}
        
        # 2. Try PM2
        subprocess.run(['pm2', 'restart', service_name], check=True)
        return {"status": "success", "provider": "pm2", "service": service_name}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        action = "status"
    else:
        action = sys.argv[1]
    
    if action == "status":
        report = {
            "timestamp": datetime.now().isoformat(),
            "vitals": get_vitals(),
            "docker": get_docker(),
            "pm2": get_pm2()
        }
        print(json.dumps(report, indent=2))
    elif action == "logs":
        service = sys.argv[2] if len(sys.argv) > 2 else ""
        print(get_logs(service))
    elif action == "restart":
        service = sys.argv[2] if len(sys.argv) > 2 else ""
        print(json.dumps(restart_service(service), indent=2))
