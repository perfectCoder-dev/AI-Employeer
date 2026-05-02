"""
Central configuration for Personal AI Employee.

This module:
1. Loads paths from environment variables (with sensible defaults)
2. Validates all paths and credentials on startup
3. Creates missing folders automatically
4. Provides clear error messages if something is misconfigured
5. Supports multiple environments (dev, test, prod)

Usage:
    from config import setup_logging, validate_config
    
    # At startup, ALWAYS call this:
    validate_config()
    
    # Then use paths confidently:
    email_file = config.NEEDS_ACTION / "email_123.md"
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# CORE PATHS — Read from environment, fallback to defaults
# ============================================================================

VAULT_DIR = Path(os.getenv(
    "VAULT_DIR",
    Path.home() / "Desktop" / "omer" / "AI_Employee_Vault"
)).expanduser().resolve()

SCRIPTS_DIR = Path(os.getenv(
    "SCRIPTS_DIR",
    VAULT_DIR / "scripts"
)).expanduser().resolve()

# ============================================================================
# CREDENTIALS — Must exist and be readable
# ============================================================================

CREDENTIALS_PATH = VAULT_DIR / "credentials" / "credentials.json"
TOKEN_PATH = VAULT_DIR / "credentials" / "token.json"

# ============================================================================
# WORKFLOW FOLDERS — Created automatically if missing
# ============================================================================

# Raw incoming items (before processing)
INBOX = VAULT_DIR / "Inbox"

# After gmail_watcher.py detects an email and auto-triggers reasoning
NEEDS_ACTION = VAULT_DIR / "Needs_Action"

# reasoning_loop.py creates Plan.md here and puts file here
PLANS = VAULT_DIR / "Plans"

# HITL: awaiting human approval (you drag to Approved/)
PENDING_APPROVAL = VAULT_DIR / "Pending_Approval"

# HITL: you manually moved file here to approve execution
APPROVED = VAULT_DIR / "Approved"

# approval_watcher.py moves file here after execution
DONE = VAULT_DIR / "Done"

# approval_watcher.py moves file here if rejection detected
REJECTED = VAULT_DIR / "Rejected"

# approval_watcher.py moves file here if execution failed
FAILED = VAULT_DIR / "Failed"

# Daily JSON logs of all actions taken
LOGS = VAULT_DIR / "Logs"

# All workflow folders (used for validation and creation)
WORKFLOW_FOLDERS = [
    INBOX, NEEDS_ACTION, PLANS, PENDING_APPROVAL, 
    APPROVED, DONE, REJECTED, FAILED, LOGS
]

# ============================================================================
# SCRIPT-SPECIFIC PATHS
# ============================================================================

# Tracks which Gmail message IDs have been processed (prevents duplicates)
PROCESSED_IDS = SCRIPTS_DIR / "processed_ids.json"

# Environment file (contains secrets like GROQ_API_KEY, LinkedIn credentials)
ENV_PATH = SCRIPTS_DIR / ".env"

# ============================================================================
# GMAIL CONFIGURATION
# ============================================================================

# OAuth scopes needed to read inbox, send emails, and mark as read
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

# How often gmail_watcher.py polls Gmail (in seconds)
GMAIL_POLL_INTERVAL = int(os.getenv("GMAIL_POLL_INTERVAL", "120"))

# Gmail query to find emails that need action
GMAIL_QUERY = "is:inbox -is:archived -is:spam newer_than:1d"

# ============================================================================
# LLM CONFIGURATION — Groq (for email reply generation)
# ============================================================================

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Must be set in .env

# ============================================================================
# LINKEDIN CONFIGURATION
# ============================================================================

LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
LOG_FILE = LOGS / "agent.log"

# ============================================================================
# TIMEOUTS & RETRY CONFIGURATION (defensive against flaky services)
# ============================================================================

GMAIL_TIMEOUT = int(os.getenv("GMAIL_TIMEOUT", "10"))
GMAIL_RETRIES = int(os.getenv("GMAIL_RETRIES", "3"))
GMAIL_RETRY_DELAY = float(os.getenv("GMAIL_RETRY_DELAY", "2"))

# ============================================================================
# ENVIRONMENT DETECTION
# ============================================================================

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_DEBUG = ENVIRONMENT == "development"

# ============================================================================
# VALIDATION & STARTUP
# ============================================================================

def setup_logging() -> logging.Logger:
    """Configure logging to both file and console."""
    logger = logging.getLogger("ai_employee")
    logger.setLevel(LOG_LEVEL)
    
    formatter = logging.Formatter(LOG_FORMAT)
    
    # File handler
    try:
        LOGS.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setLevel(LOG_LEVEL)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"⚠️  WARNING: Could not set up file logging: {e}")
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def validate_config() -> bool:
    """Validate all configuration at startup."""
    logger = logging.getLogger("ai_employee")
    logger.info("=" * 70)
    logger.info("🚀 AI EMPLOYEE STARTUP VALIDATION")
    logger.info("=" * 70)
    
    errors = []
    warnings = []
    
    # VAULT DIRECTORY
    logger.info(f"📁 Vault: {VAULT_DIR}")
    
    if not VAULT_DIR.exists():
        errors.append(f"❌ VAULT_DIR does not exist: {VAULT_DIR}")
    elif not VAULT_DIR.is_dir():
        errors.append(f"❌ VAULT_DIR is not a directory: {VAULT_DIR}")
    elif not os.access(VAULT_DIR, os.R_OK | os.W_OK):
        errors.append(f"❌ No read/write permission on VAULT_DIR: {VAULT_DIR}")
    else:
        logger.info("✅ Vault directory accessible")
    
    # WORKFLOW FOLDERS (create if missing)
    logger.info("📂 Workflow folders:")
    
    for folder in WORKFLOW_FOLDERS:
        try:
            folder.mkdir(parents=True, exist_ok=True)
            if not os.access(folder, os.W_OK):
                errors.append(f"❌ No write permission: {folder}")
            else:
                logger.info(f"   ✅ {folder.name}")
        except Exception as e:
            errors.append(f"❌ Could not create {folder}: {e}")
    
    # CREDENTIALS
    logger.info("🔐 Credentials:")
    
    if not CREDENTIALS_PATH.exists():
        errors.append(
            f"❌ credentials.json missing: {CREDENTIALS_PATH}\n"
            f"   → Run: python scripts/authenticate_gmail.py"
        )
    else:
        logger.info(f"   ✅ credentials.json exists")
        try:
            with open(CREDENTIALS_PATH, 'r') as f:
                json.load(f)
            logger.info(f"   ✅ credentials.json is valid JSON")
        except json.JSONDecodeError as e:
            errors.append(f"❌ credentials.json is corrupted: {e}")
    
    if TOKEN_PATH.exists():
        logger.info(f"   ✅ token.json exists (already authorized)")
    else:
        warnings.append(
            f"⚠️  token.json missing (you'll need to authenticate)\n"
            f"   → Run: python scripts/authenticate_gmail.py"
        )
    
    # ENVIRONMENT VARIABLES
    logger.info("🔑 Secrets:")
    
    if not GROQ_API_KEY:
        errors.append(
            f"❌ GROQ_API_KEY not set in {ENV_PATH}\n"
            f"   → Get free key at https://console.groq.com"
        )
    else:
        logger.info(f"   ✅ GROQ_API_KEY is set")
    
    if LINKEDIN_EMAIL and LINKEDIN_PASSWORD:
        logger.info(f"   ✅ LinkedIn credentials are set")
    else:
        warnings.append(
            "⚠️  LinkedIn credentials not set\n"
            "   → LinkedIn auto-posting will be disabled"
        )
    
    # CONFIGURATION VALIDITY
    logger.info("⚙️  Configuration:")
    
    if GMAIL_POLL_INTERVAL <= 0:
        errors.append(
            f"❌ GMAIL_POLL_INTERVAL must be > 0, got: {GMAIL_POLL_INTERVAL}"
        )
    elif GMAIL_POLL_INTERVAL < 60:
        warnings.append(
            f"⚠️  GMAIL_POLL_INTERVAL is very fast ({GMAIL_POLL_INTERVAL}s)\n"
            f"   → Risk of hitting Gmail API rate limits"
        )
    else:
        logger.info(f"   ✅ Poll interval: {GMAIL_POLL_INTERVAL}s")
    
    if ENVIRONMENT not in ["development", "test", "production"]:
        warnings.append(f"⚠️  Unknown ENVIRONMENT: {ENVIRONMENT}")
    else:
        logger.info(f"   ✅ Environment: {ENVIRONMENT}")
    
    # SUMMARY
    logger.info("=" * 70)
    
    if warnings:
        logger.warning(f"\n⚠️  {len(warnings)} WARNING(S):")
        for w in warnings:
            logger.warning(f"   {w}\n")
    
    if errors:
        logger.error(f"\n❌ {len(errors)} CRITICAL ERROR(S):")
        for e in errors:
            logger.error(f"   {e}\n")
        logger.error("=" * 70)
        sys.exit(1)
    
    logger.info("✅ ALL CHECKS PASSED — System ready to run\n")
    logger.info("=" * 70)
    return True


def load_processed_ids() -> set:
    """Load the set of processed Gmail message IDs."""
    if not PROCESSED_IDS.exists():
        return set()
    
    try:
        with open(PROCESSED_IDS, 'r') as f:
            data = json.load(f)
            return set(data.get("ids", []))
    except (json.JSONDecodeError, IOError) as e:
        logging.getLogger("ai_employee").warning(
            f"Could not load processed_ids.json: {e}. Starting fresh."
        )
        return set()


def save_processed_ids(ids: set) -> None:
    """Save the set of processed Gmail message IDs."""
    try:
        PROCESSED_IDS.parent.mkdir(parents=True, exist_ok=True)
        with open(PROCESSED_IDS, 'w') as f:
            json.dump({"ids": list(ids)}, f, indent=2)
    except IOError as e:
        logging.getLogger("ai_employee").error(
            f"Could not save processed_ids.json: {e}"
        )


if __name__ == "__main__":
    logger = setup_logging()
    validate_config()
