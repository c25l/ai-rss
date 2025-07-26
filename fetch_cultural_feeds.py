#!/usr/bin/env python3
"""
Fetch articles from cultural interest feeds and return as JSON
"""
import json
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from feeds import Feeds

def fetch_cultural_articles():
    """Fetch articles from cultural interest feeds"""
    cultural_feeds = [
        "https://rss.metafilter.com/metafilter.rss",
        "https://acoup.blog/feed/"
    ]
    
    print("Fetching articles from cultural interest feeds...", file=sys.stderr)
    articles = Feeds.fetch_articles(cultural_feeds, days=1)
    print(f"Fetched {len(articles)} articles", file=sys.stderr)
    
    # Convert articles to JSON format
    articles_data = []
    for article in articles:
        articles_data.append({
            "title": article.title,
            "url": article.url,
            "source": article.source,
            "summary": article.summary,
            "published_at": article.published_at
        })
    
    result = {
        "articles": articles_data,
        "total_articles": len(articles_data),
        "feeds": cultural_feeds
    }
    
    return result

if __name__ == "__main__":
    result = fetch_cultural_articles()
    print(json.dumps(result, indent=2))