from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth import get_google_credentials


class Calendar:
    def __init__(self):
        # Use shared OAuth credentials for Calendar, Gmail, and Tasks
        self.creds = get_google_credentials()
        self.service = build('calendar', 'v3', credentials=self.creds)

    def list_calendars(self):
        """List all available calendars (including shared ones)."""
        try:
            calendar_list = self.service.calendarList().list().execute()
            calendars = []
            for calendar in calendar_list.get('items', []):
                calendars.append({
                    'id': calendar['id'],
                    'summary': calendar.get('summary', 'No Name'),
                    'description': calendar.get('description', ''),
                    'primary': calendar.get('primary', False),
                    'accessRole': calendar.get('accessRole', 'unknown')
                })
            return calendars
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []

    def get_upcoming_events(self, days: int = 7, limit: int = 20, calendar_ids: list = None):
        """Fetch upcoming events for next N days from specified calendars or all calendars."""
        try:
            # Calculate time range
            from datetime import timezone
            now = datetime.now(timezone.utc)
            time_min = now.isoformat()
            time_max = (now + timedelta(days=days)).isoformat()

            # If no calendar_ids specified, get all calendars
            if calendar_ids is None:
                calendars = self.list_calendars()
                calendar_ids = [cal['id'] for cal in calendars]
            else:
                calendars = self.list_calendars()

            # Create calendar ID to name mapping
            cal_names = {cal['id']: cal['summary'] for cal in calendars}

            all_events = []

            # Fetch events from each calendar
            for cal_id in calendar_ids:
                try:
                    events_result = self.service.events().list(
                        calendarId=cal_id,
                        timeMin=time_min,
                        timeMax=time_max,
                        maxResults=limit,
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()

                    events = events_result.get('items', [])

                    # Parse events into consistent format
                    for event in events:
                        parsed = self._parse_event(event, cal_id, cal_names.get(cal_id, cal_id))
                        if parsed:
                            all_events.append(parsed)
                except HttpError as e:
                    print(f'Error fetching events from calendar {cal_id}: {e}')
                    continue

            # Sort all events by start time
            all_events.sort(key=lambda x: x['start'])

            # Limit total results
            return all_events[:limit]

        except HttpError as error:
            print(f'An error occurred: {error}')
            return []

    def search_events(self, start_date: datetime = None, end_date: datetime = None,
                     title_contains: str = None, limit: int = 50, calendar_ids: list = None):
        """Search events by date range or title across all calendars."""
        try:
            from datetime import timezone
            # Default to last 30 days to next 90 days if not specified
            if start_date is None:
                start_date = datetime.now(timezone.utc) - timedelta(days=30)
            if end_date is None:
                end_date = datetime.now(timezone.utc) + timedelta(days=90)

            # Ensure timezone-aware and format with Z suffix
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)

            time_min = start_date.isoformat().replace('+00:00', 'Z')
            time_max = end_date.isoformat().replace('+00:00', 'Z')

            # If no calendar_ids specified, get all calendars
            if calendar_ids is None:
                calendars = self.list_calendars()
                calendar_ids = [cal['id'] for cal in calendars]
            else:
                calendars = self.list_calendars()

            # Create calendar ID to name mapping
            cal_names = {cal['id']: cal['summary'] for cal in calendars}

            all_events = []

            # Fetch events from each calendar
            for cal_id in calendar_ids:
                try:
                    events_result = self.service.events().list(
                        calendarId=cal_id,
                        timeMin=time_min,
                        timeMax=time_max,
                        maxResults=limit,
                        singleEvents=True,
                        orderBy='startTime',
                        q=title_contains if title_contains else None
                    ).execute()

                    events = events_result.get('items', [])

                    # Parse events
                    for event in events:
                        parsed = self._parse_event(event, cal_id, cal_names.get(cal_id, cal_id))
                        if parsed:
                            # Additional title filtering if needed
                            if title_contains is None or title_contains.lower() in parsed['title'].lower():
                                all_events.append(parsed)
                except HttpError as e:
                    print(f'Error searching events in calendar {cal_id}: {e}')
                    continue

            # Sort all events by start time
            all_events.sort(key=lambda x: x['start'])

            # Limit total results
            return all_events[:limit]

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

    def _parse_event(self, event, calendar_id=None, calendar_name=None):
        """Parse Google Calendar event into consistent format."""
        try:
            from datetime import timezone
            title = event.get('summary', 'No Title')

            # Handle both date and dateTime
            start_data = event.get('start', {})
            end_data = event.get('end', {})

            if 'dateTime' in start_data:
                start = datetime.fromisoformat(start_data['dateTime'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(end_data['dateTime'].replace('Z', '+00:00'))
            else:
                # All-day event - make it timezone-aware
                start = datetime.fromisoformat(start_data['date']).replace(tzinfo=timezone.utc)
                end = datetime.fromisoformat(end_data['date']).replace(tzinfo=timezone.utc)

            description = event.get('description', '')
            location = event.get('location', '')
            event_id = event.get('id', '')

            parsed = {
                "title": title,
                "start": start,
                "end": end,
                "description": description,
                "location": location,
                "_event_id": event_id
            }

            if calendar_id:
                parsed["_calendar_id"] = calendar_id
            if calendar_name:
                parsed["calendar_name"] = calendar_name

            return parsed
        except Exception as e:
            print(f"Error parsing event: {e}")
            return None


if __name__ == "__main__":
    # Test usage
    print("Initializing Google Calendar...")
    cal = Calendar()

    print("\n=== Available Calendars ===")
    calendars = cal.list_calendars()
    for i, calendar in enumerate(calendars):
        primary_marker = " [PRIMARY]" if calendar['primary'] else ""
        print(f"{i+1}. {calendar['summary']}{primary_marker}")
        print(f"   ID: {calendar['id']}")
        print(f"   Access: {calendar['accessRole']}")

    print("\n=== Upcoming Events (All Calendars) ===")
    upcoming = cal.get_upcoming_events(days=14, limit=10)
    for i, event in enumerate(upcoming):
        cal_name = event.get('calendar_name', 'unknown')
        print(f"\n{i+1}. {event['title']}")
        print(f"   Start: {event['start']}")
        print(f"   End: {event['end']}")
        if event['location']:
            print(f"   Location: {event['location']}")
        print(f"   Calendar: {cal_name}")
