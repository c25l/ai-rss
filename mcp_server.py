#!/usr/bin/env /home/chris/miniforge3/bin/python3
"""
AIRSS MCP Server - Exposes daily workflow functionality via FastMCP
"""
from fastmcp import FastMCP
from datetime import datetime
from typing import Optional
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = '/home/chris/source/airss/.env'
print(load_dotenv(dotenv_path=env_path))

# Import all modules
from weather import Weather
from spaceweather import SpaceWeather
from emailer import Emailer
from gcal import Calendar
from gtasks import Tasks
from journal import Journal
from research import Research
from stocks import Stocks
from astronomy import Astronomy

# Initialize FastMCP server
mcp = FastMCP("airss", dependencies=["feedparser", "requests", "bs4", "caldav", "icalendar", "markdown", "python-dotenv"])

# ============================================================================
# WEATHER & SPACE WEATHER
# ============================================================================

@mcp.tool()
def get_weather_forecast(max_periods: int = 6) -> str:
    """Get weather forecast for the next few periods (default 6)."""
    weather = Weather()
    return weather.format_forecast(max_periods=max_periods)


@mcp.tool()
def get_spaceweather_forecast() -> str:
    """Get current space weather conditions and forecast."""
    spaceweather = SpaceWeather()
    return spaceweather.format_forecast()


@mcp.tool()
def get_astronomy_tonight() -> str:
    """Get tonight's astronomical visibility - planets, moon, ISS passes, constellations."""
    astronomy = Astronomy()
    return astronomy.format_output()


# ============================================================================
# STOCK MARKET DATA
# ============================================================================

@mcp.tool()
def get_stock_quote(symbol: str) -> str:
    """
    Get real-time quote for a single stock symbol.

    Args:
        symbol: Stock ticker symbol (e.g., 'MSFT', 'NVDA', '^DJI', '^GSPC')

    Returns:
        Formatted stock quote string
    """
    try:
        stocks = Stocks()
        quote = stocks.get_quote(symbol)
        if quote:
            return stocks.format_quote(quote)
        return f"No data available for {symbol}"
    except Exception as e:
        return f"Error fetching stock data: {str(e)}"


@mcp.tool()
def get_stock_summary(symbols: Optional[str] = None) -> str:
    """
    Get stock market summary for multiple symbols.

    Args:
        symbols: Comma-separated stock symbols (default: 'MSFT,NVDA,^DJI,^GSPC')

    Returns:
        Formatted stock summary string
    """
    try:
        stocks = Stocks()
        if symbols:
            symbol_list = [s.strip() for s in symbols.split(',')]
            return stocks.format_summary(symbol_list)
        return stocks.format_summary()
    except Exception as e:
        return f"Error fetching stock data: {str(e)}"


# ============================================================================
# RSS FEEDS
# ============================================================================

@mcp.tool()
def get_feed_articles(feed_url: str, days: int = 1) -> str:
    """
    Fetch articles from an RSS feed.

    Args:
        feed_url: URL of the RSS feed
        days: Number of days back to fetch articles (default 1)

    Returns:
        Formatted string with article information
    """
    articles = Feeds.get_articles(feed_url, days=days)
    if not articles:
        return "No articles found."

    output = []
    for article in articles:
        output.append(article.out_rich())

    return "\n\n".join(output)


# ============================================================================
# EMAIL
# ============================================================================

@mcp.tool()
def send_email(content: str, subject: Optional[str] = None, to_addr: Optional[str] = None) -> str:
    """
    Send an email with markdown content.

    Args:
        content: Email body (supports markdown)
        subject: Email subject (optional)
        to_addr: Recipient email address (optional, defaults to FROM_EMAIL)

    Returns:
        Success message
    """
    emailer = Emailer()
    emailer.send_email(content, subject, to_addr)
    return f"Email sent successfully to {to_addr or emailer.from_email}"


