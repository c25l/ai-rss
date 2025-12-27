#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Article clustering using embeddings and similarity measures
Uses Ollama with qwen3-embedding for embeddings

"""
import os
import numpy as np
from typing import List, Tuple, Optional
from datamodel import Article, Group
from datetime import datetime
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
from ollama import Ollama
from dotenv import load_dotenv
from cache import Cache

# Load environment variables
load_dotenv()


class ArticleClusterer:
    def __init__(self, embedding_model: str = None):
        """
        Initialize the article clusterer

        Args:
            embedding_model: Ollama model to use for embeddings (default: uses OLLAMA_EMBEDDING_MODEL from .env)
        """
        # Initialize Ollama client
        self.ollama = Ollama()

        # Override embedding model if specified
        if embedding_model:
            self.ollama.embedding_model = embedding_model

        # Initialize cache for embeddings
        self.cache = Cache()

    def get_embedding(self, text: str, max_length: int = 8000) -> Optional[np.ndarray]:
        """
        Get embedding vector for text using Ollama

        Args:
            text: Text to embed
            max_length: Maximum text length to send (default: 8000)

        Returns:
            numpy array of embedding vector, or None if failed
        """
        try:
            # Truncate text to max_length
            truncated_text = text[:max_length]
            
            # Use Ollama embeddings API
            embedding = self.ollama.get_embedding(truncated_text)

            if embedding and len(embedding) > 0:
                return np.array(embedding)

            print(f"  Warning: Failed to get embedding from Ollama")
            return None

        except Exception as e:
            print(f"  Warning: Ollama connection error: {e}")
            return None

    def embed_article(self, article: Article) -> Optional[np.ndarray]:
        """
        Generate embedding for an article using title + summary

        Args:
            article: Article object to embed

        Returns:
            numpy array of embedding vector, or None if failed
        """
        # Combine title and summary for richer representation with context
        from datetime import datetime
        date_str = article.published_at if hasattr(article, 'published_at') and article.published_at else datetime.now().strftime("%Y-%m-%d")
        text = f"News article from {date_str}: {article.title}\n\nURL: {article.url}\n\nSummary: {article.summary}"
        embedding = self.get_embedding(text)

        if embedding is not None:
            article.vector = embedding

        return embedding

    def embed_articles(self, articles: List[Article]) -> List[Article]:
        """
        Generate embeddings for multiple articles.
        Uses cache to avoid re-embedding articles from previous days (7-day rolling window).

       Args:
            articles: List of Article objects

        Returns:
            List of articles with embeddings (filters out failed embeddings)
        """
        # Load cached articles from last 7 days
        cached_articles = self.cache.get_cached_articles(days=7)

        embedded_articles = []
        new_articles = []  # Articles that need to be cached
        cache_hits = 0
        cache_misses = 0

        for i, article in enumerate(articles):
            # Check cache first
            if article.url and article.url in cached_articles:
                # Cache hit - restore embedding from cache
                cached_data = cached_articles[article.url]
                article.vector = np.array(cached_data['vector'])
                embedded_articles.append(article)
                cache_hits += 1
            else:
                # Cache miss - need to embed
                embedding = self.embed_article(article)
                if embedding is not None:
                    embedded_articles.append(article)
                    new_articles.append(article)
                    cache_misses += 1

        # Cache newly embedded articles
        if new_articles:
            self.cache.set_article_embeddings(new_articles)

        print(f"  Embedding cache: {cache_hits} hits, {cache_misses} misses ({cache_hits}/{len(articles)} = {100*cache_hits/len(articles) if articles else 0:.1f}% cache hit rate)")

        return embedded_articles

    def cosine_similarity_matrix(self, articles: List[Article]) -> np.ndarray:
        """
        Calculate pairwise cosine similarity between articles

        Args:
            articles: List of Article objects with embeddings

        Returns:
            2D numpy array of similarity scores
        """
        vectors = np.array([article.vector for article in articles])
        return cosine_similarity(vectors)

    def find_similar_articles(
        self,
        article: Article,
        candidates: List[Article],
        threshold: float = 0.7,
        top_k: int = 10
    ) -> List[Tuple[Article, float]]:
        """
        Find articles similar to a given article

        Args:
            article: Reference article
            candidates: List of candidate articles to compare against
            threshold: Minimum similarity score (0-1)
            top_k: Maximum number of results to return

        Returns:
            List of (article, similarity_score) tuples, sorted by similarity
        """
        if article.vector is None:
            self.embed_article(article)

        if article.vector is None:
            return []

        similarities = []
        for candidate in candidates:
            if candidate.vector is None:
                continue

            # Calculate cosine similarity
            sim = cosine_similarity(
                article.vector.reshape(1, -1),
                candidate.vector.reshape(1, -1)
            )[0][0]

            if sim >= threshold:
                similarities.append((candidate, float(sim)))

        # Sort by similarity (descending) and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]


    def cluster_articles_threshold(
        self,
        articles: List[Article],
        similarity_threshold: float = 0.66
    ) -> List[Group]:
        """
        Cluster articles using simple similarity threshold
        Greedy algorithm: each article joins the first cluster above threshold,
        or creates a new cluster

        Args:
            articles: List of Article objects with embeddings
            similarity_threshold: Minimum similarity to join a cluster

        Returns:
            List of Group objects containing clustered articles
        """
        if not articles:
            return []

        # Ensure all articles have embeddings
        articles = [a for a in articles if a.vector is not None]

        if not articles:
            print("No articles with embeddings to cluster")
            return []

        groups = []

        for article in articles:
            # Try to find a group this article belongs to
            best_group = None
            best_similarity = 0

            for group in groups:
                # Calculate average similarity to articles in this group
                similarities = []
                for group_article in group.articles:
                    sim = cosine_similarity(
                        article.vector.reshape(1, -1),
                        group_article.vector.reshape(1, -1)
                    )[0][0]
                    similarities.append(sim)

                avg_similarity = np.mean(similarities)

                if avg_similarity >= similarity_threshold and avg_similarity > best_similarity:
                    best_group = group
                    best_similarity = avg_similarity

            if best_group:
                # Add to existing group
                best_group.articles.append(article)
            else:
                # Create new group
                group = Group(
                    text=article.title[:100],  # Use article title as group name
                    articles=[article]
                )
                groups.append(group)

        return groups

    def generate_cluster_title(self, group: Group) -> str:
        """
        Use the first article's title as the cluster title

        Args:
            group: Group object containing clustered articles

        Returns:
            First article's title, or "Empty Group" if no articles
        """
        if not group.articles:
            return "Empty Group"

        return group.articles[0].title

    def generate_cluster_summary(self, group: Group, max_articles: int = 10) -> str:
        """
        Generate a summary of a cluster using LLM

        Args:
            group: Group object containing clustered articles
            max_articles: Maximum number of articles to include in context

        Returns:
            Generated summary string
        """
        if not group.articles:
            return "No articles in this group."

        # Build context from articles
        context_parts = []
        for i, article in enumerate(group.articles[:max_articles]):
            context_parts.append(f"Article {i+1}: {article.title}\n{article.summary[:300]}")

        context = "\n\n".join(context_parts)

        prompt = f"""Summarize the key themes and main points from these {len(group.articles)} related articles. Focus on what's happening and why it matters. Keep it to 2-3 sentences.

