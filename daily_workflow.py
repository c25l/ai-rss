#!/usr/bin/env python3
import ollama
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
import journal_calendar
import stocks
import astronomy
from datamodel import Article
import os
import google_auth
import cross_reference
import archive

def main():
    dotenv.load_dotenv("/Media/source/airss/.env")
    os.chdir("/Media/source/airss/")
    articles = []
    content_sections = []

    # Step 1: Refresh Google OAuth tokens if needed
    print("Checking Google OAuth tokens...")
    try:
        google_auth.get_google_credentials()
        print("✓ Google credentials refreshed")
    except Exception as e:
        print(f"Warning: Could not refresh Google credentials: {e}")


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
        top_continuing = news_obj.rank_clusters(categorized['continuing'], 'continuing', top_k=3)
        top_new = news_obj.rank_clusters(categorized['new'], 'new', top_k=5)
        top_dormant = news_obj.rank_clusters(categorized['dormant'], 'dormant', top_k=2)

        # Format output ourselves (no AI summarization)
        news_output = []

        if top_continuing:
            news_output.append("## Continuing Coverage")
            for group in top_continuing:
                rep_article = group.articles[0] if group.articles else None
                if rep_article:
                    news_output.append(f"**[{rep_article.title}]({rep_article.url})** ({len(group.articles)} new articles today, {group.total_count} total)<br/>")

        if top_new:
            news_output.append("\n## New Today")
            for group in top_new:
                rep_article = group.articles[0] if group.articles else None
                if rep_article:
                    news_output.append(f"**[{rep_article.title}]({rep_article.url})** ({len(group.articles)} articles)<br/>")

        if top_dormant:
            news_output.append("\n## No Longer in the News")
            for group in top_dormant:
                title = getattr(group, 'representative_title', 'Unknown')
                news_output.append(f"**{title}** ({group.total_count} articles from previous days)<br/>")

        content_sections.append(f"# Daily News Intelligence Brief\n\n" + "\n".join(news_output))
        print("✓ News Intelligence Brief generated")
    except Exception as e:
        print(f"Warning: Could not generate News Intelligence Brief: {e}")
        content_sections.append(f"# Daily News Intelligence Brief\n\nError generating news briefing: {e}")

# Tech News
    try:
        print("Fetching and ranking tech news articles...")
        tech_obj = tech_news.TechNews()
        tech_output = tech_obj.pull_data(days=1, top_k=5, use_ranking=True)

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
        out4 = ollama.Ollama().generate(preprompt+research_prompt+rsch)
        content_sections.append(f"# Research Preprints\n\n{out4}")

    # Combine all sections
    final_content = "\n\n---\n\n".join(content_sections)

    # Prepare subject for archive and email
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    subject = f"H3LPeR - {today}"

    # Archive the briefing
    try:
        archiver = archive.Archiver()
        archiver.save_briefing(
            content_markdown=final_content,
            subject=subject,
            metadata={"article_count": len(articles) if articles else 0}
        )
        print(f"✓ Briefing archived and available in webapp")
    except Exception as e:
        print(f"Warning: Could not archive briefing: {e}")

    # Send email with simplified styling
    try:
        emailer.Emailer().send_email(final_content, subject=subject)
        print("✓ Email sent")
    except Exception as e:
        print(f"Warning: Could not send email: {e}")

if __name__ == "__main__":
    main()
