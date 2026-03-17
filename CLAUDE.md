# Personal AI Employee - Claude Code Instructions

## Project Overview
This is a Personal AI Employee built for the Panaversity Hackathon 0.
It autonomously monitors Gmail, reasons about tasks, and takes actions with human approval.

## Vault Structure
- `Needs_Action/` — incoming tasks (DO NOT delete files here, let reasoning_loop.py process them)
- `Plans/` — Claude creates Plan.md files here after analyzing tasks
- `Pending_Approval/` — tasks waiting for human approval
- `Approved/` — human-approved tasks ready for execution
- `Done/` — completed tasks
- `Failed/` — tasks that failed during execution
- `Logs/` — daily JSON logs of all actions

## How to Run
```bash
# Install dependencies
cd scripts && uv sync

# Authenticate Gmail (first time only)
cd scripts && .venv/bin/python authenticate_gmail.py

# Run Gmail watcher
cd scripts && .venv/bin/python gmail_watcher.py

# Run reasoning loop (processes Needs_Action/)
cd scripts && .venv/bin/python reasoning_loop.py

# Run approval watcher (executes approved tasks)
cd scripts && .venv/bin/python approval_watcher.py

# Run everything at once
cd scripts && .venv/bin/python main.py
```

## Agent Skills
All skills are documented in `.claude/skills/`:
- `gmail-watcher/` — how to monitor Gmail
- `linkedin-poster/` — how to post on LinkedIn
- `reasoning-loop/` — how to analyze tasks and create plans
- `hitl-approval/` — how to handle human-in-the-loop approvals

## Rules Claude Must Follow
1. NEVER take irreversible actions without human approval
2. ALWAYS create a Plan.md before executing any action
3. ALWAYS move files to Pending_Approval/ and wait for human to move to Approved/
4. ALWAYS log every action to Logs/YYYY-MM-DD.json
5. NEVER commit credentials.json, token.json, or .env files
6. For email actions: extract recipient from the `from:` field in frontmatter
7. For LinkedIn posts: use browser automation via Playwright

## MCP Server
Gmail Send MCP server is at `mcp-servers/gmail-send/`
Start it with: `node mcp-servers/gmail-send/index.js`
It exposes one tool: `send_email(to, subject, body)`
