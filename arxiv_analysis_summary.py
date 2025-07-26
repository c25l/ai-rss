#!/usr/bin/env python3
"""
ArXiv Paper Analysis with Vectorization Filtering
Uses existing embedding system to filter papers against research preferences
"""

import requests
import numpy as np
import json
from datetime import datetime
import feedparser
import re
from collections import Counter

def analyze_arxiv_papers(json_file):
    """Analyze the extracted ArXiv papers and provide summary statistics."""
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    papers = data['papers']
    total_papers = data['total_papers']
    
    print(f"ArXiv Papers Analysis Summary")
    print(f"{'='*50}")
    print(f"Total Papers Extracted: {total_papers}")
    print(f"Source: {data['source_url']}")
    print(f"Fetch Timestamp: {data['fetch_timestamp']}")
    print(f"Date Range: Last 24 hours from July 16, 2025")
    
    # Analyze categories
    print(f"\n{'='*50}")
    print(f"CATEGORY DISTRIBUTION")
    print(f"{'='*50}")
    
    all_categories = []
    for paper in papers:
        all_categories.extend(paper['categories'])
    
    category_counts = Counter(all_categories)
    for category, count in category_counts.most_common(10):
        percentage = (count / total_papers) * 100
        print(f"{category:15} {count:4d} papers ({percentage:5.1f}%)")
    
    # Show first 10 papers with full details
    print(f"\n{'='*50}")
    print(f"FIRST 10 PAPERS (SAMPLE)")
    print(f"{'='*50}")
    
    for i, paper in enumerate(papers[:10], 1):
        print(f"\n{i}. {paper['title']}")
        print(f"   ArXiv ID: {paper['arxiv_id']}")
        print(f"   URL: {paper['arxiv_url']}")
        print(f"   Categories: {', '.join(paper['categories'])}")
        print(f"   Abstract: {paper['abstract'][:300]}...")
    
    # Show papers by major AI/ML topics
    print(f"\n{'='*50}")
    print(f"PAPERS BY MAJOR TOPICS")
    print(f"{'='*50}")
    
    ai_papers = [p for p in papers if 'cs.AI' in p['categories']]
    ml_papers = [p for p in papers if 'cs.LG' in p['categories']]
    cv_papers = [p for p in papers if 'cs.CV' in p['categories']]
    cl_papers = [p for p in papers if 'cs.CL' in p['categories']]
    
    print(f"Artificial Intelligence (cs.AI): {len(ai_papers)} papers")
    print(f"Machine Learning (cs.LG): {len(ml_papers)} papers")
    print(f"Computer Vision (cs.CV): {len(cv_papers)} papers")
    print(f"Computational Linguistics (cs.CL): {len(cl_papers)} papers")
    
    # Recent hot topics based on titles
    print(f"\n{'='*50}")
    print(f"HOT TOPICS (Based on Title Keywords)")
    print(f"{'='*50}")
    
    all_titles = ' '.join([paper['title'].lower() for paper in papers])
    
    hot_keywords = [
        'llm', 'large language model', 'transformer', 'diffusion', 
        'reinforcement learning', 'neural', 'deep learning', 'attention',
        'federated', 'multimodal', 'generative', 'classification',
        'optimization', 'agent', 'reasoning', 'vision'
    ]
    
    keyword_counts = {}
    for keyword in hot_keywords:
        count = all_titles.count(keyword)
        if count > 0:
            keyword_counts[keyword] = count
    
    sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
    for keyword, count in sorted_keywords[:10]:
        print(f"{keyword:20} {count:3d} mentions")
    
    return {
        'total_papers': total_papers,
        'categories': category_counts,
        'ai_papers': len(ai_papers),
        'ml_papers': len(ml_papers),
        'hot_keywords': keyword_counts
    }

if __name__ == "__main__":
    json_file = "/Users/chris/source/airss/arxiv_papers_20250716_190453.json"
    analysis = analyze_arxiv_papers(json_file)