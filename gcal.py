from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth import get_google_credentials


class Calendar:
    def __init__(self):
        # Use shared OAuth credentials for Calendar, Gmail, and Tasks
        self.creds = get_google_credentials()
        self.service = build('calendar', 'v3', credentials=self.creds)

    def get_upcoming_events(self, days: int = 7, limit: int = 20):
        """Fetch upcoming events for next N days."""
        try:
            # Calculate time range
            now = datetime.utcnow()
            time_min = now.isoformat() + 'Z'
            time_max = (now + timedelta(days=days)).isoformat() + 'Z'

            # Fetch events
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=limit,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])

            # Parse events into consistent format
            parsed_events = []
            for event in events:
                parsed = self._parse_event(event)
                if parsed:
                    parsed_events.append(parsed)

            return parsed_events

        except HttpError as error:
            print(f'An error occurred: {error}')
            return []

    def search_events(self, start_date: datetime = None, end_date: datetime = None,
                     title_contains: str = None, limit: int = 50):
        """Search events by date range or title."""
        try:
            # Default to last 30 days to next 90 days if not specified
            if start_date is None:
                start_date = datetime.now() - timedelta(days=30)
            if end_date is None:
                end_date = datetime.now() + timedelta(days=90)

            time_min = start_date.isoformat() + 'Z'
            time_max = end_date.isoformat() + 'Z'

            # Fetch events
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=limit,
                singleEvents=True,
                orderBy='startTime',
                q=title_contains if title_contains else None
            ).execute()

            events = events_result.get('items', [])

            # Parse events
            parsed_events = []
            for event in events:
                parsed = self._parse_event(event)
                if parsed:
                    # Additional title filtering if needed
                    if title_contains is None or title_contains.lower() in parsed['title'].lower():
                        parsed_events.append(parsed)

            return parsed_events

        except HttpError as error:
            print(f'An error occurred: {error}')
            return []

    def create_event(self, title: str, start: datetime, end: datetime,
                    description: str = "", location: str = ""):
        """Create a new calendar event."""
        try:
            event_body = {
                'summary': title,
                'start': {
                    'dateTime': start.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end.isoformat(),
                    'timeZone': 'UTC',
                },
            }

            if description:
                event_body['description'] = description
            if location:
                event_body['location'] = location

            event = self.service.events().insert(
                calendarId='primary',
                body=event_body
            ).execute()

            return self._parse_event(event)

        except HttpError as error:
            print(f'An error occurred: {error}')
            return None

    def update_event(self, event_dict: dict, title: str = None, start: datetime = None,
                    end: datetime = None, description: str = None, location: str = None):
        """Update an existing event. Pass event dict from get/search methods."""
        try:
            if '_event_id' not in event_dict:
                raise ValueError("Event dict must come from get_upcoming_events or search_events")

            event_id = event_dict['_event_id']

            # Fetch the current event
            event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()

            # Update fields
            if title is not None:
                event['summary'] = title
            if start is not None:
                event['start'] = {
                    'dateTime': start.isoformat(),
                    'timeZone': 'UTC',
                }
            if end is not None:
                event['end'] = {
                    'dateTime': end.isoformat(),
                    'timeZone': 'UTC',
                }
            if description is not None:
                event['description'] = description
            if location is not None:
                event['location'] = location

            # Update the event
            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()

            return self._parse_event(updated_event)

        except HttpError as error:
            print(f'An error occurred: {error}')
            return None

    def delete_event(self, event_dict: dict):
        """Delete an event. Pass event dict from get/search methods."""
        try:
            if '_event_id' not in event_dict:
                raise ValueError("Event dict must come from get_upcoming_events or search_events")

            event_id = event_dict['_event_id']

            self.service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()

            return {"status": "deleted", "title": event_dict['title']}

        except HttpError as error:
            print(f'An error occurred: {error}')
            return None

    def _parse_event(self, event):
        """Parse Google Calendar event into consistent format."""
        try:
            title = event.get('summary', 'No Title')

            # Handle both date and dateTime
            start_data = event.get('start', {})
            end_data = event.get('end', {})

            if 'dateTime' in start_data:
                start = datetime.fromisoformat(start_data['dateTime'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(end_data['dateTime'].replace('Z', '+00:00'))
            else:
                # All-day event
                start = datetime.fromisoformat(start_data['date'])
                end = datetime.fromisoformat(end_data['date'])

            description = event.get('description', '')
            location = event.get('location', '')
            event_id = event.get('id', '')

            return {
                "title": title,
                "start": start,
                "end": end,
                "description": description,
                "location": location,
                "_event_id": event_id
            }
        except Exception as e:
            print(f"Error parsing event: {e}")
            return None


if __name__ == "__main__":
    # Test usage
    print("Initializing Google Calendar...")
    cal = Calendar()

    print("\nTesting upcoming events...")
    upcoming = cal.get_upcoming_events(days=14, limit=5)
    for i, event in enumerate(upcoming):
        print(f"\n{i+1}. {event['title']}")
        print(f"   Start: {event['start']}")
        print(f"   End: {event['end']}")
        if event['location']:
            print(f"   Location: {event['location']}")