@mcp.tool()
def read_inbox(limit: int = 20) -> str:
    """
    Read recent emails from inbox.

    Args:
        limit: Maximum number of emails to retrieve (default 20)

    Returns:
        JSON string with email list
    """
    emailer = Emailer()
    emails = emailer.read_inbox(limit=limit)

    # Clean up for JSON serialization (remove internal objects)
    clean_emails = []
    for email in emails:
        clean_emails.append({
            "subject": email["subject"],
            "from": email["from"],
            "date": email["date"],
            "snippet": email["snippet"]
        })

    return json.dumps(clean_emails, indent=2)


@mcp.tool()
def read_starred_emails(limit: int = 20) -> str:
    """
    Read starred/flagged emails.

    Args:
        limit: Maximum number of emails to retrieve (default 20)

    Returns:
        JSON string with starred email list
    """
    emailer = Emailer()
    emails = emailer.read_starred(limit=limit)

    clean_emails = []
    for email in emails:
        clean_emails.append({
            "subject": email["subject"],
            "from": email["from"],
            "date": email["date"],
            "snippet": email["snippet"]
        })

    return json.dumps(clean_emails, indent=2)


@mcp.tool()
def search_emails(query: str, limit: int = 20) -> str:
    """
    Search emails by subject or sender.

    Args:
        query: Search term (searches in subject and from fields)
        limit: Maximum number of results (default 20)

    Returns:
        JSON string with matching emails
    """
    emailer = Emailer()
    emails = emailer.search_emails(query, limit=limit)

    clean_emails = []
    for email in emails:
        clean_emails.append({
            "subject": email["subject"],
            "from": email["from"],
            "date": email["date"],
            "snippet": email["snippet"]
        })

    return json.dumps(clean_emails, indent=2)


@mcp.tool()
def send_matching_drafts() -> str:
    """
    Find and send drafts that match criteria:
    - Subject is a date (YYYY-MM-DD, yyyymmdd, yymmdd, YY-MM-DD)
    - OR recipient is cpbnel.news@gmail.com

    All matching drafts are sent to cpbnel.news@gmail.com with today's date as subject.
    Drafts are deleted after sending.

    Returns:
        JSON string with sent count and details
    """
    emailer = Emailer()
    result = emailer.send_matching_drafts()
    return json.dumps(result, indent=2)


# ============================================================================
# CALENDAR
# ============================================================================

@mcp.tool()
def list_calendars() -> str:
    """
    List all available Google Calendars (including shared calendars).

    Returns:
        JSON string with calendar list including ID, name, and access role
    """
    cal = Calendar()
    calendars = cal.list_calendars()
    return json.dumps(calendars, indent=2)


@mcp.tool()
def get_upcoming_events(days: int = 7, limit: int = 20) -> str:
    """
    Get upcoming calendar events from all calendars (including shared family calendars).

    Args:
        days: Number of days ahead to look (default 7)
        limit: Maximum number of events (default 20)

    Returns:
        JSON string with event list
    """
    cal = Calendar()
    events = cal.get_upcoming_events(days=days, limit=limit)

    clean_events = []
    for event in events:
        clean_events.append({
            "title": event["title"],
            "start": event["start"].isoformat(),
            "end": event["end"].isoformat(),
            "description": event["description"],
            "location": event["location"],
            "calendar": event.get("calendar_name", "Unknown")
        })

    return json.dumps(clean_events, indent=2)


@mcp.tool()
def search_calendar_events(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    title_contains: Optional[str] = None,
    limit: int = 50
) -> str:
    """
    Search calendar events by date range and/or title.

    Args:
        start_date: Start date in ISO format (YYYY-MM-DD) (optional)
        end_date: End date in ISO format (YYYY-MM-DD) (optional)
        title_contains: Search term for event title (optional)
        limit: Maximum number of results (default 50)

    Returns:
        JSON string with matching events
    """
    cal = Calendar()

    # Convert date strings to datetime objects if provided
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None

    events = cal.search_events(
        start_date=start_dt,
        end_date=end_dt,
        title_contains=title_contains,
        limit=limit
    )

    clean_events = []
    for event in events:
        clean_events.append({
            "title": event["title"],
            "start": event["start"].isoformat(),
            "end": event["end"].isoformat(),
            "description": event["description"],
            "location": event["location"],
            "calendar": event.get("calendar_name", "Unknown")
        })

    return json.dumps(clean_events, indent=2)


