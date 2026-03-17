# AI Employee Watcher Scripts

This package contains automated watcher scripts for the Personal AI Employee Obsidian vault system.

## Purpose
These scripts monitor the vault for changes and automatically process tasks according to the defined workflow:
- Watch for new files in the Inbox
- Process files based on their content and metadata
- Move processed files through the workflow (Needs Action → Pending Approval → Approved/Done/Rejected)

## Installation
```bash
uv sync
```

## Running the Watcher
```bash
uv run vault-watcher
```