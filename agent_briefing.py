#!/usr/bin/env python
"""
Agent-Centric Briefing System

This module implements a new architectural approach where an LLM agent
has full autonomy to decide what content matters and how to present it.

Unlike the old constrained approach (where LLM only ranked pre-formatted content),
this system gives the agent:
- Tools: RSS feed reader, web scraper
- Sources: A list of sites to monitor
- Full creative freedom: decide structure, importance, presentation

The agent acts as an intelligent editor/analyst rather than a simple filter.
"""

import datetime
import json
import os
import re
import yaml
from typing import List, Dict, Any, Optional
from copilot import Copilot
from feeds import Feeds
from datamodel import Article
import requests
from bs4 import BeautifulSoup


class AgentTools:
    """Tools available to the agent for gathering and processing information.
    
    This class provides both data-fetching tools (RSS, web scraping) and 
    API-based tools for weather, space conditions, and astronomy.
    """
    
    @staticmethod
    def fetch_rss_feed(feed_url: str, days: int = 1) -> List[Article]:
        """
        Fetch articles from an RSS feed.
        
        Args:
            feed_url: URL of the RSS feed
            days: Number of days back to fetch articles (default: 1)
            
        Returns:
            List of Article objects
        """
        try:
            return Feeds.get_articles(feed_url, days=days)
        except Exception as e:
            print(f"Error fetching RSS feed {feed_url}: {e}")
            return []
    
    @staticmethod
    def scrape_webpage(url: str) -> Dict[str, Any]:
        """
        Scrape a webpage and return structured content.
        
        Args:
            url: URL of the webpage to scrape
            
        Returns:
            Dictionary with keys: 'title', 'text', 'links'
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text(separator=' ', strip=True)
            
            # Get title
            title = soup.title.string if soup.title else "No title"
            
            # Get links
            links = [a.get('href') for a in soup.find_all('a', href=True)]
            
            return {
                'url': url,
                'title': title,
                'text': text[:5000],  # Limit text length
                'links': links[:50]  # Limit number of links
            }
        except Exception as e:
            print(f"Error scraping webpage {url}: {e}")
            return {
                'url': url,
                'title': 'Error',
                'text': f'Failed to scrape: {str(e)}',
                'links': []
            }
    
    @staticmethod
    def fetch_tldr_tech(date: Optional[datetime.datetime] = None) -> List[Article]:
        """
        Fetch TLDR tech newsletter articles for a specific date.
        
        Args:
            date: Date to fetch (defaults to today)
            
        Returns:
            List of Article objects from TLDR
        """
        if date is None:
            date = datetime.datetime.now()
        
        articles = []
        
        # TLDR AI newsletter
        try:
            url = f"https://tldr.tech/ai/{date:%Y-%m-%d}"
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            article_elements = soup.find_all("article")
            print(f"Found {len(article_elements)} articles from TLDR AI")
            
            for elem in article_elements:
                articles.append(Article(
                    title=str(elem),
                    summary="",
                    published_at=date,
                    source="tldr.tech/ai",
                    url=url
                ))
        except Exception as e:
            print(f"Error fetching TLDR AI: {e}")
        
        # TLDR Tech newsletter
        try:
            url = f"https://tldr.tech/tech/{date:%Y-%m-%d}"
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            article_elements = soup.find_all("article")
            print(f"Found {len(article_elements)} articles from TLDR Tech")
            
            for elem in article_elements:
                articles.append(Article(
                    title=str(elem),
                    summary="",
                    published_at=date,
                    source="tldr.tech",
                    url=url
                ))
        except Exception as e:
            print(f"Error fetching TLDR Tech: {e}")
        
        return articles
    
    @staticmethod
    def fetch_hacker_news_daily(date: Optional[datetime.datetime] = None) -> List[Article]:
        """
        Fetch Hacker News Daily digest for a specific date.
        
        Args:
            date: Date to fetch (defaults to yesterday)
            
        Returns:
            List of Article objects from HN Daily
        """
        if date is None:
            date = datetime.datetime.now() - datetime.timedelta(days=1)
        
        articles = []
        
        try:
            url = f"https://www.daemonology.net/hn-daily/{date:%Y-%m-%d}.html"
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            story_links = soup.find_all("span", class_="storylink")
            print(f"Found {len(story_links)} articles from HN Daily")
            
            for elem in story_links:
                articles.append(Article(
                    title=str(elem),
                    summary="",
                    published_at=date,
                    source="hacker news daily",
                    url=url
                ))
        except Exception as e:
            print(f"Error fetching HN Daily: {e}")
        
        return articles
    
    @staticmethod
    def fetch_bluesky_feed(handle: str, limit: int = 20) -> List[Article]:
        """
        Fetch posts from a Bluesky user's feed.
        
        Args:
            handle: Bluesky handle (e.g., 'user.bsky.social')
            limit: Maximum number of posts to fetch (default: 20)
            
        Returns:
            List of Article objects from Bluesky
        """
        articles = []
        
        try:
            from atproto import Client
            
            # Create client without authentication (for public feeds)
            client = Client()
            
            # Fetch the author's feed
            profile_feed = client.get_author_feed(actor=handle, limit=limit)
            
            print(f"Found {len(profile_feed.feed)} posts from Bluesky user {handle}")
            
            for feed_view in profile_feed.feed:
                post = feed_view.post
                record = post.record
                
                # Get post text
                text = record.text if hasattr(record, 'text') else ''
                
                # Get post URL
                post_uri = post.uri
                # Convert AT-URI to web URL
                # Format: at://did:plc:xxx/app.bsky.feed.post/xxx
                post_url = f"https://bsky.app/profile/{handle}/post/{post_uri.split('/')[-1]}"
                
                # Get creation time
                created_at = record.created_at if hasattr(record, 'created_at') else datetime.datetime.now().isoformat()
                
                articles.append(Article(
                    title=text[:100] + ('...' if len(text) > 100 else ''),  # Use first 100 chars as title
                    summary=text,
                    published_at=created_at,
                    source=f"bluesky:{handle}",
                    url=post_url
                ))
        except ImportError:
            print("Error: atproto library not installed. Install with: pip install atproto")
        except Exception as e:
            print(f"Error fetching Bluesky feed for {handle}: {e}")
        
        return articles
    
    @staticmethod
    def get_weather_forecast(lat: float = 40.165729, lon: float = -105.101194) -> Dict[str, Any]:
        """
        Get weather forecast from National Weather Service API.
        
        Args:
            lat: Latitude (default: Longmont, CO)
            lon: Longitude (default: Longmont, CO)
            
        Returns:
            Dictionary with forecast data including temperature, conditions, alerts
        """
        try:
            # Import here to avoid circular dependency
            import weather
            w = weather.Weather()
            
            # Get forecast data
            forecast_html = w.pull_data()
            
            # Get alerts
            alerts = w.get_alerts(lat=lat, lon=lon)
            
            # Parse forecast for structured data
            soup = BeautifulSoup(forecast_html, 'html.parser')
            periods = soup.find_all('div', class_='forecast-text')
            
            forecast_periods = []
            for period in periods[:3]:  # Get next 3 periods
                forecast_periods.append(period.get_text(strip=True))
            
            return {
                'forecast_html': forecast_html,
                'forecast_text': ' '.join(forecast_periods),
                'alerts': alerts,
                'location': f'lat={lat}, lon={lon}'
            }
        except Exception as e:
            print(f"Error fetching weather: {e}")
            return {
                'error': str(e),
                'forecast_text': 'Weather data unavailable'
            }
    
    @staticmethod
    def get_space_weather() -> Dict[str, Any]:
        """
        Get space weather conditions including solar activity and geomagnetic indices.
        
        Returns:
            Dictionary with space weather data including Kp index, solar flux
        """
        try:
            import spaceweather
            sw = spaceweather.SpaceWeather()
            
            # Get space weather data
            forecast = sw.format_forecast()
            
            return {
                'forecast': forecast,
                'source': 'NOAA Space Weather Prediction Center'
            }
        except Exception as e:
            print(f"Error fetching space weather: {e}")
            return {
                'error': str(e),
                'forecast': 'Space weather data unavailable'
            }
    
    @staticmethod
    def get_astronomy_viewing(lat: float = 40.1672, lon: float = -105.1019) -> Dict[str, Any]:
        """
        Get astronomical viewing conditions for tonight.
        
        Args:
            lat: Latitude (default: Longmont, CO)
            lon: Longitude (default: Longmont, CO)
            
        Returns:
            Dictionary with astronomy data including moon phase, planet visibility, sunset times
        """
        try:
            import astronomy
            import os
            
            # Set location if different from default
            os.environ['LATITUDE'] = str(lat)
            os.environ['LONGITUDE'] = str(lon)
            
            astro = astronomy.Astronomy()
            viewing_info = astro.format_output()
            
            return {
                'viewing_info': viewing_info,
                'location': f'lat={lat}, lon={lon}'
            }
        except Exception as e:
            print(f"Error fetching astronomy data: {e}")
            return {
                'error': str(e),
                'viewing_info': 'Astronomy data unavailable'
            }
    
    @staticmethod
    def get_wikipedia_summary(topic: str, sentences: int = 3) -> Dict[str, Any]:
        """
        Fetch Wikipedia summary for historical/background context.
        
        Useful for adding context about people, organizations, events, or concepts
        mentioned in the news.
        
        Args:
            topic: Topic to look up (e.g., "Donald Trump", "Artificial Intelligence")
            sentences: Number of sentences to return (default 3)
            
        Returns:
            Dictionary with summary, url, and title
            
        Example:
            context = get_wikipedia_summary("NATO")
            # Returns summary of NATO with link to full article
        """
        try:
            import requests
            
            # Wikipedia API endpoint
            url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + topic.replace(" ", "_")
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                # Get extract and limit to requested sentences
                extract = data.get('extract', '')
                sentences_list = extract.split('. ')[:sentences]
                summary = '. '.join(sentences_list)
                if not summary.endswith('.'):
                    summary += '.'
                
                return {
                    'topic': topic,
                    'summary': summary,
                    'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                    'title': data.get('title', topic),
                    'success': True
                }
            else:
                return {
                    'topic': topic,
                    'summary': f"No Wikipedia article found for '{topic}'",
                    'url': '',
                    'title': topic,
                    'success': False
                }
        except Exception as e:
            return {
                'topic': topic,
                'summary': f"Error fetching Wikipedia: {str(e)}",
                'url': '',
                'title': topic,
                'success': False
            }
    
    @staticmethod
    def fetch_all_sources(sources: List[Dict[str, str]], days: int = 1) -> Dict[str, List[Article]]:
        """
        Fetch content from all configured sources.
        
        Args:
            sources: List of source dictionaries with 'name', 'url', 'type' keys
            days: Number of days back to fetch articles
            
        Returns:
            Dictionary mapping source names to lists of articles
        """
        all_content = {}
        
        for source in sources:
            source_name = source.get('name', 'Unknown')
            source_url = source.get('url')
            source_type = source.get('type', 'rss')
            
            print(f"Fetching {source_name} ({source_type})...")
            
            try:
                if source_type == 'rss':
                    articles = AgentTools.fetch_rss_feed(source_url, days=days)
                    all_content[source_name] = articles
                elif source_type == 'scrape':
                    scraped = AgentTools.scrape_webpage(source_url)
                    # Convert scraped content to Article-like structure
                    article = Article(
                        title=scraped['title'],
                        url=scraped['url'],
                        summary=scraped['text'][:500],
                        source=source_name,
                        published_at=datetime.datetime.now().isoformat()
                    )
                    all_content[source_name] = [article]
                elif source_type == 'tldr':
                    articles = AgentTools.fetch_tldr_tech()
                    all_content[source_name] = articles
                elif source_type == 'hn-daily':
                    articles = AgentTools.fetch_hacker_news_daily()
                    all_content[source_name] = articles
                elif source_type == 'bluesky':
                    # For Bluesky, the 'url' field should contain the handle
                    handle = source_url
                    limit = source.get('limit', 20)  # Optional limit parameter
                    articles = AgentTools.fetch_bluesky_feed(handle, limit=limit)
                    all_content[source_name] = articles
                else:
                    print(f"Unknown source type: {source_type}")
            except Exception as e:
                print(f"Error fetching {source_name}: {e}")
                all_content[source_name] = []
        
        return all_content


def _repair_json(s):
    """Attempt to repair truncated or slightly malformed JSON.

    Handles: unclosed strings, trailing commas, unbalanced brackets/braces.
    Uses a stack to close structures in the correct order.
    """
    result = s.rstrip()

    # Close any unclosed quoted string
    in_string = False
    escaped = False
    for ch in result:
        if escaped:
            escaped = False
            continue
        if ch == '\\':
            escaped = True
            continue
        if ch == '"':
            in_string = not in_string
    if in_string:
        result += '"'

    # Remove trailing commas before closing brackets/braces (outside strings)
    result = re.sub(r',(\s*[}\]])', r'\1', result)

    # Use a stack to track open structures and close in correct order
    stack = []
    in_str = False
    esc = False
    for ch in result:
        if esc:
            esc = False
            continue
        if ch == '\\':
            esc = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch == '{':
            stack.append('}')
        elif ch == '[':
            stack.append(']')
        elif ch in ('}', ']'):
            if stack and stack[-1] == ch:
                stack.pop()

    # Close remaining open structures in reverse order
    result += ''.join(reversed(stack))
    return result


def _truncate_at_error(s, error):
    """Truncate JSON at the error position, backing up to the last complete object/array boundary."""
    pos = getattr(error, 'pos', None)
    if pos is None or pos <= 0:
        return None
    # Back up from error position to the last '}' or ']' that ends a complete node
    candidate = s[:pos]
    # Find the last closing brace/bracket before the error
    for i in range(len(candidate) - 1, -1, -1):
        if candidate[i] in ('}', ']'):
            return candidate[:i + 1]
    return None


class AgentBriefing:
    """
    Agent-centric briefing system.
    
    The agent acts as a CURATOR with full autonomy to:
    - Decide what content is important
    - Choose how to structure the briefing
    - Select and organize content from sources
    - Cite original sources with inline links
    - Use minimal bridging text to show connections
    
    The agent's role is CURATION and CITATION, not text generation.
    Content should be passed through from upstream sources, not rewritten.
    """
    
    # Default sources - can be customized
    # Sources with kind="research" are separated from the news briefing
    # and processed independently through research batches.
    DEFAULT_SOURCES = [
        # News sources
        {"name": "NYT US News", "url": "https://rss.nytimes.com/services/xml/rss/nyt/US.xml", "type": "rss"},
        {"name": "NYT World News", "url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "type": "rss"},
        {"name": "The Atlantic", "url": "https://www.theatlantic.com/feed/all/", "type": "rss"},
        {"name": "Heather Cox Richardson", "url": "https://heathercoxrichardson.substack.com/feed", "type": "rss"},
        {"name": "MetaFilter", "url": "https://rss.metafilter.com/metafilter.rss", "type": "rss"},
        {"name": "ACOUP", "url": "https://acoup.blog/feed/", "type": "rss"},
        {"name": "Longmont Leader", "url": "https://www.longmontleader.com/rss/", "type": "rss"},
        {"name": "Nature", "url": "https://www.nature.com/nature.rss", "type": "rss"},
        {"name": "r/Longmont", "url": "https://www.reddit.com/r/Longmont.rss", "type": "rss"},
        
        # Tech sources
        {"name": "Microsoft Research", "url": "https://www.microsoft.com/en-us/research/feed/", "type": "rss"},
        {"name": "Google AI Blog", "url": "https://blog.google/technology/ai/rss/", "type": "rss"},
        {"name": "TLDR Tech", "url": None, "type": "tldr"},  # Fetched via custom method
        {"name": "Hacker News Daily", "url": None, "type": "hn-daily"},  # Fetched via custom method
        
        # Bluesky sources (examples - users can add their own)
        # {"name": "Bluesky Official", "url": "bsky.app", "type": "bluesky", "limit": 10},
        # {"name": "Example User", "url": "username.bsky.social", "type": "bluesky", "limit": 20},
        
        # Research sources
        {"name": "ArXiv CS", "url": "https://export.arxiv.org/rss/cs.DC+cs.SY+cs.PF+cs.AR", "type": "rss"},
    ]
    
    def __init__(self, sources: List[Dict[str, str]] = None, agent: Copilot = None):
        """
        Initialize the agent-centric briefing system.
        
        The system uses GitHub Copilot CLI locally with gpt-5.2 by default.
        No external API calls - all LLM interactions go through Copilot CLI.
        
        Args:
            sources: List of source dictionaries (uses DEFAULT_SOURCES if None)
            agent: Copilot instance (creates new one if None, defaults to gpt-5.2)
        """
        self.agent = agent or Copilot()  # Uses Copilot CLI with claude-opus-4.6 by default
        self.tools = AgentTools()
        self.raw_content = {}
        self.preferences = self._load_preferences()
        self.sources = sources or self.preferences.get('sources') or self.DEFAULT_SOURCES
    
    def _load_preferences(self) -> Dict[str, Any]:
        """
        Load user preferences from preferences.yaml if it exists.
        
        Returns:
            Dictionary with preferences, or default preferences if file doesn't exist
        """
        default_prefs = {
            'focus_areas': [],
            'exclude_topics': [],
            'preferred_sources': [],
            'content_preferences': {
                'include_wikipedia_context': True,
                'max_articles_per_section': 5,
                'min_article_age_hours': 0,
                'geographic_focus': None
            },
            'research_batches': [],
            'email_preferences': {
                'include_weather': True,
                'include_astronomy': True,
                'include_stocks': False,
                'subject_format': "Agent-Driven H3LPeR Briefing - {date}"
            }
        }
        
        try:
            pref_file = 'preferences.yaml'
            if os.path.exists(pref_file):
                with open(pref_file, 'r') as f:
                    loaded_prefs = yaml.safe_load(f) or {}
                
                # Deep merge with defaults
                for key in default_prefs:
                    if key not in loaded_prefs:
                        loaded_prefs[key] = default_prefs[key]
                    elif isinstance(default_prefs[key], dict) and isinstance(loaded_prefs[key], dict):
                        # Merge nested dictionaries
                        for nested_key in default_prefs[key]:
                            if nested_key not in loaded_prefs[key]:
                                loaded_prefs[key][nested_key] = default_prefs[key][nested_key]
                
                return loaded_prefs
        except Exception as e:
            print(f"Warning: Could not load preferences.yaml: {e}")
        
        return default_prefs
    
    def fetch_all_content(self, days: int = 1) -> Dict[str, List[Article]]:
        """
        Fetch content from all sources.
        
        Args:
            days: Number of days back to fetch
            
        Returns:
            Dictionary mapping source names to article lists
        """
        self.raw_content = self.tools.fetch_all_sources(self.sources, days=days)
        
        # Apply article age filtering if specified in preferences
        min_age_hours = self.preferences.get('content_preferences', {}).get('min_article_age_hours', 0)
        if min_age_hours > 0:
            import datetime as dt
            cutoff_time = dt.datetime.now() - dt.timedelta(hours=min_age_hours)
            filtered_content = {}
            for source_name, articles in self.raw_content.items():
                filtered_articles = [
                    article for article in articles 
                    if article.published_at and article.published_at < cutoff_time
                ]
                filtered_content[source_name] = filtered_articles
                if len(filtered_articles) < len(articles):
                    print(f"Filtered {len(articles) - len(filtered_articles)} recent articles from {source_name}")
            self.raw_content = filtered_content
        
        return self.raw_content
    
    def _split_sources_by_kind(self) -> tuple:
        """Split configured sources into news and research lists based on 'kind' field.

        Returns:
            (news_sources, research_sources) — two lists of source dicts.
        """
        news_sources = []
        research_sources = []
        for source in self.sources:
            if source.get('kind', 'news') == 'research':
                research_sources.append(source)
            else:
                news_sources.append(source)
        return news_sources, research_sources

    def _process_research_batches(self, research_content: Dict[str, List[Article]]) -> List[Dict[str, Any]]:
        """Process research content through configured batches.

        Each batch in ``research_batches`` produces a separate section with its
        own ranking and paper limit.  Research sources may be assigned to a
        specific batch via the ``batch`` field on the source; unassigned sources
        are included in every batch.

        Args:
            research_content: mapping of source name → articles (already fetched)

        Returns:
            List of dicts, one per batch, each with keys:
              - name: batch display name
              - articles: ranked list of Article objects for this batch
        """
        batches_cfg = self.preferences.get('research_batches', [])
        if not batches_cfg:
            # Fallback: single unnamed batch with all research content
            all_articles = [a for arts in research_content.values() for a in arts]
            if all_articles:
                return [{"name": "Research", "articles": all_articles}]
            return []

        # Build a lookup of source → assigned batch name (if any)
        source_batch_map = {}
        for source in self.sources:
            if source.get('kind', 'news') == 'research' and source.get('batch'):
                source_batch_map[source['name']] = source['batch']

        results = []
        for batch in batches_cfg:
            batch_name = batch.get('name', 'Research')
            max_papers = batch.get('max_papers', 10)
            categories = batch.get('categories', [])

            # Collect articles for this batch
            batch_articles = []
            for source_name, articles in research_content.items():
                assigned = source_batch_map.get(source_name)
                # Include if explicitly assigned to this batch, or if unassigned
                if assigned is None or assigned == batch_name:
                    batch_articles.extend(articles)

            if not batch_articles:
                continue

            # Filter by categories if provided
            if categories:
                filtered = []
                for article in batch_articles:
                    text = f"{article.title} {article.summary}".lower()
                    if any(cat.lower() in text for cat in categories):
                        filtered.append(article)
                if filtered:
                    batch_articles = filtered
                    print(f"Batch '{batch_name}': filtered to {len(batch_articles)} papers matching categories")

            # Rank if needed
            use_ranking = batch.get('use_original_ranking', True)
            if use_ranking and len(batch_articles) > max_papers:
                batch_articles = self._rank_research_papers(batch_articles, top_k=max_papers)
            else:
                batch_articles = batch_articles[:max_papers]

            results.append({"name": batch_name, "articles": batch_articles})

        return results
    
    def _format_content_for_agent(self, content: Dict[str, List[Article]]) -> str:
        """
        Format raw content into a structured prompt for the agent.
        
        Args:
            content: Dictionary mapping source names to article lists
            
        Returns:
            Formatted string representation of all content
        """
        formatted_sections = []
        
        for source_name, articles in content.items():
            if not articles:
                continue
            
            formatted_sections.append(f"\n### SOURCE: {source_name}")
            formatted_sections.append(f"Articles available: {len(articles)}\n")
            
            for i, article in enumerate(articles[:50], 1):  # Limit to 50 per source
                formatted_sections.append(f"{i}. **{article.title}**")
                formatted_sections.append(f"   URL: {article.url}")
                formatted_sections.append(f"   Published: {article.published_at}")
                if article.summary:
                    summary_preview = article.summary[:200].replace('\n', ' ')
                    formatted_sections.append(f"   Summary: {summary_preview}...")
                formatted_sections.append("")
        
        return "\n".join(formatted_sections)
    
    def generate_briefing(self, days: int = 1, include_weather: bool = True, 
                         include_stocks: bool = True, include_astronomy: bool = True,
                         use_enhanced_prompting: bool = True) -> dict:
        """
        Generate a complete briefing using the agent's autonomous curation.
        
        The agent returns a structured JSON document (schema_version 1) that
        can be rendered directly to HTML without intermediate Markdown.
        
        Args:
            days: Number of days back to fetch content
            include_weather: Whether to include weather/space weather/astronomy
            include_stocks: Whether to include stock market data
            include_astronomy: Whether to include astronomical viewing data
            use_enhanced_prompting: Use multi-step reasoning with example format
            
        Returns:
            Parsed briefing dict conforming to schema_version 1
            
        Raises:
            ValueError: If the LLM returns invalid JSON or schema validation fails
        """
        # Split sources into news and research
        news_sources, research_sources = self._split_sources_by_kind()

        # Fetch news content
        print("Fetching news content...")
        news_content = self.tools.fetch_all_sources(news_sources, days=days)

        # Fetch research content separately
        research_content = {}
        if research_sources:
            print("Fetching research content...")
            research_content = self.tools.fetch_all_sources(research_sources, days=days)

        # Store combined raw_content for backward compat
        self.raw_content = {**news_content, **research_content}

        # Apply article age filtering if specified in preferences
        min_age_hours = self.preferences.get('content_preferences', {}).get('min_article_age_hours', 0)
        if min_age_hours > 0:
            import datetime as dt
            cutoff_time = dt.datetime.now() - dt.timedelta(hours=min_age_hours)
            for store in (news_content, research_content):
                for source_name in list(store):
                    orig = store[source_name]
                    filtered = [a for a in orig if a.published_at and a.published_at < cutoff_time]
                    if len(filtered) < len(orig):
                        print(f"Filtered {len(orig) - len(filtered)} recent articles from {source_name}")
                    store[source_name] = filtered

        # Process research batches
        research_batches = self._process_research_batches(research_content) if research_content else []
        
        # Calculate totals
        total_news = sum(len(articles) for articles in news_content.values())
        total_research = sum(len(b['articles']) for b in research_batches)
        total_articles = total_news + total_research
        print(f"Fetched {total_news} news articles from {len(news_content)} sources")
        if research_batches:
            for batch in research_batches:
                print(f"Research batch '{batch['name']}': {len(batch['articles'])} papers")
        
        # Format news content for agent
        formatted_content = self._format_content_for_agent(news_content)

        # Format research batches as separate sections for the prompt
        research_prompt_parts = []
        for batch in research_batches:
            batch_lines = [f"\n### RESEARCH BATCH: {batch['name']}"]
            batch_lines.append(f"Papers: {len(batch['articles'])}\n")
            for i, article in enumerate(batch['articles'], 1):
                batch_lines.append(f"{i}. **{article.title}**")
                batch_lines.append(f"   URL: {article.url}")
                batch_lines.append(f"   Published: {article.published_at}")
                if article.summary:
                    summary_preview = article.summary[:200].replace('\n', ' ')
                    batch_lines.append(f"   Summary: {summary_preview}...")
                batch_lines.append("")
            research_prompt_parts.append("\n".join(batch_lines))
        formatted_research = "\n".join(research_prompt_parts)
        
        # Fetch API-based data using tools
        tool_data = []
        
        if include_weather:
            try:
                print("Fetching weather data via API...")
                weather_data = self.tools.get_weather_forecast()
                tool_data.append(f"### WEATHER FORECAST\n{weather_data.get('forecast_text', 'N/A')}")
                
                print("Fetching space weather data...")
                space_weather_data = self.tools.get_space_weather()
                tool_data.append(f"### SPACE WEATHER\n{space_weather_data.get('forecast', 'N/A')}")
            except Exception as e:
                print(f"Could not fetch weather data: {e}")
        
        if include_astronomy:
            try:
                print("Fetching astronomy viewing data...")
                astro_data = self.tools.get_astronomy_viewing()
                tool_data.append(f"### TONIGHT'S SKY\n{astro_data.get('viewing_info', 'N/A')}")
            except Exception as e:
                print(f"Could not fetch astronomy data: {e}")
        
        if include_stocks:
            try:
                import stocks
                stock_summary = stocks.Stocks().format_summary(['MSFT', 'NVDA', '^DJI', '^GSPC'])
                tool_data.append(f"### STOCK MARKET DATA\n{stock_summary}")
            except Exception as e:
                print(f"Could not fetch stock data: {e}")
        
        # Construct the agent prompt
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        if use_enhanced_prompting:
            # Build preferences section if there are preferences set
            prefs_section = ""
            if (self.preferences.get('focus_areas') or self.preferences.get('exclude_topics') or 
                self.preferences.get('preferred_sources') or self.preferences.get('content_preferences', {}).get('max_articles_per_section') or
                self.preferences.get('content_preferences', {}).get('geographic_focus')):
                prefs_section = "\nUSER PREFERENCES:\n"
                
                if self.preferences.get('focus_areas'):
                    prefs_section += f"\nFocus on these topics:\n" + "\n".join([f"- {area}" for area in self.preferences['focus_areas']])
                
                if self.preferences.get('exclude_topics'):
                    prefs_section += f"\n\nDe-emphasize these topics:\n" + "\n".join([f"- {topic}" for topic in self.preferences['exclude_topics']])
                
                if self.preferences.get('preferred_sources'):
                    prefs_section += f"\n\nPrioritize these sources:\n" + "\n".join([f"- {source}" for source in self.preferences['preferred_sources']])
                
                max_per_section = self.preferences.get('content_preferences', {}).get('max_articles_per_section')
                if max_per_section:
                    prefs_section += f"\n\nContent limits: Maximum {max_per_section} articles per section"
                
                geo_focus = self.preferences.get('content_preferences', {}).get('geographic_focus')
                if geo_focus:
                    prefs_section += f"\n\nGeographic focus: {geo_focus}"
                
                prefs_section += "\n"
            
            # Build the schema example — conditionally include weather section
            weather_example = ""
            if tool_data:
                weather_example = """,
    {{
      "title": "Weather & Conditions",
      "text": "Weather forecast text here",
      "children": [
        {{
          "title": "Space Weather",
          "text": "Space weather info"
        }},
        {{
          "title": "Tonight's Sky",
          "text": "Astronomy viewing info"
        }}
      ]
    }}"""

            # Build exclusion note for disabled sections
            excluded_sections = []
            if not include_weather:
                excluded_sections.append("weather")
                excluded_sections.append("space weather")
            if not include_astronomy:
                excluded_sections.append("astronomy / tonight's sky")
            if not include_stocks:
                excluded_sections.append("stock market")
            exclusion_note = ""
            if excluded_sections:
                exclusion_note = "\n- DO NOT include sections for: " + ", ".join(excluded_sections) + ". These are disabled."

            # Build research batch instructions
            research_batch_names = [b['name'] for b in research_batches]
            research_section_note = ""
            research_example = ""
            if research_batches:
                research_section_note = (
                    "\n- RESEARCH SECTIONS: The following research batches MUST each appear as their own "
                    "top-level section, separate from the news sections: "
                    + ", ".join(f'"{n}"' for n in research_batch_names)
                    + ". Use the exact batch name as the section title. "
                    "Only include papers listed in the corresponding RESEARCH BATCH above."
                )
                research_example = ",\n    ".join(
                    f'{{"title": "{name}", "text": "Top papers from this research batch", '
                    f'"children": [{{"title": "Paper title", "url": "https://arxiv.org/...", '
                    f'"text": "Key finding or contribution", '
                    f'"article": {{"title": "Paper title", "url": "https://arxiv.org/...", '
                    f'"source": "ArXiv", "summary": "Paper abstract excerpt"}}}}]}}'
                    for name in research_batch_names
                )
                research_example = ",\n    " + research_example

            agent_prompt = f"""You are an intelligent briefing CURATOR for {today}.

