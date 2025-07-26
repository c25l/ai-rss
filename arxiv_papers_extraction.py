#!/usr/bin/env python3
"""
ArXiv RSS Feed Parser
Fetches and extracts ALL papers from the ArXiv RSS feed for cs.AI and cs.LG
Returns comprehensive list with titles, authors, abstracts, and URLs
"""

import feedparser
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any

def extract_authors_from_description(description: str) -> List[str]:
    """Extract authors from the RSS description field."""
    # Look for pattern like "Authors: Author1, Author2, Author3"
    author_match = re.search(r'Authors?:\s*([^<\n]+)', description)
    if author_match:
        authors_str = author_match.group(1).strip()
        # Split by comma and clean up
        authors = [author.strip() for author in authors_str.split(',')]
        return authors
    return []

def extract_abstract_from_description(description: str) -> str:
    """Extract abstract from the RSS description field."""
    # The abstract typically comes after the authors line
    # Look for content after "Authors:" line
    lines = description.split('\n')
    abstract_started = False
    abstract_lines = []
    
    for line in lines:
        line = line.strip()
        if 'Authors:' in line:
            abstract_started = True
            continue
        elif abstract_started and line:
            # Remove HTML tags
            clean_line = re.sub(r'<[^>]+>', '', line)
            if clean_line.strip():
                abstract_lines.append(clean_line.strip())
    
    return ' '.join(abstract_lines) if abstract_lines else description

def extract_arxiv_id_from_url(url: str) -> str:
    """Extract ArXiv ID from the URL."""
    match = re.search(r'arxiv\.org/abs/(\d+\.\d+)', url)
    return match.group(1) if match else ""

def fetch_() -> List[Dict[str, Any]]:
    """Fetch all papers from the ArXiv RSS feed."""
    rss_url = "https://export.arxiv.org/rss/cs.AI+cs.LG"
    
    print(f"Fetching RSS feed from: {rss_url}")
    feed = feedparser.parse(rss_url)
    
    if feed.bozo:
        print("Warning: RSS feed may have parsing issues")
    
    papers = []
    yesterday = datetime.now() - timedelta(days=1)
    
    print(f"Found {len(feed.entries)} total entries in RSS feed")
    
    for i, entry in enumerate(feed.entries, 1):
        # Extract basic information
        title = entry.title if hasattr(entry, 'title') else "No title"
        link = entry.link if hasattr(entry, 'link') else ""
        description = entry.description if hasattr(entry, 'description') else ""
        
        # Extract authors and abstract from description
        authors = extract_authors_from_description(description)
        abstract = extract_abstract_from_description(description)
        
        # Extract ArXiv ID
        arxiv_id = extract_arxiv_id_from_url(link)
        
        # Get publication date
        pub_date = entry.published if hasattr(entry, 'published') else ""
        
        # Get categories/tags
        categories = []
        if hasattr(entry, 'tags'):
            categories = [tag.term for tag in entry.tags]
        
        paper_info = {
            "paper_number": i,
            "title": title,
            "arxiv_id": arxiv_id,
            "arxiv_url": link,
            "authors": authors,
            "abstract": abstract,
            "publication_date": pub_date,
            "categories": categories,
            "raw_description": description  # For debugging
        }
        
        papers.append(paper_info)
        
        print(f"Processed paper {i}: {title[:80]}...")
    
    return papers

def save_papers_to_json(papers: List[Dict[str, Any]], filename: str = None) -> str:
    """Save papers to JSON file."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"arxiv_papers_{timestamp}.json"
    
    filepath = f"/Users/chris/source/airss/{filename}"
    
    data = {
        "fetch_timestamp": datetime.now().isoformat(),
        "total_papers": len(papers),
        "source_url": "https://export.arxiv.org/rss/cs.AI+cs.LG",
        "papers": papers
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(papers)} papers to {filepath}")
    return filepath

def print_papers_summary(papers: List[Dict[str, Any]]):
    """Print a summary of all papers."""
    print(f"\n{'='*80}")
    print(f"ARXIV PAPERS SUMMARY - {len(papers)} PAPERS FOUND")
    print(f"{'='*80}")
    
    for paper in papers:
        print(f"\n{paper['paper_number']}. {paper['title']}")
        print(f"   ArXiv ID: {paper['arxiv_id']}")
        print(f"   Authors: {', '.join(paper['authors']) if paper['authors'] else 'No authors found'}")
        print(f"   URL: {paper['arxiv_url']}")
        print(f"   Date: {paper['publication_date']}")
        print(f"   Categories: {', '.join(paper['categories']) if paper['categories'] else 'No categories'}")
        print(f"   Abstract: {paper['abstract'][:200]}..." if len(paper['abstract']) > 200 else f"   Abstract: {paper['abstract']}")

if __name__ == "__main__":
    try:
        print("Starting ArXiv RSS feed extraction...")
        papers = fetch_arxiv_papers()
        
        # Save to JSON file
        json_file = save_papers_to_json(papers)
        
        # Print summary
        print_papers_summary(papers)
        
        print(f"\n{'='*80}")
        print(f"EXTRACTION COMPLETE")
        print(f"Total papers extracted: {len(papers)}")
        print(f"Data saved to: {json_file}")
        print(f"{'='*80}")
        
    except Exception as e:
        print(f"Error during extraction: {e}")
        import traceback
        traceback.print_exc()