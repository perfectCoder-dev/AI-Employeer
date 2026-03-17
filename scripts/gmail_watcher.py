import os
import json
import time
import yaml
from datetime import datetime
from pathlib import Path
import logging
import pickle
import base64
from email.mime.text import MIMEText

# Google API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the scopes required for Gmail API
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

class GmailWatcher:
    def __init__(self, vault_path="/Users/muhammadomerfarooq/Desktop/AI_Employee_Vault"):
        self.vault_path = Path(vault_path).resolve()
        import os
        self.credentials_path = Path(os.getenv('CREDENTIALS_PATH', './credentials/credentials.json'))
        self.token_path = Path(os.getenv('TOKEN_PATH', './credentials/token.json'))
        self.processed_ids_path = self.vault_path / "scripts" / "processed_ids.json"
        self.needs_action_path = self.vault_path / "Needs_Action"
        self.logs_path = self.vault_path / "Logs"

        # Create directories if they don't exist
        self.needs_action_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)

        from dotenv import load_dotenv
        load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
        # Load config from environment variables
        self.config = {
            'vault_paths': {
                'inbox': os.getenv('INBOX_PATH', './Inbox'),
                'needs_action': os.getenv('NEEDS_ACTION_PATH', './Needs_Action'),
                'done': os.getenv('DONE_PATH', './Done'),
                'pending_approval': os.getenv('PENDING_APPROVAL_PATH', './Pending_Approval'),
                'approved': os.getenv('APPROVED_PATH', './Approved'),
                'rejected': os.getenv('REJECTED_PATH', './Rejected'),
                'logs': os.getenv('LOGS_PATH', './Logs'),
                'plans': os.getenv('PLANS_PATH', './Plans'),
            },
            'watcher': {
                'recursive': os.getenv('WATCHER_RECURSIVE', 'true').lower() == 'true',
                'file_extensions': [os.getenv('WATCHER_FILE_EXTENSIONS', '.md')],
                'poll_interval': int(os.getenv('WATCHER_POLL_INTERVAL', '1')),
            },
            'processing_rules': {
                'auto_move_new_files_to_needs_action': os.getenv('AUTO_MOVE_NEW_FILES_TO_NEEDS_ACTION', 'true').lower() == 'true',
                'log_processed_files': os.getenv('LOG_PROCESSED_FILES', 'true').lower() == 'true',
                'backup_before_processing': os.getenv('BACKUP_BEFORE_PROCESSING', 'false').lower() == 'true',
            }
        }

        # Load processed email IDs
        self.processed_email_ids = self.load_processed_ids()

        # Initialize Gmail service
        self.service = self.authenticate_gmail()

    def authenticate_gmail(self):
        """Authenticate with Gmail API using OAuth2"""
        creds = None

        # Load existing token if available
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)

        # If there are no valid credentials, request authorization
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.warning(f"Token refresh failed: {e}")
                    # If refresh fails, delete the token file and start fresh
                    if self.token_path.exists():
                        self.token_path.unlink()
                    creds = None

            if not creds:
                # Check if credentials.json exists
                if not self.credentials_path.exists():
                    raise FileNotFoundError(
                        f"Credentials file not found at {self.credentials_path}. "
                        f"Please create a Google Cloud project, enable the Gmail API, "
                        f"and download the credentials.json file."
                    )

                # Start the OAuth flow
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), SCOPES
                )
                creds = flow.run_local_server(port=0)

                # Save the credentials for the next run
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())

        # Build the Gmail service
        service = build('gmail', 'v1', credentials=creds)
        logger.info("Successfully authenticated with Gmail API")
        return service

    def load_processed_ids(self):
        """Load previously processed email IDs from JSON file"""
        if self.processed_ids_path.exists():
            try:
                with open(self.processed_ids_path, 'r') as f:
                    return set(json.load(f))
            except json.JSONDecodeError:
                logger.warning("Could not decode processed_ids.json, starting with empty set")
                return set()
        else:
            logger.info("Processed IDs file not found, starting with empty set")
            return set()

    def save_processed_ids(self):
        """Save processed email IDs to JSON file"""
        with open(self.processed_ids_path, 'w') as f:
            json.dump(list(self.processed_email_ids), f)

    def get_unread_important_emails(self):
        """Retrieve unread important emails from Gmail"""
        try:
            # Query for unread emails marked as important
            query = "is:unread in:inbox -category:promotions -category:social -category:updates"
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=50  # Limit to prevent too many emails at once
            ).execute()

            messages = results.get('messages', [])
            logger.info(f"Found {len(messages)} unread important emails")

            return messages
        except HttpError as error:
            logger.error(f"An error occurred while fetching emails: {error}")
            return []

    def get_email_details(self, msg_id):
        """Get detailed information about a specific email"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()

            # Extract headers
            headers = {header['name'].lower(): header['value']
                      for header in message['payload'].get('headers', [])}

            # Extract snippet
            snippet = message.get('snippet', '')

            # Extract body (prefer plain text)
            body = self.extract_body(message)

            # Get timestamp
            timestamp_ms = int(message['internalDate'])
            received_time = datetime.fromtimestamp(timestamp_ms / 1000)

            return {
                'id': msg_id,
                'from': headers.get('from', ''),
                'to': headers.get('to', ''),
                'subject': headers.get('subject', '(no subject)'),
                'received': received_time.isoformat(),
                'snippet': snippet,
                'body': body,
                'labels': message.get('labelIds', [])
            }
        except HttpError as error:
            logger.error(f"An error occurred while getting email details: {error}")
            return None

    def extract_body(self, message):
        """Extract email body content"""
        body = ""
        payload = message.get('payload', {})

        # Handle multipart messages
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8')
                    break
                elif part['mimeType'] == 'text/html' and not body:
                    # Fallback to HTML if plain text not available
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8')
        else:
            # Handle simple messages
            if 'body' in payload and 'data' in payload['body']:
                data = payload['body']['data']
                body = base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8')

        return body

    def create_note_from_email(self, email_data):
        """Create a markdown note from email data"""
        # Determine priority based on labels
        priority = "high" if "IMPORTANT" in email_data['labels'] else "medium"

        # Create YAML frontmatter
        frontmatter = {
            'type': 'email',
            'from': email_data['from'],
            'subject': email_data['subject'],
            'received': email_data['received'],
            'priority': priority,
            'status': 'needs-action',
            'original_email_id': email_data['id']
        }

        # Create filename based on subject and timestamp
        safe_subject = "".join(c for c in email_data['subject'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        if not safe_subject:
            safe_subject = "untitled_email"
        safe_subject = safe_subject[:50]  # Limit length
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"email_{timestamp}_{safe_subject.replace(' ', '_')}.md"
        filepath = self.needs_action_path / filename

        # Write the note with YAML frontmatter
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("---\n")
            yaml.dump(frontmatter, f, default_flow_style=False, allow_unicode=True)
            f.write("---\n\n")
            f.write(f"# {email_data['subject']}\n\n")
            f.write(f"**From:** {email_data['from']}\n\n")
            f.write(f"**Received:** {email_data['received']}\n\n")
            f.write("**Email Content:**\n\n")
            if email_data['body']:
                f.write(email_data['body'])
            else:
                f.write(email_data['snippet'])
            f.write("\n")

        logger.info(f"Created note for email: {filepath.name}")
        return filepath

    def log_activity(self, message):
        """Log activity to the vault's Logs folder"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        log_filename = f"gmail_watcher_log_{timestamp}.txt"
        log_path = self.logs_path / log_filename

        with open(log_path, 'w') as log_file:
            log_file.write(f"{datetime.now().isoformat()} - {message}\n")

    def mark_as_read(self, msg_id):
        """Mark an email as read to avoid re-processing"""
        try:
            # Remove UNREAD label
            self.service.users().messages().modify(
                userId='me',
                id=msg_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            logger.debug(f"Marked email {msg_id} as read")
        except HttpError as error:
            logger.error(f"Failed to mark email {msg_id} as read: {error}")

    def run_once(self):
        """Run one iteration of checking for new emails"""
        logger.info("Checking for new unread important emails...")

        # Get unread important emails
        messages = self.get_unread_important_emails()

        new_emails_count = 0

        for msg in messages:
            msg_id = msg['id']

            # Skip if already processed
            if msg_id in self.processed_email_ids:
                continue

            # Get detailed email information
            email_data = self.get_email_details(msg_id)
            if email_data is None:
                continue

            # Create a note from the email
            self.create_note_from_email(email_data)

            # Mark as processed
            self.processed_email_ids.add(msg_id)
            new_emails_count += 1

            # Optionally mark as read to prevent re-processing
            self.mark_as_read(msg_id)

        # Save processed IDs
        self.save_processed_ids()

        logger.info(f"Processed {new_emails_count} new emails")
        self.log_activity(f"Gmail Watcher processed {new_emails_count} new emails")

        return new_emails_count

    def run_continuous(self, interval_minutes=2):
        """Run the watcher continuously with specified interval"""
        logger.info(f"Starting Gmail Watcher (checking every {interval_minutes} minutes)")

        while True:
            try:
                self.run_once()
                time.sleep(interval_minutes * 60)  # Convert minutes to seconds
            except KeyboardInterrupt:
                logger.info("Gmail Watcher stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in Gmail Watcher: {e}")
                time.sleep(60)  # Wait a minute before retrying


def main():
    """Main entry point for the Gmail Watcher"""
    print("Initializing Gmail Watcher...")

    try:
        watcher = GmailWatcher()
        watcher.run_continuous(interval_minutes=2)
    except Exception as e:
        logger.error(f"Failed to start Gmail Watcher: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()