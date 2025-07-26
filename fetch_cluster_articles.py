#!/usr/bin/env python3
"""
Script to fetch and cluster articles from specified RSS feeds
"""

import json
from collections import defaultdict
from feeds import Feeds
from datamodel import Article, Group

# RSS feeds to process
FEED_URLS = [
    # Local and world news
    "https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.theatlantic.com/feed/all/",
    "https://heathercoxrichardson.substack.com/feed",
    
    # Cultural interest
    "https://rss.metafilter.com/metafilter.rss",
    "https://acoup.blog/feed/",
    
    # AI articles
    "https://www.microsoft.com/en-us/research/feed/",
    "https://www.nature.com/nature.rss",
    "https://tldr.tech/api/rss/ai",
    
    # Local news
    "https://www.longmontleader.com/rss/"
]

def cluster_articles_mathematically(articles):
    """Simplified clustering approach based on keyword matching"""
    if len(articles) < 2:
        for i, article in enumerate(articles):
            article.cluster = i
        return articles
    
    # Predefined tags for clustering
    tags = [
        'Russia', 'Ukraine', 'NATO', 'Israel', 'Palestine', 'Hamas', 'Gaza',
        'China', 'Taiwan', 'Iran', 'Houthis', 'European Union',
        'United Kingdom', 'Germany', 'France', 'Japan', 'South Korea', 'Australia',
        'Canada', 'Mexico', 'Brazil', 'Argentina', 'Turkey', 'Saudi Arabia',
        'United States', 'Joe Biden', 'Trump', 'Donald Trump', 'India',
        'Artificial Intelligence', 'Machine Learning', 'ChatGPT', 'OpenAI', 'AI',
        'Technology', 'Science', 'Climate Change', 'Energy', 'Space',
        'Politics', 'Economy', 'Finance', 'Healthcare', 'Education',
        'Election', 'Democracy', 'War', 'Military', 'Defense',
        'Research', 'Study', 'Data', 'Innovation', 'Development'
    ]
    
    # Simple keyword matching and clustering
    for i, article in enumerate(articles):
        article_text = f"{article.title} {article.summary}".lower()
        matched_keywords = []
        for tag in tags:
            if tag.lower() in article_text:
                matched_keywords.append(tag)
        article.keywords = matched_keywords[:5]  # Limit to top 5
        
        # Simple hash-based clustering from keywords
        if matched_keywords:
            cluster_hash = hash(frozenset(matched_keywords[:2]))  # Use top 2 keywords for clustering
            article.cluster = abs(cluster_hash) % 8  # Limit to 8 clusters
        else:
            article.cluster = 0  # Default cluster for articles without keywords
    
    return articles

def make_labelled_groups(articles):
    """Convert clustered articles to labeled groups"""
    cluster_groups = defaultdict(list)
    for article in articles:
        cluster_groups[article.cluster].append(article)
    
    groups = {}
    for cluster_id, cluster_articles in cluster_groups.items():
        # Generate group label from top keywords
        keys = defaultdict(int)
        for article in cluster_articles:
            for keyword in article.keywords:
                keys[keyword] += 1
        
        if keys:
            top_keywords = sorted(keys.items(), key=lambda x: x[1], reverse=True)
            headline = ", ".join([keyword for keyword, count in top_keywords[:3]])
        else:
            headline = f"Miscellaneous News"
        
        groups[cluster_id] = Group(text=headline, articles=cluster_articles)
    
    return groups

def main():
    print("Fetching articles from RSS feeds...")
    
    # Fetch articles
    articles = Feeds.fetch_articles(FEED_URLS, days=1)
    print(f"Fetched {len(articles)} articles")
    
    if not articles:
        print("No articles found")
        return
    
    # Cluster articles
    print("Clustering articles...")
    clustered_articles = cluster_articles_mathematically(articles)
    groups = make_labelled_groups(clustered_articles)
    
    # Convert to JSON for output
    groups_data = {}
    for group_id, group in groups.items():
        groups_data[str(group_id)] = {
            "text": group.text,
            "article_count": len(group.articles),
            "articles": []
        }
        for article in group.articles:
            groups_data[str(group_id)]["articles"].append({
                "title": article.title,
                "url": article.url,
                "source": article.source,
                "summary": article.summary[:300] + "..." if len(article.summary) > 300 else article.summary,
                "keywords": article.keywords
            })
    
    result = {
        "groups": groups_data,
        "total_articles": len(articles),
        "group_count": len(groups_data),
        "feeds_processed": len(FEED_URLS)
    }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()