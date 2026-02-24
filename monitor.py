import os
import psutil
import subprocess
import json
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
        res = subprocess.run(['docker', 'ps', '--format', '{{.Names}}|{{.Status}}|{{.State}}'], capture_output=True, text=True)
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

if __name__ == "__main__":
    report = {
        "timestamp": datetime.now().isoformat(),
        "vitals": get_vitals(),
        "docker": get_docker(),
        "pm2": get_pm2()
    }
    print(json.dumps(report, indent=2))
