#!/usr/bin/env python
"""
ArXiv Citation Graph Analyzer

This module fetches recent arXiv papers, builds a directed citation graph,
and identifies the most-cited papers based on references from today's submissions.

The approach:
1. Fetch papers from arXiv posted in the last N days (using existing RSS feeds)
2. For each paper, extract references using Semantic Scholar API
3. Build a directed graph where edges point from citing paper -> cited paper
4. Calculate in-degree (citation count) for each paper
5. Return papers with highest citation count from recent submissions

This helps identify important/foundational papers that today's research is building upon.

Note: This version works with or without external network access by using the 
existing feeds.py infrastructure for arXiv RSS feeds.
"""

from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict, Tuple, Optional
import time
import re
import signal

# Try to import optional dependencies
try:
    import arxiv
    ARXIV_AVAILABLE = True
except ImportError:
    ARXIV_AVAILABLE = False

try:
    from semanticscholar import SemanticScholar
    S2_AVAILABLE = True
except ImportError:
    S2_AVAILABLE = False

# Import local dependencies
from feeds import Feeds
from datamodel import Article


class ApiTimeoutError(Exception):
    """Raised when an API operation times out"""
    pass


def timeout_handler(signum, frame):
    """Signal handler for timeout"""
    raise ApiTimeoutError("Operation timed out")


