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


def categorize_email_by_content(content):
    """Classify email into specific categories"""
    categories = {
        'sales_inquiry': ['web development', 'project proposal', 'service offering', 'quote', 'pricing', 'estimate', 'collaboration', 'business opportunity', 'proposal'],
        'support_issue': ['problem', 'issue', 'bug', 'error', 'trouble', 'help', 'support', 'fix', 'broken', 'not working'],
        'networking': ['connect', 'linkedin', 'network', 'introduction', 'opportunity', 'collaboration', 'meet', 'relationship'],
        'meeting_request': ['meeting', 'call', 'schedule', 'appointment', 'calendar', 'availability', 'zoom', 'teams', 'discuss'],
        'informational': ['thank you', 'appreciate', 'nice to meet', 'follow up', 'update', 'just saying hi']
    }

    content_lower = content.lower()
    scores = {}

    for category, keywords in categories.items():
        score = sum(1 for keyword in keywords if keyword in content_lower)
        scores[category] = score

    # Return the highest scoring category
    return max(scores, key=scores.get) if max(scores.values()) > 0 else 'general'


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

    # Enhanced pattern matching
    patterns = {
        'urgent_indicators': [
            r'\burgen(t|cy|cies)',
            r'asap',
            r'as soon as possible',
            r'by end of (day|week|month)',
            r'immediately',
            r'within (\d+) (hours|days)',
            r'critical',
            r'high priority',
            r'expedited'
        ],
        'meeting_requests': [
            r'(schedule|book|set up|arrange) (a )?meeting',
            r'available for (a )?call',
            r'when (are you|can we) talk',
            r'sync up',
            r'catch up',
            r'zoom|teams|call',
            r'calendar',
            r'free (slot|time|time slot)',
            r'appointment'
        ],
        'project_inquiries': [
            r'web development',
            r'project proposal',
            r'service offering',
            r'quote|pricing|cost|estimate',
            r'estimate',
            r'collaboration',
            r'partnership',
            r'business opportunity',
            r'development work'
        ],
        'social_media': [
            r'linkedin (post|share|article)',
            r'social media',
            r'content creation',
            r'brand awareness',
            r'post idea',
            r'publish content'
        ]
    }

    # Score content against patterns
    scores = {}
    for category, regex_list in patterns.items():
        score = 0
        for pattern in regex_list:
            matches = re.findall(pattern, content.lower(), re.IGNORECASE)
            score += len(matches)
        scores[category] = score

    # Determine action type based on highest scoring category
    action_type = max(scores, key=scores.get) if max(scores.values()) > 0 else "manual"

    # Determine urgency
    urgency, priority_score = calculate_priority_score(content)

    # Determine action type mapping
    action_type_mapping = {
        'urgent_indicators': 'email_send',
        'meeting_requests': 'email_send',
        'project_inquiries': 'email_send',
        'social_media': 'linkedin_post',
        'manual': 'manual'
    }

    final_action_type = action_type_mapping.get(action_type, 'manual')

    # Check for informational indicators
    content_lower = content.lower()
    informational_indicators = ['no action needed', 'for reference', 'just for info', 'informational', 'as a note']
    is_informational = any(indicator in content_lower for indicator in informational_indicators)

    # Determine if action is required
    action_keywords = ['email', 'send', 'contact', 'reach out', 'reply', 'response', 'linkedin', 'post', 'share', 'urgent', 'important', 'need to', 'required', 'request', 'ask']
    action_required = any(keyword in content_lower for keyword in action_keywords) and not is_informational

    # Create more specific steps based on identified patterns
    steps = generate_contextual_steps(action_type, content)

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
        "action_type": final_action_type,
        "priority": urgency,
        "priority_score": priority_score
    }


