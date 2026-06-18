# Personal AI Employee - Agent Documentation

## System Overview
This system consists of autonomous agents, a Gmail MCP server, and a **Web Dashboard** working together as a university department email assistant.

---

## Agent 1: Gmail Watcher
**File:** `scripts/gmail_watcher.py`
**Type:** Perception Agent (Watcher)
**Trigger:** launchd KeepAlive service; polls every 2 minutes by default
**Input:** Department Gmail inbox (unread important emails)
**Output:** `.md` files in `Needs_Action/`

### What it does:
- Authenticates with Gmail API using OAuth2
- Polls for unread important emails every 2 minutes
- Creates structured markdown files with YAML frontmatter and Gmail message IDs in filenames to avoid collisions
- Marks processed emails as read
- Logs activity to `Logs/`

### Auto-trigger
After processing new emails, gmail_watcher automatically triggers 
reasoning_loop.py — no human intervention needed.

---

## Agent 2: Reasoning Loop
**File:** `scripts/reasoning_loop.py`
**Type:** Reasoning Agent (Brain)
**Trigger:** Auto-triggered by gmail_watcher when new emails are found
**Input:** `.md` files in `Needs_Action/`
**Output:** `Plan.md` files in `Plans/`, exact email approval drafts in `Pending_Approval/`

### University Handbook Grounding
After processing emails, reasoning_loop automatically:
- Classifies the inquiry into university categories such as registration, attendance, exams, fee/refund, scholarship, conduct, hostel, library/IT, or grievance
- Retrieves relevant sections from `docs/University_Handbook.md`
- Drafts an exact reply using the handbook context
- Creates an approval artifact containing `draft_body` and handbook page references
- Human reviews and approves the exact reply before it can be sent

### What it does:
- Reads all files in `Needs_Action/`
- Analyzes content using `docs/University_Handbook.md` as context
- Classifies action type: `email_send` or `manual`
- Creates structured Plan.md with recommended steps
- Routes handbook-backed drafts: action-required → `Pending_Approval/`, informational → `Done/`

---

## Agent 3: HITL Approval Watcher
**File:** `scripts/approval_watcher.py`
**Type:** Execution Agent (Hands)
**Trigger:** Watchdog on `Approved/` folder
**Input:** `.md` files moved to `Approved/` by human
**Output:** Real-world actions (emails sent, LinkedIn posts published)

### What it does:
- Monitors `Approved/` folder using watchdog
- Routes based on `type:` in YAML frontmatter:
  - `email` / `email_send` → sends the exact approved `draft_body` via Gmail API
  - `linkedin_post` → posts via Playwright browser automation
  - `plan` → moves to Done/ (no action needed)
- Refuses to send old-style email files that do not contain `draft_body`
- Skips duplicate `action_id`s using `Logs/execution_receipts.json`
- Moves processed files to `Done/` or `Failed/`
- Logs all actions to `Logs/YYYY-MM-DD.json`

---

## Agent 4: LinkedIn Poster
**File:** `scripts/linkedin_poster.py`
**Type:** Action Agent
**Trigger:** Called by approval_watcher when type: linkedin_post
**Post Source:** Optional only. `AUTO_LINKEDIN_POSTS=false` by default for university department deployments.
**Human role:** Approve only — never write content
**Input:** `.md` file with post content
**Output:** Live LinkedIn post

### What it does:
- Launches Playwright browser (Chromium)
- Logs into LinkedIn using credentials from `.env`
- Navigates to feed and clicks "Start a post"
- Types post content and clicks Post
- Falls back to queue approach if automation fails

---

## MCP Server: Gmail Send
**File:** `mcp-servers/gmail-send/index.js`
**Type:** Tool Server (Model Context Protocol)
**Protocol:** MCP over stdio
**Tool:** `send_email(to, subject, body)`

### What it does:
- Exposes Gmail send functionality as an MCP tool
- Claude Code can call it directly to send emails
- Uses existing OAuth credentials (token.json + credentials.json)

---