class ArxivCitationAnalyzer:
    """
    Analyzes arXiv papers to find most-cited papers from recent submissions.
    """
    
    def __init__(self, api_key: Optional[str] = None, use_rss: bool = True, api_timeout: int = 30):
        """
        Initialize the analyzer.
        
        Args:
            api_key: Optional Semantic Scholar API key for higher rate limits
            use_rss: If True, use RSS feeds (more reliable). If False, use arxiv API.
            api_timeout: Timeout in seconds for API calls (default: 30)
        """
        self.use_rss = use_rss
        self.api_timeout = api_timeout
        if not use_rss and ARXIV_AVAILABLE:
            self.arxiv_client = arxiv.Client()
        else:
            self.arxiv_client = None
            
        if S2_AVAILABLE:
            self.s2_client = SemanticScholar(api_key=api_key) if api_key else SemanticScholar()
        else:
            self.s2_client = None
            print("Warning: semanticscholar package not available. Citation analysis will be limited.")
            
        self.citation_graph = defaultdict(int)  # cited_paper_id -> citation_count
        self.paper_info = {}  # paper_id -> paper metadata
        
    def _extract_arxiv_id(self, url_or_id: str) -> Optional[str]:
        """
        Extract clean arXiv ID from URL or raw ID.
        
        Args:
            url_or_id: URL like 'http://arxiv.org/abs/2101.12345v2' or ID like '2101.12345'
            
        Returns:
            Clean arXiv ID without version, e.g., '2101.12345'
        """
        # Match patterns like 2101.12345v2 or 2101.12345
        match = re.search(r'(\d{4}\.\d{4,5})', url_or_id)
        if match:
            return match.group(1)
        return None
    
    def fetch_recent_arxiv_papers_rss(
        self,
        categories: List[str] = ["cs.AI", "cs.LG", "cs.CL"],
        days: int = 1
    ) -> List[Article]:
        """
        Fetch recent papers from arXiv using RSS feeds.
        
        Args:
            categories: List of arXiv category codes (e.g., ['cs.AI', 'cs.LG'])
            days: Number of days to look back
            
        Returns:
            List of Article objects from feeds.py
        """
        # Build RSS URL for categories
        category_str = "+".join(categories)
        feed_url = f"https://export.arxiv.org/rss/{category_str}"
        
        print(f"Fetching arXiv papers from RSS: {feed_url}")
        articles = Feeds.get_articles(feed_url, days=days)
        
        print(f"Fetched {len(articles)} papers from arXiv RSS feed")
        return articles
    
    def fetch_recent_arxiv_papers(
        self, 
        categories: List[str] = ["cs.AI", "cs.LG", "cs.CL"],
        days: int = 1,
        max_results: int = 100
    ):
        """
        Fetch recent papers from arXiv.
        
        Args:
            categories: List of arXiv category codes (e.g., ['cs.AI', 'cs.LG'])
            days: Number of days to look back
            max_results: Maximum number of papers to fetch (only used with API mode)
            
        Returns:
            List of Article objects or arxiv.Result objects depending on mode
        """
        if self.use_rss or not ARXIV_AVAILABLE:
            return self.fetch_recent_arxiv_papers_rss(categories, days)
        
        # API mode (requires arxiv package and network access)
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Build query for multiple categories
        category_query = " OR ".join([f"cat:{cat}" for cat in categories])
        
        search = arxiv.Search(
            query=category_query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )
        
        papers = []
        for result in self.arxiv_client.results(search):
            # Filter by date
            if result.published >= cutoff_date:
                papers.append(result)
        
        print(f"Fetched {len(papers)} papers from arXiv API")
        return papers
    
    def get_paper_references(self, arxiv_id: str) -> List[str]:
        """
        Get references for a paper using Semantic Scholar API.
        
        Args:
            arxiv_id: arXiv ID (e.g., '2101.12345')
            
        Returns:
            List of arXiv IDs that this paper references
        """
        if not S2_AVAILABLE or not self.s2_client:
            return []
            
        try:
            # Set up timeout using signal (Unix only)
            # Note: This is not thread-safe. Use only in single-threaded contexts.
            # For multi-threaded applications, consider using threading.Timer instead.
            if hasattr(signal, 'SIGALRM'):
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(self.api_timeout)
            
            try:
                # Query Semantic Scholar using arXiv ID
                paper = self.s2_client.get_paper(f"ARXIV:{arxiv_id}")
                
                if not paper or not paper.references:
                    return []
                
                # Extract arXiv IDs from references
                arxiv_refs = []
                for ref in paper.references:
                    if ref.externalIds and 'ArXiv' in ref.externalIds:
                        ref_arxiv_id = self._extract_arxiv_id(ref.externalIds['ArXiv'])
                        if ref_arxiv_id:
                            arxiv_refs.append(ref_arxiv_id)
                
                return arxiv_refs
            finally:
                # Disable alarm
                if hasattr(signal, 'SIGALRM'):
                    signal.alarm(0)
            
        except ApiTimeoutError:
            print(f"  Timeout fetching references for {arxiv_id}")
            return []
        except Exception:
            # Silently ignore errors to continue with other papers
            # Common errors: paper not in Semantic Scholar, rate limits, network issues
            return []
    
    def _format_published_date(self, published) -> str:
        """
        Format published date consistently.
        
        Args:
            published: Date as string or datetime object
            
        Returns:
            ISO format date string
        """
        if hasattr(published, 'isoformat'):
            return published.isoformat()
        return str(published) if published else ''
    
    def build_citation_graph(
        self, 
        papers: List,
        delay: float = 0.5
    ) -> Dict[str, int]:
        """
        Build citation graph from papers and their references.
        
        Args:
            papers: List of Article or arxiv.Result objects
            delay: Delay between API calls (seconds) to respect rate limits
            
        Returns:
            Dictionary mapping cited paper IDs to citation counts
        """
        if not S2_AVAILABLE:
            print("Semantic Scholar not available - cannot build citation graph")
            return {}
            
        print(f"Building citation graph for {len(papers)} papers...")
        
        for i, paper in enumerate(papers):
            # Handle both Article and arxiv.Result objects
            if isinstance(paper, Article):
                arxiv_id = self._extract_arxiv_id(paper.url)
                title = paper.title
                summary = paper.summary
                published = self._format_published_date(paper.published_at)
                url = paper.url
            else:
                # arxiv.Result object
                arxiv_id = self._extract_arxiv_id(paper.entry_id)
                title = paper.title
                summary = paper.summary
                published = self._format_published_date(paper.published)
                url = paper.entry_id
                
            if not arxiv_id:
                continue
            
            # Store paper info
            self.paper_info[arxiv_id] = {
                'title': title,
                'authors': [] if isinstance(paper, Article) else [author.name for author in paper.authors],
                'published': published,
                'url': url,
                'summary': summary
            }
            
            # Get references
            print(f"  [{i+1}/{len(papers)}] Fetching references for {arxiv_id}...")
            references = self.get_paper_references(arxiv_id)
            
            if references:
                print(f"    Found {len(references)} arXiv references")
            
            # Update citation graph
            for ref_id in references:
                self.citation_graph[ref_id] += 1
                
                # Store basic info for cited paper if not already present
                if ref_id not in self.paper_info:
                    self.paper_info[ref_id] = {
                        'title': 'Unknown',
                        'authors': [],
                        'published': None,
                        'url': f"https://arxiv.org/abs/{ref_id}",
                        'summary': ''
                    }
            
            # Respect API rate limits
            time.sleep(delay)
        
        print(f"Citation graph built: {len(self.citation_graph)} unique cited papers")
        return self.citation_graph
    
    def get_most_cited_papers(
        self, 
        top_n: int = 10,
        min_citations: int = 2
    ) -> List[Tuple[str, int, Dict]]:
        """
        Get the most-cited papers from the citation graph.
        
        Args:
            top_n: Number of top papers to return
            min_citations: Minimum citation count threshold
            
        Returns:
            List of tuples (arxiv_id, citation_count, paper_info)
        """
        # Filter and sort by citation count
        cited_papers = [
            (paper_id, count) 
            for paper_id, count in self.citation_graph.items()
            if count >= min_citations
        ]
        cited_papers.sort(key=lambda x: x[1], reverse=True)
        
        # Get top N with paper info
        results = []
        for paper_id, count in cited_papers[:top_n]:
            paper_info = self.paper_info.get(paper_id, {})
            results.append((paper_id, count, paper_info))
        
        return results
    
    def enrich_paper_info(self, arxiv_id: str) -> Dict:
        """
        Enrich paper info by fetching full details from Semantic Scholar.
        
        Args:
            arxiv_id: arXiv ID
            
        Returns:
            Enriched paper info dictionary
        """
        if not S2_AVAILABLE or not self.s2_client:
            return self.paper_info.get(arxiv_id, {})
            
        try:
            # Set up timeout using signal (Unix only)
            # Note: This is not thread-safe. Use only in single-threaded contexts.
            if hasattr(signal, 'SIGALRM'):
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(self.api_timeout)
            
            try:
                paper = self.s2_client.get_paper(f"ARXIV:{arxiv_id}")
                if paper:
                    return {
                        'title': paper.title or 'Unknown',
                        'authors': [author.name for author in (paper.authors or [])],
                        'published': paper.publicationDate,
                        'url': f"https://arxiv.org/abs/{arxiv_id}",
                        'summary': paper.abstract or '',
                        'citation_count': paper.citationCount or 0,
                        'influential_citation_count': paper.influentialCitationCount or 0
                    }
            finally:
                # Disable alarm
                if hasattr(signal, 'SIGALRM'):
                    signal.alarm(0)
                    
        except ApiTimeoutError:
            print(f"  Timeout enriching info for {arxiv_id}")
        except Exception:
            # Return existing info if enrichment fails (e.g., network issue, paper not found)
            pass
        
        return self.paper_info.get(arxiv_id, {})
    
    def analyze(
        self,
        categories: List[str] = ["cs.AI", "cs.LG", "cs.CL"],
        days: int = 1,
        max_papers: int = 100,
        top_n: int = 10,
        min_citations: int = 2,
        api_delay: float = 0.5
    ) -> List[Tuple[str, int, Dict]]:
        """
        Complete analysis pipeline.
        
        Args:
            categories: arXiv categories to analyze
            days: Days to look back for papers
            max_papers: Max papers to fetch from arXiv
            top_n: Number of top cited papers to return
            min_citations: Minimum citation threshold
            api_delay: Delay between API calls
            
        Returns:
            List of (arxiv_id, citation_count, paper_info) tuples
        """
        # Fetch recent papers
        papers = self.fetch_recent_arxiv_papers(
            categories=categories,
            days=days,
            max_results=max_papers
        )
        
        if not papers:
            print("No papers found!")
            return []
        
        # Build citation graph
        self.build_citation_graph(papers, delay=api_delay)
        
        # Get most cited papers
        top_papers = self.get_most_cited_papers(
            top_n=top_n,
            min_citations=min_citations
        )
        
        # Enrich info for top papers
        print(f"\nEnriching info for top {len(top_papers)} papers...")
        enriched_results = []
        for arxiv_id, count, info in top_papers:
            enriched_info = self.enrich_paper_info(arxiv_id)
            enriched_results.append((arxiv_id, count, enriched_info))
            time.sleep(api_delay)
        
        return enriched_results
    
    def format_results(self, results: List[Tuple[str, int, Dict]]) -> str:
        """
        Format results as markdown.
        
        Args:
            results: List of (arxiv_id, citation_count, paper_info)
            
        Returns:
            Formatted markdown string
        """
        if not results:
            return "No highly-cited papers found."
        
        output = ["# Most Cited Papers from Recent arXiv Submissions\n"]
        output.append(f"*Based on citation analysis of recent papers*\n")
        
        for i, (arxiv_id, cite_count, info) in enumerate(results, 1):
            title = info.get('title', 'Unknown')
            authors = info.get('authors', [])
            url = info.get('url', f"https://arxiv.org/abs/{arxiv_id}")
            total_citations = info.get('citation_count', 'Unknown')
            
            output.append(f"\n## {i}. [{title}]({url})")
            output.append(f"- **arXiv ID**: {arxiv_id}")
            output.append(f"- **Cited by recent papers**: {cite_count} times")
            if total_citations != 'Unknown':
                output.append(f"- **Total citations**: {total_citations}")
            if authors:
                author_str = ", ".join(authors[:3])
                if len(authors) > 3:
                    author_str += f" et al. ({len(authors)} authors)"
                output.append(f"- **Authors**: {author_str}")
            
            summary = info.get('summary', '')
            if summary:
                # Truncate long summaries
                if len(summary) > 300:
                    summary = summary[:300] + "..."
                output.append(f"\n{summary}")
        
        return "\n".join(output)


