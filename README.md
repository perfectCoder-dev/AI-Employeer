# 🤖 Personal AI Employee — Panaversity Hackathon 0

**Author:** Muhammad Umar Farooq  
**GitHub:** [omerfarooq223](https://github.com/omerfarooq223)  
**Tier:** Silver  
**Stack:** Claude Code + Obsidian + Python + Flask + Node.js + Gmail API + Groq LLaMA 3.3 70B

---

## What Is This?

A fully autonomous Personal AI Employee that monitors your Gmail, reasons about incoming tasks, waits for your approval, and takes real-world actions — all while you stay in control.

> "Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop."

---

## Architecture
```
[launchd] Every 2 min:
gmail_watcher.py → detects email → Needs_Action/
                                        ↓ (auto-triggers)
                                reasoning_loop.py → Plans/ + Pending_Approval/
                                                              ↓
                                                    [HUMAN: drag to Approved/]
                                                              ↓
[launchd] Always running:                                     ↓
approval_watcher.py ←────────────────────────────────────────┘
        ↓                    ↓
Groq AI reply sent     LinkedIn posted
        ↓                    ↓
                         Done/

```
---

## Silver Tier Features

| Feature | Implementation |
|---|---|
| Gmail Watcher | Polls every 2 min, creates `.md` files in `Needs_Action/` |
| Approval Watcher | Watches `Approved/`, executes actions automatically |
| Claude Reasoning Loop | Analyzes emails with enhanced rule-based system, creates structured `Plan.md` files with priority scoring |
| Gmail Send MCP Server | Node.js MCP server, sends real emails via Gmail API |
| AI-Generated Replies | Uses enhanced contextual analysis to write appropriate email replies (with Groq LLaMA 3.3 70B as optional enhancement) |
| HITL Approval Workflow | Human moves file to `Approved/` to trigger execution |
| LinkedIn Auto-Poster | AI generates posts from business activity → Playwright auto-posts |
| Cron Scheduling | launchd plists run watchers on startup and every 2 min |
| Agent Skills | 4 SKILL.md files documenting all agent capabilities |
| Smart Prioritization | Automatic priority scoring based on urgency indicators, importance, and content analysis |
| Enhanced Categorization | Intelligent email classification into sales, support, meetings, networking, and informational categories |
| **Web Dashboard** | Flask + vanilla JS/CSS dashboard at `http://localhost:5000` — live KPIs, one-click approve/reject, activity timeline |

---

## Project Structure
```
personal-ai-employee/
│
├── CLAUDE.md                          # Claude Code instructions & rules
├── AGENTS.md                          # Agent documentation
├── README.md                          # Project overview & setup guide
├── .gitignore
│
├── dashboard/                         # ✨ Web Dashboard (Flask)
│   ├── app.py                         # REST API server (8 endpoints)
│   └── static/
│       ├── index.html                 # Single-page dashboard app
│       ├── style.css                  # Dark glassmorphism UI
│       └── app.js                     # Live data + approve/reject logic
│
├── docs/
│   ├── Company_Handbook.md            # AI decision-making context
│   ├── Dashboard.md                   # Obsidian dashboard overview
│   ├── GUARDRAILS.md                  # Safety rules and risk thresholds
│   └── DEPLOYMENT.md                  # Deployment config and service management
│
├── .claude/
│   ├── settings.local.json
│   └── skills/
│       ├── gmail-watcher/
│       │   └── SKILL.md               # Gmail watcher skill docs
│       ├── linkedin-poster/
│       │   └── SKILL.md               # LinkedIn poster skill docs
│       ├── reasoning-loop/
│       │   └── SKILL.md               # Reasoning loop skill docs
│       └── hitl-approval/
│           └── SKILL.md               # HITL approval skill docs
│
├── scripts/
│   ├── config.py                      # Central configuration — all paths and constants
│   ├── gmail_watcher.py               # Polls Gmail, auto-triggers reasoning loop
│   ├── reasoning_loop.py              # Claude brain — creates Plan.md + LinkedIn posts
│   ├── approval_watcher.py            # HITL orchestrator — sends emails, posts LinkedIn
│   ├── linkedin_poster.py             # Playwright browser automation for LinkedIn
│   ├── authenticate_gmail.py          # Gmail OAuth setup
│   ├── main.py                        # Entry point, runs all agents
│   ├── test_pipeline.py               # Basic pipeline tests
│   ├── .env.example                   # Environment variables template
│   ├── pyproject.toml                 # Python dependencies
│   └── uv.lock
│
├── mcp-servers/
│   └── gmail-send/
│       ├── index.js                   # Gmail Send MCP server
│       ├── package.json
│       └── package-lock.json
│
├── credentials/                       # Never committed — in .gitignore
│   ├── credentials.json               # Gmail OAuth app credentials
│   └── token.json                     # Gmail user token
│
├── Inbox/                             # Raw incoming items
├── Needs_Action/                      # Watcher drops files here
├── Plans/                             # reasoning_loop creates Plan.md here
├── Pending_Approval/                  # Awaiting human approval
├── Approved/                          # Human moves files here to approve
├── Done/                              # Completed tasks
├── Rejected/                          # Rejected tasks
├── Failed/                            # Error files
└── Logs/                              # Daily JSON action logs
```

---

## Setup Instructions

### Prerequisites
- Python 3.13+
- Node.js v22+
- Claude Code
- Gmail account with OAuth credentials
- Groq API key (free at console.groq.com)
- LinkedIn account

### 1. Clone the repo
```bash
git clone https://github.com/omerfarooq223/personal-ai-employee
cd personal-ai-employee
```

### 2. Install Python dependencies
```bash
cd scripts
uv sync
.venv/bin/playwright install chromium
```

### 3. Set up Gmail OAuth
Place your `credentials.json` from Google Cloud Console in `credentials/`, then:
```bash
cd scripts
.venv/bin/python authenticate_gmail.py
```
Complete the browser OAuth flow. `token.json` will be created in `credentials/`.

### 4. Install MCP server dependencies
```bash
cd mcp-servers/gmail-send
npm install
```

### 5. Set up environment variables
```bash
# Copy the example file
cp scripts/.env.example scripts/.env

# Fill in your credentials
LINKEDIN_EMAIL=your_linkedin_email
LINKEDIN_PASSWORD=your_linkedin_password
GROQ_API_KEY=your_groq_api_key
```

### 6. Start the watchers
```bash
# Load launchd agents (runs on startup automatically)
launchctl load ~/Library/LaunchAgents/com.aiemployee.gmailwatcher.plist
launchctl load ~/Library/LaunchAgents/com.aiemployee.approvalwatcher.plist
```

### 7. Launch the Web Dashboard
```bash
cd dashboard
python3 app.py
# → open http://127.0.0.1:5000 in your browser
```

### 8. Or run everything manually
```bash
cd personal-ai-employee

# Terminal 1 - Approval watcher
.venv/bin/python scripts/approval_watcher.py

# Terminal 2 - Gmail watcher
.venv/bin/python scripts/gmail_watcher.py

# Terminal 3 - Reasoning loop (when emails arrive)
.venv/bin/python scripts/reasoning_loop.py

# Terminal 4 - Web Dashboard
cd dashboard && python3 app.py
```

---

## How It Works — End-to-End Flow

1. **Email Inbound:** A new message arrives in the Gmail inbox.
2. **Detection:** `gmail_watcher.py` (running every 2 min via `launchd`) detects it automatically.
3. **Trigger:** `gmail_watcher.py` auto-triggers `reasoning_loop.py` immediately.
4. **AI Processing:** `reasoning_loop.py` analyzes the email and performs two actions:
    * Creates `Plan.md` and moves it to `Pending_Approval/`.
    * Auto-generates a LinkedIn post based on the detected business activity.
5. **Human Gatekeeper:** > 💡 **Manual Step:** You drag the file from `Pending_Approval/` to `Approved/`. This is the **only** manual interaction required.
6. **Approval Detection:** `approval_watcher.py` (always running via `launchd`) detects the file move instantly.
7. **Execution:** **Groq LLaMA 3.3 70B** generates the contextual reply, which is sent via the Gmail API.
8. **Cleanup:** The file is moved to `Done/` and the entire action is logged to `Logs/`.

---

## Human-in-the-Loop (HITL)

No sensitive action is ever taken without human approval. The workflow:
```
AI proposes → Human decides → AI executes
```

**Via Web Dashboard (recommended):**  
Open `http://127.0.0.1:5000` → click **Pending Approval** → click **✓ Approve** or **✗ Reject**

**Via file system:**  
To **approve**: move file from `Pending_Approval/` → `Approved/`  
To **reject**: move file from `Pending_Approval/` → `Rejected/`

---

## Technology Stack — How Each Is Used

| Technology | How It's Used |
|---|---|
| **Claude Code** | Primary AI brain — reads vault, runs reasoning loop, fixes errors autonomously |
| **Python 3.13** | All watcher scripts and agent logic |
| **Flask + Vanilla JS** | Web dashboard — live KPIs, approve/reject UI, activity log at `localhost:5000` |
| **Groq LLaMA 3.3 70B** | Generates contextual email replies and LinkedIn post content |
| **Gmail API** | Reads inbox, sends replies, marks emails as read |
| **Playwright** | Browser automation for LinkedIn posting |
| **Node.js MCP** | Gmail Send MCP server — exposes send_email tool to Claude Code |
| **Obsidian** | Local markdown vault — secondary view of all agent activity |
| **launchd** | macOS service manager — keeps watchers running 24/7 |
| **uv** | Fast Python package manager for dependency management |

---

## Security

- `credentials.json`, `token.json`, `.env` are in `.gitignore` — never committed
- All data stored locally in Obsidian vault
- No third-party cloud storage
- Payments and irreversible actions always require human approval

---

## Agent Skills

All AI functionality is documented as Claude Agent Skills in `.claude/skills/`:

- **gmail-watcher** — monitors Gmail, creates action items
- **linkedin-poster** — auto-posts to LinkedIn via Playwright
- **reasoning-loop** — analyzes tasks, creates structured plans
- **hitl-approval** — orchestrates human approval workflow

---

## Web Dashboard

A purpose-built command center for monitoring and controlling all agents.

**Start:**
```bash
cd dashboard && python3 app.py
# → http://127.0.0.1:5000
```

**Views:**

| View | What you see |
|---|---|
| Dashboard | 6 live KPI cards, agent pipeline diagram, recent activity, action breakdown chart |
| Pending Approval | All items awaiting approval — one-click ✓ Approve / ✗ Reject |
| Needs Action | Items currently queued for AI processing |
| Done | Successfully completed emails and LinkedIn posts |
| Plans | All AI-generated action plans with priority and steps |
| Activity Log | Full audit timeline from daily JSON logs |
| Failed | Items that encountered errors — for debugging |

**API endpoints** (`dashboard/app.py`):

| Endpoint | Method | Description |
|---|---|---|
| `/api/stats` | GET | KPI counts + action breakdown + recent activity |
| `/api/folder/<key>` | GET | List any workflow folder |
| `/api/file/<folder>/<name>` | GET | Read a single markdown file (parsed frontmatter + body) |
| `/api/approve/<name>` | POST | Move file `Pending_Approval/` → `Approved/` |
| `/api/reject/<name>` | POST | Move file `Pending_Approval/` → `Rejected/` |
| `/api/logs` | GET | All entries from daily JSON log files |
| `/api/agent-log` | GET | Last 200 lines of `agent.log` |
| `/api/all-items` | GET | Every item across all folders (for timeline view) |