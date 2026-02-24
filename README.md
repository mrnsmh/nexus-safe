# Skill: Nexus-Safe (V1.3.0)

Autonomous SRE agent for local system monitoring and controlled recovery.

## 🛡️ Hardened Security Policy
- **No Network**: 100% local operation.
- **Safe-by-default**: Restarts are disabled until `NEXUS_SAFE_ALLOW_RESTARTS=true` is set.
- **Controlled Restarts**: Restricted to `NEXUS_SAFE_ALLOWED_DOCKER` and `NEXUS_SAFE_ALLOWED_PM2` lists.
- **Log-First Enforcement**: You MUST call `/nexus-safe logs <service>` before attempting a recovery.

## ⚙️ Environment Variables
- `NEXUS_SAFE_ALLOW_RESTARTS`: "true" to enable recovery.
- `NEXUS_SAFE_ALLOWED_DOCKER`: Comma-separated (ex: "api,db").
- `NEXUS_SAFE_ALLOWED_PM2`: Comma-separated (ex: "worker").
- `NEXUS_SAFE_MAX_RESTARTS`: Max attempts in window (Default: 3).

## 🚀 Commands
- **/nexus-safe status**: System vitals and service list.
- **/nexus-safe logs <target>**: Fetch latest logs (required for recovery).
- **/nexus-safe recover <target>**: Logic-based service restart.

## 📋 Installation
1. `pip install psutil`
2. Ensure `docker` and `pm2` are in PATH.
