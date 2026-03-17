#!/usr/bin/env python3
"""
Claude "brain" - Reasoning Loop Script

This script scans .md files in Needs_Action/, analyzes them using company handbook context,
and creates Plan.md files in Plans/. It then moves the original files based on whether
action is required.
"""

import os
import yaml
import json
import shutil
from pathlib import Path
from datetime import datetime
import re


def read_markdown_with_frontmatter(file_path):
    """Read a markdown file and extract YAML frontmatter and content."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if content.startswith('---'):
        # Find the end of YAML frontmatter
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter_str = parts[1].strip()
            markdown_content = parts[2].strip()

            try:
                frontmatter = yaml.safe_load(frontmatter_str)
                return frontmatter, markdown_content
            except yaml.YAMLError as e:
                print(f"Error parsing YAML frontmatter: {e}")
                return {}, content

    return {}, content


def read_company_handbook(vault_dir):
    """Read the company handbook for context."""
    handbook_path = vault_dir / 'Company_Handbook.md'
    if handbook_path.exists():
        with open(handbook_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


def create_plan_based_on_rules(content, handbook_context, original_filename):
    """
    Create a plan using smart rule-based logic (fallback when no API key available).
    """
    # Basic rule-based analysis
    content_lower = content.lower()

    # Check for informational indicators first
    informational_indicators = ['no action needed', 'for reference', 'just for info', 'informational', 'as a note']
    is_informational = any(indicator in content_lower for indicator in informational_indicators)

    # Determine if action is required based on content
    action_keywords = ['email', 'send', 'contact', 'reach out', 'reply', 'response', 'linkedin', 'post', 'share', 'urgent', 'important', 'need to', 'required', 'request', 'ask']
    action_required = any(keyword in content_lower for keyword in action_keywords) and not is_informational

    # Determine action type if required
    action_type = "manual"  # default

    if ('email' in content_lower or 'send' in content_lower or 'contact' in content_lower or
        'reply' in content_lower or 'schedule' in content_lower or 'meeting' in content_lower or
        'availability' in content_lower or 'let me know' in content_lower or 'please' in content_lower):
        action_type = "email_send"
    elif 'linkedin' in content_lower or 'post' in content_lower:
        action_type = "linkedin_post"

    # Create summary based on content
    lines = content.split('\n')
    summary_lines = [line.strip() for line in lines if line.strip()][:3]  # First few non-empty lines
    summary = ' '.join(summary_lines)[:200]  # Limit length

    if len(content) > 200:
        summary += "..."

    # Create recommended steps based on content
    steps = []

    if action_type == "email_send":
        steps.extend([
            "Review the email content and recipient details",
            "Draft appropriate response considering company guidelines",
            "Send the email after approval"
        ])
    elif action_type == "linkedin_post":
        steps.extend([
            "Review the post content for appropriateness",
            "Ensure it aligns with company messaging",
            "Schedule or publish the LinkedIn post"
        ])
    else:
        if is_informational:
            steps.extend([
                "Review the information for awareness",
                "File appropriately for reference",
                "No further action required"
            ])
        else:
            steps.extend([
                "Analyze the content thoroughly",
                "Follow company guidelines as outlined in handbook",
                "Take appropriate action based on requirements"
            ])

    # Add a generic step
    steps.append("Document the outcome and close the task")

    return {
        "summary": summary,
        "steps": steps,
        "action_required": "yes" if action_required else "no",
        "action_type": action_type
    }


def create_plan_file(original_file_path, plan_data, vault_dir):
    """Create a Plan.md file based on the analysis."""
    # Generate plan filename
    original_name = original_file_path.stem
    plan_filename = f"PLAN_{original_name}.md"
    plan_path = vault_dir / 'Plans' / plan_filename

    # Ensure Plans directory exists
    (vault_dir / 'Plans').mkdir(exist_ok=True)

    # Create the plan content
    plan_content = f"""---
type: plan
source_file: {original_file_path.name}
created: {datetime.now().isoformat()}
status: pending
---
## Task Summary
{plan_data['summary']}

