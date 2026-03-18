import os
import time

from dotenv import load_dotenv
from pathlib import Path
import logging
import os
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load configuration from .env
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
config = {
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

class VaultEventHandler(FileSystemEventHandler):
    """Handles file system events in the vault"""

    def __init__(self, vault_root):
        self.vault_root = Path(vault_root)
        self.inbox_path = self.vault_root / config['vault_paths']['inbox']
        self.needs_action_path = self.vault_root / config['vault_paths']['needs_action']
        self.done_path = self.vault_root / config['vault_paths']['done']
        self.pending_approval_path = self.vault_root / config['vault_paths']['pending_approval']
        self.approved_path = self.vault_root / config['vault_paths']['approved']
        self.rejected_path = self.vault_root / config['vault_paths']['rejected']
        self.logs_path = self.vault_root / config['vault_paths']['logs']

        # Get workflow folder names from config
        self.workflow_folders = [
            config['vault_paths']['inbox'],
            config['vault_paths']['needs_action'],
            config['vault_paths']['done'],
            config['vault_paths']['pending_approval'],
            config['vault_paths']['approved'],
            config['vault_paths']['rejected'],
            config['vault_paths']['logs'],
            config['vault_paths']['plans']
        ]

    def on_created(self, event):
        if event.is_directory:
            return

        # Only process .md files
        if event.src_path.endswith('.md'):
            logger.info(f"New file detected: {event.src_path}")
            self.process_new_file(event.src_path)

    def on_modified(self, event):
        if event.is_directory:
            return

        # Only process .md files
        if event.src_path.endswith('.md'):
            logger.info(f"File modified: {event.src_path}")

    def process_new_file(self, file_path):
        """Process a newly created file"""
        try:
            # Move new files from anywhere in the vault to Needs_Action if they're not already in a workflow folder
            file_path = Path(file_path)

            # Determine if the file is already in a workflow folder
            current_folder = file_path.parent.name

            if current_folder not in self.workflow_folders:
                # Check if auto-moving is enabled in config
                if config.get('processing_rules', {}).get('auto_move_new_files_to_needs_action', True):
                    # This is a new file that should be moved to Needs_Action
                    target_path = self.needs_action_path / file_path.name
                    file_path.rename(target_path)
                    logger.info(f"Moved new file to Needs_Action: {target_path}")

                    # Log the action if enabled
                    if config.get('processing_rules', {}).get('log_processed_files', True):
                        self.log_action(f"Auto-moved new file to Needs_Action: {file_path.name}")
                else:
                    logger.info(f"Auto-move disabled, leaving file in place: {file_path}")
            else:
                logger.info(f"File already in workflow: {file_path}")

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")

    def log_action(self, action_message):
        """Log an action to the logs folder"""
        try:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            log_filename = f"log_{timestamp}.txt"
            log_path = self.logs_path / log_filename

            with open(log_path, 'a') as log_file:
                log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {action_message}\n")
        except Exception as e:
            logger.error(f"Error writing to log: {str(e)}")


def watch_vault_changes():
    """Start watching the vault for changes"""
    vault_root = Path(".").resolve()  # Assuming we run from the vault root

    # Navigate up to find the actual vault root if we're in the scripts directory
    if 'scripts' in str(vault_root):
        vault_root = vault_root.parent

    event_handler = VaultEventHandler(vault_root)
    observer = Observer()

    # Get watcher configuration
    recursive = config.get('watcher', {}).get('recursive', True)
    poll_interval = config.get('watcher', {}).get('poll_interval', 1)

    # Watch the entire vault directory
    observer.schedule(event_handler, str(vault_root), recursive=recursive)

    logger.info(f"Starting vault watcher for directory: {vault_root} (recursive: {recursive})")
    observer.start()

    try:
        while True:
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("Vault watcher stopped.")

    observer.join()


def main():
    """Main entry point for the script"""
    print("AI Employee Vault Watcher starting...")
    watch_vault_changes()


if __name__ == "__main__":
    main()
