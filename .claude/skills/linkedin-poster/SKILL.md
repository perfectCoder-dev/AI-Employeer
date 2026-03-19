# LinkedIn Poster Skill

## Overview
Automatically posts to LinkedIn based on business activity detected by the reasoning loop.
The AI generates the post content — humans only approve or reject.

## Trigger
Auto-triggered by reasoning_loop.py when business emails are processed.
Never requires human to write post content.

## Input
A `.md` file in `Pending_Approval/` with this format:
```
---
type: linkedin_post
title: "Post title"
created: [timestamp]
---

Post content here...
#hashtag1 #hashtag2
```

## Output
- Live post published on LinkedIn
- File moved to `Done/`
- Action logged to `Logs/YYYY-MM-DD.json`
- On failure: post queued in `Logs/linkedin_queue.json`

## How It Works
1. reasoning_loop.py detects business activity in emails
2. Groq LLaMA 3.3 70B generates relevant post content
3. File created in `Pending_Approval/` automatically
4. Human drags to `Approved/` to approve
5. approval_watcher.py calls this skill
6. Playwright launches Chromium browser
7. Logs into LinkedIn using credentials from `.env`
8. Navigates to feed → clicks "Start a post"
9. Types content → clicks Post
10. Browser closes → file moved to Done/

## Fallback
If Playwright fails:
- Post queued in `Logs/linkedin_queue.json` with status: queued_for_manual_post
- Dashboard.md updated with notification

## Credentials Required
In `scripts/.env`:
- `LINKEDIN_EMAIL`
- `LINKEDIN_PASSWORD`

## Script
`scripts/linkedin_poster.py`
