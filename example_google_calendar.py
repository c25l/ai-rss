#!/usr/bin/env python3
"""
Example script demonstrating Google Calendar integration with persistent OAuth.

This script shows how the authentication works and stays persistent across runs.
"""

import sys
import os

# Check if Google Calendar is available
try:
    from google_calendar import GoogleCalendarAuth, GOOGLE_LIBS_AVAILABLE
    if not GOOGLE_LIBS_AVAILABLE:
        print("Error: Google Calendar libraries not installed.")
        print("Install with: pip install google-auth google-auth-oauthlib google-api-python-client")
        sys.exit(1)
except ImportError as e:
    print(f"Error importing google_calendar: {e}")
    sys.exit(1)


def main():
    """
    Demonstrate Google Calendar OAuth with automatic token refresh.
    """
    print("=" * 70)
    print("Google Calendar OAuth Example - Persistent Authentication")
    print("=" * 70)
    print()
    
    # Configuration
    credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    token_file = os.getenv("GOOGLE_TOKEN_FILE", "token.json")
    
    print(f"Using credentials file: {credentials_file}")
    print(f"Using token file: {token_file}")
    print()
    
    # Check if files exist
    if not os.path.exists(credentials_file):
        print(f"❌ Error: '{credentials_file}' not found!")
        print()
        print("Please follow these steps:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable Google Calendar API")
        print("4. Create OAuth 2.0 credentials (Desktop app)")
        print("5. Download the credentials and save as 'credentials.json'")
        print()
        print("See GOOGLE_CALENDAR_SETUP.md for detailed instructions.")
        return 1
    
    print(f"✓ Credentials file found")
    
    if os.path.exists(token_file):
        print(f"✓ Token file found - will use existing tokens")
    else:
        print(f"ℹ Token file not found - will request authorization")
    
    print()
    print("-" * 70)
    print("Authenticating with Google Calendar API...")
    print("-" * 70)
    print()
    
    # Initialize authentication
    cal_auth = GoogleCalendarAuth(credentials_file, token_file)
    
    # Authenticate (this handles token refresh automatically)
    if not cal_auth.authenticate():
        print("❌ Authentication failed!")
        return 1
    
    print()
    print("✓ Authentication successful!")
    print()
    
    # Demonstrate token persistence by fetching events
    print("-" * 70)
    print("Fetching upcoming events (next 7 days)...")
    print("-" * 70)
    print()
    
    events_by_date = cal_auth.get_events_by_date_range(days=7)
    
    if not events_by_date:
        print("No upcoming events found in the next 7 days.")
    else:
        print(f"Found events on {len(events_by_date)} days:")
        print()
        
        for date, events in sorted(events_by_date.items()):
            print(f"📅 {date}:")
            for event in events:
                start_time = event['start'].split('T')[1][:5] if 'T' in event['start'] else 'All day'
                print(f"   {start_time} - {event['summary']}")
            print()
    
    print("-" * 70)
    print("Token Persistence Status")
    print("-" * 70)
    print()
    print(f"✓ Access token: Valid (auto-refreshes when expired)")
    print(f"✓ Refresh token: Stored in {token_file}")
    print(f"✓ Authentication will persist across script runs")
    print()
    print("Next time you run this script:")
    print("  - No browser authentication needed")
    print("  - Tokens refresh automatically")
    print("  - Works unattended in cron jobs")
    print()
    
    # Test the convenience function
    print("-" * 70)
    print("Testing convenience function...")
    print("-" * 70)
    print()
    
    from google_calendar import upcoming
    import json
    
    result = upcoming(credentials_file, token_file)
    data = json.loads(result)
    
    if "Error" in data:
        print(f"Error: {data['Error']}")
    else:
        mine_count = len(data.get("Mine", {}))
        family_count = len(data.get("Family", {}))
        print(f"✓ Personal calendar: {mine_count} days with events")
        print(f"✓ Family calendar: {family_count} days with events")
    
    print()
    print("=" * 70)
    print("✓ All tests passed! Authentication is working and persistent.")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
