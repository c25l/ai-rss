"""
Shared Google OAuth authentication for Gmail, Calendar, and Tasks.
Run once to authenticate, then all three services work automatically.
"""

import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow, Flow


# All scopes we need for Gmail, Calendar, and Tasks
SCOPES = [
    'https://www.googleapis.com/auth/calendar',           # Full calendar access
    'https://www.googleapis.com/auth/gmail.modify',       # Gmail read/send/modify
    'https://www.googleapis.com/auth/tasks',              # Google Tasks access
]


def get_google_credentials():
    """
    Get or refresh Google OAuth credentials for Gmail, Calendar, and Tasks.

    Returns:
        Credentials object that can be used with any Google API service
    """
    credentials_file = os.environ.get('GOOGLE_CREDENTIALS_PATH', '/Media/source/airss/credentials.json')
    token_file = os.environ.get('GOOGLE_TOKEN_PATH', '/Media/source/airss/token.pickle')

    creds = None

    # Check if token file exists
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials available, run OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Automatically refresh the token
            print("Refreshing access token...")
            creds.refresh(Request())
        else:
            # Run OAuth flow for first time
            if not os.path.exists(credentials_file):
                raise FileNotFoundError(
                    f"Credentials file not found at {credentials_file}.\n"
                    "Please download OAuth 2.0 credentials from Google Cloud Console.\n"
                    "Follow the setup instructions."
                )

            print("Running OAuth flow - browser will open...")
            print("You'll be asked to authorize access to:")
            print("  - Google Calendar")
            print("  - Gmail")
            print("  - Google Tasks")
            ## TODO need to change the app flow to something that can be done on a headless machine from a headed one.
            flow = Flow.from_client_secrets_file(
                credentials_file, SCOPES,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob')
            #creds = flow.run_console(port=0)

            # Tell the user to go to the authorization URL.
            auth_url, _ = flow.authorization_url(prompt='consent')

            print('Please go to this URL: {}'.format(auth_url))

            # The user will get an authorization code. This code is used to get the
            # access token.
            code = input('Enter the authorization code: ')
            flow.fetch_token(code=code)
            creds = flow.credentials

        # Save credentials for next time
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)

        print(f"✓ Credentials saved to {token_file}")
        print("✓ Future runs will automatically refresh tokens - no re-authentication needed!")

    return creds


if __name__ == "__main__":
    """Test authentication"""
    print("Testing Google OAuth authentication...")
    print("=" * 60)

    try:
        creds = get_google_credentials()
        print("\n✓ Authentication successful!")
        print("\nYou can now use:")
        print("  - gcal.py for Google Calendar")
        print("  - Gmail API (when implemented)")
        print("  - Google Tasks API (when implemented)")
    except Exception as e:
        print(f"\n✗ Authentication failed: {e}")
