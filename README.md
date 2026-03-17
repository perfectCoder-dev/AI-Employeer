# 🤖 Personal AI Employee — Panaversity Hackathon 0

**Author:** Muhammad Umar Farooq  
**GitHub:** [omerfarooq223](https://github.com/omerfarooq223)  
**Tier:** Silver  
**Stack:** Claude Code + Obsidian + Python + Node.js + Gmail API

---

## What Is This?

A fully autonomous Personal AI Employee that monitors your Gmail, reasons about incoming tasks, waits for your approval, and takes real-world actions — all while you stay in control.

> "Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop."

---

## Architecture
```
Gmail → gmail_watcher.py → Needs_Action/
                                ↓
                        reasoning_loop.py → Plans/ + Pending_Approval/
                                                        ↓
                                              [YOU approve by moving file]
                                                        ↓
                                        approval_watcher.py → Gmail MCP → Real Email Sent → Done/
```

---

## Silver Tier Features

| Feature | Implementation |
|---|---|
| Gmail Watcher | Polls every 2 min, creates `.md` files in `Needs_Action/` |
| Approval Watcher | Watches `Approved/`, executes actions automatically |
| Claude Reasoning Loop | Analyzes emails, creates structured `Plan.md` files |
| Gmail Send MCP Server | Node.js MCP server, sends real emails via Gmail API |
| AI-Generated Replies | Uses Groq LLaMA 3.3 70B to write contextual email replies |
| HITL Approval Workflow | Human moves file to `Approved/` to trigger execution |
| LinkedIn Poster | Auto-posts via Playwright browser automation |
| Cron Scheduling | launchd plists run watchers on startup and every 2 min |
| Agent Skills | 4 SKILL.md files documenting all agent capabilities |

---

## Project Structure
```
personal-ai-employee/
│
├── CLAUDE.md                          # Claude Code instructions & rules
├── AGENTS.md                          # Agent documentation
├── README.md                          # Project overview & setup guide
├── Company_Handbook.md                # AI decision-making context
├── Dashboard.md                       # Live activity dashboard
├── .gitignore
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
│   ├── gmail_watcher.py               # Polls Gmail every 2 minutes
│   ├── linkedin_poster.py             # Auto-posts to LinkedIn via Playwright
│   ├── reasoning_loop.py              # Claude brain, creates Plan.md files
│   ├── approval_watcher.py            # HITL orchestrator
│   ├── authenticate_gmail.py          # Gmail OAuth setup
│   ├── main.py                        # Entry point, runs all agents
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

### 1. Clone the repo
```bash
git clone https://github.com/omerfarooq223/AI_Employee_Vault
cd AI_Employee_Vault
```

### 2. Install Python dependencies
```bash
cd scripts
uv sync
```

### 3. Set up Gmail OAuth
Place your `credentials.json` from Google Cloud Console in `scripts/`, then:
```bash
cd scripts
.venv/bin/python authenticate_gmail.py
```
Complete the browser OAuth flow. `token.json` will be created.

### 4. Install MCP server dependencies
```bash
cd mcp-servers/gmail-send
npm install
```

### 5. Set up environment variables
```bash
# scripts/.env
LINKEDIN_ACCESS_TOKEN=your_token_here
```

### 6. Start the watchers
```bash
# Load launchd agents (runs on startup automatically)
launchctl load ~/Library/LaunchAgents/com.aiemployee.gmailwatcher.plist
launchctl load ~/Library/LaunchAgents/com.aiemployee.approvalwatcher.plist
```

---

## How It Works — End to End

1. **Email arrives** in `purposework56@gmail.com`
2. **`gmail_watcher.py`** detects it and creates a `.md` file in `Needs_Action/`
3. **`reasoning_loop.py`** analyzes the email using `Company_Handbook.md` context, creates a `Plan.md` in `Plans/`, moves original to `Pending_Approval/`
4. **You review** the plan in Obsidian and drag the file to `Approved/`
5. **`approval_watcher.py`** detects the approval, sends a real reply email via Gmail API
6. File moves to `Done/`, action logged to `Logs/YYYY-MM-DD.json`

---

## Human-in-the-Loop (HITL)

No sensitive action is ever taken without human approval. The workflow:
```
AI proposes → Human decides → AI executes
```

To **approve**: move file from `Pending_Approval/` → `Approved/`  
To **reject**: move file from `Pending_Approval/` → `Rejected/`

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
- **linkedin-poster** — queues LinkedIn posts for review
- **reasoning-loop** — analyzes tasks, creates structured plans
- **hitl-approval** — orchestrates human approval workflow

---

## Demo Video

[Link to demo video]

---

## Submission

Hackathon: [Panaversity Personal AI Employee Hackathon 0](https://forms.gle/JR9T1SJq5rmQyGkGA)  
Tier: **Silver**