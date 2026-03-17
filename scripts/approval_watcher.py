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
from pathlib import Path
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
            credentials_path = Path('/Users/muhammadomerfarooq/Desktop/AI_Employee_Vault/credentials/credentials.json')
            token_path = Path('/Users/muhammadomerfarooq/Desktop/AI_Employee_Vault/credentials/token.json')

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

                # Build a clean reply body
                original_subject = frontmatter.get('subject', '')
                original_from = frontmatter.get('from', '')
                body = f"""Thank you for reaching out regarding "{original_subject}".

We have received your message and will get back to you shortly.

Best regards,
AI Employee
purposework56@gmail.com"""

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