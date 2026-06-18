import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from config import CREDENTIALS_PATH, TOKEN_PATH, GMAIL_SCOPES

# Define the Gmail API scopes
SCOPES = GMAIL_SCOPES

def authenticate_gmail():
    """Authenticate and return Gmail service object."""
    creds = None

    # Token file stores the user's access and refresh tokens
    token_file = TOKEN_PATH

    # Check if token.json exists and load credentials
    if token_file.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
        except Exception:
            creds = None

    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            credentials_file = CREDENTIALS_PATH
            if not credentials_file.exists():
                print(f"Error: {credentials_file} not found.")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_file), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save as JSON (not pickle)
        token_file.parent.mkdir(parents=True, exist_ok=True)
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
        print(f"Credentials saved to {token_file}")

    service = build('gmail', 'v1', credentials=creds)
    return service

if __name__ == '__main__':
    print("Starting Gmail authentication...")
    service = authenticate_gmail()

    if service:
        print("Authentication successful!")
        try:
            profile = service.users().getProfile(userId='me').execute()
            print(f"Authenticated as: {profile.get('emailAddress')}")
        except Exception as e:
            print(f"Could not fetch profile: {e}")
    else:
        print("Authentication failed.")
