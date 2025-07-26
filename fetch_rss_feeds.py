#!/usr/bin/env python3
"""
Direct RSS feed fetching script for the requested feeds
"""
import json
from feeds import Feeds

def fetch_categorized_feeds():
    """Fetch RSS feeds organized by category"""
    
    # Define feed categories
    feed_categories = {
        "Local and World News": [
            "https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
            "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", 
            "https://www.theatlantic.com/feed/all/",
            "https://heathercoxrichardson.substack.com/feed"
        ],
        "Cultural Interest": [
            "https://rss.metafilter.com/metafilter.rss",
            "https://acoup.blog/feed/"
        ],
        "AI Articles": [
            "https://www.microsoft.com/en-us/research/feed/",
            "https://www.nature.com/nature.rss",
            "https://tldr.tech/api/rss/ai"
        ],
        "Local Longmont News": [
            "https://www.longmontleader.com/rss/",
            "https://www.reddit.com/r/Longmont/.rss"
        ]
    }
    
    results = {}
    
    for category, feeds in feed_categories.items():
        print(f"\nFetching {category}...")
        try:
            articles = Feeds.fetch_articles(feeds, days=1)
            results[category] = {
                "feed_count": len(feeds),
                "feeds": feeds,
                "article_count": len(articles),
                "articles": []
            }
            
            for article in articles:
                results[category]["articles"].append({
                    "title": article.title,
                    "url": article.url,
                    "source": article.source,
                    "summary": article.summary,
                    "published_at": article.published_at
                })
                
            print(f"Found {len(articles)} articles in {category}")
            
        except Exception as e:
            print(f"Error fetching {category}: {e}")
            results[category] = {
                "feed_count": len(feeds),
                "feeds": feeds,
                "article_count": 0,
                "articles": [],
                "error": str(e)
            }
    
    return results

if __name__ == "__main__":
    results = fetch_categorized_feeds()
    
    # Save to file
    with open("fetched_articles_categorized.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("\n=== RESULTS SUMMARY ===")
    total_articles = 0
    for category, data in results.items():
        print(f"\n{category}:")
        print(f"  Feeds: {data['feed_count']}")
        print(f"  Articles: {data['article_count']}")
        if "error" in data:
            print(f"  Error: {data['error']}")
        else:
            total_articles += data['article_count']
            
    print(f"\nTotal articles fetched: {total_articles}")