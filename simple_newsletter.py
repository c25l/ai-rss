#!/usr/bin/env python3
"""
Simple newsletter generation without MCP complexity to test the workflow
"""
import sys
sys.path.append('.')

import feeds
from datamodel import Article, Group
from collections import defaultdict

def simple_cluster_articles(articles):
    """Simple clustering by keywords"""
    tags = [
        'Russia', 'Ukraine', 'NATO', 'Israel', 'Palestine', 'Hamas', 'Gaza',
        'China', 'Taiwan', 'Iran', 'Houthis', 'European Union',
        'United Kingdom', 'Germany', 'France', 'Japan', 'South Korea', 'Australia',
        'Canada', 'Mexico', 'Brazil', 'Argentina', 'Turkey', 'Saudi Arabia',
        'United States', 'Joe Biden', 'Trump', 'India',
        'Artificial Intelligence', 'Machine Learning', 'ChatGPT', 'OpenAI',
        'Technology', 'Science', 'Climate Change', 'Energy', 'Space',
        'Politics', 'Economy', 'Finance', 'Healthcare', 'Education'
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
            article.cluster = abs(cluster_hash) % 10  # Limit to 10 clusters
        else:
            article.cluster = 0  # Default cluster for articles without keywords
    
    return articles

def make_groups(articles):
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
            headline = f"Group {cluster_id}"
        
        groups[cluster_id] = Group(text=headline, articles=cluster_articles)
    
    return groups

def generate_newsletter_content(groups):
    """Generate newsletter markdown content"""
    content = f"# AIRSS Newsletter - 2025-06-28\n\n"
    
    for group_id, group in groups.items():
        if len(group.articles) < 2:  # Skip small groups
            continue
            
        content += f"## {group.text}\n\n"
        
        for article in group.articles:
            content += f"- **[{article.title}]({article.url})** - {article.source}\n"
            if article.summary:
                content += f"  {article.summary[:200]}...\n"
            content += "\n"
    
    return content

def main():
    try:
        print("Fetching articles...")
        articles = feeds.Feeds.fetch_articles(feeds.FEEDS)
        print(f"Got {len(articles)} articles")
        
        print("Clustering articles...")
        clustered = simple_cluster_articles(articles)
        
        print("Creating groups...")
        groups = make_groups(clustered)
        print(f"Created {len(groups)} groups")
        
        print("Generating newsletter...")
        newsletter = generate_newsletter_content(groups)
        
        print("Newsletter generated:")
        print("=" * 50)
        print(newsletter)
        
        return newsletter
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()