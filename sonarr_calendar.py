import os
from datetime import datetime, timedelta, timezone
import requests
from icalendar import Calendar as iCalendar


class SonarrCalendar:
    def __init__(self, base_url=None, api_key=None):
        """
        Initialize Sonarr calendar integration.

        Args:
            base_url: Sonarr base URL (e.g., http://localhost:8989)
            api_key: Sonarr API key
        """
        self.base_url = base_url or os.getenv('SONARR_URL', 'http://localhost:8989')
        self.api_key = api_key or os.getenv('SONARR_API_KEY')

        if not self.api_key:
            raise ValueError("Sonarr API key not provided. Set SONARR_API_KEY environment variable.")

    def get_calendar_events(self, start_date=None, end_date=None, limit=100):
        """
        Fetch calendar events from Sonarr's iCal feed.

        Args:
            start_date: Start datetime for event range (timezone-aware)
            end_date: End datetime for event range (timezone-aware)
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries in standardized format
        """
        try:
            # Default to yesterday through +14 days
            if start_date is None:
                start_date = datetime.now(timezone.utc) - timedelta(days=1)
            if end_date is None:
                end_date = datetime.now(timezone.utc) + timedelta(days=14)

            # Ensure timezone-aware
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)

            # Construct iCal feed URL
            ical_url = f"{self.base_url}/feed/v3/calendar/Sonarr.ics"
            params = {'apikey': self.api_key}

            # Fetch iCal data
            response = requests.get(ical_url, params=params, timeout=10)
            response.raise_for_status()

            # Parse iCal
            cal = iCalendar.from_ical(response.content)

            events = []
            for component in cal.walk():
                if component.name == "VEVENT":
                    event = self._parse_ical_event(component)
                    if event:
                        # Filter by date range
                        if start_date <= event['start'] <= end_date:
                            events.append(event)

            # Sort by start time
            events.sort(key=lambda x: x['start'])

            # Limit results
            return events[:limit]

        except requests.exceptions.RequestException as e:
            print(f"Error fetching Sonarr calendar: {e}")
            return []
        except Exception as e:
            print(f"Error parsing Sonarr calendar: {e}")
            return []

    def _parse_ical_event(self, component):
        """
        Parse an iCal event component into standardized format.

        Args:
            component: iCalendar VEVENT component

        Returns:
            Event dictionary or None if parsing fails
        """
        try:
            title = str(component.get('summary', 'No Title'))

            # Get start and end times
            start = component.get('dtstart').dt
            end = component.get('dtend').dt if component.get('dtend') else None

            # Handle date vs datetime
            if isinstance(start, datetime):
                if start.tzinfo is None:
                    start = start.replace(tzinfo=timezone.utc)
            else:
                # It's a date, convert to datetime
                start = datetime.combine(start, datetime.min.time()).replace(tzinfo=timezone.utc)

            if end:
                if isinstance(end, datetime):
                    if end.tzinfo is None:
                        end = end.replace(tzinfo=timezone.utc)
                else:
                    end = datetime.combine(end, datetime.min.time()).replace(tzinfo=timezone.utc)
            else:
                # Default end time to 1 hour after start
                end = start + timedelta(hours=1)

            description = str(component.get('description', ''))
            location = str(component.get('location', ''))
            uid = str(component.get('uid', ''))

            return {
                'title': title,
                'start': start,
                'end': end,
                'description': description,
                'location': location,
                'calendar_name': 'Sonarr',
                '_event_id': uid,
                '_calendar_id': 'sonarr'
            }

        except Exception as e:
            print(f"Error parsing iCal event: {e}")
            return None


if __name__ == "__main__":
    # Test usage
    print("Initializing Sonarr Calendar...")
    try:
        sonarr = SonarrCalendar()

        print("\n=== Upcoming Sonarr Events (Next 14 Days) ===")
        events = sonarr.get_calendar_events()

        if events:
            for i, event in enumerate(events):
                print(f"\n{i+1}. {event['title']}")
                print(f"   Start: {event['start']}")
                print(f"   End: {event['end']}")
                if event['description']:
                    print(f"   Description: {event['description'][:100]}...")
                if event['location']:
                    print(f"   Location: {event['location']}")
        else:
            print("No upcoming events found.")

    except ValueError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"Error: {e}")
