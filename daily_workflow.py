#!/usr/bin/env python
import datetime
import hashlib
import json
import requests
import dotenv
from bs4 import BeautifulSoup
import weather
import research
import spaceweather
import news
import tech_news
import stocks
import astronomy
from datamodel import Article
import os
import sys
from emailer import Emailer

BRIEFING_ARCHIVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "briefings")


def _markdown_to_json_briefing(content_sections, date_str):
    """Convert markdown content sections to JSON briefing format."""
    children = []
    
    for section in content_sections:
        # Split into title and content
        lines = section.strip().split('\n', 1)
        if not lines:
            continue
            
        title = lines[0].strip('#').strip()
        text = lines[1].strip() if len(lines) > 1 else ""
        
        children.append({
            "title": title,
            "text": text
        })
    
    return {
        "schema_version": 1,
        "title": f"H3LPeR Daily Briefing - {date_str}",
        "date": date_str,
        "model": "stable-workflow",
        "children": children
    }


def main():
    # Load environment - use .env from current directory or specify via ENV_FILE
    env_file = os.getenv("ENV_FILE", ".env")
    if os.path.exists(env_file):
        dotenv.load_dotenv(env_file)
    
    # Change to working directory if specified
    work_dir = os.getenv("WORK_DIR")
    if work_dir and os.path.exists(work_dir):
        os.chdir(work_dir)
    
    articles = []
    content_sections = []


    preprompt="""
        Please be concise and to the point in your summaries.
        Do not introduce or conclude, do not summarize the work done unless specifically asked to.
    """

# Weather, space weather, and astronomy
    weather_forecast = weather.Weather().format_forecast()
    spaceweather_forecast = spaceweather.SpaceWeather().format_forecast()

    # Get astronomical viewing data
    try:
        print("Fetching astronomical visibility data...")
        astro = astronomy.Astronomy()
        astro_info = astro.format_output()
    except Exception as e:
        print(f"Warning: Could not fetch astronomical data: {e}")
        astro_info = "Error fetching tonight's sky data"

    out1 = f"## Weather Forecast\n\n{weather_forecast}\n\n## Space Weather\n\n{spaceweather_forecast}\n\n## Tonight's Sky\n\n{astro_info}"
    content_sections.append(f"# Daily Weather, Space & Sky Summary\n\n{out1}")



# News Intelligence Brief
    try:
        print("Fetching and clustering news articles...")
        news_obj = news.News()
        categorized = news_obj.pull_data(return_structured=True)

        # Rank each category
        print("Ranking news clusters...")
        top_continuing = news_obj.rank_clusters(categorized['continuing'], 'continuing', top_k=5)
        top_new = news_obj.rank_clusters(categorized['new'], 'new', top_k=7)
        top_dormant = news_obj.rank_clusters(categorized['dormant'], 'dormant', top_k=3)

        # Format output ourselves (no AI summarization)
        news_output = []

        if top_continuing:
            news_output.append("## Continuing Coverage")
            for group in top_continuing:
                rep_article = group.articles[0] if group.articles else None
                if rep_article:
                    news_output.append(f"- **[{rep_article.title}]({rep_article.url})** ({len(group.articles)} new articles today, {group.total_count} total)")

        if top_new:
            news_output.append("\n## New Today")
            for group in top_new:
                rep_article = group.articles[0] if group.articles else None
                if rep_article:
                    news_output.append(f"- **[{rep_article.title}]({rep_article.url})** ({len(group.articles)} articles)")

        if top_dormant:
            news_output.append("\n## No Longer in the News")
            for group in top_dormant:
                title = getattr(group, 'representative_title', 'Unknown')
                news_output.append(f"- **{title}** ({group.total_count} articles from previous days)")

        content_sections.append(f"# Daily News Intelligence Brief\n\n" + "\n".join(news_output))
        print("✓ News Intelligence Brief generated")
    except Exception as e:
        print(f"Warning: Could not generate News Intelligence Brief: {e}")
        content_sections.append(f"# Daily News Intelligence Brief\n\nError generating news briefing: {e}")

