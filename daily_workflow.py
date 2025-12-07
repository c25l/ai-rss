#!/usr/bin/env python3
import claude
import datetime
import requests
import dotenv
from bs4 import BeautifulSoup
import weather
import research
import spaceweather
import emailer
import news
import journal_calendar
import stocks
import astronomy
from datamodel import Article
import os
import google_auth

def determine_edition():
    """Determine if this is a morning or evening edition based on current time"""
    current_hour = datetime.datetime.now().hour
    # Before noon (12:00) = morning, after = evening
    return "morning" if current_hour < 12 else "evening"

def main(edition=None):
    dotenv.load_dotenv("/Media/source/airss/.env")
    os.chdir("/Media/source/airss/")
    articles = []
    content_sections = []

    # Determine edition type
    if edition is None:
        edition = determine_edition()

    edition_title = "Morning" if edition == "morning" else "Evening"

    # Step 0: Refresh Google OAuth tokens if needed
    print("Checking Google OAuth tokens...")
    try:
        google_auth.get_google_credentials()
        print("✓ Google credentials refreshed")
    except Exception as e:
        print(f"Warning: Could not refresh Google credentials: {e}")

    # Step 1: Check and send matching drafts
    print("Checking for matching draft emails to send...")
    try:
        em = emailer.Emailer()
        draft_result = em.send_matching_drafts()
        if draft_result['sent'] > 0:
            print(f"Sent {draft_result['sent']} draft email(s) to cpbnel.news@gmail.com")
            for detail in draft_result['details']:
                if 'error' not in detail:
                    print(f"  - Original subject: '{detail['original_subject']}' -> Sent as: '{detail['sent_subject']}'")
        else:
            print("No matching drafts found.")
    except Exception as e:
        print(f"Warning: Could not process drafts: {e}")

    preprompt="""
        Please be concise and to the point in your summaries.
        Do not introduce or conclude, do not summarize the work done unless specifically asked to.
    """

# Subtask 1: Generate weather and space weather summaries (edition-dependent)
    if edition == "morning":
        # Morning: Full weather forecast
        weather_forecast = weather.Weather().format_forecast()
        spaceweather_forecast = spaceweather.SpaceWeather().format_forecast()
        out1 = f"## Weather Forecast\n\n{weather_forecast}\n\n## Space Weather\n\n{spaceweather_forecast}"
        content_sections.append(f"# Daily Weather and Space Weather Summary\n\n{out1}")
    else:
        # Evening: Brief weather summary (fewer periods)
        weather_summary = weather.Weather().format_forecast(max_periods=3)
        out1 = f"## Weather Summary\n\n{weather_summary}"
        content_sections.append(f"# Weather Summary\n\n{out1}")

# Subtask 2: Journal+Calendar Section (edition-dependent)
    journal_calendar_data = journal_calendar.JournalCalendar().format_output()

    if edition == "morning":
        today_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
        journal_calendar_prompt = f"""
Today is {today_date}.

Analyze this personal data and provide a concise Journal+Calendar brief with these three subsections:

IMPORTANT CONTEXT ABOUT CALENDARS:
- "Personal" calendar = MY events (things I need to do)
- All other calendars (<other>@gmail.com, School, HOME, etc.) = OTHER PEOPLE's movements and family logistics
- Consider how others' schedules might affect my day or require coordination

## Calendar Review
- Note MY events (from Personal calendar) that are significant or unusual
- Highlight family/household logistics from other calendars that I should be aware of
- Flag any potential conflicts or coordination needs between my schedule and others'
- Focus on today's events and important upcoming events

## Journal Themes
- Identify 2-3 main themes or patterns from recent journal entries
- Keep it brief and insightful

## Open Tasks
- Present the tasks in priority order as shown (by due date)
- Highlight any that seem particularly urgent for today

Please be concise and actionable. Do not add fluff or unnecessary commentary.

# Begin data:

"""
    else:
        # Evening: Focus on completed tasks and reflection
        today_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
        journal_calendar_prompt = f"""
Today is {today_date}.

Analyze this personal data and provide a concise Evening Journal+Calendar brief with these three subsections:

IMPORTANT CONTEXT ABOUT CALENDARS:
- "Personal" calendar = MY events (things I did/need to do)
- All other calendars  (<other>@gmail.com, School, HOME, etc.) = OTHER PEOPLE's movements and family logistics
- Consider how others' schedules affected or will affect my activities

## Calendar Review
- Note MY completed events from yesterday (Personal calendar) and any follow-up needed
- Preview tomorrow's key events for both me and family logistics
- Flag any coordination needs for tomorrow

## Journal Themes
- Identify key themes or insights from today's activities
- Keep it brief and reflective

## Task Progress
- Show which tasks were completed today (if visible in data)
- Highlight remaining urgent tasks for tomorrow

Please be concise and reflective. Focus on the day's accomplishments and tomorrow's priorities.

# Begin data:

"""

    out3 = claude.Claude().generate(preprompt + journal_calendar_prompt + journal_calendar_data)
    content_sections.append(f"# Journal+Calendar\n\n{out3}")

