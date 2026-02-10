#!/usr/bin/env python
"""
Citation Cache Module

Provides local SQLite caching for citation data to improve performance.
Caches citation relationships and paper metadata to avoid repeated API calls.
"""

import sqlite3
import json
import os
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Tuple, Optional
from contextlib import contextmanager


class CitationCache:
    """Local SQLite cache for citation data."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize citation cache.
        
        Args:
            db_path: Path to SQLite database file. Defaults to briefings/citations_cache.db
        """
        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "briefings",
                "citations_cache.db"
            )
        
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_db(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Table for paper metadata
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS papers (
                    arxiv_id TEXT PRIMARY KEY,
                    title TEXT,
                    authors TEXT,
                    published TEXT,
                    summary TEXT,
                    url TEXT,
                    total_citations INTEGER,
                    last_updated TEXT
                )
            """)
            
            # Table for citation relationships (citing_paper -> cited_paper)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS citations (
                    citing_paper TEXT,
                    cited_paper TEXT,
                    last_updated TEXT,
                    PRIMARY KEY (citing_paper, cited_paper)
                )
            """)
            
            # Index for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_cited_paper 
                ON citations(cited_paper)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_last_updated 
                ON papers(last_updated)
            """)
    
    def cache_paper(self, arxiv_id: str, paper_data: Dict):
        """
        Cache paper metadata.
        
        Args:
            arxiv_id: arXiv paper ID
            paper_data: Dictionary with paper metadata
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            authors_json = json.dumps(paper_data.get('authors', []))
            now = datetime.now(timezone.utc).isoformat()
            
            cursor.execute("""
                INSERT OR REPLACE INTO papers 
                (arxiv_id, title, authors, published, summary, url, total_citations, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                arxiv_id,
                paper_data.get('title', ''),
                authors_json,
                paper_data.get('published', ''),
                paper_data.get('summary', ''),
                paper_data.get('url', f'https://arxiv.org/abs/{arxiv_id}'),
                paper_data.get('citation_count', 0),
                now
            ))
    
    def cache_citations(self, citing_paper: str, cited_papers: List[str]):
        """
        Cache citation relationships.
        
        Args:
            citing_paper: arXiv ID of the citing paper
            cited_papers: List of arXiv IDs of cited papers
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now(timezone.utc).isoformat()
            
            for cited in cited_papers:
                cursor.execute("""
                    INSERT OR REPLACE INTO citations 
                    (citing_paper, cited_paper, last_updated)
                    VALUES (?, ?, ?)
                """, (citing_paper, cited, now))
    
    def get_paper(self, arxiv_id: str, max_age_days: int = 30) -> Optional[Dict]:
        """
        Get cached paper metadata.
        
        Args:
            arxiv_id: arXiv paper ID
            max_age_days: Maximum age of cached data in days
            
        Returns:
            Paper metadata dict or None if not cached or too old
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cutoff = (datetime.now(timezone.utc) - timedelta(days=max_age_days)).isoformat()
            
            cursor.execute("""
                SELECT * FROM papers 
                WHERE arxiv_id = ? AND last_updated > ?
            """, (arxiv_id, cutoff))
            
            row = cursor.fetchone()
            if row:
                return {
                    'arxiv_id': row['arxiv_id'],
                    'title': row['title'],
                    'authors': json.loads(row['authors']) if row['authors'] else [],
                    'published': row['published'],
                    'summary': row['summary'],
                    'url': row['url'],
                    'citation_count': row['total_citations'],
                    'last_updated': row['last_updated']
                }
            return None
    
    def get_citations(self, arxiv_id: str, max_age_days: int = 30) -> Optional[List[str]]:
        """
        Get cached citations for a paper.
        
        Args:
            arxiv_id: arXiv paper ID
            max_age_days: Maximum age of cached data in days
            
        Returns:
            List of cited paper IDs or None if not cached or too old
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cutoff = (datetime.now(timezone.utc) - timedelta(days=max_age_days)).isoformat()
            
            cursor.execute("""
                SELECT cited_paper FROM citations 
                WHERE citing_paper = ? AND last_updated > ?
            """, (arxiv_id, cutoff))
            
            rows = cursor.fetchall()
            if rows:
                return [row['cited_paper'] for row in rows]
            return None
    
    def get_most_cited(self, min_citations: int = 1, limit: int = 15) -> List[Tuple[str, int]]:
        """
        Get most cited papers from cache.
        
        Args:
            min_citations: Minimum citation count
            limit: Maximum number of papers to return
            
        Returns:
            List of (arxiv_id, citation_count) tuples
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT cited_paper, COUNT(*) as count
                FROM citations
                GROUP BY cited_paper
                HAVING count >= ?
                ORDER BY count DESC
                LIMIT ?
            """, (min_citations, limit))
            
            return [(row['cited_paper'], row['count']) for row in cursor.fetchall()]
    
    def get_cache_stats(self) -> Dict:
        """
        Get statistics about cached data.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as count FROM papers")
            papers_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM citations")
            citations_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT MAX(last_updated) as latest FROM papers")
            latest_paper = cursor.fetchone()['latest']
            
            cursor.execute("SELECT MAX(last_updated) as latest FROM citations")
            latest_citation = cursor.fetchone()['latest']
            
            return {
                'papers_cached': papers_count,
                'citations_cached': citations_count,
                'latest_paper_update': latest_paper,
                'latest_citation_update': latest_citation,
                'db_path': self.db_path
            }
    
    def clear_old_data(self, max_age_days: int = 90):
        """
        Clear cached data older than specified age.
        
        Args:
            max_age_days: Maximum age to keep in days
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cutoff = (datetime.now(timezone.utc) - timedelta(days=max_age_days)).isoformat()
            
            cursor.execute("DELETE FROM papers WHERE last_updated < ?", (cutoff,))
            cursor.execute("DELETE FROM citations WHERE last_updated < ?", (cutoff,))
            
            print(f"Cleared cached data older than {max_age_days} days")


if __name__ == "__main__":
    # Test the cache
    cache = CitationCache()
    
    # Test caching a paper
    test_paper = {
        'title': 'Test Paper',
        'authors': ['Alice', 'Bob'],
        'published': '2024-01-01',
        'summary': 'A test paper',
        'citation_count': 100
    }
    
    cache.cache_paper('1234.5678', test_paper)
    cache.cache_citations('1234.5678', ['9999.8888', '7777.6666'])
    
    # Test retrieval
    retrieved = cache.get_paper('1234.5678')
    print("Retrieved paper:", retrieved)
    
    citations = cache.get_citations('1234.5678')
    print("Retrieved citations:", citations)
    
    # Get stats
    stats = cache.get_cache_stats()
    print("\nCache stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
