#!/usr/bin/env python3
"""
Basic pipeline tests for Personal AI Employee
"""
import json
import yaml
from pathlib import Path

VAULT_DIR = Path("/Users/muhammadomerfarooq/Desktop/AI_Employee_Vault")

def test_vault_structure():
    """Test all required folders exist"""
    required_folders = ['Needs_Action', 'Plans', 'Pending_Approval', 
                       'Approved', 'Done', 'Failed', 'Logs', 'Inbox']
    for folder in required_folders:
        assert (VAULT_DIR / folder).exists(), f"Missing folder: {folder}"
    print("✅ Vault structure OK")

def test_credentials_exist():
    """Test credentials are in place"""
    assert (VAULT_DIR / 'credentials' / 'credentials.json').exists(), "Missing credentials.json"
    assert (VAULT_DIR / 'credentials' / 'token.json').exists(), "Missing token.json"
    print("✅ Credentials OK")

def test_env_file():
    """Test .env has required keys"""
    env_path = VAULT_DIR / 'scripts' / '.env'
    assert env_path.exists(), "Missing .env file"
    content = env_path.read_text()
    assert 'LINKEDIN_EMAIL' in content, "Missing LINKEDIN_EMAIL"
    assert 'LINKEDIN_PASSWORD' in content, "Missing LINKEDIN_PASSWORD"
    assert 'GROQ_API_KEY' in content, "Missing GROQ_API_KEY"
    print("✅ Environment variables OK")

def test_reasoning_loop():
    """Test reasoning loop creates correct plan"""
    import sys
    sys.path.insert(0, str(VAULT_DIR / 'scripts'))
    from reasoning_loop import create_plan_based_on_rules

    test_content = "Please send an email to the client about the project proposal"
    plan = create_plan_based_on_rules(test_content, "", "test.md")
    assert plan['action_required'] == 'yes', "Should require action"
    assert plan['action_type'] == 'email_send', "Should be email_send type"
    print("✅ Reasoning loop OK")

def test_mcp_server_exists():
    """Test MCP server files exist"""
    assert (VAULT_DIR / 'mcp-servers' / 'gmail-send' / 'index.js').exists()
    assert (VAULT_DIR / 'mcp-servers' / 'gmail-send' / 'package.json').exists()
    print("✅ MCP server OK")

def test_skills_exist():
    """Test all SKILL.md files exist"""
    skills = ['gmail-watcher', 'linkedin-poster', 'reasoning-loop', 'hitl-approval']
    for skill in skills:
        path = VAULT_DIR / '.claude' / 'skills' / skill / 'SKILL.md'
        assert path.exists(), f"Missing SKILL.md for {skill}"
    print("✅ Agent skills OK")

if __name__ == "__main__":
    print("Running AI Employee pipeline tests...\n")
    test_vault_structure()
    test_credentials_exist()
    test_env_file()
    test_reasoning_loop()
    test_mcp_server_exists()
    test_skills_exist()
    print("\n✅ All tests passed!")
