import os
import psutil
import subprocess
import json
import sys
from datetime import datetime

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
    """Local log retrieval for Docker or PM2."""
    try:
        # Check if it's a docker container first
        docker_check = subprocess.run(['docker', 'inspect', service_name], capture_output=True)
        if docker_check.returncode == 0:
            res = subprocess.run(['docker', 'logs', '--tail', str(lines), service_name], capture_output=True, text=True)
            return res.stdout + res.stderr
        # Otherwise try PM2
        res = subprocess.run(['pm2', 'logs', service_name, '--lines', str(lines), '--nostream'], capture_output=True, text=True)
        return res.stdout
    except Exception as e:
        return f"Error retrieving logs for {service_name}: {str(e)}"

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    
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
