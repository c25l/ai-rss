#!/usr/bin/env python3
"""
MCP Server 1: RSS Feed Fetcher & Clustering Service
Handles RSS feed fetching and provides data to Claude for clustering
"""

import asyncio
import json
import sys
import requests
import time
import logging
from typing import Any, Sequence
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
from collections import defaultdict
from datetime import datetime

# Import existing modules
import feeds
from datamodel import Article, Group

mcp_server = Server("rss-clustering-service")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/chris/source/airss/logs/rss_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('rss_server')



# Default research feeds for ArXiv
DEFAULT_RESEARCH_FEEDS = ["https://export.arxiv.org/rss/cs.AI+cs.LG"]

@mcp_server.list_resources()
async def handle_list_resources() -> list[Resource]:
    return [
        Resource(
            uri="feed://status",
            name="Service Status",
            description="Current status of the RSS clustering service",
            mimeType="application/json",
        )
    ]

@mcp_server.list_resource_templates()
async def handle_list_resource_templates() -> list[Resource]:
    return []

@mcp_server.read_resource()
async def handle_read_resource(uri: str) -> str:
    uri_str = str(uri)
    if uri_str == "feed://status":
        status = {
            "service": "rss-clustering-service", 
            "status": "running",
            # "feeds_configured": len(feeds.FEEDS),
            "timestamp": datetime.now().isoformat()
        }
        return json.dumps(status, indent=2)
    
    raise ValueError(f"Unknown resource: {uri_str}")

@mcp_server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_clustered_articles",
            description="Fetch RSS articles and return them clustered and ready for newsletter generation",
            inputSchema={
                "type": "object",
                "properties": {
                    "days_back": {
                        "type": "number",
                        "description": "Days back to fetch articles (default: 1)",
                        "default": 1
                    },
                    "feeds":{
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                        "description" : "list of feeds to fetch",
                        "default":[]
                        }
                }
            },
        ),
        Tool(
            name="get_articles",
            description="Fetch RSS articles and return them without grouping, with pagination support.",
            inputSchema={
                "type": "object",
                "properties": {
                    "days_back": {
                        "type": "number",
                        "description": "Days back to fetch articles (default: 1)",
                        "default": 1
                    },
                    "feeds":{
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                        "description" : "list of feeds to fetch",
                        "default":[]
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of articles to return (default: 20)",
                        "default": 20
                    },
                    "offset": {
                        "type": "number",
                        "description": "Number of articles to skip for pagination (default: 0)",
                        "default": 0
                    }
                }
            },
        )
    ]

# Store for clustered groups that will be passed to newsletter service
stored_groups = {}

def cluster_articles_mathematically(articles):
    """Simplified clustering approach to avoid numpy array issues"""
    if len(articles) < 2:
        for i, article in enumerate(articles):
            article.cluster = i
        return articles
    
    # Assign keywords based on predefined tags
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
            headline = f"Group {cluster_id}"
        
        groups[cluster_id] = Group(text=headline, articles=cluster_articles)
    
    return groups

async def handle_get_clustered_articles(arguments: dict) -> list[TextContent]:
    feed_urls = arguments.get("feeds", [])
    if isinstance(feed_urls, str):
        feed_urls = [feed_urls]
    days_back = arguments.get("days_back", 1)
    try:
        days_back = int(days_back)
    except ValueError:
        days_back = 1

    print(f"Fetching and clustering articles from past {days_back} days from {feed_urls}")
    articles = feeds.Feeds.fetch_articles(feed_urls, days=days_back)
    print(f"Fetched {len(articles)} articles")

    if not articles:
        return [TextContent(type="text", text=json.dumps({
            "groups": {},
            "total_articles": 0,
            "message": "No articles found"
        }, indent=2))]

    clustered_articles = cluster_articles_mathematically(articles)
    groups = make_labelled_groups(clustered_articles)

    groups_data = {}
    for group_id, group in groups.items():
        groups_data[str(group_id)] = {
            "text": group.text,
            "article_count": len(group.articles),
            "articles": [
                {
                    "title": article.title,
                    "url": article.url,
                    "source": article.source,
                    "summary": article.summary,
                    "keywords": article.keywords
                } for article in group.articles
            ]
        }

    return [TextContent(type="text", text=json.dumps({
        "groups": groups_data,
        "total_articles": len(articles),
        "group_count": len(groups_data)
    }, indent=2))]

async def handle_get_articles(arguments: dict) -> list[TextContent]:
    feed_urls = arguments.get("feeds", [])
    if isinstance(feed_urls, str):
        feed_urls = [feed_urls]
    days_back = arguments.get("days_back", 1)
    limit = arguments.get("limit", 20)
    offset = arguments.get("offset", 0)
    
    try:
        days_back = int(days_back)
    except ValueError:
        days_back = 1

    print(f"Fetching articles from past {days_back} days from {feed_urls}")
    articles = feeds.Feeds.fetch_articles(feed_urls, days=days_back)
    print(f"Fetched {len(articles)} articles")

    if not articles:
        return [TextContent(type="text", text=json.dumps({
            "articles": [],
            "total_articles": 0,
            "total_available": 0,
            "offset": offset,
            "limit": limit,
            "has_more": False
        }, indent=2))]

    # Apply pagination
    paginated_articles = articles[offset:offset + limit]
    
    data = [
        {
            "title": article.title,
            "url": article.url,
            "summary": article.summary[:500] + ("..." if len(article.summary) > 500 else "")
        } for article in paginated_articles
    ]

    return [TextContent(type="text", text=json.dumps({
        "articles": data,
        "total_articles": len(data),
        "total_available": len(articles),
        "offset": offset,
        "limit": limit,
        "has_more": offset + len(data) < len(articles)
    }, indent=2))]

@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent | ImageContent | EmbeddedResource]:
    if name == "get_clustered_articles":
        return await handle_get_clustered_articles(arguments or {})
    elif name == "get_articles":
        return await handle_get_articles(arguments or {})
 
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    # Run the server using stdin/stdout streams
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="rss-clustering-service",
                server_version="1.0.0",
                capabilities=mcp_server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
