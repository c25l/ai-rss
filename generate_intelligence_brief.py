#!/usr/bin/env python3
"""
Generate Intelligence Brief from RSS feeds
"""

import json
from datetime import datetime
from collections import defaultdict
from feeds import Feeds
from datamodel import Article

def load_feeds():
    """Load RSS feed URLs from feeds.txt"""
    feeds = []
    try:
        with open('feeds.txt', 'r') as f:
            content = f.read()
            # Parse each line as a Python list
            for line in content.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and line.endswith('],'):
                    try:
                        # Remove trailing comma and eval
                        feed_data = eval(line[:-1])  # Remove comma and parse
                        if len(feed_data) >= 3:
                            feeds.append(feed_data[2])  # URL is the 3rd element
                    except Exception as e:
                        print(f"Error parsing line: {line} - {e}")
                        continue
    except FileNotFoundError:
        print("feeds.txt not found, using default feeds")
    
    # Add some default feeds if none loaded
    if not feeds:
        feeds = [
            "https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
            "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
            "https://www.theatlantic.com/feed/all/",
            "https://www.nature.com/nature.rss",
            "https://rss.metafilter.com/metafilter.rss",
            "https://heathercoxrichardson.substack.com/feed",
            "https://www.microsoft.com/en-us/research/feed/",
            "https://tldr.tech/api/rss/ai"
        ]
    
    return feeds

def cluster_articles_with_keywords(articles):
    """Simple clustering based on keyword matching"""
    # Intelligence-focused tags
    tags = [
        'Trump', 'Biden', 'United States', 'Politics', 'Election', 'Congress',
        'Russia', 'Ukraine', 'NATO', 'Putin', 'War', 'Military', 'Defense',
        'China', 'Taiwan', 'Xi Jinping', 'Trade', 'Economy', 'Sanctions',
        'Israel', 'Palestine', 'Hamas', 'Gaza', 'Middle East', 'Iran',
        'European Union', 'Germany', 'France', 'United Kingdom', 'Brexit',
        'Artificial Intelligence', 'AI', 'Technology', 'Cybersecurity', 'Cyber',
        'Climate Change', 'Energy', 'Oil', 'Nuclear', 'Renewable',
        'COVID', 'Health', 'Medicine', 'Disease', 'Pandemic',
        'Space', 'NASA', 'Satellite', 'Rocket',
        'Finance', 'Market', 'Stock', 'Inflation', 'Federal Reserve'
    ]
    
    # Assign keywords and cluster
    for article in articles:
        article_text = f"{article.title} {article.summary}".lower()
        matched_keywords = []
        for tag in tags:
            if tag.lower() in article_text:
                matched_keywords.append(tag)
        article.keywords = matched_keywords[:5]
        
        # Cluster based on primary keywords
        if matched_keywords:
            # Use top 2-3 keywords for clustering
            cluster_key = frozenset(matched_keywords[:3])
            article.cluster = abs(hash(cluster_key)) % 8  # 8 clusters
        else:
            article.cluster = 7  # Miscellaneous cluster
    
    return articles

def create_labeled_groups(articles):
    """Create labeled groups from clustered articles"""
    cluster_groups = defaultdict(list)
    for article in articles:
        cluster_groups[article.cluster].append(article)
    
    groups = {}
    for cluster_id, cluster_articles in cluster_groups.items():
        # Generate group label from top keywords
        keyword_counts = defaultdict(int)
        for article in cluster_articles:
            for keyword in article.keywords:
                keyword_counts[keyword] += 1
        
        if keyword_counts:
            top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
            headline = ", ".join([keyword for keyword, count in top_keywords[:3]])
        else:
            headline = f"Miscellaneous News"
        
        groups[cluster_id] = {
            'text': headline,
            'articles': cluster_articles,
            'count': len(cluster_articles)
        }
    
    return groups

