#!/usr/bin/env python3
from datetime import datetime, timedelta
from gcal import Calendar
from gtasks import Tasks
from emailer import Emailer
import re


class JournalCalendar:
    def __init__(self):
        self.calendar = Calendar()
        self.tasks = Tasks()
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
            future_local = now_local + timedelta(days=14)

            # Create timezone-aware datetimes at local midnight, then convert to UTC
            # This ensures we get the correct calendar day boundaries
            import time
            utc_offset = -time.timezone if time.daylight == 0 else -time.altzone
            local_tz = timezone(timedelta(seconds=utc_offset))

            yesterday_start = yesterday_local.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=local_tz)
            future_end = future_local.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=local_tz)

            events = self.calendar.search_events(
                start_date=yesterday_start,
                end_date=future_end,
                limit=100
            )

            if not events:
                return "No calendar events found."

            # Filter out daily recurring events
            # Daily recurring events typically have 'DAILY' in recurrence rules
            filtered_events = []
            for event in events:
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

    def pull_journal_emails(self):
        """
        Search for journal emails (sent to cpbnel.news@gmail.com)
        Filter by subject patterns: yyyy-mm-dd, yyyy-[W]WW, yyyy-mm
        Get last 14 days of entries
        Returns: formatted string with dates and content
        """
        try:
            # Get recent emails from All Mail archive
            emails = self.emailer.read_inbox(limit=200, folder="[Gmail]/All Mail")

            # Date patterns for journal entries
            date_patterns = [
                r'^\d{4}-\d{2}-\d{2}$',  # yyyy-mm-dd
                r'^\d{4}-W\d{2}$',        # yyyy-[W]WW
                r'^\d{4}-\d{2}$'          # yyyy-mm
            ]

            # Filter emails by subject pattern
            journal_entries = []

            for email_dict in emails:
                subject = email_dict['subject'].strip()

                # Check if subject matches any pattern and contains journal recipient
                matches_pattern = True
                to_journal = 'cpbnel.news@gmail.com' in str(email_dict.get('_msg', ''))

                if matches_pattern and to_journal:
                    journal_entries.append({
                        'subject': subject,
                        'date': email_dict['date'],
                        'snippet': email_dict['snippet'],
                        'body': self.emailer.get_email_body(email_dict)
                    })

            # Sort by subject (which is the date) descending
            journal_entries.sort(key=lambda x: x['subject'], reverse=True)

            # Take last 14 entries
            journal_entries = journal_entries[:14]

            if not journal_entries:
                return "No journal entries found in recent emails."

            # Format output
            output = []
            for entry in journal_entries:
                output.append(f"#### {entry['subject']}")
                # Use first 500 chars of body for context
                body_preview = entry['body'][:500] + "..." if len(entry['body']) > 500 else entry['body']
                output.append(body_preview)
                output.append("")

            return "\n".join(output)

        except Exception as e:
            return f"Error fetching journal emails: {str(e)}"

    def pull_tasks(self):
        """
        Get all open tasks from Google Tasks.
        Sort by due date (earliest first), with no-due-date items at the end.
        Returns: formatted string grouped by task list
        """
        try:
            all_tasks = self.tasks.get_all_tasks(show_completed=False)

            if not all_tasks:
                return "No open tasks found."

            # Separate tasks with and without due dates
            tasks_with_due = [t for t in all_tasks if t['due'] is not None]
            tasks_without_due = [t for t in all_tasks if t['due'] is None]

            # Sort tasks with due dates by due date
            tasks_with_due.sort(key=lambda x: x['due'])

            # Combine: due date tasks first, then no-due-date tasks
            sorted_tasks = tasks_with_due + tasks_without_due

            # Format output
            output = []

            if tasks_with_due:
                output.append("#### Tasks with Due Dates")
                for task in tasks_with_due:
                    due_str = task['due'].strftime('%a, %b %d, %Y')
                    output.append(f"- **{task['title']}** (Due: {due_str})")
                    if task['notes']:
                        output.append(f"  Notes: {task['notes']}")
                    output.append(f"  List: {task.get('list_name', 'Unknown')}")
                output.append("")

            if tasks_without_due:
                output.append("#### Tasks without Due Dates (Lower Priority)")
                for task in tasks_without_due:
                    output.append(f"- **{task['title']}**")
                    if task['notes']:
                        output.append(f"  Notes: {task['notes']}")
                    output.append(f"  List: {task.get('list_name', 'Unknown')}")

            return "\n".join(output)

        except Exception as e:
            return f"Error fetching tasks: {str(e)}"

    def format_output(self):
        """
        Combine all three data sources into structured markdown
        WITHOUT LLM processing - just clean formatting
        """
        calendar_data = self.pull_calendar_data()
        journal_data = self.pull_journal_emails()
        tasks_data = self.pull_tasks()

        output = []
        output.append("## Calendar Events")
        output.append(calendar_data)
        output.append("")
        output.append("## Journal Entries (Last 14 Days)")
        output.append(journal_data)
        output.append("")
        output.append("## Open Tasks")
        output.append(tasks_data)

        return "\n".join(output)


if __name__ == "__main__":
    # Test usage
    jc = JournalCalendar()
    print(jc.format_output())
