# University Department Agent

This deployment is configured for a university department inbox.

## Knowledge Base

- Source PDF: `Handbook Undergraduate Studies 2025-26 150126.pdf`
- Extracted knowledge file: `docs/University_Handbook.md`
- Runtime setting: `UNIVERSITY_HANDBOOK_PATH`

The extracted file preserves page markers, so draft approvals can show which handbook pages informed the reply.

## Email Flow

1. `gmail_watcher.py` reads unread department emails and creates markdown files in `Needs_Action/`.
2. `reasoning_loop.py` classifies each message into academic categories such as registration, attendance, semester freeze, withdrawal, exams, fees/refunds, scholarships, discipline, hostel, library/IT, or grievance.
3. `handbook_knowledge.py` retrieves relevant handbook pages.
4. `email_drafts.py` creates an exact `email_send` approval artifact in `Pending_Approval/`.
5. A human reviews the draft reply and handbook context.
6. `approval_watcher.py` sends only the approved `draft_body`.

## Safety Rules

- The executor must not generate a new email after approval.
- Approved email files without `draft_body` are moved to `Failed/`.
- Duplicate `action_id`s are skipped.
- Gmail watcher filenames include the Gmail message ID and use unique paths to prevent overwrites.
- If the handbook does not answer the question, the draft asks for department verification instead of inventing policy.
- LinkedIn posting is disabled by default with `AUTO_LINKEDIN_POSTS=false`.
- Production dashboard access requires `DASHBOARD_APPROVAL_TOKEN`.

## Production Dashboard Access

Set `DASHBOARD_APPROVAL_TOKEN` in `scripts/.env`. The dashboard prompts for this token in the browser and sends it as `X-Approval-Token` for API requests.

## Updating The Handbook

Replace `docs/University_Handbook.md` by re-extracting the updated PDF, or set `UNIVERSITY_HANDBOOK_PATH` to another extracted handbook markdown file.