## Web Dashboard
**Files:** `dashboard/app.py`, `dashboard/static/`  
**Type:** Monitoring & Control UI  
**URL:** `http://127.0.0.1:5000`  
**Start:** `cd dashboard && ../scripts/.venv/bin/python app.py`
**Production auth:** Set `DASHBOARD_APPROVAL_TOKEN`; the browser prompts for it and sends it as `X-Approval-Token`.

### What it does:
- Serves a real-time dark glassmorphism web dashboard
- Reads live data from all vault folders and JSON log files
- Exposes 8 REST API endpoints consumed by the frontend
- Allows one-click **Approve** / **Reject** from the browser (moves files via the API)
- Protects dashboard read/write APIs with `DASHBOARD_APPROVAL_TOKEN` when configured
- Auto-refreshes every 30 seconds

### Views:
| View | Description |
|---|---|
| Dashboard | KPI cards, agent pipeline diagram, recent activity, action breakdown |
| Pending Approval | One-click ✓ Approve / ✗ Reject for each item |
| Needs Action | Items queued for AI processing |
| Done | Completed items with full content viewer |
| Plans | AI-generated action plans |
| Activity Log | Full audit timeline from `Logs/*.json` |
| Failed | Items that errored — for debugging |

### API Endpoints:
| Endpoint | Method | Description |
|---|---|---|
| `/api/stats` | GET | KPIs + breakdown + recent activity |
| `/api/folder/<key>` | GET | List any workflow folder |
| `/api/file/<folder>/<name>` | GET | Read single file (frontmatter + body) |
| `/api/approve/<name>` | POST | Move Pending_Approval → Approved |
| `/api/reject/<name>` | POST | Move Pending_Approval → Rejected |
| `/api/logs` | GET | All daily JSON log entries |
| `/api/agent-log` | GET | Last 200 lines of agent.log |
| `/api/all-items` | GET | All items across all folders |

When `DASHBOARD_APPROVAL_TOKEN` is set, all API endpoints require `X-Approval-Token`.

---

## Human-in-the-Loop (HITL) Flow
```
AI proposes → Human decides → AI executes

1. Agent detects task → creates Plan.md
2. Exact draft/action sits in Pending_Approval/ (AI cannot proceed)
3. Human reviews the exact draft and handbook context:
   - Option A: Web Dashboard → Pending Approval → click ✓ Approve
   - Option B: Drag file from Pending_Approval/ → Approved/ in Finder
4. Agent executes and moves to Done/
```

---

## Scheduling
| Agent | Schedule | Method |
|---|---|---|
| Gmail Watcher | Polls every 2 minutes by default | launchd KeepAlive plist |
| Approval Watcher | Always running | launchd KeepAlive |
| Reasoning Loop | On demand | Auto-triggered by gmail_watcher |
| **Web Dashboard** | Always running in production, or manual locally | launchd plist or `cd dashboard && ../scripts/.venv/bin/python app.py` |

Production plist templates live in `launchd/*.plist.template`. Render them by replacing `__VAULT_DIR__` with the absolute vault path, then copy them to `~/Library/LaunchAgents/`.

---

## Shared Configuration
**File:** `scripts/config.py`
**Type:** Central Configuration Module

All agents import from this file. No hardcoded paths anywhere.

| Constant | Value |
|---|---|
| `VAULT_DIR` | Vault root path |
| `CREDENTIALS_PATH` | Gmail credentials.json |
| `TOKEN_PATH` | Gmail token.json |
| `NEEDS_ACTION` | Needs_Action/ folder |
| `PLANS` | Plans/ folder |
| `PENDING_APPROVAL` | Pending_Approval/ folder |
| `APPROVED` | Approved/ folder |
| `DONE` | Done/ folder |
| `FAILED` | Failed/ folder |
| `LOGS` | Logs/ folder |
| `PROCESSED_IDS` | processed_ids.json |
| `GROQ_MODEL` | llama-3.3-70b-versatile |
| `UNIVERSITY_HANDBOOK_PATH` | docs/University_Handbook.md |
| `AUTO_LINKEDIN_POSTS` | false by default |
| `DASHBOARD_APPROVAL_TOKEN` | Required in production for dashboard API access |
