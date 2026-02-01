# Google Calendar OAuth Setup Guide

This guide will help you set up Google Calendar API authentication to prevent login drops and ensure persistent access.

## Prerequisites

- A Google account
- Access to Google Cloud Console
- Python 3.7 or higher

## Step 1: Install Required Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your project name/ID

## Step 3: Enable Google Calendar API

1. In Google Cloud Console, go to **APIs & Services** > **Library**
2. Search for "Google Calendar API"
3. Click on it and press **Enable**

## Step 4: Configure OAuth Consent Screen

1. Go to **APIs & Services** > **OAuth consent screen**
2. Choose **External** user type (unless you have a Google Workspace)
3. Fill in the required information:
   - App name: "AI RSS Calendar Integration" (or your preferred name)
   - User support email: Your email
   - Developer contact email: Your email
4. Click **Save and Continue**
5. On the Scopes page, click **Add or Remove Scopes**
6. Add the scope: `https://www.googleapis.com/auth/calendar.readonly`
7. Click **Save and Continue**
8. Add your email as a test user
9. Click **Save and Continue**

### Important: Publishing the App

⚠️ **Critical for Token Persistence**: If your OAuth consent screen is in "Testing" mode, refresh tokens will expire after 7 days, causing authentication to drop.

To prevent this:
1. On the OAuth consent screen page, click **Publish App**
2. Submit the app for verification (if required)
3. OR keep it in Testing mode but be aware you'll need to re-authenticate every 7 days

## Step 5: Create OAuth Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. Choose application type: **Desktop app**
4. Name it: "AI RSS Desktop Client" (or your preferred name)
5. Click **Create**
6. Download the credentials JSON file
7. Save it as `credentials.json` in your project directory

## Step 6: First-Time Authentication

Run the authentication flow:

```bash
python google_calendar.py
```

This will:
1. Open a browser window for authentication
2. Ask you to sign in with your Google account
3. Request permission to access your calendar (read-only)
4. Save a `token.json` file with your refresh token

**Important**: Keep the `token.json` file secure and do not commit it to version control.

## Step 7: Update .gitignore

Make sure your `.gitignore` includes:

```
credentials.json
token.json
```

## How Token Persistence Works

The implementation automatically handles token refresh:

1. **Access Token**: Valid for 1 hour, automatically refreshed
2. **Refresh Token**: Long-lived (or 7 days in Testing mode)
3. **Automatic Refresh**: When the access token expires, the refresh token is used to get a new one
4. **No Manual Intervention**: Once authenticated, the system maintains access automatically

## Token Storage

- `credentials.json`: OAuth client credentials (from Google Cloud Console)
- `token.json`: Contains both access token and refresh token (auto-generated)

The `token.json` file is automatically updated whenever tokens are refreshed.

## Troubleshooting

### "invalid_grant" Error

This usually means:
- The refresh token has expired (app in Testing mode for >7 days)
- The user revoked access
- Password was changed

**Solution**: Delete `token.json` and re-authenticate.

### Refresh Token Not Generated

Make sure:
- Your OAuth consent screen is properly configured
- You're using the latest version of the code
- The OAuth flow includes `access_type=offline`

### Token Expires Every 7 Days

Your app is in **Testing mode**. Either:
- Publish your app to Production mode (no more 7-day expiry)
- Accept that you'll need to re-authenticate weekly

### Browser Doesn't Open for Authentication

The script will print a URL. Copy and paste it into your browser manually.

## Security Best Practices

1. **Never commit credentials**: Keep `credentials.json` and `token.json` out of version control
2. **Restrict scopes**: Only request the permissions you need (we use read-only calendar access)
3. **Secure token storage**: Ensure `token.json` has appropriate file permissions
4. **Monitor access**: Regularly review which apps have access to your Google account at [myaccount.google.com/permissions](https://myaccount.google.com/permissions)

## Using in Your Application

### Basic Usage

```python
from google_calendar import GoogleCalendarAuth

# Initialize
cal_auth = GoogleCalendarAuth(
    credentials_file='credentials.json',
    token_file='token.json'
)

# Authenticate (automatic token refresh)
if cal_auth.authenticate():
    # Get upcoming events
    events = cal_auth.get_upcoming_events(max_results=10)
    
    # Or get events by date range
    events_by_date = cal_auth.get_events_by_date_range(days=7)
```

### Integration with Existing Code

Replace the Apple Calendar import:

```python
# Old (Apple Calendar)
# import calendar_manually

# New (Google Calendar)
import google_calendar

# The interface is similar
events_json = google_calendar.upcoming(
    credentials_file='credentials.json',
    token_file='token.json'
)
```

## Environment Variables (Optional)

You can set environment variables for credential paths:

```bash
export GOOGLE_CREDENTIALS_FILE="/path/to/credentials.json"
export GOOGLE_TOKEN_FILE="/path/to/token.json"
```

Then update the code to use `os.getenv()` for these paths.

## Further Reading

- [Google Calendar API Documentation](https://developers.google.com/calendar/api/v3/reference)
- [OAuth 2.0 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)
- [Managing OAuth Tokens](https://developers.google.com/identity/protocols/oauth2/web-server#offline)
