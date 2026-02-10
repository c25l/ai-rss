#!/usr/bin/env python
"""
Citation Data Manager

Handles running citation analysis on research feeds and storing results.
This is called by the daily workflow to analyze papers and generate
citation rankings that can be displayed on the static site.
"""

import json
import os
from datetime import datetime
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
    categories: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run citation analysis on research feeds and return structured results.
    
    Args:
        days: Number of days to look back for papers
        top_n: Number of top papers to return
        min_citations: Minimum citation threshold
        categories: arXiv categories to analyze (defaults to all research categories)
        
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
    
    # Initialize Research with citation ranker
    research = Research(use_dual_ranker=False, use_citation_ranker=True)
    
    # Override categories on the citation ranker
    if research.citation_ranker:
        research.citation_ranker.categories = categories
    
    # Run citation analysis
    ranked_articles = research.citation_ranker.rank(
        articles=[],  # Not used - citation ranker fetches directly
        target=top_n,
        days=days,
        min_citations=min_citations
    )
    
    # Convert articles to serializable format
    papers = []
    for article in ranked_articles:
        paper = {
            "title": article.title,
            "url": article.url,
            "summary": article.summary,
            "published_at": str(article.published_at) if article.published_at else None,
            "citation_count": getattr(article, 'citation_count', 0),
            "total_citations": getattr(article, 'total_citations', 0),
        }
        papers.append(paper)
    
    # Create result document
    result = {
        "generated_at": datetime.now().isoformat(),
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
    min_citations: int = 1
) -> Optional[Dict[str, Any]]:
    """
    Run citation analysis and save results.
    This is the main entry point called by the daily workflow.
    
    Args:
        days: Number of days to look back for papers
        top_n: Number of top papers to return
        min_citations: Minimum citation threshold
        
    Returns:
        Citation data dict, or None on error
    """
    try:
        data = run_citation_analysis(days=days, top_n=top_n, min_citations=min_citations)
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