def main():
    """CLI interface for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analyze arXiv papers to find most-cited papers from recent submissions"
    )
    parser.add_argument(
        '--categories', 
        nargs='+', 
        default=['cs.AI', 'cs.LG', 'cs.CL'],
        help='arXiv categories to analyze (default: cs.AI cs.LG cs.CL)'
    )
    parser.add_argument(
        '--days', 
        type=int, 
        default=1,
        help='Days to look back (default: 1)'
    )
    parser.add_argument(
        '--max-papers', 
        type=int, 
        default=50,
        help='Maximum papers to fetch (default: 50, only for API mode)'
    )
    parser.add_argument(
        '--top-n', 
        type=int, 
        default=10,
        help='Number of top cited papers to show (default: 10)'
    )
    parser.add_argument(
        '--min-citations', 
        type=int, 
        default=2,
        help='Minimum citation count threshold (default: 2)'
    )
    parser.add_argument(
        '--api-key',
        default=None,
        help='Semantic Scholar API key (optional, for higher rate limits)'
    )
    parser.add_argument(
        '--use-api',
        action='store_true',
        help='Use arXiv API instead of RSS feeds (requires network access)'
    )
    
    args = parser.parse_args()
    
    print("=== arXiv Citation Graph Analyzer ===\n")
    print(f"Categories: {', '.join(args.categories)}")
    print(f"Days back: {args.days}")
    print(f"Max papers: {args.max_papers}")
    print(f"Top N: {args.top_n}")
    print(f"Min citations: {args.min_citations}")
    print(f"Mode: {'API' if args.use_api else 'RSS'}\n")
    
    analyzer = ArxivCitationAnalyzer(api_key=args.api_key, use_rss=not args.use_api)
    
    results = analyzer.analyze(
        categories=args.categories,
        days=args.days,
        max_papers=args.max_papers,
        top_n=args.top_n,
        min_citations=args.min_citations
    )
    
    print("\n" + "="*60)
    print(analyzer.format_results(results))


if __name__ == "__main__":
    main()
