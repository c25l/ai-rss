#!/usr/bin/env python3
"""
Cross-Reference Module for AIRSS Daily Briefing
Detects conflicts and opportunities between calendar events, tasks, and weather forecasts.
"""

from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
import re
from gcal import Calendar
from gtasks import Tasks
import weather as weather_module
import ollama
from cache import Cache


class CrossReference:
    """
    Generates intelligent cross-referencing insights by analyzing:
    - Calendar events (from gcal.py)
    - Tasks (from gtasks.py)
    - Weather forecasts (from weather.py)

    Uses Claude LLM for natural language understanding and synthesis.
    """

    def __init__(self):
        self.calendar = Calendar()
        self.tasks = Tasks()
        self.weather = weather_module.Weather()
        self.cache = Cache()

    def _parse_weather_data(self):
        """
        Parse weather.py HTML output to extract structured forecast periods.
        Uses cache to avoid redundant HTTP requests (1-hour TTL).

        Returns:
            list of dicts: Forecast periods with structure:
                {
                    'name': str (e.g., "This Afternoon", "Tonight"),
                    'description': str (full forecast text),
                    'has_rain': bool,
                    'has_snow': bool,
                    'temperature': int or None
                }
            Returns empty list if parsing fails.
        """
        # Check cache first
        cached = self.cache.get_weather()
        if cached is not None:
            return cached

        try:
            html = self.weather.pull_data()
            if html == "failed":
                print("Warning: Weather data fetch failed")
                return []

            soup = BeautifulSoup(html, "html.parser")
            periods = soup.find_all("div", class_="row-forecast")

            if not periods:
                print("Warning: No weather forecast periods found")
                return []

            forecast_periods = []
            for period in periods[:6]:  # Get first 6 periods (today through tomorrow)
                label_div = period.find("div", class_="forecast-label")
                text_div = period.find("div", class_="forecast-text")

                if not label_div or not text_div:
                    continue

                name = label_div.get_text(strip=True)
                description = text_div.get_text(strip=True)

                # Detect weather conditions
                desc_lower = description.lower()
                has_rain = 'rain' in desc_lower or 'shower' in desc_lower
                has_snow = 'snow' in desc_lower

                # Extract temperature
                temp_match = re.search(r'\b(high|low)\s+(?:near\s+)?(\d+)', description, re.IGNORECASE)
                temperature = int(temp_match.group(2)) if temp_match else None

                forecast_periods.append({
                    'name': name,
                    'description': description,
                    'has_rain': has_rain,
                    'has_snow': has_snow,
                    'temperature': temperature
                })

            # Cache the parsed weather data
            if forecast_periods:
                self.cache.set_weather(forecast_periods)

            return forecast_periods

        except Exception as e:
            print(f"Warning: Weather parsing failed: {e}")
            return []

    def get_structured_data(self, edition="morning"):
        """
        Extract structured data from all sources (calendar, tasks, weather).
        Uses cache for calendar/tasks (daily TTL) and weather (1-hour TTL).

        Args:
            edition: "morning" or "evening" - affects which events are prioritized

        Returns:
            dict with keys:
                - all_events: list of event dicts
                - today_events: list of today's event dicts
                - tomorrow_events: list of tomorrow's event dicts
                - tasks: list of task dicts
                - weather_periods: list of weather period dicts
        """
        try:
            now = datetime.now()
            today = now.date()
            tomorrow = (now + timedelta(days=1)).date()

            # Get calendar events - try API first, cache as fallback
            yesterday = now - timedelta(days=1)
            future = now + timedelta(days=14)
            try:
                all_events = self.calendar.search_events(
                    start_date=yesterday,
                    end_date=future,
                    limit=100
                )
                # Cache fresh data for fallback
                self.cache.set_calendar(all_events)
            except Exception as e:
                print(f"  Google Calendar API failed, trying cache: {e}")
                all_events = self.cache.get_calendar()
                if all_events is None:
                    print("  No cached calendar data available")
                    all_events = []

            # Filter events by date
            today_events = [e for e in all_events if e['start'].date() == today]
            tomorrow_events = [e for e in all_events if e['start'].date() == tomorrow]

            # Get incomplete tasks - try API first, cache as fallback
            try:
                tasks = self.tasks.get_all_tasks(show_completed=False, limit=100)
                # Cache fresh data for fallback
                self.cache.set_tasks(tasks)
            except Exception as e:
                print(f"  Google Tasks API failed, trying cache: {e}")
                tasks = self.cache.get_tasks()
                if tasks is None:
                    print("  No cached tasks data available")
                    tasks = []

            # Get weather forecast
            weather_periods = self._parse_weather_data()

            return {
                'all_events': all_events,
                'today_events': today_events,
                'tomorrow_events': tomorrow_events,
                'tasks': tasks,
                'weather_periods': weather_periods
            }

        except Exception as e:
            print(f"Warning: Failed to get structured data: {e}")
            return {
                'all_events': [],
                'today_events': [],
                'tomorrow_events': [],
                'tasks': [],
                'weather_periods': []
            }

    def _serialize_for_json(self, obj):
        """Helper to serialize datetime objects for JSON"""
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        return obj

    def _build_morning_prompt(self, data):
        """
        Build Claude prompt for morning edition insights.

        Args:
            data: dict from get_structured_data()

        Returns:
            str: Prompt for Claude
        """
        now = datetime.now()
        today = now.strftime("%A, %B %d, %Y")

        # Prepare clean event data for JSON (remove internal _event_id, _calendar_id)
        clean_events = []
        for event in data['today_events']:
            clean_events.append({
                'title': event['title'],
                'start': self._serialize_for_json(event['start']),
                'end': self._serialize_for_json(event['end']),
                'location': event.get('location', ''),
                'description': event.get('description', ''),
                'calendar': event.get('calendar_name', 'Unknown')
            })

        # Prepare clean task data
        clean_tasks = []
        for task in data['tasks']:
            # Only include tasks that are urgent (due within 7 days or no due date)
            if task.get('due'):
                days_until_due = (task['due'].date() - now.date()).days
                if days_until_due > 7:
                    continue  # Skip tasks due far in future

            clean_tasks.append({
                'title': task['title'],
                'notes': task.get('notes', ''),
                'due': self._serialize_for_json(task['due']) if task.get('due') else 'No due date',
                'list': task.get('list_name', 'Unknown')
            })

        # Build prompt
        prompt = f"""Analyze this personal data and identify smart cross-references and conflicts.

TODAY: {today}

# CALENDAR EVENTS (today only)
{json.dumps(clean_events, indent=2)}

# TASKS (urgent tasks - due within 7 days or no due date)
{json.dumps(clean_tasks, indent=2)}

# WEATHER FORECAST (today through tomorrow)
{json.dumps(data['weather_periods'], indent=2)}

YOUR TASK: Identify and report ONLY the following types of insights:

1. **Weather Conflicts** (HIGH PRIORITY)
   - Calendar events that may be affected by rain/snow (look for outdoor keywords: outdoor, park, garden, walk, hike, picnic, sports, etc.)
   - Tasks that appear outdoor-related during bad weather periods
   - Format: "⚠️ [Event/Task title] at [time] may conflict with [weather condition]"

2. **Preparation Reminders** (MEDIUM PRIORITY)
   - Events today or tomorrow that might need special preparation
   - Format: "📋 Prep needed for [event]: [suggestion]"

3. **Time Blocking Opportunities** (LOW PRIORITY)
   - Identify gaps in today's calendar that are >= 2 hours long
   - Suggest which urgent tasks (due within 3 days) could fit in those gaps
   - Format: "⏰ [X] hours free from [time]-[time], could complete: [task title]"

CRITICAL RULES:
- Be concise - maximum 5 insights total
- Only mention TRUE conflicts/opportunities based on the data provided
- Do NOT fabricate events, tasks, or weather conditions
- Prioritize weather conflicts above all else
- If outdoor keywords are not present, do NOT assume an event is outdoor
- Format each insight on its own line with <br/> at the end
- If no meaningful insights exist, return empty string

OUTPUT FORMAT:
- Simple bulleted list with emoji prefixes
- Each item ends with <br/>
- No introductory text or conclusions
- Return empty string if no insights found

Example output:
⚠️ "Garden work" task scheduled during afternoon thunderstorms (60% rain, 2-5pm)<br/>
⏰ 3 hours free from 10am-1pm, could complete: Submit quarterly report (due Dec 12)<br/>
"""

        return prompt

    def _build_evening_prompt(self, data):
        """
        Build Claude prompt for evening edition insights (focus on tomorrow).

        Args:
            data: dict from get_structured_data()

        Returns:
            str: Prompt for Claude
        """
        now = datetime.now()
        tomorrow = (now + timedelta(days=1)).strftime("%A, %B %d, %Y")

        # Prepare clean event data for tomorrow
        clean_events = []
        for event in data['tomorrow_events']:
            clean_events.append({
                'title': event['title'],
                'start': self._serialize_for_json(event['start']),
                'end': self._serialize_for_json(event['end']),
                'location': event.get('location', ''),
                'description': event.get('description', ''),
                'calendar': event.get('calendar_name', 'Unknown')
            })

        # Get only very urgent tasks (due within 3 days)
        clean_tasks = []
        for task in data['tasks']:
            if task.get('due'):
                days_until_due = (task['due'].date() - now.date()).days
                if days_until_due <= 3:
                    clean_tasks.append({
                        'title': task['title'],
                        'due': self._serialize_for_json(task['due']),
                        'notes': task.get('notes', '')
                    })

        # Get tomorrow's weather (periods that contain "tomorrow" or specific day name)
        tomorrow_weather = [p for p in data['weather_periods']
                          if 'tomorrow' in p['name'].lower() or tomorrow.split(',')[0] in p['name']]

        prompt = f"""Analyze tomorrow's schedule and identify key preparation needs.

TOMORROW: {tomorrow}

# TOMORROW'S EVENTS
{json.dumps(clean_events, indent=2)}

# URGENT TASKS (due within 3 days)
{json.dumps(clean_tasks, indent=2)}

# TOMORROW'S WEATHER
{json.dumps(tomorrow_weather, indent=2)}

YOUR TASK: Provide brief tomorrow prep tips (maximum 3 items):

1. Weather-related prep (if outdoor events conflict with rain/snow)
2. Time blocking suggestions (if gaps exist and urgent tasks need completion)
3. Meeting prep reminders (if significant meetings are scheduled)

RULES:
- Maximum 3 items total
- Only TRUE insights based on provided data
- Format each item with <br/> at the end
- No introductory text
- Return empty string if no prep needed

OUTPUT FORMAT:
- Bulleted list with emoji prefixes (⚠️ 📋 ⏰)
- Each item ends with <br/>

Example:
⚠️ Tomorrow's 2pm outdoor event may conflict with afternoon rain (70% chance)<br/>
⏰ 2-hour gap from 10am-12pm, complete urgent task: File taxes (due Dec 13)<br/>
"""

        return prompt

    def generate_insights(self, edition="morning"):
        """
        Main entry point - generate cross-reference insights using Claude.

        Args:
            edition: "morning" or "evening"

        Returns:
            str: Markdown-formatted insights with <br/> tags, or empty string if no insights
        """
        try:
            # Get structured data
            data = self.get_structured_data(edition)

            # Check if we have any data to work with
            if edition == "morning":
                if not data['today_events'] and not data['tasks'] and not data['weather_periods']:
                    print("No data available for morning cross-referencing")
                    return ""
            else:  # evening
                if not data['tomorrow_events'] and not data['tasks'] and not data['weather_periods']:
                    print("No data available for evening cross-referencing")
                    return ""

            # Build appropriate prompt
            if edition == "morning":
                prompt = self._build_morning_prompt(data)
            else:
                prompt = self._build_evening_prompt(data)

            # Generate insights using Ollama
            print(f"Generating {edition} cross-reference insights...")
            result = ollama.Ollama().generate(prompt)

            # Clean up result
            if result:
                result = result.strip()
                # Ensure we have <br/> tags if there are multiple lines
                if result and '\n' in result and '<br/>' not in result:
                    lines = [line.strip() for line in result.split('\n') if line.strip()]
                    result = '<br/>'.join(lines)

            return result if result else ""

        except Exception as e:
            print(f"Warning: Cross-reference insights generation failed: {e}")
            import traceback
            traceback.print_exc()
            return ""


if __name__ == "__main__":
    # Test the module
    print("Testing CrossReference module...\n")

    cr = CrossReference()

    # Test weather parsing
    print("=== Weather Parsing Test ===")
    weather_data = cr._parse_weather_data()
    print(f"Found {len(weather_data)} weather periods:")
    for period in weather_data:
        print(f"  - {period['name']}: {period['description'][:50]}...")

    # Test structured data extraction
    print("\n=== Structured Data Test ===")
    data = cr.get_structured_data(edition="morning")
    print(f"Today's events: {len(data['today_events'])}")
    print(f"Tomorrow's events: {len(data['tomorrow_events'])}")
    print(f"Tasks: {len(data['tasks'])}")
    print(f"Weather periods: {len(data['weather_periods'])}")

    # Test insights generation
    print("\n=== Morning Insights Test ===")
    insights = cr.generate_insights(edition="morning")
    if insights:
        print("Generated insights:")
        print(insights)
    else:
        print("No insights generated")

    print("\n=== Evening Insights Test ===")
    insights = cr.generate_insights(edition="evening")
    if insights:
        print("Generated insights:")
        print(insights)
    else:
        print("No insights generated")