def generate_contextual_steps(action_type, content):
    """Generate steps based on detected action type"""
    base_steps = [
        "Analyze the request details thoroughly",
        "Reference company handbook for guidelines",
        "Prepare appropriate response/action"
    ]

    if action_type == 'urgent_indicators':
        base_steps.extend([
            "Prioritize this request due to urgency indicators",
            "Respond within 24 hours as specified",
            "Escalate if needed"
        ])
    elif action_type == 'meeting_requests':
        base_steps.extend([
            "Check calendar availability",
            "Propose suitable meeting times",
            "Send calendar invite once agreed"
        ])
    elif action_type == 'project_inquiries':
        base_steps.extend([
            "Review project requirements",
            "Prepare project proposal if appropriate",
            "Coordinate with relevant team members"
        ])
    elif action_type == 'social_media':
        base_steps.extend([
            "Review content for brand alignment",
            "Schedule for optimal posting time",
            "Monitor engagement after posting"
        ])

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
        vault_dir = Path("/Users/muhammadomerfarooq/Desktop/AI_Employee_Vault")

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
    """Main function to process all files in Needs_Action/ directory. Returns list of processed file data."""
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

    return processed_files


def generate_linkedin_post(vault_dir, handbook_content, processed_files):
    """Auto-generate a LinkedIn post based on business activity."""
    if not processed_files:
        return

    # Build post based on recent business activity
    topics = []
    for f in processed_files:
        category = f.get('category', 'general')
        if category == 'sales_inquiry':
            topics.append("client inquiries")
        elif category == 'meeting_request':
            topics.append("business meetings")
        elif category == 'project_inquiries':
            topics.append("new projects")

    if not topics:
        return

    # Try Groq API for post generation
    post_content = None
    try:
        import requests
        import os
        from dotenv import load_dotenv
        load_dotenv(vault_dir / 'scripts' / '.env')
        groq_key = os.getenv('GROQ_API_KEY')

        if groq_key:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {
                            "role": "system",
                            "content": f"""You are a professional LinkedIn content writer.
Write a short, engaging LinkedIn post to generate business leads.
Keep it under 200 words. Include 3-5 relevant hashtags.
Base it on the company context provided.
Company context: {handbook_content[:300]}"""
                        },
                        {
                            "role": "user",
                            "content": f"Write a LinkedIn post about our business activity today. We handled: {', '.join(set(topics))}. Make it professional and engaging to attract potential clients."
                        }
                    ],
                    "temperature": 0.8,
                    "max_tokens": 300
                },
                timeout=10
            )
            if response.status_code == 200:
                post_content = response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"Groq API failed for LinkedIn post: {e}")

    # Fallback post
    if not post_content:
        topic_str = ' and '.join(set(topics))
        post_content = f"""Staying busy with {topic_str} today! 

Our team is committed to delivering excellent results for every client inquiry we receive.

If you're looking for professional services, we'd love to hear from you.

#Business #ProfessionalServices #AI #Automation #BuildingInPublic"""

    # Create the LinkedIn post file in Pending_Approval/
    today = datetime.now().strftime('%Y%m%d_%H%M%S')
    post_filename = f"linkedin_post_{today}.md"
    post_path = vault_dir / 'Pending_Approval' / post_filename

    post_content_md = f"""---
type: linkedin_post
title: "Auto-generated LinkedIn Post"
created: {datetime.now().isoformat()}
---

{post_content}"""

    with open(post_path, 'w', encoding='utf-8') as f:
        f.write(post_content_md)

    print(f"Auto-generated LinkedIn post: {post_filename}")
    print("Move from Pending_Approval/ to Approved/ to post on LinkedIn")


def main():
    """Main entry point."""
    print("Starting Claude Reasoning Loop...")
    processed_files = process_needs_action_files()
    print("Reasoning Loop completed!")

    # Auto-generate LinkedIn post if emails were processed
    if processed_files:
        vault_dir = Path("/Users/muhammadomerfarooq/Desktop/AI_Employee_Vault")
        handbook_content = read_company_handbook(vault_dir)
        generate_linkedin_post(vault_dir, handbook_content, processed_files)


if __name__ == "__main__":
    main()