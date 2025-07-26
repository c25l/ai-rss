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
import numpy as np
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

# Research preference topics extracted from research_interests_analysis.md
RESEARCH_PREFERENCE_TOPICS = [
    "Large Language Models", "Transformer architectures", "Attention mechanisms", 
    "Model scaling laws", "Training efficiency", "Mixture of Experts", 
    "Chain-of-thought reasoning", "Test-time computation", "RLHF alignment",
    "Experimental design", "Causal inference", "A/B testing methodology", 
    "Sequential analysis", "Treatment effects", "Online controlled experiments",
    "Representation learning", "Universal embeddings", "Geometric deep learning",
    "Information theory", "Optimization theory", "Parameter-efficient methods",
    "AI safety", "AI alignment", "Interpretability", "AI governance",
    "Foundation models", "Multimodal learning", "Scientific AI", 
    "Causal reasoning", "Mathematical foundations", "Computational efficiency"
]

# Quality criteria for vector-based validation
QUALITY_CRITERIA = [
    "clear testable hypothesis with specific measurable claims",
    "rigorous experimental methodology with proper baselines and controls", 
    "mathematical concepts that connect logically with meaningful notation",
    "reproducible methods with sufficient implementation details",
    "substantial contribution avoiding jargon and terminology mixing",
    "precise problem statement with convincing evidence presented",
    "proper statistical analysis and evaluation metrics",
    "novel technical approach with theoretical or empirical validation"
]

# Anti-quality patterns to filter out
ANTI_QUALITY_PATTERNS = [
    "vague claims without testable hypotheses",
    "experimental results without proper baselines or controls",
    "mathematical notation that obscures rather than clarifies", 
    "missing critical implementation details for reproducibility",
    "jargon mixing unrelated fields without justification",
    "unclear problem statements with weak evidence",
    "poor experimental design with inadequate evaluation",
    "incremental work without significant novel contributions"
]

# Default validation prompt based on arxiv.txt criteria
DEFAULT_ARXIV_VALIDATION_PROMPT = """You are reviewing an ArXiv paper for a high-level AI/ML practitioner. Apply this rigorous evaluation:

**CORE QUALITY CHECKS:**
1. **Thesis Clarity**: Is the central claim precisely stated and testable? Can you identify the specific hypothesis being tested?
2. **Mathematical Rigor**: Do the mathematical concepts connect logically? Does notation serve the argument or obscure it?
3. **Experimental Validity**: Are experimental claims backed by proper methodology with appropriate baselines?
4. **Substance over Jargon**: Does the writing prioritize clear explanations over terminology salad?

**RED FLAGS - Reject if present:**
- Terminology mixing unrelated fields without clear justification
- Mathematical notation that doesn't advance the argument
- Experimental claims without proper baselines or controls
- Missing critical implementation details for claimed results
- Acknowledgments prominently mentioning AI writing tools
- Vague problem statements or unclear contributions

**TESTABILITY REQUIREMENTS:**
Only recommend if you can clearly answer:
- What specific, measurable problem does this solve?
- What is the core testable hypothesis?
- What would constitute convincing evidence for/against the claims?
- Are the methods reproducible with sufficient detail?

**DECISION:**
Respond with ONLY 'YES' if the paper has a clear testable thesis, avoids jargon for substance, and meets rigorous experimental standards. Respond with 'NO' if it fails any critical quality check or has significant red flags.

\nothink"""

