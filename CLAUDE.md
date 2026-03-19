# Personal AI Employee - Claude Code Instructions

## IMPORTANT: Read This First
This system runs autonomously. Most agents run in the background via launchd.
Claude Code is only needed to run the reasoning loop when new emails arrive.

---

## Project Overview
A Personal AI Employee that monitors Gmail, reasons about tasks, and takes
real-world actions with human approval. Local-first, agent-driven, HITL.

## Vault Location
/Users/muhammadomerfarooq/Desktop/AI_Employee_Vault

## Python Interpreter
ALWAYS use: /Users/muhammadomerfarooq/Desktop/AI_Employee_Vault/.venv/bin/python
NEVER use: python or python3 directly

---

## System Architecture

### Always Running (Background — no human needed)
These run automatically via launchd on startup:

| Agent | Script | Schedule | What it does |
|---|---|---|---|
| Gmail Watcher | `scripts/gmail_watcher.py` | Every 2 min | Detects new emails → creates `.md` in `Needs_Action/` |
| Approval Watcher | `scripts/approval_watcher.py` | Always on | Watches `Approved/` → sends emails, posts LinkedIn |

### Auto-triggered (No human needed)
| Agent | Script | Trigger | What it does |
|---|---|---|---|
| Reasoning Loop | `scripts/reasoning_loop.py` | Auto-triggered by gmail_watcher when new emails found | Analyzes emails → creates Plan.md → routes to Pending_Approval/ |

---

## Full Autonomous Flow (No Human Input Needed Except Approval)
```
[AUTOMATIC] Gmail arrives
      ↓
[AUTOMATIC] gmail_watcher.py detects it → creates .md in Needs_Action/
      ↓
[AUTOMATIC] gmail_watcher.py triggers reasoning_loop.py automatically
      ↓
[AUTOMATIC] Plan.md created → file moved to Pending_Approval/
      ↓
[HUMAN] Only step: drag file from Pending_Approval/ to Approved/
      ↓
[AUTOMATIC] approval_watcher.py detects it → sends reply/posts LinkedIn → Done/
```

---

## When Claude Code Is Needed
Claude Code is only needed when:
1. A script crashes and needs fixing
2. You want to manually trigger the pipeline for testing

**The system runs fully autonomously — no Claude Code prompting needed.**

**Claude does NOT need to:**
- Run gmail_watcher.py (launchd does it every 2 min)
- Run reasoning_loop.py (gmail_watcher triggers it automatically)
- Run approval_watcher.py (launchd keeps it always running)
- Wait for human input (approval_watcher watches Approved/ automatically)

**Only human action required:**
- Drag file from Pending_Approval/ to Approved/ to approve

---

## Key File Locations
- Scripts: `scripts/`
- Credentials: `credentials/`
- Environment: `scripts/.env`
- Processed IDs: `scripts/processed_ids.json`
- Logs: `Logs/YYYY-MM-DD.json`

---

## Rules
See `docs/GUARDRAILS.md` for full safety rules. Summary:
1. NEVER act without human approval for emails/LinkedIn
2. ALWAYS use `.venv/bin/python`
3. ALWAYS work from vault root
4. NEVER commit credentials

## Agent Skills
- `.claude/skills/gmail-watcher/SKILL.md`
- `.claude/skills/linkedin-poster/SKILL.md`
- `.claude/skills/reasoning-loop/SKILL.md`
- `.claude/skills/hitl-approval/SKILL.md`

## Deployment
See `docs/DEPLOYMENT.md` for launchd setup and service management.

## Guardrails
See `docs/GUARDRAILS.md` for safety rules and risk thresholds.

## MCP Server
Location: `mcp-servers/gmail-send/index.js`
Tool: `send_email(to, subject, body)`

---

## LinkedIn Autonomous Workflow

### How LinkedIn Posting Works
The AI proactively generates LinkedIn posts based on business activity.
You never write the post — the AI writes it, you just approve.
```
[AUTOMATIC] reasoning_loop.py processes emails
              ↓
[AUTOMATIC] Detects business activity (inquiries, meetings, projects)
              ↓
[AUTOMATIC] Groq LLaMA generates relevant LinkedIn post
              ↓
[AUTOMATIC] Creates linkedin_post.md in Pending_Approval/
              ↓
[HUMAN] Only step: drag file from Pending_Approval/ to Approved/
              ↓
[AUTOMATIC] approval_watcher.py detects it
              ↓
[AUTOMATIC] Playwright logs into LinkedIn → posts → Done/
```

### What Triggers a LinkedIn Post
reasoning_loop.py auto-generates a post when it processes:
- Sales inquiries (new client interest)
- Meeting requests (business activity)
- Project inquiries (new opportunities)

### LinkedIn Credentials
Stored in `scripts/.env`:
- `LINKEDIN_EMAIL` — your LinkedIn email
- `LINKEDIN_PASSWORD` — your LinkedIn password

### Fallback Behavior
If Playwright automation fails:
- Post queued in `Logs/linkedin_queue.json`
- Dashboard.md notified
- Human can manually post from queue

### LinkedIn Post Guidelines
- Under 200 words
- 3-5 relevant hashtags
- Professional tone
- Never post confidential client information