YOUR ROLE: Curate and cite content from sources. Return a structured JSON document.
The briefing has two distinct parts: NEWS sections and RESEARCH sections.

=== NEWS CONTENT (from {len(news_content)} sources, {total_news} articles) ===

{formatted_content}

{"=== RESEARCH CONTENT ===" + chr(10) + formatted_research if formatted_research else ""}

API-BASED DATA:
{chr(10).join(tool_data) if tool_data else "No API data available"}
{prefs_section}
APPROACH:
1. Scan news sources for major stories, patterns, and connections.
2. Rank stories by importance. Group related stories from different sources.
3. Create logical NEWS sections based on discovered themes.
4. For each RESEARCH BATCH, create a separate section with the top papers.
5. Select key excerpts from original sources. Use minimal bridging text.

OUTPUT FORMAT — Return ONLY valid JSON (no markdown fences, no commentary).
All string values must be plain text (no HTML, no markdown).

The document must conform to this schema:

{{
  "schema_version": 1,
  "title": "{today}",
  "date": "{today}",
  "children": [
    {{
      "title": "Section heading (theme name)",
      "text": "Optional brief connector text (1-2 sentences max)",
      "children": [
        {{
          "title": "Article or item title",
          "url": "https://...",
          "text": "Key excerpt or quote from the article",
          "article": {{
            "title": "Article title",
            "url": "https://...",
            "source": "Source name",
            "published_at": "date string",
            "summary": "Article summary text"
          }}
        }},
        {{
          "title": "Another article",
          "url": "https://..."
        }}
      ]
    }}{weather_example}{research_example}
  ]
}}

