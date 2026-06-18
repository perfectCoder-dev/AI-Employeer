# Personal AI Employee — Dashboard

## Web Dashboard (Primary)

A real-time browser-based command center for monitoring and controlling all agents.

**URL:** `http://127.0.0.1:5000`

**Start:**
```bash
cd dashboard && ../scripts/.venv/bin/python app.py
```

Production deployments should set `DASHBOARD_APPROVAL_TOKEN`. When it is set, the browser prompts for the token and sends it as `X-Approval-Token` for all API requests.

### Views

| View | What you see |
|---|---|
| **Dashboard** | 6 KPI cards, agent pipeline diagram, recent activity feed, action breakdown chart |
| **Pending Approval** | All items awaiting your decision — one-click ✓ Approve or ✗ Reject |
| **Needs Action** | Items currently queued for AI processing |
| **Done** | Successfully completed emails and LinkedIn posts |
| **Plans** | All AI-generated action plans with priority, steps, and action type |
| **Activity Log** | Full chronological audit trail from `Logs/*.json` |
| **Failed** | Items that encountered errors — for debugging |

### HITL Approval (via Dashboard)

1. Open `http://127.0.0.1:5000`
2. Enter `DASHBOARD_APPROVAL_TOKEN` if prompted
3. Click **Pending Approval** in the sidebar
4. Review the exact draft/action, then click **✓ Approve** — file moves to `Approved/`, `approval_watcher.py` executes it
5. Or click **✗ Reject** — file moves to `Rejected/`, no action taken

### API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/stats` | GET | KPIs, action breakdown, recent activity |
| `/api/folder/<key>` | GET | List a workflow folder (`pending_approval`, `done`, `plans`, etc.) |
| `/api/file/<folder>/<name>` | GET | Read a markdown file (parsed frontmatter + body) |
| `/api/approve/<name>` | POST | Move `Pending_Approval/` → `Approved/` |
| `/api/reject/<name>` | POST | Move `Pending_Approval/` → `Rejected/` |
| `/api/logs` | GET | All entries from daily JSON log files |
| `/api/agent-log` | GET | Last 200 lines of `agent.log` |
| `/api/all-items` | GET | Every item across all workflow folders |

When `DASHBOARD_APPROVAL_TOKEN` is set, every endpoint requires the `X-Approval-Token` header. In production, startup fails if the token is missing.

---

## Obsidian Dashboard (Secondary)

For browsing vault files visually in Obsidian.

- [[Inbox]] — Raw incoming items
- [[Needs_Action]] — Tasks requiring attention
- [[Pending_Approval]] — Awaiting human review
- [[Approved]] — Green-lit tasks
- [[Done]] — Completed work
- [[Rejected]] — Discontinued tasks
- [[Failed]] — Tasks that encountered errors
- [[Plans]] — AI-generated action plans
- [[Logs]] — Daily JSON action logs

## Daily Checklist

- [ ] Open web dashboard at `http://127.0.0.1:5000`
- [ ] Enter dashboard token if prompted
- [ ] Review and action items in **Pending Approval**
- [ ] Check **Failed** for any script errors
- [ ] Review **Activity Log** for overnight activity

## Reference & Documentation

- [[AGENTS|System Documentation]]
- [[DEPLOYMENT|Deployment Config]]
- [[GUARDRAILS|System Guardrails]]
- [[University_Handbook|University Handbook]]
- [[UNIVERSITY_AGENT|University Agent Notes]]

Production note: set `DASHBOARD_APPROVAL_TOKEN` to require `X-Approval-Token` on dashboard read and write requests.