@mcp.tool()
def create_calendar_event(
    title: str,
    start: str,
    end: str,
    description: str = "",
    location: str = ""
) -> str:
    """
    Create a new calendar event.

    Args:
        title: Event title
        start: Start datetime in ISO format (YYYY-MM-DDTHH:MM:SS)
        end: End datetime in ISO format (YYYY-MM-DDTHH:MM:SS)
        description: Event description (optional)
        location: Event location (optional)

    Returns:
        Confirmation message with event details
    """
    cal = Calendar()

    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)

    result = cal.create_event(
        title=title,
        start=start_dt,
        end=end_dt,
        description=description,
        location=location
    )

    return f"Event created: {result['title']} on {result['start'].strftime('%Y-%m-%d %H:%M')}"


@mcp.tool()
def delete_calendar_event_by_title(title: str, start_date: str) -> str:
    """
    Delete a calendar event by title and start date.

    Args:
        title: Exact title of the event to delete
        start_date: Start date in ISO format (YYYY-MM-DD) to narrow search

    Returns:
        Confirmation message
    """
    cal = Calendar()

    # Search for the event
    start_dt = datetime.fromisoformat(start_date)
    end_dt = start_dt.replace(hour=23, minute=59, second=59)

    events = cal.search_events(
        start_date=start_dt,
        end_date=end_dt,
        title_contains=title,
        limit=10
    )

    # Find exact match
    for event in events:
        if event["title"] == title:
            result = cal.delete_event(event)
            return f"Event deleted: {result['title']}"

    return f"No event found with title '{title}' on {start_date}"


# ============================================================================
# GOOGLE TASKS
# ============================================================================

@mcp.tool()
def get_task_lists() -> str:
    """
    Get all Google Tasks task lists.

    Returns:
        JSON string with task list information
    """
    tasks = Tasks()
    task_lists = tasks.get_task_lists()

    return json.dumps(task_lists, indent=2)


@mcp.tool()
def get_tasks(tasklist_id: str = '@default', show_completed: bool = False, limit: int = 100) -> str:
    """
    Get tasks from a specific task list.

    Args:
        tasklist_id: ID of task list (default: '@default' for default list)
        show_completed: Include completed tasks (default: False)
        limit: Maximum number of tasks (default: 100)

    Returns:
        JSON string with task list
    """
    tasks = Tasks()
    task_list = tasks.get_tasks(
        tasklist_id=tasklist_id,
        show_completed=show_completed,
        limit=limit
    )

    clean_tasks = []
    for task in task_list:
        clean_tasks.append({
            "title": task["title"],
            "notes": task["notes"],
            "status": task["status"],
            "is_completed": task["is_completed"],
            "due": task["due"].isoformat() if task["due"] else None,
            "completed": task["completed"].isoformat() if task["completed"] else None
        })

    return json.dumps(clean_tasks, indent=2)


@mcp.tool()
def get_all_tasks(show_completed: bool = False, limit: int = 100) -> str:
    """
    Get tasks from all task lists.

    Args:
        show_completed: Include completed tasks (default: False)
        limit: Maximum number of tasks per list (default: 100)

    Returns:
        JSON string with all tasks
    """
    tasks = Tasks()
    all_tasks = tasks.get_all_tasks(show_completed=show_completed, limit=limit)

    clean_tasks = []
    for task in all_tasks:
        clean_tasks.append({
            "title": task["title"],
            "notes": task["notes"],
            "status": task["status"],
            "is_completed": task["is_completed"],
            "list_name": task.get("list_name", "Unknown"),
            "due": task["due"].isoformat() if task["due"] else None,
            "completed": task["completed"].isoformat() if task["completed"] else None
        })

    return json.dumps(clean_tasks, indent=2)


@mcp.tool()
def create_task(
    title: str,
    notes: str = "",
    due: Optional[str] = None,
    tasklist_id: str = '@default'
) -> str:
    """
    Create a new Google Task.

    Args:
        title: Task title
        notes: Task description/notes (optional)
        due: Due date in ISO format YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS (optional)
        tasklist_id: ID of task list (default: '@default')

    Returns:
        Confirmation message with task details
    """
    tasks = Tasks()

    due_dt = datetime.fromisoformat(due) if due else None

    result = tasks.create_task(
        title=title,
        notes=notes,
        due=due_dt,
        tasklist_id=tasklist_id
    )

    due_str = f" (due: {result['due'].strftime('%Y-%m-%d')})" if result['due'] else ""
    return f"Task created: {result['title']}{due_str}"


