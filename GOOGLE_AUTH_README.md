# Google Calendar Authentication - Quick Start

## The Problem

Google Calendar OAuth tokens were expiring, causing authentication to drop unexpectedly. This happened because:
- Access tokens expire after 1 hour
- The previous implementation didn't properly handle token refresh
- Apps in "Testing" mode have refresh tokens that expire after 7 days

## The Solution

We've implemented a robust Google Calendar OAuth handler that:
- ✅ Automatically refreshes access tokens when they expire
- ✅ Persists refresh tokens in a secure `token.json` file
- ✅ Works unattended in scheduled jobs (cron, etc.)
- ✅ Provides clear error messages and recovery steps
- ✅ Maintains backward compatibility with Apple Calendar

## Quick Setup (5 minutes)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Google Calendar Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create/select a project
3. Enable "Google Calendar API"
4. Create OAuth credentials (Desktop app type)
5. Download as `credentials.json` in the project directory

**Detailed instructions**: See [GOOGLE_CALENDAR_SETUP.md](GOOGLE_CALENDAR_SETUP.md)

### 3. First-Time Authentication

```bash
python example_google_calendar.py
```

This will:
- Open your browser for authentication
- Save tokens to `token.json`
- Test that everything works

### 4. Enable in Your Application

Set environment variable:
```bash
export USE_GOOGLE_CALENDAR=true
```

Or in Python:
```python
from modules.journal import Journal
j = Journal(use_google_calendar=True)
```

## How It Works

### Token Lifecycle

1. **First Run**: User authenticates via browser → tokens saved to `token.json`
2. **Subsequent Runs**: Tokens loaded from `token.json` → access token refreshed if expired
3. **Automatic Refresh**: When access token expires (1 hour), refresh token gets a new one
4. **No Manual Intervention**: Works automatically in background jobs

### File Structure

```
credentials.json  ← Your OAuth client ID (from Google Cloud Console)
token.json        ← Auto-generated, contains access + refresh tokens
```

**Important**: Never commit these files! They're in `.gitignore`.

## Production Deployment

### ⚠️ Important: Publish Your App

If your OAuth consent screen is in **Testing mode**, refresh tokens expire after 7 days!

**To prevent this**:
1. Go to Google Cloud Console → OAuth consent screen
2. Click "Publish App"
3. Your tokens will now persist indefinitely (until manually revoked)

See [GOOGLE_CALENDAR_SETUP.md](GOOGLE_CALENDAR_SETUP.md) for details.

## Environment Variables

Optional configuration:

```bash
# Enable Google Calendar (default: false)
export USE_GOOGLE_CALENDAR=true

# Custom credential paths (optional)
export GOOGLE_CREDENTIALS_FILE="/path/to/credentials.json"
export GOOGLE_TOKEN_FILE="/path/to/token.json"
```

## Troubleshooting

### "invalid_grant" Error

**Cause**: Refresh token expired (usually means app in Testing mode for >7 days)

**Fix**: 
```bash
rm token.json
python example_google_calendar.py  # Re-authenticate
```

### Browser Doesn't Open

The script will print a URL. Copy and paste it into your browser manually.

### Still Using Apple Calendar?

That's fine! The code supports both:
- Apple Calendar: Local macOS Calendar access (no OAuth needed)
- Google Calendar: Cross-platform, OAuth-based (this implementation)

Switch between them with `USE_GOOGLE_CALENDAR` environment variable.

## Testing Your Setup

Run the example script:
```bash
python example_google_calendar.py
```

Expected output:
- ✓ Authentication successful
- ✓ Events fetched
- ✓ Token persistence confirmed

## Integration Examples

### Basic Usage

```python
from google_calendar import GoogleCalendarAuth

cal_auth = GoogleCalendarAuth()
if cal_auth.authenticate():
    events = cal_auth.get_upcoming_events(max_results=10)
    for event in events:
        print(event['summary'])
```

### In Journal Module

```python
from modules.journal import Journal

# Use Google Calendar
j = Journal(use_google_calendar=True)
j.pull_data()
```

### Scheduled Jobs

```bash
# crontab example - runs daily at 8am
0 8 * * * cd /path/to/ai-rss && USE_GOOGLE_CALENDAR=true python daily_workflow.py
```

The authentication persists across runs, so no browser interaction needed!

## Security Notes

- ✅ Read-only calendar access (can't modify events)
- ✅ Tokens stored locally, not in git
- ✅ OAuth 2.0 industry standard
- ✅ Refresh tokens encrypted by Google
- ⚠️ Keep `token.json` secure (contains access credentials)

## Need Help?

1. Check [GOOGLE_CALENDAR_SETUP.md](GOOGLE_CALENDAR_SETUP.md) for detailed setup
2. Run `python example_google_calendar.py` to test your configuration
3. Check Google Cloud Console for API quota and errors

## What's Different from Before?

**Before**: Tokens expired → authentication dropped → manual re-auth needed

**Now**: Tokens expire → automatically refresh → keeps working indefinitely

No more unexpected login drops! 🎉
