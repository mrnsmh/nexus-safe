# Skill: Nexus-Safe

A zero-trust, local-only system supervisor designed for maximum security and privacy.

## 🛡️ Security Architecture
- **No External Calls**: Does not contact any third-party gateway by default.
- **Privacy by Design**: Monitoring is strictly local. Reports are delivered directly into the agent conversation.
- **Restricted Scope**: Operations are limited to monitoring system health and restarting local Docker/PM2 services.

## 📋 Capabilities
- **Resource Audit**: Real-time CPU, RAM, and Disk usage analysis.
- **Service Monitoring**: Status checks of Docker containers and PM2 processes.
- **Smart Recovery**: Context-aware service restarts (checking logs before acting).

## ⚙️ Configuration
No external credentials required.
- `NEXUS_SAFE_MAX_RESTARTS`: (Optional) Max auto-restarts per hour (Default: 2).

## 🚀 Usage
- **/nexus-safe status** : Full local system health report.
- **/nexus-safe logs <service>** : Retrieve the last 50 lines of logs for diagnostic.
- **/nexus-safe recover <service>** : Safe, manual recovery trigger.