RULES:
- Every node MUST have a "title" (string).
- "text", "url", "article", "children" are all optional.
- "article" (when present) should have at least "title" and "url".
- Nesting can be arbitrary depth.
- schema_version MUST be 1.

CONTENT RULES:
- Create 4-8 THEMED NEWS SECTIONS as top-level children (e.g. "AI & Technology", "World Affairs", "Science", "Local News").
- Each section should contain 2-5 article children. DO NOT put single articles as top-level children.
- Include 15-25 news articles total across all news sections.
- Use "text" on section nodes for brief connectors or context (1-2 sentences).
- Use "text" on article nodes for key excerpts or quotes from the source.
- Prioritize quality sources over quantity.{research_section_note}{exclusion_note}
- NEWS and RESEARCH sections must be separate — do not mix research papers into news sections.

Your response must start with {{ and end with }}. No other text before or after.
All strings must use proper JSON escaping (escape double quotes with backslash).
Return ONLY the JSON object."""
        else:
            prefs_section = ""
            agent_prompt = f"""You are an intelligent briefing CURATOR for {today}.

Return a structured JSON document curating the most important content.
NEWS and RESEARCH content are separated — keep them in distinct sections.

NEWS CONTENT:
{formatted_content}

{"RESEARCH CONTENT:\n" + formatted_research if formatted_research else ""}

