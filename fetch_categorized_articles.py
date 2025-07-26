#!/usr/bin/env python3
"""
Fetch RSS articles organized by category for newsletter workflow
"""

import json
from datetime import datetime
from feeds import Feeds

def main():
    """Fetch articles from multiple RSS feeds organized by category"""
    
    # RSS feeds organized by category
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
        "Local": [
            "https://www.longmontleader.com/rss/"
        ]
    }
    
    results = {}
    total_articles = 0
    
    print("Fetching articles from RSS feeds organized by category...")
    print("=" * 60)
    
    for category, feed_urls in feed_categories.items():
        print(f"\n📰 {category}")
        print("-" * 40)
        
        try:
            # Fetch articles from feeds in this category
            articles = Feeds.fetch_articles(feed_urls, days=1)
            
            # Convert articles to serializable format
            article_data = []
            for article in articles:
                article_data.append({
                    "title": article.title,
                    "url": article.url,
                    "source": article.source,
                    "summary": article.summary[:200] + "..." if len(article.summary) > 200 else article.summary,
                    "published_at": article.published_at
                })
            
            results[category] = {
                "article_count": len(articles),
                "articles": article_data
            }
            
            total_articles += len(articles)
            
            print(f"✅ Found {len(articles)} articles")
            for article in articles[:3]:  # Show first 3 articles as preview
                print(f"   • {article.title}")
            if len(articles) > 3:
                print(f"   ... and {len(articles) - 3} more")
                
        except Exception as e:
            print(f"❌ Error fetching from {category}: {str(e)}")
            results[category] = {
                "article_count": 0,
                "articles": [],
                "error": str(e)
            }
    
    print("\n" + "=" * 60)
    print(f"📊 SUMMARY: Fetched {total_articles} total articles across {len(results)} categories")
    
    # Save results to JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"categorized_articles_{timestamp}.json"
    
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "total_articles": total_articles,
        "categories": results
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"💾 Results saved to: {output_file}")
    
    return output_data

if __name__ == "__main__":
    main()