#!/usr/bin/env python
"""
Citation Data Manager

Handles running citation analysis on research feeds and storing results.
This is called by the daily workflow to analyze papers and generate
citation rankings that can be displayed on the static site.
"""

import json
import os
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from research import Research
from citation_cache import CitationCache


CITATIONS_DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "briefings",
    "citations_latest.json"
)


def run_citation_analysis(
    days: int = 1,
    top_n: int = 50,
    min_citations: int = 1,
    categories: Optional[List[str]] = None,
    articles: Optional[List] = None
) -> Dict[str, Any]:
    """
    Run citation analysis on research feeds and return structured results.
    
    Args:
        days: Number of days to look back for papers
        top_n: Number of top papers to return
        min_citations: Minimum citation threshold
        categories: arXiv categories to analyze (defaults to all research categories)
        articles: Pre-fetched Article objects to analyze (skips RSS re-fetch if provided)
        
    Returns:
        Dictionary with citation analysis results
    """
    # Default categories include both AI/ML and Systems/Architecture
    if categories is None:
        categories = [
            "cs.AI", "cs.LG", "cs.CL", "cs.CV",  # AI & ML
            "cs.DC", "cs.SY", "cs.PF", "cs.AR"   # Systems & Architecture
        ]
    
    print(f"Running citation analysis on {len(categories)} categories...")
    print(f"  Days: {days}, Top N: {top_n}, Min citations: {min_citations}")
    print(f"  Categories: {', '.join(categories)}")
    
    if articles:
        print(f"  Using {len(articles)} pre-fetched articles (no RSS re-fetch)")
    
    # Initialize Research with citation ranker
    try:
        research = Research(use_dual_ranker=False, use_citation_ranker=True)
    except Exception as e:
        print(f"ERROR: Failed to initialize Research module: {e}")
        print("This may be due to missing dependencies (arxiv, semanticscholar packages)")
        print("Install with: pip install arxiv semanticscholar")
        return _create_empty_result(days, top_n, min_citations, categories, str(e))
    
    # Override categories on the citation ranker
    if research.citation_ranker:
        research.citation_ranker.categories = categories
    else:
        print("ERROR: Citation ranker not available")
        return _create_empty_result(days, top_n, min_citations, categories, "Citation ranker not initialized")
    
    # Run citation analysis
    try:
        if articles:
            # Use pre-fetched articles — bypass RSS re-fetch
            ranked_articles = research.citation_ranker.rank_from_articles(
                articles=articles,
                target=top_n,
                min_citations=min_citations
            )
        else:
            ranked_articles = research.citation_ranker.rank(
                articles=[],  # Not used - citation ranker fetches directly
                target=top_n,
                days=days,
                min_citations=min_citations
            )
    except Exception as e:
        print(f"ERROR: Citation analysis failed: {e}")
        print("This may be due to:")
        print("  - Network connectivity issues (arXiv RSS feeds unreachable)")
        print("  - API rate limiting (Semantic Scholar)")
        print("  - No papers found in the specified time period")
        return _create_empty_result(days, top_n, min_citations, categories, str(e))
    
    if not ranked_articles:
        print("WARNING: No papers found in citation analysis")
        print("Possible reasons:")
        print("  - arXiv RSS feeds may be empty or unreachable")
        print("  - No papers matched the minimum citation threshold")
        print("  - Network connectivity issues")
        print("\nTip: Try running with fewer days or lower min_citations threshold")
        return _create_empty_result(days, top_n, min_citations, categories, "No papers found")
    
    # Convert articles to serializable format
    papers = []
    for article in ranked_articles:
        # Handle published_at datetime serialization
        if article.published_at:
            if hasattr(article.published_at, 'isoformat'):
                published_at = article.published_at.isoformat()
            else:
                published_at = str(article.published_at)
        else:
            published_at = None
        
        paper = {
            "title": article.title,
            "url": article.url,
            "summary": article.summary,
            "published_at": published_at,
            "citation_count": getattr(article, 'citation_count', 0),
            "total_citations": getattr(article, 'total_citations', 0),
        }
        papers.append(paper)
    
    # Create result document
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analysis_params": {
            "days": days,
            "top_n": top_n,
            "min_citations": min_citations,
            "categories": categories,
        },
        "papers": papers,
        "paper_count": len(papers),
    }
    
    print(f"✓ Citation analysis complete: {len(papers)} papers found")
    return result


