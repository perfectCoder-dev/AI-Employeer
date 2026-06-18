# AI Employee — Safety & Guardrails

## Hard Rules (Never Violated)
1. NEVER send emails without human approval of the exact `draft_body`
2. NEVER post on LinkedIn without human approval  
3. NEVER delete files from the vault
4. NEVER store credentials in code or commit them to git
5. NEVER process more than 50 emails in one run
6. NEVER auto-approve — all actions require human moving file to Approved/
7. NEVER post on LinkedIn without human approval
8. NEVER post confidential client information on LinkedIn
9. NEVER post more than once per reasoning loop cycle
10. NEVER run production dashboard APIs without `DASHBOARD_APPROVAL_TOKEN`
11. NEVER remove `draft_body` fail-closed behavior from approved email execution

## Soft Rules (Best Effort)
1. Reply emails within 150 words
2. LinkedIn posts under 300 characters
3. Log every action to Logs/
4. Fall back to template reply if Groq API fails

## Risk Thresholds
| Action | Auto-Approve | Requires Human |
|---|---|---|
| Read email | ✅ | ❌ |
| Create Plan.md | ✅ | ❌ |
| Send email reply | ❌ | ✅ Always |
| Post on LinkedIn | ❌ | ✅ Always |
| Delete files | ❌ | ❌ Never |
| Generate LinkedIn post | ✅ Auto (AI writes it) | ❌ |
| Post on LinkedIn | ❌ | ✅ Always |

## Fallback Behaviors
- Groq API fails → use contextual template reply
- LinkedIn automation fails → queue post in linkedin_queue.json
- Gmail API fails → move file to Failed/, log error
- Unknown email type → move to Pending_Approval/ for human review
- Email send files without `draft_body` → move to Failed/ and do not generate after approval
- Duplicate `action_id` execution → skip and log as duplicate
- Dashboard token missing in production → fail startup / return service unavailable
- Duplicate Gmail note filename → create a unique filename instead of overwriting

## Audit Trail
All actions logged to: Logs/YYYY-MM-DD.json
Format: timestamp, action, filename, details, success
Retention: kept indefinitely (never auto-deleted)
