"""Central configuration for Personal AI Employee"""
from pathlib import Path

# Vault
VAULT_DIR = Path("/Users/muhammadomerfarooq/Desktop/AI_Employee_Vault")

# Credentials
CREDENTIALS_PATH = VAULT_DIR / "credentials" / "credentials.json"
TOKEN_PATH = VAULT_DIR / "credentials" / "token.json"

# Folders
NEEDS_ACTION = VAULT_DIR / "Needs_Action"
PLANS = VAULT_DIR / "Plans"
PENDING_APPROVAL = VAULT_DIR / "Pending_Approval"
APPROVED = VAULT_DIR / "Approved"
DONE = VAULT_DIR / "Done"
FAILED = VAULT_DIR / "Failed"
LOGS = VAULT_DIR / "Logs"
INBOX = VAULT_DIR / "Inbox"

# Scripts
SCRIPTS_DIR = VAULT_DIR / "scripts"
ENV_PATH = SCRIPTS_DIR / ".env"
PROCESSED_IDS = SCRIPTS_DIR / "processed_ids.json"

# Gmail
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

# Groq
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Timing
GMAIL_POLL_INTERVAL = 120  # seconds
