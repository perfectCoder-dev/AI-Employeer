#!/usr/bin/env python3
"""
HITL Approval Watcher - Watches the Approved/ directory and executes actions based on file types.
"""

import os
import sys
import json
import yaml
import shutil
import logging
import datetime
import re
from dotenv import load_dotenv
load_dotenv('/Users/muhammadomerfarooq/Desktop/AI_Employee_Vault/scripts/.env')
from pathlib import Path
from config import VAULT_DIR, CREDENTIALS_PATH, TOKEN_PATH, NEEDS_ACTION, PLANS, PENDING_APPROVAL, APPROVED, DONE, FAILED, LOGS, PROCESSED_IDS, ENV_PATH
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import mimetypes

# Add the scripts directory to the path so we can import other modules
sys.path.insert(0, '/Users/muhammadomerfarooq/Desktop/AI_Employee_Vault/scripts')
os.chdir('/Users/muhammadomerfarooq/Desktop/AI_Employee_Vault/scripts')

# Import the LinkedIn poster module
try:
    from linkedin_poster import process_markdown_file
    print("LinkedIn poster imported successfully!")
except ImportError as e:
    print(f"Warning: Could not import linkedin_poster: {e}. LinkedIn functionality will be disabled.")
    process_markdown_file = None


def categorize_email_by_content(content):
    """Classify email into specific categories"""
    categories = {
        'sales_inquiry': ['web development', 'project proposal', 'service offering', 'quote', 'pricing', 'estimate', 'collaboration', 'business opportunity', 'proposal', 'development work'],
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


def generate_contextual_reply(original_content, original_subject, original_from, handbook_context):
    """Generate more contextual email replies without API"""

    # Extract key information from the original email
    # Determine tone based on sender's language
    formal_indicators = ['dear', 'regards', 'sincerely', 'respectfully', 'hello', 'good morning', 'good afternoon']
    casual_indicators = ['hi', 'hey', 'thanks', 'awesome', 'cool', 'sounds good']

    is_formal = any(indicator in original_content.lower() for indicator in formal_indicators)
    is_casual = any(indicator in original_content.lower() for indicator in casual_indicators)

    # Get sender name
    name_match = re.search(r'^([A-Za-z\s]+)(?:\s*<|$)', original_from)
    sender_name = name_match.group(1).strip().split()[0] if name_match else "there"

    # Generate reply based on content category
    category = categorize_email_by_content(original_content)

    # Template-based response generation
    templates = {
        'sales_inquiry': {
            'formal': f"""Dear {sender_name},

Thank you for your inquiry regarding "{original_subject}". I appreciate you reaching out about this opportunity.

I will review your requirements and prepare a detailed proposal for you. Our team specializes in delivering high-quality solutions tailored to client needs.

I will follow up with you within 24-48 hours with more specific information.

Best regards,
AI Employee Assistant""",
            'casual': f"""Hi {sender_name},

Thanks for reaching out about "{original_subject}"! We'd love to hear more about your project and see how we can help.

I'm putting together a detailed proposal based on your requirements and will send it over soon. Looking forward to potentially working together!

Best,
AI Employee Assistant"""
        },
        'support_issue': {
            'formal': f"""Dear {sender_name},

Thank you for bringing this matter to our attention. We take all support requests seriously and appreciate you providing the details about "{original_subject}".

Our technical team will investigate the issue and provide a resolution as quickly as possible. You can expect an initial response within 24 hours.

We apologize for any inconvenience this may have caused.

Best regards,
AI Employee Assistant""",
            'casual': f"""Hi {sender_name},

Thanks for letting us know about the issue with "{original_subject}". We're looking into it right away!

Someone will reach out with a solution shortly. Thanks for your patience as we get this sorted out.

Best,
AI Employee Assistant"""
        },
        'meeting_request': {
            'formal': f"""Dear {sender_name},

Thank you for your interest in scheduling a meeting regarding "{original_subject}". I appreciate you reaching out.

I will check our calendar availability and propose suitable meeting times for discussion. Please allow 24-48 hours for confirmation.

Looking forward to our conversation.

Best regards,
AI Employee Assistant""",
            'casual': f"""Hi {sender_name},

Thanks for wanting to connect about "{original_subject}"! I'll check our schedule and get back to you with some available time slots soon.

Appreciate your interest in connecting with us!

Best,
AI Employee Assistant"""
        },
        'networking': {
            'formal': f"""Dear {sender_name},

Thank you for reaching out and expressing interest in connecting. I appreciate you contacting us regarding "{original_subject}".

I will review your connection request and respond accordingly. Thank you for your interest in our services.

Best regards,
AI Employee Assistant""",
            'casual': f"""Hi {sender_name},

Thanks for reaching out! Appreciate the connection interest regarding "{original_subject}".

Happy to explore potential synergies. Looking forward to learning more about your interests.

Best,
AI Employee Assistant"""
        },
        'informational': {
            'formal': f"""Dear {sender_name},

Thank you for your message regarding "{original_subject}". I appreciate you keeping us informed.

Your information has been noted and will be kept on file for reference. Thank you for sharing this with us.

Best regards,
AI Employee Assistant""",
            'casual': f"""Hi {sender_name},

Thanks for sharing this information about "{original_subject}". Appreciate you keeping us in the loop!

Have a great day!

Best,
AI Employee Assistant"""
        }
    }

    # Get appropriate template based on category and tone
    template_category = templates.get(category, templates.get('sales_inquiry'))  # Default fallback

    if is_casual or (not is_formal and is_casual):  # If casual or neutral, use casual
        return template_category['casual']
    else:
        return template_category['formal']


class ApprovalWatcher(FileSystemEventHandler):
    def __init__(self, approved_dir, done_dir, failed_dir):
        self.approved_dir = Path(approved_dir)
        self.done_dir = Path(done_dir)
        self.failed_dir = Path(failed_dir)

        # Create destination directories if they don't exist
        self.done_dir.mkdir(parents=True, exist_ok=True)
        self.failed_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self.setup_logging()

    def setup_logging(self):
        """Setup logging to stdout only — JSON log file is managed separately."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def on_created(self, event):
        """Handle file creation events in the watched directory."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only process .md files
        if file_path.suffix.lower() == '.md':
            self.process_file(file_path)

    def on_moved(self, event):
        """Handle file move events in the watched directory."""
        if event.is_directory:
            return

        # Handle files that are moved into the directory
        dest_path = Path(event.dest_path)
        if dest_path.suffix.lower() == '.md':
            self.process_file(dest_path)

    def send_gmail(self, to, subject, body):
        """Send email using Gmail API with stored credentials."""
        try:
            # Load credentials and token from scripts directory
            import os
            credentials_path = CREDENTIALS_PATH
            token_path = TOKEN_PATH

            if not credentials_path.exists():
                raise FileNotFoundError(f"Credentials file not found: {credentials_path}")

            if not token_path.exists():
                raise FileNotFoundError(f"Token file not found: {token_path}")

            # Load the token
            creds = Credentials.from_authorized_user_file(str(token_path), ['https://www.googleapis.com/auth/gmail.send'])

            # Refresh credentials if they are expired
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())

            # Build the Gmail service
            service = build('gmail', 'v1', credentials=creds)

            # Create the email message
            import base64
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            message.attach(MIMEText(body, 'plain'))

            raw_message = message.as_string()
            encoded_message = base64.urlsafe_b64encode(raw_message.encode()).decode()

            # Send the email
            send_message = service.users().messages().send(
                userId="me",
                body={'raw': encoded_message}
            ).execute()

            self.logger.info(f"Email sent successfully. Message ID: {send_message['id']}")
            return True

        except Exception as e:
            self.logger.error(f"Error sending email: {str(e)}")
            raise

    def process_file(self, file_path):
        """Process a newly created or moved .md file."""
        self.logger.info(f"Processing file: {file_path}")

        try:
            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse YAML frontmatter
            if content.startswith('---'):
                end_frontmatter = content.find('---', 3)
                if end_frontmatter != -1:
                    frontmatter_str = content[3:end_frontmatter].strip()
                    try:
                        frontmatter = yaml.safe_load(frontmatter_str)
                        action_type = frontmatter.get('type', '').lower()
                    except yaml.YAMLError as e:
                        self.logger.error(f"Error parsing YAML frontmatter in {file_path}: {e}")
                        self.move_to_failed(file_path)
                        return
                else:
                    self.logger.error(f"No closing --- found in frontmatter of {file_path}")
                    self.move_to_failed(file_path)
                    return
            else:
                self.logger.error(f"No YAML frontmatter found in {file_path}")
                self.move_to_failed(file_path)
                return

            # Route based on action type
            if action_type == 'linkedin_post':
                if process_markdown_file:
                    self.logger.info(f"Executing LinkedIn post for {file_path}")
                    success = process_markdown_file(str(file_path))
                    # linkedin_poster.py handles file moving internally
                    # so we don't need to move it again here
                    if not success:
                        if file_path.exists():
                            self.move_to_failed(file_path)
                else:
                    self.logger.error(f"LinkedIn poster module not available for {file_path}")
                    if file_path.exists():
                        self.move_to_failed(file_path)

            elif action_type in ('email_send', 'email', 'email_request', 'email_action'):
                self.logger.info(f"Sending email for {file_path}")

                # Extract email details from frontmatter
                to = frontmatter.get('to')
                # Auto-detect sender if 'to' is missing
                if not to:
                    from_field = frontmatter.get('from', '')
                    import re as re2
                    match = re2.search(r'<(.+?)>', from_field)
                    to = match.group(1) if match else from_field

                subject = frontmatter.get('subject', 'Re: No Subject')
                # Add Re: prefix if not already there
                if not subject.startswith('Re:'):
                    subject = f"Re: {subject}"

                if not to:
                    self.logger.error(f"Missing 'to' in frontmatter of {file_path}")
                    self.move_to_failed(file_path)
                    return

                # Build a contextual reply using Groq API
                original_subject = frontmatter.get('subject', '')
                original_from = frontmatter.get('from', '')

                # Extract sender name
                import re as re3
                name_match = re3.match(r'^([^<]+)', original_from)
                sender_name = name_match.group(1).strip().split()[0] if name_match else "there"

                # Extract email body content
                email_body = content[content.find("**Email Content:**"):].replace("**Email Content:**", "").strip() if "**Email Content:**" in content else content

                # Try Groq API first
                body = None
                try:
                    import requests as req
                    groq_key = os.getenv('GROQ_API_KEY')
                    if groq_key:
                        handbook_path = Path("/Users/muhammadomerfarooq/Desktop/AI_Employee_Vault/Company_Handbook.md")
                        handbook = handbook_path.read_text() if handbook_path.exists() else ""

                        response = req.post(
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
                                        "content": f"""You are a professional AI Employee assistant.
Write a helpful, specific, and professional email reply.
Use the company context below to personalize your response.
Keep it under 150 words. Be warm and specific to their inquiry.
Sign off as 'AI Employee Assistant' from purposework56@gmail.com.

Company Context:
{handbook[:500]}"""
                                    },
                                    {
                                        "role": "user",
                                        "content": f"""Write a reply to this email:
Subject: {original_subject}
From: {original_from}

{email_body}"""
                                    }
                                ],
                                "temperature": 0.7,
                                "max_tokens": 300
                            },
                            timeout=10
                        )
                        if response.status_code == 200:
                            body = response.json()['choices'][0]['message']['content']
                            self.logger.info("Generated reply using Groq API")
                except Exception as e:
                    self.logger.warning(f"Groq API failed: {e}. Using fallback reply.")

                # Enhanced fallback to contextual reply with improved categorization
                if not body:
                    body = generate_contextual_reply(email_body, original_subject, original_from, "")

                # Send the email
                try:
                    self.send_gmail(to, subject, body)
                    self.move_to_done(file_path)
                except Exception as e:
                    self.logger.error(f"Failed to send email for {file_path}: {str(e)}")
                    self.move_to_failed(file_path)

            elif action_type == 'plan':
                self.logger.info(f"Moving plan {file_path} to Done/ (no execution needed)")
                self.move_to_done(file_path)

            else:
                self.logger.warning(f"Unknown action type '{action_type}' in {file_path}")
                self.move_to_failed(file_path)

        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {str(e)}")
            self.move_to_failed(file_path)

    def move_to_done(self, file_path):
        """Move file to the Done directory."""
        try:
            destination = self.done_dir / file_path.name
            shutil.move(str(file_path), str(destination))
            self.logger.info(f"Moved {file_path} to Done/: {destination}")
        except Exception as e:
            self.logger.error(f"Error moving {file_path} to Done/: {str(e)}")

    def move_to_failed(self, file_path):
        """Move file to the Failed directory."""
        try:
            destination = self.failed_dir / file_path.name
            shutil.move(str(file_path), str(destination))
            self.logger.error(f"Moved {file_path} to Failed/: {destination}")
        except Exception as e:
            self.logger.error(f"Error moving {file_path} to Failed/: {str(e)}")


def main():
    # Define directories
    approved_dir = Path("/Users/muhammadomerfarooq/Desktop/AI_Employee_Vault/Approved")
    done_dir = Path("/Users/muhammadomerfarooq/Desktop/AI_Employee_Vault/Done")
    failed_dir = Path("/Users/muhammadomerfarooq/Desktop/AI_Employee_Vault/Failed")

    # Create directories if they don't exist
    approved_dir.mkdir(parents=True, exist_ok=True)

    # Create the event handler
    event_handler = ApprovalWatcher(approved_dir, done_dir, failed_dir)

    # Create observer
    observer = Observer()
    observer.schedule(event_handler, str(approved_dir), recursive=False)

    # Start the observer
    observer.start()
    print(f"Approval watcher started. Monitoring: {approved_dir}")

    # Process any files already sitting in Approved/ on startup
    print("Scanning for existing files in Approved/...")
    for existing_file in approved_dir.glob("*.md"):
        print(f"Found existing file: {existing_file.name}")
        event_handler.process_file(existing_file)

    try:
        # Keep the script running
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping approval watcher...")
        observer.stop()

    observer.join()


if __name__ == "__main__":
    main()