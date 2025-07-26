#!/usr/bin/env python3
"""
Script to fetch articles from specific feeds for testing purposes
"""
import json
from feeds import Feeds
from datamodel import Article

def fetch_specific_feeds():
    """Fetch articles from the specified US and World news feeds"""
    target_feeds = [
        "https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://www.theatlantic.com/feed/all/",
        "https://heathercoxrichardson.substack.com/feed"
    ]
    
    print(f"Fetching articles from {len(target_feeds)} feeds...")
    articles = Feeds.fetch_articles(target_feeds, days=1)
    
    # Convert articles to JSON-serializable format
    articles_data = []
    for article in articles:
        article_dict = {
            "title": article.title,
            "url": article.url,
            "source": article.source,
            "summary": article.summary,
            "keywords": article.keywords,
            "published_at": article.published_at
        }
        articles_data.append(article_dict)
    
    result = {
        "feed_count": len(target_feeds),
        "article_count": len(articles_data),
        "feeds": target_feeds,
        "articles": articles_data,
        "timestamp": "2025-07-12"
    }
    
    return json.dumps(result, indent=2)

if __name__ == "__main__":
    result = fetch_specific_feeds()
    print(result)