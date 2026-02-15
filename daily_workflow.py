#!/usr/bin/env python
import datetime
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
from datamodel import Article, Group
import os
import sys
from emailer import Emailer


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



# News Intelligence Brief (includes Bluesky articles)
    try:
        print("Fetching and clustering news articles...")
        news_obj = news.News()
        categorized = news_obj.pull_data(return_structured=True)
        
        # Fetch Bluesky posts and extract article links to add to news
        try:
            print("Fetching Bluesky timeline for article links...")
            from atproto import Client
            import re
            
            bluesky_handle = os.environ.get('BLUESKY_HANDLE')
            bluesky_password = os.environ.get('BLUESKY_APP_PASSWORD')
            
            if bluesky_handle and bluesky_password:
                client = Client()
                client.login(bluesky_handle, bluesky_password)
                
                # Fetch home timeline
                response = client.app.bsky.feed.get_timeline({'limit': 30})
                
                # Extract article URLs from Bluesky posts
                bluesky_articles = []
                url_pattern = re.compile(r'https?://[^\s]+')
                
                if hasattr(response, 'feed') and response.feed:
                    for item in response.feed:
                        if hasattr(item, 'post') and item.post:
                            post = item.post
                            author = post.author if hasattr(post, 'author') else None
                            author_handle = author.handle if author and hasattr(author, 'handle') else 'unknown'
                            
                            record = post.record if hasattr(post, 'record') else None
                            text = record.text if record and hasattr(record, 'text') else ''
                            
                            # Find URLs in post text
                            urls = url_pattern.findall(text)
                            for url in urls:
                                # Skip Bluesky app links themselves
                                if 'bsky.app' not in url:
                                    # Create an Article from the URL
                                    article = Article(
                                        title=text[:100] + "..." if len(text) > 100 else text,
                                        url=url,
                                        summary=text,
                                        source=f"bluesky:{author_handle}",
                                        published_at=datetime.datetime.now()
                                    )
                                    bluesky_articles.append(article)
                
                # Add Bluesky articles to the 'new' category for clustering
                if bluesky_articles:
                    print(f"✓ Extracted {len(bluesky_articles)} article links from Bluesky")
                    # Wrap each Bluesky article in a Group object for compatibility
                    for article in bluesky_articles:
                        group = Group(
                            id=f"bluesky_{article.url}",
                            text=article.title,
                            articles=[article]
                        )
                        group.total_count = 1
                        group.today_count = 1
                        categorized['new'].append(group)
                else:
                    print("⚠ No article links found in Bluesky posts")
            else:
                print("⚠ Bluesky credentials not configured")
        except ImportError:
            print("⚠ atproto library not installed (pip install atproto)")
        except Exception as e:
            print(f"Warning: Could not fetch Bluesky articles: {e}")

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

# Quick Citation Analysis
    try:
        print("Running quick citation analysis on research papers...")
        from citations_data import run_citation_analysis
        
        # Run a quick analysis with lower thresholds for email display
        citation_data = run_citation_analysis(days=1, top_n=10, min_citations=1)
        
        if citation_data and citation_data.get('papers'):
            citation_output = []
            for paper in citation_data['papers'][:10]:  # Show top 10
                title = paper.get('title', 'Untitled')
                url = paper.get('url', '')
                citations = paper.get('citation_count', 0)
                
                if url:
                    citation_output.append(f"- [{title}]({url}) ({citations} citations)")
                else:
                    citation_output.append(f"- {title} ({citations} citations)")
            
            if citation_output:
                content_sections.append(f"# Top Cited Research Papers\n\n" + "\n".join(citation_output))
                print(f"✓ Citation analysis complete: {len(citation_output)} papers")
        else:
            print("⚠ No citation data available")
    except Exception as e:
        print(f"Warning: Could not run citation analysis: {e}")

    # Combine all sections
    final_content = "\n\n---\n\n".join(content_sections)

    # Send email (simple markdown format)
    try:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        subject = f"H3LPeR Daily Briefing - {today}"
        
        emailer = Emailer()
        emailer.send_email(final_content, subject=subject)
        
        print(f"✓ H3LPeR report emailed successfully")
    except Exception as e:
        print(f"ERROR: Failed to send H3LPeR email: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
