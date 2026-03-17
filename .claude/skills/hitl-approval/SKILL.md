# HITL Approval Skill

This skill enables Human-in-the-Loop (HITL) approval workflows for various actions in the AI employee system.

## Overview
The HITL approval system allows humans to review and approve automated actions before they are executed. Files placed in the `Approved/` directory are processed based on their type and executed accordingly.

## Supported Action Types

### LinkedIn Post
- **Type**: `linkedin_post`
- **Location**: Place approved LinkedIn posts in the `Approved/` directory
- **Execution**: Calls the LinkedIn poster module to publish the content
- **Frontmatter required**:
  ```yaml
  type: linkedin_post
  ```

### Email Send
- **Type**: `email_send`
- **Location**: Place email drafts in the `Approved/` directory
- **Execution**: Sends email via Gmail API using stored credentials
- **Frontmatter required**:
  ```yaml
  type: email_send
  to: recipient@example.com
  subject: Email Subject
  ```

### Plan
- **Type**: `plan`
- **Location**: Place plan documents in the `Approved/` directory
- **Execution**: Simply moves to `Done/` directory (no execution needed)
- **Frontmatter required**:
  ```yaml
  type: plan
  ```

## Directory Structure
- `Approved/` - Place files here for processing
- `Done/` - Successfully processed files
- `Failed/` - Files that failed processing

## Processing Flow
1. Place a `.md` file with appropriate YAML frontmatter in the `Approved/` directory
2. The approval watcher detects the file and reads its type
3. Based on the type, the appropriate action is executed
4. After execution, the file is moved to either `Done/` or `Failed/` directory
5. All actions are logged to `/Logs/YYYY-MM-DD.json`

## Requirements
- Valid `credentials.json` and `token.json` in `scripts/scripts/`
- Properly formatted YAML frontmatter in `.md` files
- Required Python dependencies: `watchdog`, `PyYAML`, `google-auth`, `google-api-python-client`