# Tech News
    try:
        print("Fetching and ranking tech news articles...")
        tech_obj = tech_news.TechNews()
        tech_output = tech_obj.pull_data(days=1, top_k=7, use_ranking=True)

        content_sections.append(f"# Tech News\n\n{tech_output}")
        print("✓ Tech News generated")
    except Exception as e:
        print(f"Warning: Could not generate Tech News: {e}")
        content_sections.append(f"# Tech News\n\nError generating tech news: {e}")

# Stock Market Data
    try:
        stock_summary = stocks.Stocks().format_summary(['MSFT', 'NVDA', '^DJI', '^GSPC'])
        content_sections.append(f"# Market Close Summary\n\n{stock_summary}")
    except Exception as e:
        print(f"Warning: Could not fetch stock data: {e}")

# Research Preprints
    research_prompt = """
I want at most 5 preprints about:
    - training or inference of ai models at scale.
    - especially including design of infrastructure and new hardware
please return the document
Please make sure to include inline markdown links `[article title](url)` to the original sources for these articles.

# Begin research articles:

"""
    rsch = research.Research(use_dual_ranker=False).pull_data()
    if len(rsch.strip().split("\n"))<3:
        rsch="No new research articles found."
    else:
        from copilot import Copilot
        out4 = Copilot().generate(preprompt+research_prompt+rsch)
        content_sections.append(f"# Research Preprints\n\n{out4}")

    # Combine all sections
    final_content = "\n\n---\n\n".join(content_sections)
    
    # Create JSON briefing document
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    today_short = datetime.datetime.now().strftime("%y%m%d")
    briefing_doc = _markdown_to_json_briefing(content_sections, today)
    
    # Archive the JSON briefing
    try:
        os.makedirs(BRIEFING_ARCHIVE_DIR, exist_ok=True)
        # Use a simple hash for the filename (like agent workflow)
        doc_hash = hashlib.sha256(json.dumps(briefing_doc, sort_keys=True).encode()).hexdigest()[:12]
        archive_name = f"{today_short}-{doc_hash}.json"
        archive_path = os.path.join(BRIEFING_ARCHIVE_DIR, archive_name)
        with open(archive_path, "w") as f:
            json.dump(briefing_doc, f, indent=2, default=str)
        print(f"✓ Briefing archived to {archive_path}")
    except Exception as e:
        print(f"Warning: Could not archive briefing: {e}")

    # Send email using JSON format
    try:
        subject = f"H3LPeR Daily Briefing - {today}"
        
        emailer = Emailer()
        emailer.send_email_json(briefing_doc, subject=subject)
        
        print(f"✓ H3LPeR report emailed successfully")
    except Exception as e:
        print(f"ERROR: Failed to send H3LPeR email: {e}")
        sys.exit(1)
    
    # Run citation analysis (always run to keep data fresh)
    try:
        from citations_data import generate_and_save_citations
        print("\nRunning citation analysis on research papers...")
        citation_data = generate_and_save_citations(days=1, top_n=50, min_citations=1)
        if citation_data:
            print(f"✓ Citation analysis complete: {citation_data['paper_count']} papers")
        else:
            print("⚠ Citation analysis had no results")
    except Exception as e:
        print(f"⚠ Citation analysis error: {e}")
    
    # Publish to static site (opt-in via PAGES_DIR env var)
    site_dir = os.environ.get("PAGES_DIR") or os.environ.get("GITHUB_PAGES_DIR")
    if site_dir:
        try:
            from publish_site import publish_briefing
            if publish_briefing(site_dir=site_dir):
                print("✓ Static site published")
            else:
                print("⚠ Static site publish skipped or failed")
        except Exception as e:
            print(f"⚠ Static site publish error: {e}")

if __name__ == "__main__":
    main()
