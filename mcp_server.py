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
env_path = '/Media/source/H3lPeR/.env'
print(load_dotenv(dotenv_path=env_path))

# Import all modules
from weather import Weather
from spaceweather import SpaceWeather
from emailer import Emailer
from journal import Journal
from research import Research
from stocks import Stocks
from astronomy import Astronomy
from notifier import Notifier

# Initialize FastMCP server
mcp = FastMCP("airss")

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
# JOURNAL & RESEARCH
# ============================================================================

@mcp.tool()
def get_journal_entries(days: int = 7) -> str:
    """
    Get recent journal entries and open tasks from Obsidian.

    Args:
        days: Number of days to retrieve (default 7)

    Returns:
        Formatted journal content
    """
    try:
        journal = Journal()
        journal.pull_data(days=days)
        return journal.output()
    except Exception as e:
        return f"Error accessing journal: {str(e)}"


@mcp.tool()
def search_journal_entries(search_term: str, days: int = 30) -> str:
    """
    Search Obsidian journal entries for a specific term.

    Args:
        search_term: Text to search for (case-insensitive)
        days: Number of days to search back (default 30)

    Returns:
        JSON string with matching journal entries
    """
    try:
        journal = Journal()
        results = journal.search_entries(search_term, days=days)

        if not results:
            return json.dumps({"message": f"No entries found containing '{search_term}'"}, indent=2)

        # Format results
        formatted_results = {
            "search_term": search_term,
            "matches_found": len(results),
            "entries": []
        }

        for result in results:
            formatted_results["entries"].append({
                "date": result["date"],
                "content": result["content"][:500] + "..." if len(result["content"]) > 500 else result["content"]
            })

        return json.dumps(formatted_results, indent=2)
    except Exception as e:
        return f"Error searching journal: {str(e)}"


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
# NOTIFICATIONS
# ============================================================================

@mcp.tool()
def send_notification(message: str) -> str:
    """
    Send a plain text notification via ntfy.sh to alert the user.

    Args:
        message: The notification text to send

    Returns:
        Success or failure message
    """
    try:
        notifier = Notifier()
        success = notifier.send(message)
        return "Notification sent successfully" if success else "Failed to send notification"
    except Exception as e:
        return f"Error sending notification: {str(e)}"


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    mcp.run()
