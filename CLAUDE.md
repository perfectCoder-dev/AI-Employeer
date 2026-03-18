# Personal AI Employee - Claude Code Instructions

## IMPORTANT: Read This First
When asked to "run the pipeline" or "check inbox" or any similar request,
Claude should follow the AUTONOMOUS WORKFLOW below WITHOUT asking for instructions.
All decisions should be made based on this file alone.

## Project Overview
This is a Personal AI Employee. It monitors Gmail, reasons about tasks,
and takes actions with human approval. You are the AI brain of this system.

## Vault Location
/Users/muhammadomerfarooq/Desktop/AI_Employee_Vault

## Python Interpreter
Always use: /Users/muhammadomerfarooq/Desktop/AI_Employee_Vault/.venv/bin/python
Never use: python or python3 directly

## AUTONOMOUS WORKFLOW
When triggered, follow these steps IN ORDER without asking for confirmation:

### Step 1: Clear processed IDs (only if inbox check returns 0 emails)
```bash
echo "[]" > /Users/muhammadomerfarooq/Desktop/AI_Employee_Vault/scripts/processed_ids.json
```

### Step 2: Run Gmail Watcher
```bash
cd /Users/muhammadomerfarooq/Desktop/AI_Employee_Vault
.venv/bin/python scripts/gmail_watcher.py
```
- Wait for "Processed X new emails" for 15 seconds
- If 0 emails found, clear processed_ids.json and run again within 15 seconds
- New .md files will appear in Needs_Action/
- Proceed to take Step 3 (Reasoning Loop) if news emails are found within 10 secs after the emails were found

### Step 3: Run Reasoning Loop
```bash
cd /Users/muhammadomerfarooq/Desktop/AI_Employee_Vault
.venv/bin/python scripts/reasoning_loop.py
```
- Analyzes emails with enhanced rule-based system and smart categorization
- Creates Plan.md files in Plans/ with priority scoring
- Automatically categorizes emails (sales, support, meetings, networking, informational)
- Calculates priority scores based on urgency and importance
- Moves files to Pending_Approval/ if action needed
- Moves files to Done/ if informational

### Step 4: Report to Human (HITL)
- Tell the human: "I found X emails and created X plans"
- List each file now in Pending_Approval/
- Say: "Please move files from Pending_Approval/ to Approved/ to approve"
- Wait for human confirmation before proceeding

### Step 5: Run Approval Watcher
```bash
cd /Users/muhammadomerfarooq/Desktop/AI_Employee_Vault
.venv/bin/python scripts/approval_watcher.py
```
- This watches Approved/ and executes actions
- For emails: generates Groq AI reply and sends via Gmail
- For LinkedIn: posts via Playwright browser automation
- Files move to Done/ when complete

### Step 6: Report Results
- Show what emails were sent
- Show what LinkedIn posts were published
- Show the log entry in Logs/YYYY-MM-DD.json

## Key File Locations
- Scripts: /Users/muhammadomerfarooq/Desktop/AI_Employee_Vault/scripts/
- Credentials: /Users/muhammadomerfarooq/Desktop/AI_Employee_Vault/credentials/
- Environment: /Users/muhammadomerfarooq/Desktop/AI_Employee_Vault/scripts/.env
- Processed IDs: /Users/muhammadomerfarooq/Desktop/AI_Employee_Vault/scripts/processed_ids.json

## Rules Claude Must Follow
1. NEVER take irreversible actions without human approval
2. ALWAYS run steps in the order defined above
3. ALWAYS use the .venv/bin/python interpreter
4. ALWAYS work from the vault root directory
5. NEVER commit credentials.json, token.json, or .env
6. If a script fails, read the error and fix it before continuing
7. If 0 emails found, clear processed_ids.json and retry once
8. For email replies: Enhanced contextual analysis generates appropriate replies (with optional Groq LLaMA 3.3 70B enhancement)
9. For LinkedIn: Playwright browser automation handles posting
10. Enhanced reasoning: Smart categorization and priority scoring for better task management
11. NEVER ask the human what to do — figure it out from this file

## Agent Skills
Read these files to understand each agent:
- .claude/skills/gmail-watcher/SKILL.md
- .claude/skills/linkedin-poster/SKILL.md
- .claude/skills/reasoning-loop/SKILL.md
- .claude/skills/hitl-approval/SKILL.md

## MCP Server
Gmail Send MCP is at mcp-servers/gmail-send/index.js
Start with: node mcp-servers/gmail-send/index.js
Tool available: send_email(to, subject, body)