## Recommended Steps
"""

    for i, step in enumerate(plan_data['steps'], 1):
        plan_content += f"{i}. {step}\n"

    plan_content += f"""
## Action Required
{plan_data['action_required']}  # Type: {plan_data['action_type']}
"""

    # Write the plan file
    with open(plan_path, 'w', encoding='utf-8') as f:
        f.write(plan_content)

    return plan_path


def move_file_to_destination(source_path, destination_subdir, vault_dir):
    """Move a file to the specified destination folder."""
    dest_path = vault_dir / destination_subdir / source_path.name
    dest_path.parent.mkdir(exist_ok=True)
    shutil.move(str(source_path), str(dest_path))
    return dest_path


def log_action(action, filename, details=None, vault_dir=None):
    """Log the action to a daily log file."""
    if vault_dir is None:
        vault_dir = Path("/Users/muhammadomerfarooq/Desktop/AI_Employee_Vault")

    today = datetime.now().strftime('%Y-%m-%d')
    logs_dir = vault_dir / 'Logs'
    logs_dir.mkdir(exist_ok=True)

    log_file = logs_dir / f"{today}.json"

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "filename": filename,
        "details": details
    }

    # Read existing log or create new one
    logs = []
    if log_file.exists():
        try:
            with open(log_file, 'r') as f:
                content = f.read().strip()
                if content:
                    logs = json.loads(content)
                    if not isinstance(logs, list):
                        logs = []
        except (json.JSONDecodeError, ValueError):
            # File is corrupted — reset it
            logs = []

    logs.append(log_entry)

    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2)


def process_needs_action_files():
    """Main function to process all files in Needs_Action/ directory."""
    vault_dir = Path("/Users/muhammadomerfarooq/Desktop/AI_Employee_Vault")
    needs_action_dir = vault_dir / 'Needs_Action'

    if not needs_action_dir.exists():
        print(f"Error: {needs_action_dir} does not exist")
        return

    # Get all .md files in Needs_Action directory
    md_files = list(needs_action_dir.glob('*.md'))

    if not md_files:
        print("No .md files found in Needs_Action/")
        return

    print(f"Found {len(md_files)} files to process")

    # Read company handbook for context
    handbook_content = read_company_handbook(vault_dir)

    for file_path in md_files:
        try:
            print(f"Processing: {file_path.name}")

            # Read the file content and frontmatter
            frontmatter, content = read_markdown_with_frontmatter(file_path)

            # Create plan using rule-based system
            plan_data = create_plan_based_on_rules(content, handbook_content, file_path.name)

            # Create plan file
            plan_path = create_plan_file(file_path, plan_data, vault_dir)
            print(f"Created plan: {plan_path.name}")

            # Log the plan creation
            log_action(
                action='plan_created',
                filename=file_path.name,
                details={
                    'plan_file': plan_path.name,
                    'action_required': plan_data['action_required'],
                    'action_type': plan_data['action_type']
                },
                vault_dir=vault_dir
            )

            # Move original file based on action required
            if plan_data['action_required'] == 'yes':
                # Move to Pending_Approval/
                new_location = move_file_to_destination(file_path, 'Pending_Approval', vault_dir)
                print(f"Moved {file_path.name} to Pending_Approval/")

                log_action(
                    action='file_moved_to_approval',
                    filename=file_path.name,
                    details={'destination': str(new_location)},
                    vault_dir=vault_dir
                )
            else:
                # Move to Done/
                new_location = move_file_to_destination(file_path, 'Done', vault_dir)
                print(f"Moved {file_path.name} to Done/")

                log_action(
                    action='file_moved_to_done',
                    filename=file_path.name,
                    details={'destination': str(new_location)},
                    vault_dir=vault_dir
                )

        except Exception as e:
            print(f"Error processing {file_path.name}: {str(e)}")

            # Log the error
            log_action(
                action='processing_error',
                filename=file_path.name,
                details={'error': str(e)},
                vault_dir=vault_dir
            )


def main():
    """Main entry point."""
    print("Starting Claude Reasoning Loop...")
    process_needs_action_files()
    print("Reasoning Loop completed!")


if __name__ == "__main__":
    main()