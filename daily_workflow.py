#!/usr/bin/env python
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
import tech_news
import stocks
import astronomy
from datamodel import Article
import os
import sys
import google_auth

def main():
    dotenv.load_dotenv("/home/chris/source/airss/.env")
    os.chdir("/home/chris/source/airss/")
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
    rsch = research.Research().pull_data()
    if len(rsch.strip().split("\n"))<3:
        rsch="No new research articles found."
    else:
        out4 = claude.Claude().generate(preprompt+research_prompt+rsch)
        content_sections.append(f"# Research Preprints\n\n{out4}")

    # Combine all sections
    final_content = "\n\n---\n\n".join(content_sections)

    # Send email with daily report
    try:
        email_sender = emailer.Emailer()
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        subject = f"H3LPeR {today}"

        email_sender.send_email(
            content=final_content,
            subject=subject,
            to_addr=None  # Uses TO_EMAIL from .env
        )
        print(f"✓ H3LPeR report emailed successfully to {email_sender.to_email}")
    except Exception as e:
        print(f"ERROR: Failed to send H3LPeR email: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
