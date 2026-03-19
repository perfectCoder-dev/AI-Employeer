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
[CLAUDE CODE] Run reasoning_loop.py → creates Plan.md → moves to Pending_Approval/
      ↓
[HUMAN] Reviews plan in Obsidian → drags file to Approved/ (this is the only human step)
      ↓
[AUTOMATIC] approval_watcher.py detects file → sends reply or posts LinkedIn → moves to Done/
```

---

## When Claude Code Is Triggered
Claude Code only needs to run when:
1. New files appear in `Needs_Action/` — run `reasoning_loop.py`
2. A script crashes and needs fixing

**Trigger prompt:** `Process new emails in Needs_Action/`

**What Claude does:**
```bash
cd /Users/muhammadomerfarooq/Desktop/AI_Employee_Vault
.venv/bin/python scripts/reasoning_loop.py
```

Then reports:
```
Processed X emails:
1. [filename] — Category: [category] — Priority: [high/medium/low]
   → Moved to Pending_Approval/

Please review plans in Obsidian and move approved files to Approved/.
approval_watcher.py will handle execution automatically.
```

**Claude does NOT need to:**
- Run gmail_watcher.py (launchd does it)
- Run approval_watcher.py (launchd does it)
- Wait for "done" (approval_watcher watches automatically)

---

## Key File Locations
- Scripts: `scripts/`
- Credentials: `credentials/`
- Environment: `scripts/.env`
- Processed IDs: `scripts/processed_ids.json`
- Logs: `Logs/YYYY-MM-DD.json`

---

## Rules
See `GUARDRAILS.md` for full safety rules. Summary:
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
See `DEPLOYMENT.md` for launchd setup and service management.

## Guardrails
See `GUARDRAILS.md` for safety rules and risk thresholds.

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
