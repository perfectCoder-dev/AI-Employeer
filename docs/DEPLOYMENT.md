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

## Start All Services
```bash
launchctl load ~/Library/LaunchAgents/com.aiemployee.gmailwatcher.plist
launchctl load ~/Library/LaunchAgents/com.aiemployee.approvalwatcher.plist
```

## Stop All Services
```bash
launchctl unload ~/Library/LaunchAgents/com.aiemployee.gmailwatcher.plist
launchctl unload ~/Library/LaunchAgents/com.aiemployee.approvalwatcher.plist
```

## Check Status
```bash
launchctl list | grep aiemployee
```

## Secrets Management
- credentials.json — Google OAuth app credentials (never commit)
- token.json — Google OAuth user token (never commit)
- .env — LinkedIn and Groq credentials (never commit)
- All stored in credentials/ folder, excluded via .gitignore

## Versioning
- Python deps: pyproject.toml + uv.lock
- Node deps: package.json + package-lock.json

## Scaling
- Single user deployment (local-first)
- Gmail API quota: 1B units/day (well within limits)
- Groq API: free tier, 30 req/min
