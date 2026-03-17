# Reasoning Loop Skill

The Claude "brain" - analyzes tasks and creates plans automatically.

## Description
The reasoning loop is an AI-powered task processing system that acts as Claude's "brain". It continuously monitors the `Needs_Action/` directory, analyzes incoming tasks using company context, and creates structured plans for execution.

## Functionality
- Scans all .md files in `Needs_Action/` directory
- Reads file content and YAML frontmatter
- Incorporates company handbook context for decision-making
- Generates structured Plan.md files with recommendations
- Routes tasks appropriately based on action requirements

## Processing Logic
1. **Input**: Reads markdown files from `Needs_Action/`
2. **Analysis**: Uses rule-based intelligence (with potential Anthropic API integration) to analyze content
3. **Planning**: Creates structured plans with:
   - Task summary
   - Recommended steps
   - Action requirements classification
4. **Routing**: Moves original files to appropriate destinations:
   - `Pending_Approval/` if action required (email, LinkedIn post, manual task)
   - `Done/` if informational only

## Action Types
- `email_send`: Requires sending an email
- `linkedin_post`: Requires creating a LinkedIn post
- `manual`: Requires manual intervention

## File Structure
- Input: `/Needs_Action/*.md`
- Output: `/Plans/PLAN_[original_name].md`
- Routing: `/Pending_Approval/` or `/Done/`
- Logging: `/Logs/[date].json`

## Usage
Simply place task files in `Needs_Action/` and the reasoning loop will automatically process them, create plans, and route them appropriately.