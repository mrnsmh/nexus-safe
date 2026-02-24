# Skill: Nexus-Safe (V1.1)

Superviseur système local "Zero-Trust" pour OpenClaw.

## 🛡️ Architecture de Sécurité
- **Local Uniquement** : Aucune communication réseau externe.
- **Transparence** : Utilise uniquement des outils système standards (`docker`, `pm2`).

## 📋 Capacités
- **/nexus-safe status** : Rapport complet des ressources et services.
- **/nexus-safe logs <service>** : Affiche les dernières lignes de logs d'un conteneur Docker ou d'un processus PM2.
- **/nexus-safe recover <service>** : Protocole de récupération. L'Agent doit d'abord lire les logs via `monitor.py logs`, puis décider s'il lance `docker restart` ou `pm2 restart`.

## ⚙️ Configuration
- `NEXUS_SAFE_MAX_RESTARTS` : (Optionnel, env var) Nombre max de redémarrages auto par heure.

## 🚀 Installation
Nécessite `python3` avec `psutil`. Pour installer les dépendances :
`pip install psutil`
