#!/usr/bin/env python3
"""
Fetch AI news articles from specified RSS feeds
"""

import json
import sys
from feeds import Feeds

def fetch_ai_news():
    """Fetch articles from AI-focused RSS feeds"""
    
    ai_feeds = [
        "https://www.microsoft.com/en-us/research/feed/",
        "https://www.nature.com/nature.rss", 
        "https://tldr.tech/api/rss/ai"
    ]
    
    print("Fetching AI news articles from:")
    for feed in ai_feeds:
        print(f"  - {feed}")
    
    try:
        # Fetch articles from the past 7 days
        articles = Feeds.fetch_articles(ai_feeds, days=7)
        
        # Convert articles to JSON-serializable format
        articles_data = []
        for article in articles:
            article_dict = {
                "title": article.title,
                "url": article.url,
                "source": article.source,
                "summary": article.summary,
                "published_at": article.published_at,
                "keywords": article.keywords
            }
            articles_data.append(article_dict)
        
        # Create response
        response = {
            "status": "success",
            "feeds_fetched": ai_feeds,
            "total_articles": len(articles_data),
            "articles": articles_data
        }
        
        return response
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "feeds_attempted": ai_feeds
        }

if __name__ == "__main__":
    result = fetch_ai_news()
    print(json.dumps(result, indent=2))