{"API DATA:\n" + chr(10).join(tool_data) if tool_data else ""}
{prefs_section}
OUTPUT: Return ONLY valid JSON with schema_version=1, title, date, and children array.
Each node has "title" (required), optional "text", "url", "article", "children".
No markdown, no HTML, no commentary — just the JSON object."""

        # Generate briefing using agent
        print("\nGenerating agent-driven briefing...")
        print("(This may take a minute as the agent analyzes all content...)")
        
        raw = self.agent.generate(agent_prompt)

        # Strip markdown code fences if the model wraps the JSON
        stripped = raw.strip()
        if stripped.startswith("```"):
            # Remove opening fence (```json or ```)
            stripped = stripped.split("\n", 1)[1] if "\n" in stripped else stripped[3:]
            if stripped.endswith("```"):
                stripped = stripped[:-3]
            stripped = stripped.strip()

        # If model omitted outer braces, try to recover
        if not stripped.startswith("{"):
            # Find the first { or wrap the whole thing
            brace_idx = stripped.find("{")
            if brace_idx >= 0:
                stripped = stripped[brace_idx:]
            else:
                stripped = "{" + stripped + "}"
        # Trim any trailing text after the closing brace
        if stripped.startswith("{"):
            depth = 0
            end = -1
            for i, ch in enumerate(stripped):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            if end > 0:
                stripped = stripped[:end + 1]

        try:
            doc = json.loads(stripped, strict=False)
        except json.JSONDecodeError as e:
            # Try to repair truncated JSON by closing open structures
            repaired = _repair_json(stripped)
            try:
                doc = json.loads(repaired, strict=False)
                print("Warning: repaired truncated JSON from agent output")
            except json.JSONDecodeError:
                # Truncate at error position, back up to last complete node, retry
                truncated = _truncate_at_error(stripped, e)
                if truncated:
                    repaired2 = _repair_json(truncated)
                    try:
                        doc = json.loads(repaired2, strict=False)
                        print("Warning: truncated and repaired JSON from agent output")
                    except json.JSONDecodeError:
                        raise ValueError(
                            f"Agent returned invalid JSON: {e}\n"
                            f"Raw output (first 500 chars): {raw[:500]}"
                        )
                else:
                    raise ValueError(
                        f"Agent returned invalid JSON: {e}\n"
                        f"Raw output (first 500 chars): {raw[:500]}"
                    )

        # Inject required top-level fields if the model forgot them
        if "schema_version" not in doc:
            doc["schema_version"] = 1
        if "date" not in doc:
            doc["date"] = today
        if "title" not in doc:
            doc["title"] = today
        if "children" not in doc:
            doc["children"] = []

        # Validate against schema
        from emailer import validate_briefing_json
        validate_briefing_json(doc)

        # Tag with the model that generated this briefing
        doc["model"] = self.agent.model

        return doc
    
    def _rank_research_papers(self, research_articles: List[Article], top_k: int = 10) -> List[Article]:
        """
        Rank research papers using the LLM to select the most impactful ones.
        
        Category filtering is handled upstream by _process_research_batches;
        this method focuses purely on ranking.
        
        Args:
            research_articles: List of research paper articles
            top_k: Number of top papers to return
            
        Returns:
            Ranked list of top research papers
        """
        if not research_articles or len(research_articles) <= top_k:
            return research_articles
        
        try:
            # Format articles for ranking
            formatted_items = []
            for i, article in enumerate(research_articles):
                formatted_items.append(f"[{i}] {article.title}")
            
            items_str = "\n".join(formatted_items)
            
            # Use the rank_items method from the agent (Copilot class)
            prompt_template = """Given these research papers, return the indices of the {top_k} most interesting and impactful ones.

