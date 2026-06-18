# AI Employee — Deployment Config

## Environment
- OS: macOS (Apple Silicon M2)
- Python: 3.13+
- Node.js: v22+
- Shell: zsh

## Process Management
| Process | Method | Config |
|---|---|---|
| gmail_watcher.py | launchd | ~/Library/LaunchAgents/com.aiemployee.gmailwatcher.plist |
| approval_watcher.py | launchd | ~/Library/LaunchAgents/com.aiemployee.approvalwatcher.plist |
| dashboard/app.py | launchd or manual | ~/Library/LaunchAgents/com.aiemployee.dashboard.plist |

## Required Production Environment
- `ENVIRONMENT=production`
- `VAULT_DIR=/absolute/path/to/AI_Employee_Vault`
- `DASHBOARD_APPROVAL_TOKEN=<long random token>`
- `CREDENTIALS_PATH=/absolute/path/to/credentials.json`
- `TOKEN_PATH=/absolute/path/to/token.json`
- `UNIVERSITY_HANDBOOK_PATH=/absolute/path/to/docs/University_Handbook.md`

Production startup fails if the dashboard token, Gmail token, credentials, or handbook are missing.

## Set Dashboard Approval Token
Generate a strong token:
```bash
openssl rand -hex 32
```

Add it to `scripts/.env`:
```bash
DASHBOARD_APPROVAL_TOKEN=paste_generated_token_here
```

The dashboard prompts for this value in the browser and sends it as `X-Approval-Token`. Keep it private like any other credential.

## Generate launchd Plists
Templates are tracked in `launchd/*.plist.template`. Replace `__VAULT_DIR__` with the absolute vault path, then copy the rendered files to `~/Library/LaunchAgents/`.

From the vault root, run:
```bash
mkdir -p ~/Library/LaunchAgents
sed "s#__VAULT_DIR__#$(pwd)#g" launchd/com.aiemployee.gmailwatcher.plist.template > ~/Library/LaunchAgents/com.aiemployee.gmailwatcher.plist
sed "s#__VAULT_DIR__#$(pwd)#g" launchd/com.aiemployee.approvalwatcher.plist.template > ~/Library/LaunchAgents/com.aiemployee.approvalwatcher.plist
sed "s#__VAULT_DIR__#$(pwd)#g" launchd/com.aiemployee.dashboard.plist.template > ~/Library/LaunchAgents/com.aiemployee.dashboard.plist
```

## Start All Services
```bash
launchctl load ~/Library/LaunchAgents/com.aiemployee.gmailwatcher.plist
launchctl load ~/Library/LaunchAgents/com.aiemployee.approvalwatcher.plist
launchctl load ~/Library/LaunchAgents/com.aiemployee.dashboard.plist
```

## Stop All Services
```bash
launchctl unload ~/Library/LaunchAgents/com.aiemployee.gmailwatcher.plist
launchctl unload ~/Library/LaunchAgents/com.aiemployee.approvalwatcher.plist
launchctl unload ~/Library/LaunchAgents/com.aiemployee.dashboard.plist
```

## Check Status
```bash
launchctl list | grep aiemployee
```

## Open Dashboard
Open:
```text
http://127.0.0.1:5000
```

When prompted, paste the `DASHBOARD_APPROVAL_TOKEN` value from `scripts/.env`.

## Secrets Management
- credentials.json — Google OAuth app credentials (never commit)
- token.json — Google OAuth user token (never commit)
- .env — LinkedIn and Groq credentials (never commit)
- All stored in credentials/ folder, excluded via .gitignore
- Dashboard approve/reject and read APIs are token-protected when `DASHBOARD_APPROVAL_TOKEN` is set.

## Versioning
- Python deps: pyproject.toml + uv.lock
- Node deps: package.json + package-lock.json

## Scaling
- Single user deployment (local-first)
- Gmail API quota: 1B units/day (well within limits)
- Groq API: free tier, 30 req/min
