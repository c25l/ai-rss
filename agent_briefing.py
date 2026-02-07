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
from typing import List, Dict, Any
from copilot import Copilot
from feeds import Feeds
from datamodel import Article
import requests
from bs4 import BeautifulSoup


class AgentTools:
    """Tools available to the agent for gathering and processing information."""
    
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
                else:
                    print(f"Unknown source type: {source_type}")
            except Exception as e:
                print(f"Error fetching {source_name}: {e}")
                all_content[source_name] = []
        
        return all_content


class AgentBriefing:
    """
    Agent-centric briefing system.
    
    The agent has full autonomy to:
    - Decide what content is important
    - Choose how to structure the briefing
    - Determine what to summarize and how
    - Create sections dynamically
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
        
        # Research sources
        {"name": "ArXiv CS", "url": "https://export.arxiv.org/rss/cs.DC+cs.SY+cs.PF+cs.AR", "type": "rss"},
    ]
    
    def __init__(self, sources: List[Dict[str, str]] = None, agent: Copilot = None):
        """
        Initialize the agent-centric briefing system.
        
        Args:
            sources: List of source dictionaries (uses DEFAULT_SOURCES if None)
            agent: Copilot instance (creates new one if None)
        """
        self.sources = sources or self.DEFAULT_SOURCES
        self.agent = agent or Copilot()
        self.tools = AgentTools()
        self.raw_content = {}
    
    def fetch_all_content(self, days: int = 1) -> Dict[str, List[Article]]:
        """
        Fetch content from all sources.
        
        Args:
            days: Number of days back to fetch
            
        Returns:
            Dictionary mapping source names to article lists
        """
        self.raw_content = self.tools.fetch_all_sources(self.sources, days=days)
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
                         include_stocks: bool = True, include_astronomy: bool = True) -> str:
        """
        Generate a complete briefing using the agent's autonomous decision-making.
        
        Args:
            days: Number of days back to fetch content
            include_weather: Whether to include weather/space weather/astronomy
            include_stocks: Whether to include stock market data
            include_astronomy: Whether to include astronomical viewing data
            
        Returns:
            Complete formatted briefing as markdown string
        """
        # Fetch all content
        print("Fetching content from all sources...")
        content = self.fetch_all_content(days=days)
        
        # Calculate total articles
        total_articles = sum(len(articles) for articles in content.values())
        print(f"Fetched {total_articles} total articles from {len(content)} sources")
        
        # Format content for agent
        formatted_content = self._format_content_for_agent(content)
        
        # Optional: Fetch auxiliary data
        auxiliary_data = []
        
        if include_weather:
            try:
                import weather
                import spaceweather
                weather_forecast = weather.Weather().format_forecast()
                spaceweather_forecast = spaceweather.SpaceWeather().format_forecast()
                auxiliary_data.append(f"### WEATHER DATA\n{weather_forecast}\n\n### SPACE WEATHER\n{spaceweather_forecast}")
            except Exception as e:
                print(f"Could not fetch weather data: {e}")
        
        if include_astronomy:
            try:
                import astronomy
                astro = astronomy.Astronomy()
                astro_info = astro.format_output()
                auxiliary_data.append(f"### ASTRONOMY DATA\n{astro_info}")
            except Exception as e:
                print(f"Could not fetch astronomy data: {e}")
        
        if include_stocks:
            try:
                import stocks
                stock_summary = stocks.Stocks().format_summary(['MSFT', 'NVDA', '^DJI', '^GSPC'])
                auxiliary_data.append(f"### STOCK MARKET DATA\n{stock_summary}")
            except Exception as e:
                print(f"Could not fetch stock data: {e}")
        
        # Construct the agent prompt
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        agent_prompt = f"""You are an intelligent briefing editor for {today}.

You have access to content from multiple sources (news, tech, research, etc.).
Your job is to CREATE A COMPREHENSIVE DAILY BRIEFING with COMPLETE AUTONOMY.

YOU DECIDE:
- Which stories/articles are most important
- How to structure the briefing (create your own sections)
- What context to add or synthesize
- How to present information (summaries, lists, analysis)
- What connections to draw between different topics
- The overall narrative and flow

GUIDELINES:
1. Be comprehensive but concise
2. Focus on what matters - significance, impact, relevance
3. Create logical sections that make sense for today's content
4. Include inline markdown links to sources: [Article Title](url)
5. Add your own analysis and synthesis when valuable
6. Connect related stories across different sources
7. Prioritize quality over quantity - better to cover fewer items well

AVAILABLE CONTENT:
{formatted_content}

{"AUXILIARY DATA:\n" + "\n\n".join(auxiliary_data) if auxiliary_data else ""}

Now, create the best possible daily briefing. Structure it however you think works best.
Use markdown formatting. Be creative and insightful."""

        # Generate briefing using agent
        print("\nGenerating agent-driven briefing...")
        print("(This may take a minute as the agent analyzes all content...)")
        
        try:
            briefing = self.agent.generate(agent_prompt)
            return briefing
        except Exception as e:
            print(f"Error generating briefing: {e}")
            return f"# Error Generating Briefing\n\nFailed to generate briefing: {str(e)}"
    
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
