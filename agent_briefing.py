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
                else:
                    print(f"Unknown source type: {source_type}")
            except Exception as e:
                print(f"Error fetching {source_name}: {e}")
                all_content[source_name] = []
        
        return all_content


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
        self.sources = sources or self.DEFAULT_SOURCES
        self.agent = agent or Copilot()  # Uses Copilot CLI with gpt-5.2 by default
        self.tools = AgentTools()
        self.raw_content = {}
        self.preferences = self._load_preferences()
    
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
                'hybrid_research_ranking': True,
                'max_articles_per_section': 5,
                'min_article_age_hours': 0,
                'geographic_focus': None
            },
            'research_preferences': {
                'use_original_ranking': True,
                'max_research_papers': 10,
                'research_categories': []
            },
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
                         use_enhanced_prompting: bool = True) -> str:
        """
        Generate a complete briefing using the agent's autonomous curation.
        
        The agent acts as a CURATOR: selecting, organizing, and citing content
        from sources. The agent uses direct quotes/excerpts with inline citations
        and minimal bridging text, rather than writing summaries or analysis.
        
        Args:
            days: Number of days back to fetch content
            include_weather: Whether to include weather/space weather/astronomy
            include_stocks: Whether to include stock market data
            include_astronomy: Whether to include astronomical viewing data
            use_enhanced_prompting: Use multi-step reasoning with example format
            
        Returns:
            Complete formatted briefing as markdown string
        """
        # Fetch all content
        print("Fetching content from all sources...")
        content = self.fetch_all_content(days=days)
        
        # Apply hybrid research ranking if preferences say so
        if self.preferences.get('content_preferences', {}).get('hybrid_research_ranking', False):
            research_sources = ['ArXiv CS', 'arXiv', 'arxiv']  # Common research source names
            for source_name in content:
                if any(research_src.lower() in source_name.lower() for research_src in research_sources):
                    print(f"Applying hybrid ranking to research source: {source_name}")
                    max_papers = self.preferences.get('research_preferences', {}).get('max_research_papers', 10)
                    content[source_name] = self._rank_research_papers(content[source_name], top_k=max_papers)
        
        # Calculate total articles
        total_articles = sum(len(articles) for articles in content.values())
        print(f"Fetched {total_articles} total articles from {len(content)} sources")
        
        # Format content for agent
        formatted_content = self._format_content_for_agent(content)
        
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
            # Multi-step reasoning with example format
            
            # Build preferences section if there are preferences set
            prefs_section = ""
            if (self.preferences.get('focus_areas') or self.preferences.get('exclude_topics') or 
                self.preferences.get('preferred_sources') or self.preferences.get('content_preferences', {}).get('max_articles_per_section') or
                self.preferences.get('content_preferences', {}).get('geographic_focus')):
                prefs_section = "\n═══════════════════════════════════════════════════════════════\n\nUSER PREFERENCES:\n"
                
                if self.preferences.get('focus_areas'):
                    prefs_section += f"\n**Focus on these topics:**\n" + "\n".join([f"- {area}" for area in self.preferences['focus_areas']])
                
                if self.preferences.get('exclude_topics'):
                    prefs_section += f"\n\n**De-emphasize these topics:**\n" + "\n".join([f"- {topic}" for topic in self.preferences['exclude_topics']])
                
                if self.preferences.get('preferred_sources'):
                    prefs_section += f"\n\n**Prioritize these sources:**\n" + "\n".join([f"- {source}" for source in self.preferences['preferred_sources']])
                
                # Add content constraints
                max_per_section = self.preferences.get('content_preferences', {}).get('max_articles_per_section')
                if max_per_section:
                    prefs_section += f"\n\n**Content limits:** Maximum {max_per_section} articles per section"
                
                geo_focus = self.preferences.get('content_preferences', {}).get('geographic_focus')
                if geo_focus:
                    prefs_section += f"\n\n**Geographic focus:** {geo_focus}"
                
                prefs_section += "\n"
            
            agent_prompt = f"""You are an intelligent briefing CURATOR for {today}.

YOUR ROLE: Curate and cite content from sources - NOT to write new text.
- CURATE: Select, organize, and group the most important content
- CITE: Link directly to original sources with inline citations
- PRESERVE: Pass through original text from articles, don't rewrite
- CONNECT: Show relationships between sources with minimal bridging text

═══════════════════════════════════════════════════════════════

AVAILABLE TOOLS & DATA:

You have access to:
1. **News articles** from {len(content)} sources ({total_articles} articles)
2. **Weather & Space conditions** (real-time API data)
3. **Astronomical viewing info** (tonight's sky)
4. **Stock market data** (today's close)
5. **Wikipedia summaries** (optional: use get_wikipedia_summary(topic) for context)

CONTENT BY SOURCE:
{formatted_content}

API-BASED DATA:
{chr(10).join(tool_data) if tool_data else "No API data available"}
{prefs_section}
═══════════════════════════════════════════════════════════════

YOUR APPROACH (Multi-Step Reasoning):

STEP 1: IDENTIFY KEY THEMES
- Scan all sources for major stories, patterns, and connections
- Look for recurring topics across different sources
- Note any breaking news or significant developments

STEP 2: PRIORITIZE & GROUP
- Rank stories by importance, impact, and relevance
- Group related stories from different sources
- Identify connections between topics

STEP 3: STRUCTURE YOUR BRIEFING
- Create logical sections based on discovered themes
- Don't force content into predetermined categories
- Let the content guide your structure

STEP 4: CURATE & CITE
- Select key excerpts from original sources (use direct quotes)
- Provide inline citations to every source
- Use minimal bridging text to show connections
- Let the sources speak for themselves

═══════════════════════════════════════════════════════════════

EXAMPLE OUTPUT PATTERN:

# Daily Briefing - {today}

## [Most Important Theme]

**[Source A: Article Title](url)**
> "[Direct quote or key excerpt from the article]"

**[Source B: Related Article](url)**  
> "[Direct quote showing related angle]"

**Connection:** These sources show [brief connection in 1 sentence].

**Related:**
- [Source C: Article Title](url)
- [Source D: Article Title](url)

## [Second Theme]

**[Source E: Article Title](url)**
> "[Key excerpt from source]"

**See also:**
- [Source F](url)
- [Source G](url)

## Weather & Space Conditions

- **Weather:** [Direct info from weather API]
- **Space Weather:** [Direct info from space weather API]
- **Tonight's Sky:** [Direct info from astronomy API]

═══════════════════════════════════════════════════════════════

CRITICAL RULES:
✓ Use direct quotes/excerpts from sources (in blockquotes with >)
✓ Every piece of content must have an inline citation [Title](url)
✓ Minimize your own writing - let sources provide the text
✓ Group related sources under themes
✓ Use brief bridging text ONLY to show connections (1-2 sentences max)
✓ Create sections based on discovered themes
✓ Prioritize quality sources over quantity
✓ USE PROPER MARKDOWN FORMATTING: 
  - # for main title "# Daily Briefing - {today}"
  - ## for each theme/section heading (e.g., "## Technology Developments")
  - **[text](url)** for article links
  - > for blockquotes
✓ Start with: # Daily Briefing - {today}
✓ Use ## for EVERY section/theme heading

OPTIONAL ENHANCEMENTS:
• You can use get_wikipedia_summary(topic) to add historical context for people, organizations, or events
• Add context sparingly - only when it genuinely helps understanding

❌ DO NOT write summaries in your own words
❌ DO NOT add extensive commentary or analysis
❌ DO NOT rewrite article content
❌ DO NOT omit the # symbol from headings
❌ DO NOT use plain text for section headings - always use ##

OUTPUT MUST start with exactly:
# Daily Briefing - {today}

Then use ## for each theme/section.

Now, curate and cite the available content following this approach.
Focus on selection and organization, not text generation.
Use proper markdown formatting with # for headings."""
        else:
            # Original simple prompt (updated for curation focus)
            agent_prompt = f"""You are an intelligent briefing CURATOR for {today}.

YOUR ROLE: Curate and cite content from sources - NOT to write new text.
- CURATE: Select and organize the most important content
- CITE: Link directly to original sources with inline citations
- PRESERVE: Pass through original text from articles
- MINIMAL WRITING: Use brief text only to show connections

YOU DECIDE:
- Which stories/articles are most important
- How to structure the briefing (create your own sections)
- How to group related content
- What connections to highlight between sources

CRITICAL RULES:
✓ Use direct quotes/excerpts from sources (blockquotes with >)
✓ Every piece of content must have inline citation [Title](url)
✓ Minimize your own writing - let sources provide the text
✓ Group related sources under themes
✓ Brief bridging text ONLY for connections (1-2 sentences max)

❌ DO NOT write summaries in your own words
❌ DO NOT add extensive commentary
❌ DO NOT rewrite article content

AVAILABLE CONTENT:
{formatted_content}

{"API DATA:\n" + chr(10).join(tool_data) if tool_data else ""}
{prefs_section}
Now, curate and cite the best content. Structure it with themes/sections.
Focus on selection and organization, not text generation."""

        # Generate briefing using agent
        print("\nGenerating agent-driven briefing...")
        print("(This may take a minute as the agent analyzes all content...)")
        
        try:
            briefing = self.agent.generate(agent_prompt)
            return briefing
        except Exception as e:
            print(f"Error generating briefing: {e}")
            return f"# Error Generating Briefing\n\nFailed to generate briefing: {str(e)}"
    
    def _rank_research_papers(self, research_articles: List[Article], top_k: int = 10) -> List[Article]:
        """
        Rank research papers using the original ranking algorithm.
        
        This provides a hybrid approach: agent curates most content, but research
        papers use the proven ranking algorithm from the constrained approach.
        
        Args:
            research_articles: List of research paper articles
            top_k: Number of top papers to return
            
        Returns:
            Ranked list of top research papers
        """
        if not research_articles or len(research_articles) <= top_k:
            return research_articles
        
        # Filter by research categories if specified
        preferred_categories = self.preferences.get('research_preferences', {}).get('research_categories', [])
        if preferred_categories:
            filtered_articles = []
            for article in research_articles:
                # Check if article title or summary contains any of the preferred categories
                article_text = f"{article.title} {article.summary}".lower()
                if any(cat.lower() in article_text for cat in preferred_categories):
                    filtered_articles.append(article)
            
            if filtered_articles:
                print(f"Filtered to {len(filtered_articles)} papers matching preferred categories")
                research_articles = filtered_articles
        
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