Papers:
{items}

Return ONLY a JSON array of indices, like: [0, 3, 7, 12, 18]
Focus on: novelty, potential impact, clarity, and relevance to current developments."""
            
            ranked_indices = self.agent.rank_items(items_str, prompt_template, top_k=top_k)
            
            # Return ranked articles
            return [research_articles[i] for i in ranked_indices if i < len(research_articles)]
        except Exception as e:
            print(f"Error ranking research papers: {e}")
            # Fall back to returning first top_k
            return research_articles[:top_k]
    
    def generate_focused_briefing(self, focus_areas: List[str], days: int = 1) -> str:
        """
        Generate a briefing focused on specific topic areas.
        
        Args:
            focus_areas: List of topics to focus on (e.g., ["AI research", "local news"])
            days: Number of days back to fetch content
            
        Returns:
            Focused briefing as markdown string
        """
        # Fetch all content
        content = self.fetch_all_content(days=days)
        formatted_content = self._format_content_for_agent(content)
        
        focus_str = ", ".join(focus_areas)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        agent_prompt = f"""You are an intelligent briefing editor for {today}.

Create a focused briefing on these specific topics: {focus_str}

From all available content, select and synthesize information related to these focus areas.
Create appropriate sections, provide context, and draw connections.
Include inline markdown links to sources: [Article Title](url)

AVAILABLE CONTENT:
{formatted_content}

Generate a comprehensive briefing focused specifically on: {focus_str}"""

        try:
            briefing = self.agent.generate(agent_prompt)
            return briefing
        except Exception as e:
            return f"# Error Generating Focused Briefing\n\nFailed: {str(e)}"


def main():
    """Example usage of the agent-centric briefing system."""
    import sys
    
    # Create briefing system
    briefing_system = AgentBriefing()
    
    # Generate briefing
    print("=== Agent-Centric Briefing System ===\n")
    briefing = briefing_system.generate_briefing(days=1)
    
    print("\n" + "="*80)
    print("GENERATED BRIEFING")
    print("="*80 + "\n")
    print(briefing)
    
    # Optionally save to file
    if len(sys.argv) > 1 and sys.argv[1] == '--save':
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        filename = f"briefing_{today}.md"
        with open(filename, 'w') as f:
            f.write(briefing)
        print(f"\n\nBriefing saved to {filename}")


if __name__ == "__main__":
    main()