@mcp.tool()
def complete_task(title: str, tasklist_id: str = '@default') -> str:
    """
    Mark a task as completed by title.

    Args:
        title: Exact title of the task to complete
        tasklist_id: ID of task list (default: '@default')

    Returns:
        Confirmation message
    """
    tasks = Tasks()

    # Get tasks from the list
    task_list = tasks.get_tasks(tasklist_id=tasklist_id, show_completed=False, limit=100)

    # Find exact match
    for task in task_list:
        if task["title"] == title:
            result = tasks.complete_task(task)
            return f"Task completed: {result['title']}"

    return f"No task found with title '{title}' in list {tasklist_id}"


@mcp.tool()
def update_task(
    title: str,
    tasklist_id: str = '@default',
    new_title: Optional[str] = None,
    notes: Optional[str] = None,
    due: Optional[str] = None,
    status: Optional[str] = None
) -> str:
    """
    Update an existing task by title.

    Args:
        title: Current title of the task to update
        tasklist_id: ID of task list (default: '@default')
        new_title: New title (optional)
        notes: New notes (optional)
        due: New due date in ISO format YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS (optional)
        status: New status - 'completed' or 'needsAction' (optional)

    Returns:
        Confirmation message
    """
    tasks = Tasks()

    # Get tasks from the list
    task_list = tasks.get_tasks(tasklist_id=tasklist_id, show_completed=True, limit=100)

    # Find exact match
    for task in task_list:
        if task["title"] == title:
            due_dt = datetime.fromisoformat(due) if due else None
            result = tasks.update_task(
                task,
                title=new_title,
                notes=notes,
                due=due_dt,
                status=status
            )
            return f"Task updated: {result['title']}"

    return f"No task found with title '{title}' in list {tasklist_id}"


@mcp.tool()
def uncomplete_task(title: str, tasklist_id: str = '@default') -> str:
    """
    Mark a task as not completed (reopen it) by title.

    Args:
        title: Exact title of the task to uncomplete
        tasklist_id: ID of task list (default: '@default')

    Returns:
        Confirmation message
    """
    tasks = Tasks()

    # Get tasks from the list (include completed to find it)
    task_list = tasks.get_tasks(tasklist_id=tasklist_id, show_completed=True, limit=100)

    # Find exact match
    for task in task_list:
        if task["title"] == title:
            result = tasks.uncomplete_task(task)
            return f"Task reopened: {result['title']}"

    return f"No task found with title '{title}' in list {tasklist_id}"


@mcp.tool()
def delete_task(title: str, tasklist_id: str = '@default') -> str:
    """
    Delete a task by title.

    Args:
        title: Exact title of the task to delete
        tasklist_id: ID of task list (default: '@default')

    Returns:
        Confirmation message
    """
    tasks = Tasks()

    # Get tasks from the list
    task_list = tasks.get_tasks(tasklist_id=tasklist_id, show_completed=True, limit=100)

    # Find exact match
    for task in task_list:
        if task["title"] == title:
            result = tasks.delete_task(task)
            return f"Task deleted: {result['title']}"

    return f"No task found with title '{title}' in list {tasklist_id}"


# ============================================================================
# JOURNAL & RESEARCH
# ============================================================================

@mcp.tool()
def get_journal_entries() -> str:
    """
    Get recent journal entries and open tasks from Obsidian.

    Returns:
        Formatted journal content
    """
    try:
        journal = Journal()
        journal.pull_data()
        return journal.output()
    except Exception as e:
        return f"Error accessing journal: {str(e)}"


@mcp.tool()
def get_research_articles() -> str:
    """
    Get recent research articles from arXiv feeds.

    Returns:
        Formatted research articles
    """
    try:
        research = Research()
        return research.pull_data()
    except Exception as e:
        return f"Error fetching research articles: {str(e)}"


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    mcp.run()