def generate_intelligence_brief_markdown(groups):
    """Generate intelligence brief in markdown format"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Filter out entertainment/sports content
    filtered_groups = {}
    exclude_keywords = ['music', 'band', 'concert', 'album', 'song', 'singer', 'artist', 
                       'sport', 'football', 'basketball', 'baseball', 'game', 'team', 
                       'player', 'match', 'championship']
    
    for group_id, group in groups.items():
        # Check if group should be excluded
        group_text_lower = group['text'].lower()
        should_exclude = any(keyword in group_text_lower for keyword in exclude_keywords)
        
        if should_exclude:
            continue
            
        # Also filter articles within groups
        filtered_articles = []
        for article in group['articles']:
            article_text = f"{article.title} {article.summary}".lower()
            article_should_exclude = any(keyword in article_text for keyword in exclude_keywords)
            if not article_should_exclude:
                filtered_articles.append(article)
        
        if filtered_articles:  # Only keep groups with remaining articles
            filtered_groups[group_id] = {
                'text': group['text'],
                'articles': filtered_articles,
                'count': len(filtered_articles)
            }
    
    # Sort groups by article count (descending)
    sorted_groups = sorted(filtered_groups.items(), key=lambda x: x[1]['count'], reverse=True)
    
    markdown = f"""# Intelligence Brief - {today}

*Daily intelligence synthesis from monitored open sources*

---

## Executive Summary

Today's intelligence brief covers {sum(group['count'] for _, group in sorted_groups)} articles across {len(sorted_groups)} major themes. Key areas of focus include geopolitical developments, technological advances, economic indicators, and emerging security concerns.

---

"""
    
    # Generate sections for each group
    for group_id, group in sorted_groups:
        if group['count'] < 2:  # Skip groups with too few articles
            continue
            
        section_title = group['text']
        articles = group['articles']
        
        markdown += f"## {section_title}\n\n"
        markdown += f"*{group['count']} sources*\n\n"
        
        # Generate narrative analysis
        if 'Trump' in section_title or 'Politics' in section_title:
            markdown += "**Political Intelligence**: "
        elif 'Russia' in section_title or 'China' in section_title or 'Iran' in section_title:
            markdown += "**Geopolitical Assessment**: "
        elif 'AI' in section_title or 'Technology' in section_title:
            markdown += "**Technology Watch**: "
        elif 'Climate' in section_title or 'Energy' in section_title:
            markdown += "**Environmental/Energy Intelligence**: "
        else:
            markdown += "**Situational Awareness**: "
        
        # Create narrative from articles
        key_articles = articles[:3]  # Focus on top 3 articles per group
        narrative_points = []
        
        for article in key_articles:
            # Extract key insight from title/summary
            title_words = article.title.split()[:8]  # First 8 words
            insight = " ".join(title_words)
            narrative_points.append(f"[{insight}...]({article.url})")
        
        markdown += " • ".join(narrative_points) + "\n\n"
        
        # Detailed source listing
        markdown += "**Key Sources:**\n\n"
        for article in articles[:5]:  # Limit to top 5 per group
            source_name = article.source.split('/')[-1] if '/' in article.source else article.source
            markdown += f"- **[{article.title}]({article.url})** - *{source_name}*\n"
            if article.summary and len(article.summary) > 50:
                summary_preview = article.summary[:150] + "..." if len(article.summary) > 150 else article.summary
                markdown += f"  {summary_preview}\n"
            markdown += "\n"
        
        markdown += "---\n\n"
    
    # Add footer
    markdown += f"""## Intelligence Assessment

This brief synthesizes {sum(group['count'] for _, group in sorted_groups)} open-source articles from {len(set(article.source for _, group in sorted_groups for article in group['articles']))} monitored sources. 

**Confidence Levels**: Information derived from established news sources and official publications. Cross-reference recommended for operational planning.

**Next Assessment**: Daily at 0800 UTC

---

*Generated by AIRSS Intelligence System - {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}*
"""
    
    return markdown

def main():
    """Main function to generate intelligence brief"""
    print("Loading RSS feeds...")
    feed_urls = load_feeds()
    print(f"Configured {len(feed_urls)} feeds")
    
    print("Fetching articles...")
    articles = Feeds.fetch_articles(feed_urls, days=1)
    print(f"Fetched {len(articles)} articles")
    
    if not articles:
        print("No articles found")
        return
    
    print("Clustering articles...")
    clustered_articles = cluster_articles_with_keywords(articles)
    groups = create_labeled_groups(clustered_articles)
    print(f"Created {len(groups)} groups")
    
    print("Generating intelligence brief...")
    markdown_content = generate_intelligence_brief_markdown(groups)
    
    # Save to file
    output_file = f"intelligence_brief_{datetime.now().strftime('%Y%m%d')}.md"
    with open(output_file, 'w') as f:
        f.write(markdown_content)
    
    print(f"Intelligence brief saved to {output_file}")
    print(f"Brief contains {len(groups)} sections with {len(articles)} total articles")
    
    return markdown_content

if __name__ == "__main__":
    main()