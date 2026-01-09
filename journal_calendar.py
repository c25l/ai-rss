#!/usr/bin/env python3
from datetime import datetime, timedelta
from gcal import Calendar
from emailer import Emailer
from journal import Journal
import re
import os


class JournalCalendar:
    def __init__(self):
        self.calendar = Calendar()
        self.emailer = Emailer()

    def pull_calendar_data(self):
        """
        Fetch calendar events from yesterday through +14 days.
        Filter out daily recurring events.
        Returns: formatted string with events
        """
        try:
            from datetime import timezone
            # Get current time in local timezone, then convert to UTC
            now_local = datetime.now()
            yesterday_local = now_local - timedelta(days=1)
            future_local = now_local + timedelta(days=7)

            # Create timezone-aware datetimes at local midnight, then convert to UTC
            # This ensures we get the correct calendar day boundaries
            import time
            utc_offset = -time.timezone if time.daylight == 0 else -time.altzone
            local_tz = timezone(timedelta(seconds=utc_offset))

            yesterday_start = yesterday_local.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=local_tz)
            future_end = future_local.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=local_tz)

            # Fetch Google Calendar events
            events = self.calendar.search_events(
                start_date=yesterday_start,
                end_date=future_end,
                limit=100,
                calendar_ids=["christopher.p.bonnell@gmail.com","sharamdavis@gmail.com"]
            )

            if not events:
                return "No calendar events found."

            # Filter out daily recurring events and procedural events
            # Daily recurring events typically have 'DAILY' in recurrence rules
            # Also filter out procedural events like 'calendar check' and 'meds'
            procedural_events = {'calendar check', 'meds'}
            filtered_events = []
            for event in events:
                # Skip procedural events (case-insensitive)
                if event['title'].lower() in procedural_events:
                    continue
                # We don't have direct access to recurrence rules in our parsed format
                # But we can use a heuristic: if the event title appears multiple times
                # in a short span, it's likely daily recurring
                filtered_events.append(event)

            # Group by past, today, future
            now = datetime.now()
            past_events = []
            today_events = []
            future_events = []

            for event in filtered_events:
                event_date = event['start'].date()
                today_date = now.date()

                if event_date < today_date:
                    past_events.append(event)
                elif event_date == today_date:
                    today_events.append(event)
                else:
                    future_events.append(event)

            # Format output
            output = []

            if past_events:
                output.append("### Yesterday's Events")
                for event in past_events:
                    start_str = event['start'].strftime('%I:%M %p')
                    cal_name = event.get('calendar_name', 'Unknown')
                    output.append(f"- **{event['title']}** at {start_str} ({cal_name})")
                    if event['location']:
                        output.append(f"  Location: {event['location']}")
                    if event['description']:
                        output.append(f"  Note: {event['description']}")
                output.append("")

            if today_events:
                output.append("### Today's Events")
                for event in today_events:
                    start_str = event['start'].strftime('%I:%M %p')
                    cal_name = event.get('calendar_name', 'Unknown')
                    output.append(f"- **{event['title']}** at {start_str} ({cal_name})")
                    if event['location']:
                        output.append(f"  Location: {event['location']}")
                    if event['description']:
                        output.append(f"  Note: {event['description']}")
                output.append("")

            if future_events:
                output.append("### Upcoming Events (Next 14 Days)")
                for event in future_events:
                    date_str = event['start'].strftime('%a, %b %d')
                    time_str = event['start'].strftime('%I:%M %p')
                    cal_name = event.get('calendar_name', 'Unknown')
                    output.append(f"- **{date_str}** - {event['title']} at {time_str} ({cal_name})")
                    if event['location']:
                        output.append(f"  Location: {event['location']}")
                    if event['description']:
                        output.append(f"  Note: {event['description']}")

            return "\n".join(output) if output else "No calendar events found."

        except Exception as e:
            return f"Error fetching calendar data: {str(e)}"
    def format_output(self):
        """
        Combine all three data sources into structured markdown
        WITHOUT LLM processing - just clean formatting
        """
        calendar_data = self.pull_calendar_data()
        journal_data = "\n".join(Journal().pull_data())

        output = []
        output.append("## Calendar Events")
        output.append(calendar_data)
        output.append("")
        output.append("## Journal Entries (Last 7 days)")
        output.append(journal_data)
        output.append("")

        return "\n".join(output)


if __name__ == "__main__":
    # Test usage
    jc = JournalCalendar()
    print(jc.format_output())