def embed_text(text: str, query_type: str = 'document') -> np.ndarray:
    """Embed text using the nomic-embed-text model via Ollama"""
    payload = {
        "model": "nomic-embed-text",
        "prompt": ("search_document: " if query_type == 'document' else "search_query: ") + text,
    }
    try:
        response = requests.post(f"{OLLAMA_BASE_URL}/api/embeddings", json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        vector = np.array(data.get("embedding", []))
        # Normalize vector
        if len(vector) > 0:
            vector = vector / np.linalg.norm(vector)
        return vector
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return np.array([])

# Pre-compute embeddings (cached)
_preference_embeddings = None
_quality_embeddings = None
_anti_quality_embeddings = None

def get_preference_embeddings():
    """Get cached preference embeddings or compute them"""
    global _preference_embeddings
    if _preference_embeddings is None:
        logger.info(f"Computing research preference embeddings for {len(RESEARCH_PREFERENCE_TOPICS)} topics...")
        start_time = time.time()
        embeddings = []
        for topic in RESEARCH_PREFERENCE_TOPICS:
            emb = embed_text(topic, 'query')
            if len(emb) > 0:
                embeddings.append(emb)
        _preference_embeddings = np.array(embeddings) if embeddings else np.array([])
        compute_time = time.time() - start_time
        logger.info(f"Computed {len(embeddings)} preference embeddings in {compute_time:.2f}s")
    return _preference_embeddings

def get_quality_embeddings():
    """Get cached quality criteria embeddings"""
    global _quality_embeddings, _anti_quality_embeddings
    if _quality_embeddings is None:
        logger.info(f"Computing quality criteria embeddings for {len(QUALITY_CRITERIA)} positive and {len(ANTI_QUALITY_PATTERNS)} negative patterns...")
        start_time = time.time()
        
        # Positive quality patterns
        quality_embs = []
        for criterion in QUALITY_CRITERIA:
            emb = embed_text(criterion, 'query')
            if len(emb) > 0:
                quality_embs.append(emb)
        _quality_embeddings = np.array(quality_embs) if quality_embs else np.array([])
        
        # Negative quality patterns
        anti_quality_embs = []
        for pattern in ANTI_QUALITY_PATTERNS:
            emb = embed_text(pattern, 'query')
            if len(emb) > 0:
                anti_quality_embs.append(emb)
        _anti_quality_embeddings = np.array(anti_quality_embs) if anti_quality_embs else np.array([])
        
        compute_time = time.time() - start_time
        logger.info(f"Computed {len(quality_embs)} quality + {len(anti_quality_embs)} anti-quality embeddings in {compute_time:.2f}s")
    
    return _quality_embeddings, _anti_quality_embeddings

def filter_articles_by_preference(articles: list, similarity_threshold: float = 0.6) -> list:
    """Filter articles based on vector similarity to research preferences"""
    if not articles:
        return articles
        
    start_time = time.time()
    logger.info(f"Starting preference-based filtering of {len(articles)} articles (threshold: {similarity_threshold})")
    
    preference_embeddings = get_preference_embeddings()
    if len(preference_embeddings) == 0:
        logger.warning("No preference embeddings available, returning all articles")
        return articles
    
    filtered_articles = []
    
    for i, article in enumerate(articles):
        # Create article text for embedding
        article_text = f"{article.title}\n{article.summary}"
        article_embedding = embed_text(article_text, 'document')
        
        if len(article_embedding) == 0:
            continue
            
        # Calculate max similarity to any preference topic
        similarities = preference_embeddings @ article_embedding
        max_similarity = np.max(similarities) if len(similarities) > 0 else 0
        
        if max_similarity >= similarity_threshold:
            filtered_articles.append(article)
    
    filter_time = time.time() - start_time
    logger.info(f"Preference filtering completed in {filter_time:.2f}s - {len(filtered_articles)}/{len(articles)} articles passed")
    
    return filtered_articles

def validate_articles_by_quality_vectors(articles: list, quality_threshold: float = 0.65, anti_quality_threshold: float = 0.55) -> list:
    """Validate articles using vector similarity to quality criteria (fast alternative to Ollama)"""
    if not articles:
        return articles
        
    start_time = time.time()
    logger.info(f"Starting vector-based quality validation of {len(articles)} articles")
    
    quality_embeddings, anti_quality_embeddings = get_quality_embeddings()
    if len(quality_embeddings) == 0:
        logger.warning("No quality embeddings available, returning all articles")
        return articles
    
    validated_articles = []
    
    for i, article in enumerate(articles):
        # Create article text for embedding
        article_text = f"{article.title}\n{article.summary}"
        article_embedding = embed_text(article_text, 'document')
        
        if len(article_embedding) == 0:
            continue
            
        # Calculate similarity to positive quality criteria
        quality_similarities = quality_embeddings @ article_embedding
        max_quality_score = np.max(quality_similarities) if len(quality_similarities) > 0 else 0
        
        # Calculate similarity to negative quality patterns
        anti_quality_similarities = anti_quality_embeddings @ article_embedding if len(anti_quality_embeddings) > 0 else np.array([0])
        max_anti_quality_score = np.max(anti_quality_similarities) if len(anti_quality_similarities) > 0 else 0
        
        # Accept if high quality score and low anti-quality score
        if max_quality_score >= quality_threshold and max_anti_quality_score < anti_quality_threshold:
            validated_articles.append(article)
    
    validation_time = time.time() - start_time
    logger.info(f"Vector quality validation completed in {validation_time:.2f}s - {len(validated_articles)}/{len(articles)} articles passed")
    
    return validated_articles



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
        ),
        Tool(
            name="get_validated_rss_articles",
            description="Fetch RSS articles and validate them using a local Ollama model before returning. Token-efficient pre-filtering.",
            inputSchema={
                "type": "object",
                "properties": {
                    "feeds": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of RSS feed URLs to fetch"
                    },
                    "validation_prompt": {
                        "type": "string",
                        "description": "Prompt to send to the validation model for each article"
                    },
                    "validation_model": {
                        "type": "string",
                        "enum": ["qwen3:0.6b", "gemma3n:e4b", "phi4-mini-reasoning:3.8b"],
                        "description": "Model to use for validation. qwen3:0.6b=ultra-fast/binary, gemma3n:e4b=balanced/analysis, phi4-mini-reasoning:3.8b=complex reasoning",
                        "default": "qwen3:0.6b"
                    },
                    "days_back": {
                        "type": "number",
                        "description": "Days back to fetch articles (default: 1)",
                        "default": 1
                    }
                },
                "required": ["feeds", "validation_prompt"]
            }
        ),
        Tool(
            name="validate_articles_with_ollama",
            description="Validate already-fetched articles using a local Ollama model. For when Claude already has articles in context.",
            inputSchema={
                "type": "object",
                "properties": {
                    "articles": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "summary": {"type": "string"},
                                "url": {"type": "string"}
                            }
                        },
                        "description": "Array of articles to validate"
                    },
                    "validation_prompt": {
                        "type": "string",
                        "description": "Prompt to send to the validation model for each article"
                    },
                    "validation_model": {
                        "type": "string",
                        "enum": ["qwen3:0.6b", "gemma3n:e4b", "phi4-mini-reasoning:3.8b"],
                        "description": "Model to use for validation. qwen3:0.6b=ultra-fast/binary, gemma3n:e4b=balanced/analysis, phi4-mini-reasoning:3.8b=complex reasoning",
                        "default": "qwen3:0.6b"
                    }
                },
                "required": ["articles", "validation_prompt"]
            }
        ),
        Tool(
            name="ask_ollama_buddy",
            description="General purpose query to local Ollama models - your 'little buddy' for quick questions and analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Question or prompt to send to the model"
                    },
                    "model": {
                        "type": "string",
                        "enum": ["qwen3:0.6b", "gemma3n:e4b", "phi4-mini-reasoning:3.8b"],
                        "description": "Model to use. qwen3:0.6b=ultra-fast/binary, gemma3n:e4b=balanced/analysis, phi4-mini-reasoning:3.8b=complex reasoning",
                        "default": "qwen3:0.6b"
                    }
                },
                "required": ["prompt"]
            }
        ),
        Tool(
            name="get_research_articles",
            description="Fetch and validate ArXiv research articles (cs.AI+cs.LG) with Ollama pre-filtering. Uses default research feeds and rigorous quality criteria for thesis clarity, testability, and jargon evaluation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "validation_prompt": {
                        "type": "string",
                        "description": "Prompt to send to the validation model for each article. If not provided, uses default ArXiv quality criteria.",
                        "default": ""
                    },
                    "validation_model": {
                        "type": "string",
                        "enum": ["qwen3:0.6b", "gemma3n:e4b", "phi4-mini-reasoning:3.8b"],
                        "description": "Model to use for validation. qwen3:0.6b=ultra-fast/binary, gemma3n:e4b=balanced/analysis, phi4-mini-reasoning:3.8b=complex reasoning",
                        "default": "qwen3:0.6b"
                    },
                    "days_back": {
                        "type": "number",
                        "description": "Days back to fetch articles (default: 1)",
                        "default": 1
                    },
                    "feeds": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional custom feed URLs. If not provided, uses default ArXiv cs.AI+cs.LG feed",
                        "default": []
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
                },
                "required": []
            }
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
    elif name == "get_validated_rss_articles":
        # Pre-fetch validation mode
        batch_start_time = time.time()
        feed_urls = arguments.get("feeds", [])
        validation_prompt = arguments.get("validation_prompt")
        validation_model = arguments.get("validation_model", "qwen3:0.6b")
        days_back = arguments.get("days_back", 1)
        
        logger.info(f"Starting RSS validation batch - Model: {validation_model}, Feeds: {len(feed_urls)}, Days back: {days_back}")
        
        if validation_model not in OLLAMA_MODELS:
            logger.error(f"Invalid validation model requested: {validation_model}")
            return [TextContent(type="text", text=json.dumps({
                "error": f"Invalid model: {validation_model}. Available models: {list(OLLAMA_MODELS.keys())}"
            }, indent=2))]
        
        # Fetch articles first
        fetch_start = time.time()
        articles = feeds.Feeds.fetch_articles(feed_urls, days=int(days_back))
        fetch_time = time.time() - fetch_start
        logger.info(f"Fetched {len(articles)} articles in {fetch_time:.2f}s for validation with {validation_model}")
        print(f"Fetched {len(articles)} articles for validation with {validation_model}")
        
        if not articles:
            logger.warning("No articles found to validate")
            return [TextContent(type="text", text=json.dumps({
                "validated_articles": [],
                "total_articles": 0,
                "message": "No articles found to validate"
            }, indent=2))]
        
        # Convert to dict format and validate
        validation_start = time.time()
        validated_articles = []
        passed_count = 0
        failed_count = 0
        
        logger.info(f"Starting validation of {len(articles)} articles...")
        
        for i, article in enumerate(articles):
            logger.debug(f"Processing article {i+1}/{len(articles)}")
            
            article_dict = {
                "title": article.title,
                "url": article.url,
                "summary": article.summary,
                "source": article.source
            }
            validated_article = validate_article_with_ollama(article_dict, validation_prompt, validation_model)
            
            # Only include articles that pass validation (YES responses)
            validation_result = validated_article.get("validation_result", "").strip().upper()
            if validation_result == "YES":
                # Remove validation metadata from the output
                clean_article = {
                    "title": validated_article["title"],
                    "url": validated_article["url"],
                    "summary": validated_article["summary"],
                    "source": validated_article["source"]
                }
                validated_articles.append(clean_article)
                passed_count += 1
            else:
                failed_count += 1
                
            # Log progress every 10 articles
            if (i + 1) % 10 == 0 or (i + 1) == len(articles):
                progress_time = time.time() - validation_start
                avg_time_per_article = progress_time / (i + 1)
                logger.info(f"Progress: {i+1}/{len(articles)} articles processed, {passed_count} passed, {failed_count} failed, {avg_time_per_article:.2f}s avg per article")
        
        validation_time = time.time() - validation_start
        total_time = time.time() - batch_start_time
        
        logger.info(f"RSS validation batch completed - Total time: {total_time:.2f}s, Validation time: {validation_time:.2f}s, {passed_count}/{len(articles)} articles passed")
        
        return [TextContent(type="text", text=json.dumps({
            "validated_articles": validated_articles,
            "total_articles": len(validated_articles),
            "validation_model": validation_model,
            "validation_prompt": validation_prompt,
            "processing_stats": {
                "total_fetched": len(articles),
                "passed_validation": passed_count,
                "failed_validation": failed_count,
                "fetch_time_seconds": fetch_time,
                "validation_time_seconds": validation_time,
                "total_time_seconds": total_time,
                "avg_time_per_article": validation_time / len(articles) if articles else 0
            }
        }, indent=2))]
    
    elif name == "validate_articles_with_ollama":
        # Post-fetch validation mode
        batch_start_time = time.time()
        articles = arguments.get("articles", [])
        validation_prompt = arguments.get("validation_prompt")
        validation_model = arguments.get("validation_model", "qwen3:0.6b")
        
        logger.info(f"Starting post-fetch validation batch - Model: {validation_model}, Articles: {len(articles)}")
        
        if validation_model not in OLLAMA_MODELS:
            logger.error(f"Invalid validation model requested: {validation_model}")
            return [TextContent(type="text", text=json.dumps({
                "error": f"Invalid model: {validation_model}. Available models: {list(OLLAMA_MODELS.keys())}"
            }, indent=2))]
        
        print(f"Validating {len(articles)} articles with {validation_model}")
        
        validated_articles = []
        for i, article in enumerate(articles):
            logger.debug(f"Processing article {i+1}/{len(articles)} in post-fetch validation")
            
            validated_article = validate_article_with_ollama(article, validation_prompt, validation_model)
            validated_articles.append(validated_article)
            
            # Log progress every 10 articles
            if (i + 1) % 10 == 0 or (i + 1) == len(articles):
                elapsed_time = time.time() - batch_start_time
                avg_time_per_article = elapsed_time / (i + 1)
                logger.info(f"Post-fetch validation progress: {i+1}/{len(articles)} articles processed, {avg_time_per_article:.2f}s avg per article")
        
        total_time = time.time() - batch_start_time
        logger.info(f"Post-fetch validation batch completed in {total_time:.2f}s - {len(validated_articles)} articles processed")
        
        return [TextContent(type="text", text=json.dumps({
            "validated_articles": validated_articles,
            "total_articles": len(validated_articles),
            "validation_model": validation_model,
            "validation_prompt": validation_prompt,
            "processing_stats": {
                "total_time_seconds": total_time,
                "avg_time_per_article": total_time / len(articles) if articles else 0
            }
        }, indent=2))]
    
    elif name == "ask_ollama_buddy":
        # General purpose Ollama query
        start_time = time.time()
        prompt = arguments.get("prompt")
        model = arguments.get("model", "qwen3:0.6b")
        
        logger.info(f"Starting Ollama buddy query - Model: {model}, Prompt: {prompt[:100]}...")
        
        if model not in OLLAMA_MODELS:
            logger.error(f"Invalid model requested for buddy query: {model}")
            return [TextContent(type="text", text=json.dumps({
                "error": f"Invalid model: {model}. Available models: {list(OLLAMA_MODELS.keys())}"
            }, indent=2))]
        
        print(f"Querying {model} with prompt: {prompt[:100]}...")
        
        response = query_ollama(model, prompt)
        
        total_time = time.time() - start_time
        logger.info(f"Ollama buddy query completed in {total_time:.2f}s - Model: {model}")
        
        return [TextContent(type="text", text=json.dumps({
            "response": response,
            "model": model,
            "model_strengths": OLLAMA_MODELS[model]["strengths"],
            "prompt": prompt,
            "processing_stats": {
                "total_time_seconds": total_time
            }
        }, indent=2))]
    
    elif name == "get_research_articles":
        # Research articles with default ArXiv feeds
        batch_start_time = time.time()
        validation_prompt = arguments.get("validation_prompt") or DEFAULT_ARXIV_VALIDATION_PROMPT
        validation_model = arguments.get("validation_model", "qwen3:0.6b")
        days_back = arguments.get("days_back", 1)
        custom_feeds = arguments.get("feeds", [])
        
        # Use default research feeds if no custom feeds provided
        feed_urls = custom_feeds if custom_feeds else DEFAULT_RESEARCH_FEEDS
        
        logger.info(f"Starting research articles fetch - Model: {validation_model}, Feeds: {feed_urls}, Days back: {days_back}")
        
        if validation_model not in OLLAMA_MODELS:
            logger.error(f"Invalid validation model requested: {validation_model}")
            return [TextContent(type="text", text=json.dumps({
                "error": f"Invalid model: {validation_model}. Available models: {list(OLLAMA_MODELS.keys())}"
            }, indent=2))]
        
        # Fetch articles first
        fetch_start = time.time()
        articles = feeds.Feeds.fetch_articles(feed_urls, days=int(days_back))
        fetch_time = time.time() - fetch_start
        logger.info(f"Fetched {len(articles)} research articles in {fetch_time:.2f}s")
        print(f"Fetched {len(articles)} research articles")
        
        if not articles:
            logger.warning("No research articles found")
            return [TextContent(type="text", text=json.dumps({
                "research_articles": [],
                "total_articles": 0,
                "message": "No research articles found",
                "feeds_used": feed_urls
            }, indent=2))]
        
        # Filter by research preferences using vector similarity
        filter_start = time.time()
        filtered_articles = filter_articles_by_preference(articles, similarity_threshold=0.6)[:15]  # Limit to 15 articles
        filter_time = time.time() - filter_start
        
        if not filtered_articles:
            logger.warning("No articles passed preference filtering")
            return [TextContent(type="text", text=json.dumps({
                "research_articles": [],
                "total_articles": 0,
                "message": "No articles matched research preferences",
                "feeds_used": feed_urls,
                "processing_stats": {
                    "total_fetched": len(articles),
                    "passed_preference_filter": 0,
                    "fetch_time_seconds": fetch_time,
                    "filter_time_seconds": filter_time
                }
            }, indent=2))]
        
        # Validate using vector-based quality assessment (much faster than Ollama)
        validation_start = time.time()
        # Skip quality validation for now - just use preference-filtered articles
        validated_articles = filtered_articles
        validation_time = time.time() - validation_start
        
        logger.info(f"DEBUG: filtered_articles count: {len(filtered_articles)}, validated_articles count: {len(validated_articles)}")
        
        # Convert to clean article format
        clean_articles = []
        for article in filtered_articles:  # Use filtered_articles directly
            clean_article = {
                "title": article.title,
                "url": article.url,
                "summary": article.summary,
                "source": article.source
            }
            clean_articles.append(clean_article)
        
        total_time = time.time() - batch_start_time
        
        logger.info(f"Research articles processing completed!")
        logger.info(f"📊 SUMMARY: {len(validated_articles)} articles passed all filters")
        logger.info(f"🔍 PIPELINE: {len(articles)} → {len(filtered_articles)} (preference) → {len(validated_articles)} (quality)")
        logger.info(f"⏱️  TIMING: Total {total_time:.2f}s | Fetch {fetch_time:.2f}s | Filter {filter_time:.2f}s | Validation {validation_time:.2f}s")
        
        return [TextContent(type="text", text=json.dumps({
            "research_articles": clean_articles,
            "total_articles": len(clean_articles),
            "validation_method": "vector_similarity",
            "feeds_used": feed_urls,
            "processing_stats": {
                "total_fetched": len(articles),
                "passed_preference_filter": len(filtered_articles),
                "passed_quality_validation": len(validated_articles),
                "debug_filtered_count": len(filtered_articles),
                "final_articles": len(clean_articles),
                "fetch_time_seconds": fetch_time,
                "filter_time_seconds": filter_time,
                "validation_time_seconds": validation_time,
                "total_time_seconds": total_time
            }
        }, indent=2))]
        
        for i, article in enumerate(filtered_articles):
            logger.debug(f"Processing research article {i+1}/{len(articles)}")
            
            article_dict = {
                "title": article.title,
                "url": article.url,
                "summary": article.summary,
                "source": article.source
            }
            validated_article = validate_article_with_ollama(article_dict, validation_prompt, validation_model)
            
            # Only include articles that pass validation (YES responses)
            validation_result = validated_article.get("validation_result", "").strip().upper()
            if validation_result == "YES":
                # Remove validation metadata from the output
                clean_article = {
                    "title": validated_article["title"],
                    "url": validated_article["url"],
                    "summary": validated_article["summary"],
                    "source": validated_article["source"]
                }
                validated_articles.append(clean_article)
                passed_count += 1
            else:
                failed_count += 1
                
            # Log progress every 10 articles
            if (i + 1) % 10 == 0 or (i + 1) == len(articles):
                progress_time = time.time() - validation_start
                avg_time_per_article = progress_time / (i + 1)
                logger.info(f"Research articles progress: {i+1}/{len(articles)} processed, {passed_count} passed, {failed_count} failed, {avg_time_per_article:.2f}s avg per article")
        
        validation_time = time.time() - validation_start
        total_time = time.time() - batch_start_time
        
        logger.info(f"Research articles batch completed - Total time: {total_time:.2f}s, Validation time: {validation_time:.2f}s, {passed_count}/{len(articles)} articles passed")
        
        return [TextContent(type="text", text=json.dumps({
            "research_articles": validated_articles,
            "total_articles": len(validated_articles),
            "validation_model": validation_model,
            "validation_prompt": validation_prompt,
            "feeds_used": feed_urls,
            "processing_stats": {
                "total_fetched": len(articles),
                "passed_validation": passed_count,
                "failed_validation": failed_count,
                "unclear_responses": unclear_count,
                "pass_rate_percent": pass_rate,
                "fetch_time_seconds": fetch_time,
                "validation_time_seconds": validation_time,
                "total_time_seconds": total_time,
                "avg_validation_time_per_article": avg_validation_time,
                "min_validation_time": min_validation_time,
                "max_validation_time": max_validation_time
            }
        }, indent=2))]
 
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