{context}

Summary:"""

        # TODO: Replace with Azure OpenAI or another LLM service
        # For now, just return a simple summary
        return f"Group of {len(group.articles)} articles about {group.text}"

    def summarize_clusters(self, groups: List[Group], generate_titles: bool = True) -> List[Group]:
        """
        Generate titles and summaries for all clusters

        Args:
            groups: List of Group objects
            generate_titles: Whether to generate new titles (default: True)

        Returns:
            List of Group objects with updated text/summaries
        """
        print(f"\n=== Generating summaries for {len(groups)} groups ===\n")

        for i, group in enumerate(groups, 1):
            print(f"Processing group {i}/{len(groups)}...")

            if generate_titles and len(group.articles) > 1:
                title = self.generate_cluster_title(group)
                group.text = title

            # You could add a summary field to the Group class if desired
            # For now we'll just print it
            #summary = self.generate_cluster_summary(group)
            print(f"  Title: {group.text}")
            #print(f"  Summary: {summary}\n")

        return groups


if __name__ == "__main__":
    # Example usage
    clusterer = ArticleClusterer()

    # Test embedding
    test_article = Article(
        title="Test Article About AI",
        summary="This is a test article about artificial intelligence and machine learning.",
        url="https://example.com"
    )

    embedding = clusterer.embed_article(test_article)

    if embedding is not None:
        print(f" Successfully generated embedding with {len(embedding)} dimensions")
    else:
        print(" Failed to generate embedding")
