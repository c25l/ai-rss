"""
Shared Google OAuth authentication for Gmail, Calendar, and Tasks.
Run once to authenticate, then all three services work automatically.

Supports both local file storage (development) and Azure Blob Storage (production).
"""

import os
import pickle
import io
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow, Flow

# Azure Blob Storage support (optional, only needed in Azure Functions)
try:
    from azure.storage.blob import BlobServiceClient
    AZURE_BLOB_AVAILABLE = True
except ImportError:
    AZURE_BLOB_AVAILABLE = False


# All scopes we need for Gmail, Calendar, and Tasks
SCOPES = [
    'https://www.googleapis.com/auth/calendar',           # Full calendar access
    'https://www.googleapis.com/auth/gmail.modify',       # Gmail read/send/modify
    'https://www.googleapis.com/auth/tasks',              # Google Tasks access
]


def _load_token_from_blob(blob_name='token.pickle'):
    """Load token from Azure Blob Storage"""
    if not AZURE_BLOB_AVAILABLE:
        return None

    connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
    if not connection_string:
        return None

    try:
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_name = os.environ.get('AZURE_STORAGE_CONTAINER', 'airss-tokens')
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

        blob_data = blob_client.download_blob().readall()
        creds = pickle.loads(blob_data)
        print(f"✓ Loaded token from Azure Blob: {container_name}/{blob_name}")
        return creds
    except Exception as e:
        print(f"Note: Could not load token from blob storage: {e}")
        return None


def _save_token_to_blob(creds, blob_name='token.pickle'):
    """Save token to Azure Blob Storage"""
    if not AZURE_BLOB_AVAILABLE:
        return False

    connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
    if not connection_string:
        return False

    try:
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_name = os.environ.get('AZURE_STORAGE_CONTAINER', 'airss-tokens')

        # Create container if it doesn't exist
        try:
            blob_service_client.create_container(container_name)
        except Exception:
            pass  # Container already exists

        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

        # Serialize credentials and upload
        token_data = pickle.dumps(creds)
        blob_client.upload_blob(token_data, overwrite=True)

        print(f"✓ Saved token to Azure Blob: {container_name}/{blob_name}")
        return True
    except Exception as e:
        print(f"Warning: Could not save token to blob storage: {e}")
        return False


def get_google_credentials():
    """
    Get or refresh Google OAuth credentials for Gmail, Calendar, and Tasks.

    Supports both Azure Blob Storage (production) and local file storage (development).
    Priority: Azure Blob Storage > Local file

    Returns:
        Credentials object that can be used with any Google API service
    """
    credentials_file = os.environ.get('GOOGLE_CREDENTIALS_PATH', '/home/chris/source/airss/credentials.json')
    token_file = os.environ.get('GOOGLE_TOKEN_PATH', '/home/chris/source/airss/token.pickle')
    use_blob = os.environ.get('AZURE_STORAGE_CONNECTION_STRING') is not None

    creds = None

    # Try loading from Azure Blob Storage first (if configured)
    if use_blob:
        creds = _load_token_from_blob()

    # Fall back to local file if blob storage not available or failed
    if creds is None and os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
            print(f"✓ Loaded token from local file: {token_file}")

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

        # Save credentials for next time (after both refresh and initial auth)
        # Try Azure Blob Storage first
        if use_blob:
            _save_token_to_blob(creds)

        # Always save to local file as backup (if path is writable)
        try:
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
            print(f"✓ Credentials saved to {token_file}")
        except Exception as e:
            print(f"Note: Could not save to local file (not critical in Azure): {e}")

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
