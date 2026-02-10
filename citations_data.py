#!/usr/bin/env python
"""
Citation Data Manager

Handles running citation analysis on research feeds and storing results.
This is called by the daily workflow to analyze papers and generate
citation rankings that can be displayed on the static site.
"""

import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from research import Research


CITATIONS_DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "briefings",
    "citations_latest.json"
)


def run_citation_analysis(
    days: int = 1,
    top_n: int = 15,
    min_citations: int = 1,
    categories: Optional[List[str]] = None,
    fast_mode: bool = True
) -> Dict[str, Any]:
    """
    Run citation analysis on research feeds and return structured results.
    
    Args:
        days: Number of days to look back for papers
        top_n: Number of top papers to return
        min_citations: Minimum citation threshold
        categories: arXiv categories to analyze (defaults to all research categories)
        fast_mode: If True, use optimized settings (fewer papers, faster API calls)
        
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
    print(f"  Fast mode: {'enabled' if fast_mode else 'disabled'}")
    
    # Optimize parameters for fast mode
    if fast_mode:
        max_papers = 25  # Reduced from 50 - fewer API calls
        api_delay = 0.15  # Reduced from 0.5s - faster processing
        print(f"  Optimization: max_papers={max_papers}, api_delay={api_delay}s")
    else:
        max_papers = 50
        api_delay = 0.5
    
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
        ranked_articles = research.citation_ranker.rank(
            articles=[],  # Not used - citation ranker fetches directly
            target=top_n,
            days=days,
            min_citations=min_citations,
            max_papers=max_papers,
            api_delay=api_delay
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
    top_n: int = 15,
    min_citations: int = 1,
    fast_mode: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Run citation analysis and save results.
    This is the main entry point called by the daily workflow.
    
    Args:
        days: Number of days to look back for papers
        top_n: Number of top papers to return
        min_citations: Minimum citation threshold
        fast_mode: If True, use optimized settings for faster execution
        
    Returns:
        Citation data dict, or None on error
    """
    try:
        data = run_citation_analysis(
            days=days, 
            top_n=top_n, 
            min_citations=min_citations,
            fast_mode=fast_mode
        )
        save_citation_data(data)
        return data
    except Exception as e:
        print(f"Error generating citation data: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Test citation analysis
    print("Running citation analysis test...")
    data = generate_and_save_citations(days=1, top_n=15, min_citations=1)
    if data:
        print(f"\nFound {data['paper_count']} papers")
        print("\nTop 5 papers:")
        for i, paper in enumerate(data['papers'][:5], 1):
            print(f"{i}. {paper['title']}")
            print(f"   Citations: {paper['citation_count']} (total: {paper['total_citations']})")
