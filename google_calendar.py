"""
Google Calendar integration with persistent OAuth token management.

This module handles Google Calendar API authentication with automatic token refresh
to prevent authentication drops.
"""

import os
import json
import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_LIBS_AVAILABLE = True
except ImportError:
    GOOGLE_LIBS_AVAILABLE = False


# If modifying these scopes, delete the token.json file.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


class GoogleCalendarAuth:
    """
    Handles Google Calendar OAuth authentication with persistent token storage.
    
    Features:
    - Automatic token refresh when expired
    - Persistent token storage in token.json
    - Proper OAuth flow with offline access for refresh tokens
    """
    
    def __init__(self, credentials_file: str = 'credentials.json', token_file: str = 'token.json'):
        """
        Initialize the Google Calendar authentication handler.
        
        Args:
            credentials_file: Path to OAuth client credentials from Google Cloud Console
            token_file: Path to store persistent tokens (will be created on first auth)
        """
        if not GOOGLE_LIBS_AVAILABLE:
            raise ImportError(
                "Google Calendar libraries not available. "
                "Install with: pip install google-auth google-auth-oauthlib google-api-python-client"
            )
        
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.creds = None
        self.service = None
        
    def authenticate(self) -> bool:
        """
        Authenticate with Google Calendar API using OAuth 2.0.
        
        This method:
        1. Checks for existing token.json with refresh token
        2. Automatically refreshes expired access tokens
        3. Prompts for new authorization if needed
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        # Load existing credentials from token file if it exists
        if os.path.exists(self.token_file):
            try:
                self.creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
                print(f"Loaded credentials from {self.token_file}")
            except Exception as e:
                print(f"Error loading credentials: {e}")
                self.creds = None
        
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                # Token expired but we have a refresh token - automatically refresh
                try:
                    print("Access token expired, refreshing...")
                    self.creds.refresh(Request())
                    print("Token refreshed successfully")
                except Exception as e:
                    print(f"Error refreshing token: {e}")
                    print("Will request new authorization...")
                    self.creds = None
            
            # Need new authorization
            if not self.creds:
                if not os.path.exists(self.credentials_file):
                    print(f"Error: Credentials file '{self.credentials_file}' not found.")
                    print("Please download OAuth client credentials from Google Cloud Console:")
                    print("https://console.cloud.google.com/apis/credentials")
                    return False
                
                try:
                    # Run OAuth flow with offline access to get refresh token
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, 
                        SCOPES,
                        # These parameters ensure we get a refresh token
                    )
                    # Use run_local_server with prompt='consent' to ensure refresh token
                    self.creds = flow.run_local_server(
                        port=0,
                        authorization_prompt_message='Please visit this URL to authorize the application: {url}',
                        success_message='Authentication successful! You can close this window.',
                        open_browser=True
                    )
                    print("New credentials obtained successfully")
                except Exception as e:
                    print(f"Error during OAuth flow: {e}")
                    return False
            
            # Save the credentials for the next run
            try:
                with open(self.token_file, 'w') as token:
                    token.write(self.creds.to_json())
                print(f"Credentials saved to {self.token_file}")
            except Exception as e:
                print(f"Warning: Could not save credentials: {e}")
        
        # Build the service
        try:
            self.service = build('calendar', 'v3', credentials=self.creds)
            return True
        except Exception as e:
            print(f"Error building calendar service: {e}")
            return False
    
    def get_upcoming_events(self, max_results: int = 10, calendar_id: str = 'primary') -> List[Dict]:
        """
        Fetch upcoming calendar events.
        
        Args:
            max_results: Maximum number of events to return
            calendar_id: Calendar ID to query (default: 'primary')
            
        Returns:
            List of event dictionaries
        """
        if not self.service:
            if not self.authenticate():
                return []
        
        try:
            # Use timezone-aware datetime (Python 3.12 compatible)
            now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
            
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            return events
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []
    
    def get_events_by_date_range(self, days: int = 7, calendar_ids: Optional[List[str]] = None) -> Dict:
        """
        Get events organized by date for the specified number of days.
        
        Args:
            days: Number of days to look ahead
            calendar_ids: List of calendar IDs to query (default: ['primary'])
            
        Returns:
            Dictionary with dates as keys and lists of events as values
        """
        if not self.service:
            if not self.authenticate():
                return {}
        
        if calendar_ids is None:
            calendar_ids = ['primary']
        
        try:
            # Use timezone-aware datetime (Python 3.12 compatible)
            now = datetime.datetime.now(datetime.timezone.utc)
            end_date = now + datetime.timedelta(days=days)
            
            time_min = now.isoformat().replace('+00:00', 'Z')
            time_max = end_date.isoformat().replace('+00:00', 'Z')
            
            events_by_date = {}
            
            for calendar_id in calendar_ids:
                try:
                    events_result = self.service.events().list(
                        calendarId=calendar_id,
                        timeMin=time_min,
                        timeMax=time_max,
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()
                    
                    events = events_result.get('items', [])
                    
                    for event in events:
                        start = event['start'].get('dateTime', event['start'].get('date'))
                        # Parse the date with proper timezone handling
                        try:
                            if 'T' in start:
                                # DateTime format - handle timezone properly
                                event_date = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                            else:
                                # Date-only format
                                event_date = datetime.datetime.fromisoformat(start)
                        except (ValueError, AttributeError) as e:
                            print(f"Warning: Could not parse date '{start}': {e}")
                            continue
                        
                        date_key = event_date.date().isoformat()
                        
                        if date_key not in events_by_date:
                            events_by_date[date_key] = []
                        
                        events_by_date[date_key].append({
                            'summary': event.get('summary', 'No title'),
                            'start': start,
                            'end': event['end'].get('dateTime', event['end'].get('date')),
                            'calendar': calendar_id
                        })
                        
                except HttpError as error:
                    print(f'Error accessing calendar {calendar_id}: {error}')
                    continue
            
            return events_by_date
            
        except Exception as error:
            print(f'Error fetching events: {error}')
            return {}


def upcoming(credentials_file: str = 'credentials.json', token_file: str = 'token.json') -> str:
    """
    Get upcoming calendar events from Google Calendar in JSON format.
    
    This is a convenience function that matches the interface of the Apple Calendar module.
    
    Args:
        credentials_file: Path to OAuth credentials
        token_file: Path to token storage file
        
    Returns:
        JSON string with calendar events organized by type
    """
    if not GOOGLE_LIBS_AVAILABLE:
        return json.dumps({
            "Mine": {}, 
            "Family": {}, 
            "Error": "Google Calendar libraries not installed. Run: pip install google-auth google-auth-oauthlib google-api-python-client"
        })
    
    try:
        cal_auth = GoogleCalendarAuth(credentials_file, token_file)
        
        if not cal_auth.authenticate():
            return json.dumps({
                "Mine": {}, 
                "Family": {}, 
                "Error": "Authentication failed. Please check credentials."
            })
        
        # Get events from primary calendar
        all_events = cal_auth.get_events_by_date_range(days=7)
        
        # For now, treat all events as personal
        # You can extend this to query multiple calendars and categorize them
        personal_events = all_events
        family_events = {}
        
        return json.dumps({"Mine": personal_events, "Family": family_events})
        
    except Exception as e:
        return json.dumps({
            "Mine": {}, 
            "Family": {}, 
            "Error": str(e)
        })


def main():
    """Test Google Calendar integration"""
    print("Testing Google Calendar integration with OAuth...")
    print("=" * 60)
    
    if not GOOGLE_LIBS_AVAILABLE:
        print("Error: Google Calendar libraries not installed.")
        print("Install with: pip install google-auth google-auth-oauthlib google-api-python-client")
        return
    
    # Test authentication and event fetching
    cal_auth = GoogleCalendarAuth()
    
    if cal_auth.authenticate():
        print("\n✓ Authentication successful!")
        print("\nFetching upcoming events...")
        
        events = cal_auth.get_upcoming_events(max_results=10)
        
        if not events:
            print('No upcoming events found.')
        else:
            print(f'\nFound {len(events)} upcoming events:')
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(f"  - {start}: {event['summary']}")
        
        print("\nTesting date range query...")
        events_by_date = cal_auth.get_events_by_date_range(days=7)
        print(f"Events organized by date: {len(events_by_date)} dates with events")
        
    else:
        print("\n✗ Authentication failed")


if __name__ == "__main__":
    main()
