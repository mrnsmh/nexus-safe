# Skill: Nexus-Safe (V1.2)

Autonomous local System Reliability Agent. 

## 🛡️ Privacy & Security
- **Data Sovereignty**: No system data, logs, or metrics ever leave your server. This skill does not make any outbound network requests during operation.
- **Controlled Access**: Restricts agent power to system inspection and service restarts of Docker/PM2.

## 📋 Capabilities
- **/nexus-safe status** : System-wide health check (CPU, RAM, Disk, Load, Services).
- **/nexus-safe logs <service>** : Diagnostic tool to read the latest 50 lines of logs.
- **/nexus-safe recover <service>** : Smart recovery command that restarts a container or a PM2 app.

## 🚀 Installation & Prerequisites
**Internet Access Notice**: An internet connection is required *only during installation* to fetch dependencies. Once installed, the skill operates entirely offline/locally.

**System Requirements**:
- `docker` and `pm2` binaries must be accessible.
- `python3` with `psutil`.

**Setup**:
`pip install psutil`

## ⚙️ Logic & Safeguards
- **Max Restarts**: Controlled by `NEXUS_SAFE_MAX_RESTARTS` (env var).
- **Workflow**: The agent is instructed to ALWAYS read logs via `/nexus-safe logs` before triggering a recovery to prevent infinite restart loops on broken code.
