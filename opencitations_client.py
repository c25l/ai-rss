#!/usr/bin/env python
"""
OpenCitations API Client

Provides access to citation data from OpenCitations.net API.
Alternative to Semantic Scholar API with no rate limits.
"""

import requests
import time
from typing import List, Dict, Optional
import re


class OpenCitationsClient:
    """
    Client for OpenCitations API.
    
    OpenCitations provides free, open citation data with no rate limits.
    API Documentation: https://opencitations.net/index/api/v2
    """
    
    def __init__(self, base_url: str = "https://opencitations.net/index/api/v2"):
        """
        Initialize OpenCitations client.
        
        Args:
            base_url: Base URL for OpenCitations API
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'H3lPeR-Citation-Analyzer/1.0'
        })
    
    def _extract_arxiv_id(self, url_or_id: str) -> Optional[str]:
        """
        Extract clean arXiv ID from URL or raw ID.
        
        Args:
            url_or_id: URL like 'http://arxiv.org/abs/2101.12345v2' or ID like '2101.12345'
            
        Returns:
            Clean arXiv ID without version, e.g., '2101.12345'
        """
        match = re.search(r'(\d{4}\.\d{4,5})', url_or_id)
        if match:
            return match.group(1)
        return None
    
    def _arxiv_to_doi(self, arxiv_id: str) -> str:
        """
        Convert arXiv ID to DOI format expected by OpenCitations.
        
        Args:
            arxiv_id: arXiv ID like '2101.12345'
            
        Returns:
            DOI string for OpenCitations API
        """
        # OpenCitations uses DOI format. For arXiv papers, we construct a DOI-like identifier
        # Note: Not all arXiv papers have DOIs, so this may not always work
        return f"10.48550/arXiv.{arxiv_id}"
    
    def get_references(self, arxiv_id: str, timeout: int = 10) -> List[str]:
        """
        Get references cited by a paper.
        
        Args:
            arxiv_id: arXiv paper ID
            timeout: Request timeout in seconds
            
        Returns:
            List of arXiv IDs cited by this paper
        """
        doi = self._arxiv_to_doi(arxiv_id)
        
        try:
            # OpenCitations API endpoint for references
            url = f"{self.base_url}/references/{doi}"
            response = self.session.get(url, timeout=timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract arXiv IDs from references
                arxiv_refs = []
                for ref in data:
                    # Look for arXiv identifiers in the citation
                    cited = ref.get('cited', '')
                    arxiv_match = self._extract_arxiv_id(cited)
                    if arxiv_match:
                        arxiv_refs.append(arxiv_match)
                
                return arxiv_refs
            elif response.status_code == 404:
                # Paper not found in OpenCitations
                return []
            else:
                print(f"OpenCitations API error {response.status_code} for {arxiv_id}")
                return []
                
        except requests.Timeout:
            print(f"Timeout getting references for {arxiv_id}")
            return []
        except Exception as e:
            print(f"Error getting references for {arxiv_id}: {e}")
            return []
    
    def get_citations(self, arxiv_id: str, timeout: int = 10) -> int:
        """
        Get citation count for a paper.
        
        Args:
            arxiv_id: arXiv paper ID
            timeout: Request timeout in seconds
            
        Returns:
            Number of citations
        """
        doi = self._arxiv_to_doi(arxiv_id)
        
        try:
            # OpenCitations API endpoint for citations
            url = f"{self.base_url}/citations/{doi}"
            response = self.session.get(url, timeout=timeout)
            
            if response.status_code == 200:
                data = response.json()
                return len(data) if data else 0
            elif response.status_code == 404:
                return 0
            else:
                print(f"OpenCitations API error {response.status_code} for {arxiv_id}")
                return 0
                
        except requests.Timeout:
            print(f"Timeout getting citations for {arxiv_id}")
            return 0
        except Exception as e:
            print(f"Error getting citations for {arxiv_id}: {e}")
            return 0
    
    def get_metadata(self, arxiv_id: str, timeout: int = 10) -> Optional[Dict]:
        """
        Get metadata for a paper.
        
        Args:
            arxiv_id: arXiv paper ID
            timeout: Request timeout in seconds
            
        Returns:
            Dictionary with paper metadata or None
        """
        doi = self._arxiv_to_doi(arxiv_id)
        
        try:
            # OpenCitations API endpoint for metadata
            url = f"{self.base_url}/metadata/{doi}"
            response = self.session.get(url, timeout=timeout)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    paper = data[0]  # API returns array
                    return {
                        'title': paper.get('title', ''),
                        'authors': paper.get('author', '').split('; ') if paper.get('author') else [],
                        'year': paper.get('year', ''),
                        'doi': paper.get('id', ''),
                    }
            return None
                
        except Exception as e:
            print(f"Error getting metadata for {arxiv_id}: {e}")
            return None


if __name__ == "__main__":
    # Test the OpenCitations client
    client = OpenCitationsClient()
    
    # Test with a well-known arXiv paper (Attention is All You Need)
    test_arxiv_id = "1706.03762"
    
    print(f"Testing OpenCitations API with arXiv ID: {test_arxiv_id}")
    print(f"DOI format: {client._arxiv_to_doi(test_arxiv_id)}")
    
    print("\nGetting references...")
    refs = client.get_references(test_arxiv_id)
    print(f"Found {len(refs)} references")
    if refs:
        print("First 5 references:", refs[:5])
    
    print("\nGetting citation count...")
    citations = client.get_citations(test_arxiv_id)
    print(f"Citation count: {citations}")
    
    print("\nGetting metadata...")
    metadata = client.get_metadata(test_arxiv_id)
    if metadata:
        print(f"Title: {metadata.get('title', 'N/A')}")
        print(f"Authors: {', '.join(metadata.get('authors', [])[:3])}")
        print(f"Year: {metadata.get('year', 'N/A')}")
