# Skill: Nexus-Safe (V1.4) - AI-Orchestrated SRE

This skill turns the Agent into an autonomous Site Reliability Engineer. It provides raw system access, but the decision-making logic is driven by the Agent's reasoning.

## 🧠 AI Integration
The Agent should consult `AGENT_BRAIN.md` to learn the diagnostic protocols. This ensures that restarts are notProcedural, but **Logical**.

## 🛡️ Security Policies
- **Logs-First**: The `restart` command is blocked unless `logs` were read in the last 5 minutes.
- **Allowlist**: Only services in `NEXUS_SAFE_ALLOWED_DOCKER/PM2` can be touched.
- **Rate Limiting**: Hard-coded max restarts per hour.

## 🚀 Usage
- **/nexus-safe status** : Get system vitals.
- **/nexus-safe logs <service>** : Required step before any recovery.
- **/nexus-safe recover <service>** : Trigger a restart after diagnostic.

## ⚙️ Environment Configuration
- `NEXUS_SAFE_ALLOW_RESTARTS`: "true"
- `NEXUS_SAFE_ALLOWED_DOCKER`: "container1,container2"
- `NEXUS_SAFE_ALLOWED_PM2`: "app1"
