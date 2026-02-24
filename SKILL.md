# Skill: Nexus-Safe (V1.3)

Hardened SRE agent for local system monitoring and recovery.

## 🛡️ Security Policies (Hard-coded)
1. **Restart Denied by Default**: You must set `NEXUS_SAFE_ALLOW_RESTARTS=true` to enable recovery.
2. **Allowlist Only**: You can ONLY restart services explicitly listed in `NEXUS_SAFE_ALLOWED_DOCKER` or `NEXUS_SAFE_ALLOWED_PM2`.
3. **Log-First Enforcement**: Restarts are blocked unless you have checked the logs in the last 5 minutes (to ensure you've diagnosed the issue).
4. **Rate Limiting**: Restarts are limited by a sliding window (default: 3 per hour).
5. **No External Network**: Operation is strictly local.

## ⚙️ Environment Configuration
- `NEXUS_SAFE_ALLOW_RESTARTS`: "true" to enable restart capability.
- `NEXUS_SAFE_ALLOWED_DOCKER`: Comma-separated list of container names (e.g., "api,db").
- `NEXUS_SAFE_ALLOWED_PM2`: Comma-separated list of PM2 app names.
- `NEXUS_SAFE_MAX_RESTARTS`: Max restarts in window (default: 3).

## 🚀 Commands
- **/nexus-safe status** : Full system and service status.
- **/nexus-safe logs <target>** : Read logs for diagnosis (Required before restart).
- **/nexus-safe recover <target>** : Restart an allowed service. Use `--force` to skip log-freshness check.

## 📝 Audit
All actions are logged in `~/.nexus-safe/audit.log`.
