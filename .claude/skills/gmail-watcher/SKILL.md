# Gmail Watcher Skill

## Description
The Gmail Watcher skill monitors your Gmail account for unread important emails and automatically creates Obsidian notes for them in the Needs_Action folder. This allows your AI employee to process important emails as tasks in your workflow system.

## Prerequisites
1. Google Cloud Project with Gmail API enabled
2. Downloaded `credentials.json` file from Google Cloud Console
3. Place the `credentials.json` file in the credentials/ folder at the project root

## Setup Instructions
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API for your project
4. Create credentials (OAuth 2.0 Client IDs) for a desktop application
5. Download the credentials file and rename it to `credentials.json`
6. Place `credentials.json` in the credentials/ folder at the project root

## How to Invoke
```bash
# Run the Gmail watcher directly
uv run gmail-watcher

# Or from the scripts directory
cd scripts && python gmail_watcher.py
```

## Functionality
- Polls Gmail every 2 minutes for unread important emails
- Creates Markdown notes in the Needs_Action folder with YAML frontmatter
- Tracks processed emails to avoid duplicates
- Logs all activity to the Logs folder
- Automatically marks emails as read after processing

## YAML Frontmatter Fields
- `type`: Always set to 'email'
- `from`: Sender's email address
- `subject`: Email subject line
- `received`: Timestamp when email was received
- `priority`: Set to 'high' if email is marked as important
- `status`: Set to 'needs-action' for processing
- `original_email_id`: Original Gmail message ID

## Dependencies
- google-auth
- google-auth-oauthlib
- google-api-python-client
- watchdog
- pyyaml
- python-dotenv