# Subtask 3: News Intelligence Brief (edition-dependent)
    if edition == "morning":
        news_prompt="""
Your job is to generate a news briefing from pre-clustered and pre-categorized articles.

IMPORTANT: The articles below have been AUTOMATICALLY CATEGORIZED into these groups:
1. CONTINUING STORIES - Stories with ongoing coverage from previous days (only today's new articles are shown)
2. NEW STORIES - Stories appearing for the first time today
3. SINGLE ARTICLES - Standalone articles not part of a larger story
4. DORMANT STORIES - Stories that had coverage before but none today (disappeared from the news)

Your task:
- Select the TOP 3 most significant CONTINUING STORIES
- Select the TOP 3 most significant NEW STORIES
- Select the TOP 3 most significant SINGLE ARTICLES
- Note 2 DORMANT STORIES that fell out of the news (if available)
- For each story, provide ONE best representative headline/link as a markdown link `[headline](url)`
- Write a 1-2 sentence summary synthesizing the key points

Prioritize these topics if present:
- Epstein files
- AI model developments (models, training, inference)
- AI hardware developments
- AI datacenter developments
- Local Longmont news
- Astronomy / Space news

Output format:
## Continuing Coverage (Top 3)
[Story headline with link] - Brief synthesis

## New Today (Top 3)
[Story headline with link] - Brief synthesis

## Worth Noting (Top 3 Standalone Articles)
[Article headline with link] - Brief summary

## No Longer in the News (Up to 2)
[Story that disappeared] - What it was about

# Begin pre-categorized clustered news:
"""
        print("Fetching and clustering news articles...")
        out2 = claude.Claude().generate(preprompt+news_prompt+ news.News().pull_data())
        content_sections.append(f"# Daily News Intelligence Brief\n\n{out2}")
    else:
        # Evening: Brief headlines only
        news_prompt="""
Your job is to generate a brief evening news summary from pre-categorized articles.

The articles have been AUTOMATICALLY CATEGORIZED into:
- CONTINUING STORIES (ongoing coverage)
- NEW STORIES (first appearance today)
- SINGLE ARTICLES (standalone)
- DORMANT STORIES (disappeared from news)

Your task:
- Select the TOP 5 most significant stories across all categories
- For each, provide ONE headline as a markdown link `[headline](url)` and one sentence summary
- Indicate whether each is CONTINUING or NEW
- Topics of interest: Epstein files, AI developments, AI hardware, AI datacenters, Local Longmont news, Astronomy/Space news

# Begin pre-categorized clustered news:
"""
        print("Fetching and clustering news articles...")
        out2 = claude.Claude().generate(preprompt+news_prompt+ news.News().pull_data())
        content_sections.append(f"# Evening News Headlines\n\n{out2}")
# Subtask 4: Stock Market Data (evening only)
    if edition == "evening":
        try:
            stock_summary = stocks.Stocks().format_summary(['MSFT', 'NVDA', '^DJI', '^GSPC'])
            content_sections.append(f"# Market Close Summary\n\n{stock_summary}")
        except Exception as e:
            print(f"Warning: Could not fetch stock data: {e}")

# Subtask 4.5: Astronomical Visibility (evening only)
    if edition == "evening":
        try:
            print("Fetching astronomical visibility data...")
            astro = astronomy.Astronomy()
            astro_info = astro.format_output()
            content_sections.append(f"# Tonight's Sky\n\n{astro_info}")
        except Exception as e:
            print(f"Warning: Could not fetch astronomical data: {e}")

# Subtask 5: Research Preprints (morning only - full research, evening skips)
    if edition == "morning":
        research_prompt = """
I want at most 5 preprints about:
    - training or inference of ai models at scale.
    - especially including design of infrastructure and new hardware
please return the document
Please make sure to include inline markdown links `[article title](url)` to the original sources for these articles.

# Begin research articles:

"""
        rsch = research.Research().pull_data()
        if len(rsch.strip().split("\n"))<3:
            rsch="No new research articles found."
        else:
            out4 = claude.Claude().generate(preprompt+research_prompt+rsch)
            content_sections.append(f"# Research Preprints\n\n{out4}")

    # Combine all sections
    combined_content = "\n\n---\n\n".join(content_sections)

    # Final polish pass: have Claude review and clean up the entire briefing
    print("Running final polish pass...")
    polish_prompt = f"""Review and polish this {edition.lower()} briefing. Your tasks:

1. Remove any redundancies or repetitive information
2. Ensure consistent formatting throughout (use <br/> for line breaks in HTML sections)
3. Improve flow and readability
4. Keep all important information and links
5. Streamline headers - flatten hierarchy where appropriate, remove redundant headers/subheaders
6. Fix any awkward phrasing

The reader knows what to expect in this briefing format. Don't be afraid to simplify the structure - if a header and subheader say essentially the same thing, consolidate them. Aim for a clean, flat hierarchy.

Do NOT:
- Remove any data or facts
- Remove any markdown links
- Add new information not present in the original

Return the polished briefing with streamlined headers and improved flow.

---

{combined_content}
"""

    try:
        final_content = claude.Claude().generate(polish_prompt)
    except Exception as e:
        print(f"Warning: Polish pass failed, using unpolished content: {e}")
        final_content = combined_content

    # Send via emailer with edition-specific subject
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    subject = f"{edition_title} Briefing - {today}"
    emailer.send_email(final_content, subject=subject)

if __name__ == "__main__":
    main()
