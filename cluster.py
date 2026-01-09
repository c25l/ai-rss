#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Article clustering using embeddings and similarity measures
Uses Azure OpenAI for embeddings

"""
import os
import numpy as np
from typing import List, Tuple, Optional
from datamodel import Article, Group
from datetime import datetime
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ArticleClusterer:
    def __init__(self, embedding_model: str = "text-embedding-ada-002"):
        """
        Initialize the article clusterer

        Args:
            embedding_model: Azure OpenAI model to use for embeddings (default: text-embedding-ada-002)
        """
        self.embedding_model = embedding_model

        # Initialize Azure OpenAI client
        self.azure_client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-02-01",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )

    def get_embedding(self, text: str, max_length: int = 8000) -> Optional[np.ndarray]:
        """
        Get embedding vector for text using Azure OpenAI

        Args:
            text: Text to embed
            max_length: Maximum text length to send (default: 8000)

        Returns:
            numpy array of embedding vector, or None if failed
        """
        try:
            # Truncate text to max_length
            truncated_text = text[:max_length]

            # Use Azure OpenAI embeddings API
            response = self.azure_client.embeddings.create(
                model=self.embedding_model,
                input=truncated_text
            )

            if response.data and len(response.data) > 0:
                embedding = response.data[0].embedding
                if embedding:
                    return np.array(embedding)

            print(f"  Warning: Failed to get embedding")
            return None

        except Exception as e:
            print(f"  Warning: Azure OpenAI connection error: {e}")
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

       Args:
            articles: List of Article objects

        Returns:
            List of articles with embeddings (filters out failed embeddings)
        """
        embedded_articles = []

        for i, article in enumerate(articles):
            embedding = self.embed_article(article)
            if embedding is not None:
                embedded_articles.append(article)
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
        threshold: float = 0.85,
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
        similarity_threshold: float = 0.85
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
