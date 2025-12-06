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
        journal_calendar_prompt = """
Analyze this personal data and provide a concise Journal+Calendar brief with these three subsections:

## Calendar Review
- Note any events that seem significant or unusual (non-routine)
- Highlight today's events and any important upcoming events

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
        journal_calendar_prompt = """
Analyze this personal data and provide a concise Evening Journal+Calendar brief with these three subsections:

## Calendar Review
- Note yesterday's completed events and any follow-up needed
- Preview tomorrow's key events

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
Your job is to generate a news briefing from pre-clustered articles.
The articles below have been clustered by similarity - articles in the same cluster cover related topics.
There must be inline markdown links `[article title](url)` to the original sources for these articles.

- News Intelligence Brief
    - Review each cluster and synthesize the main story
    - At most 7 total stories (clusters can be combined if covering the same broader theme)
    - Please make these stories of interest if there are articles to substantiate them:
        - Epstein files
        - AI model developments
        - AI hardware developments
        - AI datacenter developments
        - Local Longmont news
        - Astronomy / Space news
- For each story, indicate if it's:
    - A continuing story (if there are articles from multiple days in the cluster)
    - A new story (if articles are all from today)
- Note any major topics from previous days that are no longer in the news

# Begin clustered news:
"""
        print("Fetching and clustering news articles...")
        out2 = claude.Claude().generate(preprompt+news_prompt+ news.News().pull_data())
        content_sections.append(f"# Daily News Intelligence Brief\n\n{out2}")
    else:
        # Evening: Brief headlines only
        news_prompt="""
Your job is to generate a brief evening news summary from pre-clustered articles.
The articles below have been clustered by similarity - each cluster represents a story.
There must be inline markdown links `[article title](url)` to the original sources for these articles.
- Present at most 5 top headlines from today (selecting the most significant clusters)
- Focus on the most significant stories
- One sentence per headline
- Topics of interest: Epstein files, AI developments, AI hardware, AI datacenters, Local Longmont news, Astronomy/Space news

# Begin clustered news:
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
5. Ensure section headers are clear and well-organized
6. Fix any awkward phrasing

Do NOT:
- Remove any data or facts
- Remove any markdown links
- Add new information not present in the original
- Change the overall structure or number of sections

Return the polished briefing maintaining all original sections and their order.

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
