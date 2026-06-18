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
from config import VAULT_DIR, CREDENTIALS_PATH, TOKEN_PATH, NEEDS_ACTION, PLANS, PENDING_APPROVAL, APPROVED, DONE, FAILED, LOGS, PROCESSED_IDS, ENV_PATH
from datetime import datetime
import re
from email_drafts import create_email_approval_artifact, generate_email_reply, read_company_handbook
from handbook_knowledge import CATEGORY_KEYWORDS, classify_university_email
from workflow_utils import append_log, move_file, read_markdown_with_frontmatter


def categorize_email_by_content(content):
    """Classify email into university department categories."""
    return classify_university_email(content)


def calculate_priority_score(content, sender_importance=1):
    """Calculate priority score based on multiple factors"""
    score = 0

    # Urgency indicators (+ points)
    urgency_terms = ['urgent', 'asap', 'immediately', 'today', 'deadline', 'critical', 'as soon as possible', 'right away']
    score += sum(10 for term in urgency_terms if term.lower() in content.lower())

    # Importance indicators (+ points)
    importance_terms = ['ceo', 'manager', 'executive', 'important', 'priority', 'vip', 'decision maker']
    score += sum(5 for term in importance_terms if term.lower() in content.lower())

    # Meeting/request indicators (+ points)
    request_terms = ['meeting', 'call', 'schedule', 'proposal', 'quote', 'urgent response']
    score += sum(3 for term in request_terms if term.lower() in content.lower())

    # Question indicators (+ points)
    question_count = len(re.findall(r'\?', content))
    score += question_count * 2

    # Length factor (longer emails might be more detailed/important)
    score += min(len(content.split()) // 100, 5)  # Max 5 points for length

    # Apply sender importance multiplier
    final_score = score * sender_importance

    # Convert to priority level
    if final_score >= 20:
        return "high", final_score
    elif final_score >= 10:
        return "medium", final_score
    else:
        return "low", final_score


def create_plan_based_on_advanced_rules(content, handbook_context, original_filename):
    """
    Create a plan using enhanced rule-based logic with advanced categorization and priority scoring.
    """
    import re

    category = classify_university_email(content)

    # Determine urgency
    urgency, priority_score = calculate_priority_score(content)

    # Check for informational indicators
    content_lower = content.lower()
    informational_indicators = [
        'no action needed',
        'for reference',
        'just for info',
        'informational',
        'as a note',
        'fyi',
        'newsletter',
        'announcement only',
    ]
    is_informational = any(indicator in content_lower for indicator in informational_indicators)

    # Determine if action is required
    question_or_request = '?' in content or any(
        keyword in content_lower
        for keyword in [
            'please',
            'kindly',
            'can i',
            'can you',
            'how do',
            'what is',
            'when',
            'where',
            'need',
            'request',
            'help',
            'eligible',
            'allowed',
        ]
    )
    action_required = question_or_request and not is_informational

    # Create more specific steps based on identified patterns
    steps = generate_contextual_steps(category, content)

    # Create summary based on content
    lines = content.split('\n')
    summary_lines = [line.strip() for line in lines if line.strip()][:3]  # First few non-empty lines
    summary = ' '.join(summary_lines)[:200]  # Limit length

    if len(content) > 200:
        summary += "..."

    return {
        "summary": summary,
        "steps": steps,
        "action_required": "yes" if action_required else "no",
        "action_type": "email_send" if action_required else "manual",
        "category": category,
        "priority": urgency,
        "priority_score": priority_score
    }


def generate_contextual_steps(action_type, content):
    """Generate steps based on detected action type"""
    base_steps = [
        "Identify the student's specific academic or administrative question",
        "Retrieve the relevant undergraduate handbook policy section",
        "Prepare a concise department reply grounded in the handbook"
    ]

    if action_type in CATEGORY_KEYWORDS:
        base_steps.append(f"Classified as: {action_type.replace('_', ' ')}")
    if action_type == 'general_inquiry':
        base_steps.append("Ask for missing student/program details if the handbook does not answer it")

    base_steps.append("Document outcome and close the task")
    return base_steps


def create_plan_based_on_rules(content, handbook_context, original_filename):
    """
    Create a plan using smart rule-based logic (fallback when no API key available).
    """
    # Use the enhanced rule-based system
    return create_plan_based_on_advanced_rules(content, handbook_context, original_filename)


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
priority: {plan_data.get('priority', 'medium')}
priority_score: {plan_data.get('priority_score', 0)}
action_type: {plan_data.get('action_type', 'manual')}
action_required: {plan_data.get('action_required', 'no')}
category: {plan_data.get('category', 'general_inquiry')}
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

## Priority Details
Priority Level: {plan_data.get('priority', 'medium')}
Priority Score: {plan_data.get('priority_score', 0)}
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


def log_detailed_action(action, filename, details=None, vault_dir=None):
    """Enhanced logging with more details"""
    if vault_dir is None:
        vault_dir = VAULT_DIR

    today = datetime.now().strftime('%Y-%m-%d')
    logs_dir = vault_dir / 'Logs'
    logs_dir.mkdir(exist_ok=True)

    log_file = logs_dir / f"{today}_detailed.json"

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "filename": filename,
        "details": details,
        "duration": None,  # Will be calculated if timing
        "success": True,   # Will be updated if needed
        "processed_by": "AI_Employee"
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
            logs = []

    logs.append(log_entry)

    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2)


def log_action(action, filename, details=None, vault_dir=None):
    """Log the action to a daily log file."""
    append_log(action, filename, details)


def process_needs_action_files():
    """Main function to process all files in Needs_Action/ directory. Returns list of processed file data."""
    vault_dir = VAULT_DIR
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
    handbook_content = read_company_handbook()
    processed_files = []

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

            # Track processed file
            processed_files.append({
                'filename': file_path.name,
                'category': plan_data.get('action_type', 'general'),
                'action_type': plan_data.get('action_type', 'general'),
                'priority': plan_data.get('priority', 'medium')
            })

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
                if plan_data['action_type'] == 'email_send':
                    draft_body = generate_email_reply(
                        original_content=content,
                        original_subject=frontmatter.get('subject', file_path.stem),
                        original_from=frontmatter.get('from', ''),
                        handbook_context=handbook_content,
                    )
                    approval_path = create_email_approval_artifact(
                        source_file=file_path,
                        original_frontmatter=frontmatter,
                        original_body=content,
                        draft_body=draft_body,
                    )
                    new_location = move_file(file_path, DONE)
                    print(f"Created approval draft: {approval_path.name}")
                    print(f"Archived source email to Done/: {new_location.name}")

                    log_action(
                        action='approval_draft_created',
                        filename=approval_path.name,
                        details={
                            'source_file': file_path.name,
                            'destination': str(approval_path),
                            'action_type': plan_data['action_type'],
                            'category': plan_data.get('category'),
                        },
                        vault_dir=vault_dir
                    )
                else:
                    # Non-email actions are already exact artifacts, so route them for review.
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

    return processed_files

def main():
    """Main entry point."""
    print("Starting Claude Reasoning Loop...")
    process_needs_action_files()
    print("Reasoning Loop completed!")


if __name__ == "__main__":
    main()
