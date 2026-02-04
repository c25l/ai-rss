"""
Shared Google OAuth authentication for Gmail, Calendar, and Tasks.
Run once to authenticate, then all three services work automatically.

Token persistence is local-file only (Azure interactions removed).
"""

import os
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow

# All scopes we need for Gmail, Calendar, and Tasks
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/tasks',
]


def get_google_credentials():
    """
    Get or refresh Google OAuth credentials for Gmail, Calendar, and Tasks.

    Returns:
        Credentials object that can be used with any Google API service
    """
    credentials_file = os.environ.get('GOOGLE_CREDENTIALS_PATH', '/home/chris/source/airss/credentials.json')
    token_file = os.environ.get('GOOGLE_TOKEN_PATH', '/home/chris/source/airss/token.pickle')

    creds = None

    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
            print(f"✓ Loaded token from local file: {token_file}")

    if not creds or not creds.valid:
        if creds and getattr(creds, 'expired', False) and getattr(creds, 'refresh_token', None):
            print("Refreshing access token...")
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_file):
                raise FileNotFoundError(
                    f"Credentials file not found at {credentials_file}.\n"
                    "Please download OAuth 2.0 credentials from Google Cloud Console."
                )

            print("Running OAuth flow - browser will open...")
            print("You'll be asked to authorize access to:")
            print("  - Google Calendar")
            print("  - Gmail")
            print("  - Google Tasks")

            flow = Flow.from_client_secrets_file(
                credentials_file, SCOPES,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob')

            auth_url, _ = flow.authorization_url(prompt='consent')
            print('Please go to this URL: {}'.format(auth_url))
            code = input('Enter the authorization code: ')
            flow.fetch_token(code=code)
            creds = flow.credentials

        try:
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
            print(f"✓ Credentials saved to {token_file}")
        except Exception as e:
            print(f"Warning: Could not save token to local file: {e}")

        print("✓ Future runs will automatically refresh tokens - no re-authentication needed!")

    return creds


if __name__ == "__main__":
    print("Testing Google OAuth authentication...")
    print("=" * 60)

    try:
        _ = get_google_credentials()
        print("\n✓ Authentication successful!")
    except Exception as e:
        print(f"\n✗ Authentication failed: {e}")