def _create_empty_result(days: int, top_n: int, min_citations: int, categories: List[str], error_msg: str) -> Dict[str, Any]:
    """
    Create an empty result with error information.
    
    Args:
        days: Days parameter
        top_n: Top N parameter
        min_citations: Min citations parameter
        categories: Categories list
        error_msg: Error message to include
        
    Returns:
        Empty result dictionary with error info
    """
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analysis_params": {
            "days": days,
            "top_n": top_n,
            "min_citations": min_citations,
            "categories": categories,
        },
        "papers": [],
        "paper_count": 0,
        "error": error_msg,
    }


def save_citation_data(data: Dict[str, Any], filepath: Optional[str] = None) -> str:
    """
    Save citation analysis results to a JSON file.
    
    Args:
        data: Citation analysis results from run_citation_analysis()
        filepath: Path to save to (defaults to CITATIONS_DATA_FILE)
        
    Returns:
        Path to saved file
    """
    if filepath is None:
        filepath = CITATIONS_DATA_FILE
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Write JSON
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✓ Citation data saved to {filepath}")
    return filepath


def load_citation_data(filepath: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Load citation analysis results from JSON file.
    
    Args:
        filepath: Path to load from (defaults to CITATIONS_DATA_FILE)
        
    Returns:
        Citation data dict, or None if file doesn't exist
    """
    if filepath is None:
        filepath = CITATIONS_DATA_FILE
    
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: Could not load citation data: {e}")
        return None


def generate_and_save_citations(
    days: int = 1,
    top_n: int = 50,
    min_citations: int = 1,
    articles: Optional[List] = None
) -> Optional[Dict[str, Any]]:
    """
    Run citation analysis and save results.
    This is the main entry point called by the daily workflow.
    
    Args:
        days: Number of days to look back for papers
        top_n: Number of top papers to return
        min_citations: Minimum citation threshold
        articles: Pre-fetched Article objects (skips RSS re-fetch if provided)
        
    Returns:
        Citation data dict, or None on error
    """
    try:
        data = run_citation_analysis(days=days, top_n=top_n, min_citations=min_citations, articles=articles)
        save_citation_data(data)
        return data
    except Exception as e:
        print(f"Error generating citation data: {e}")
        import traceback
        traceback.print_exc()
        return None


def regenerate_from_cache(
    top_n: int = 50,
    min_citations: int = 1,
    categories: Optional[List[str]] = None
) -> Optional[Dict[str, Any]]:
    """
    Regenerate citations_latest.json from the SQLite cache without re-fetching
    RSS feeds or HTML bibliographies. Only fetches arXiv metadata for papers
    not already in the cache.
    
    Args:
        top_n: Number of top papers to return
        min_citations: Minimum citation count threshold
        categories: Category list for metadata (not used for filtering)
        
    Returns:
        Citation data dict, or None on error
    """
    if categories is None:
        categories = [
            "cs.AI", "cs.LG", "cs.CL", "cs.CV",
            "cs.DC", "cs.SY", "cs.PF", "cs.AR"
        ]
    
    cache = CitationCache()
    
    import sqlite3
    conn = sqlite3.connect(cache.db_path)
    c = conn.cursor()
    
    # Get top cited papers from cache
    c.execute("""
        SELECT cited_paper, COUNT(*) as cnt
        FROM citations
        GROUP BY cited_paper
        HAVING cnt >= ?
        ORDER BY cnt DESC
        LIMIT ?
    """, (min_citations, top_n))
    top_papers = c.fetchall()
    conn.close()
    
    if not top_papers:
        print("No citation data in cache")
        return None
    
    print(f"Found {len(top_papers)} papers in cache (top {top_n}, min {min_citations} citations)")
    
    # Enrich each paper with metadata
    papers = []
    for arxiv_id, citation_count in top_papers:
        # Try cache first
        cached = cache.get_paper(arxiv_id, max_age_days=30)
        if cached:
            papers.append({
                "title": cached.get('title', arxiv_id),
                "url": cached.get('url', f"https://arxiv.org/abs/{arxiv_id}"),
                "summary": cached.get('summary', ''),
                "published_at": cached.get('published', None),
                "citation_count": citation_count,
                "total_citations": cached.get('citation_count', 0),
            })
            continue
        
        # Fetch from arXiv API (lightweight metadata only)
        paper_info = _fetch_arxiv_metadata(arxiv_id)
        if paper_info:
            cache.cache_paper(arxiv_id, paper_info)
            papers.append({
                "title": paper_info.get('title', arxiv_id),
                "url": paper_info.get('url', f"https://arxiv.org/abs/{arxiv_id}"),
                "summary": paper_info.get('summary', ''),
                "published_at": paper_info.get('published', None),
                "citation_count": citation_count,
                "total_citations": paper_info.get('citation_count', 0),
            })
        else:
            # Minimal entry with just the ID
            papers.append({
                "title": arxiv_id,
                "url": f"https://arxiv.org/abs/{arxiv_id}",
                "summary": "",
                "published_at": None,
                "citation_count": citation_count,
                "total_citations": 0,
            })
    
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analysis_params": {
            "days": 1,
            "top_n": top_n,
            "min_citations": min_citations,
            "categories": categories,
        },
        "papers": papers,
        "paper_count": len(papers),
    }
    
    save_citation_data(result)
    print(f"✓ Regenerated {len(papers)} papers from cache")
    return result


def _fetch_arxiv_metadata(arxiv_id: str) -> Optional[Dict]:
    """Fetch paper metadata from the arXiv API (Atom feed for a single paper)."""
    import requests
    try:
        resp = requests.get(
            f"http://export.arxiv.org/api/query?id_list={arxiv_id}&max_results=1",
            timeout=15
        )
        if resp.status_code != 200:
            return None
        
        from xml.etree import ElementTree as ET
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        root = ET.fromstring(resp.text)
        entry = root.find('atom:entry', ns)
        if entry is None:
            return None
        
        title = entry.findtext('atom:title', '', ns).strip().replace('\n', ' ')
        summary = entry.findtext('atom:summary', '', ns).strip().replace('\n', ' ')
        published = entry.findtext('atom:published', '', ns)[:10] if entry.findtext('atom:published', '', ns) else ''
        authors = [a.findtext('atom:name', '', ns) for a in entry.findall('atom:author', ns)]
        
        # Brief delay to be polite to arXiv API
        time.sleep(0.2)
        
        return {
            'title': title,
            'authors': authors,
            'published': published,
            'summary': summary,
            'url': f"https://arxiv.org/abs/{arxiv_id}",
            'citation_count': 0,
        }
    except Exception as e:
        print(f"  Warning: Could not fetch metadata for {arxiv_id}: {e}")
        return None


if __name__ == "__main__":
    import sys
    
    if "--from-cache" in sys.argv:
        # Regenerate from cached data (no new fetches)
        print("Regenerating from cache...")
        data = regenerate_from_cache(top_n=50, min_citations=1)
    else:
        # Full analysis
        print("Running citation analysis test...")
        data = generate_and_save_citations(days=1, top_n=50, min_citations=1)
    if data:
        print(f"\nFound {data['paper_count']} papers")
        print("\nTop 5 papers:")
        for i, paper in enumerate(data['papers'][:5], 1):
            print(f"{i}. {paper['title']}")
            print(f"   Citations: {paper['citation_count']} (total: {paper['total_citations']})")
