#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Embedding-based research paper clustering.

Uses Azure OpenAI embeddings + agglomerative clustering to group
research papers by semantic similarity, then ranks clusters and
selects a single representative article per cluster via LLM.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from typing import List, Optional

import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_distances

from copilot import Copilot
from datamodel import Article, Group


class ResearchClusterer:
    """Cluster research papers using vector embeddings.

    Pipeline:
      1. Embed articles via Azure OpenAI (batches of 20)
      2. Agglomerative clustering with cosine distance
      3. Rank clusters by importance via LLM
      4. Select one representative article per cluster via LLM
    """

    def __init__(
        self,
        llm: Optional[Copilot] = None,
        distance_threshold: float = 0.15,
        embed_batch_size: int = 20,
    ):
        self.llm = llm or Copilot()
        self.distance_threshold = distance_threshold
        self.embed_batch_size = embed_batch_size

    def _article_text(self, article: Article) -> str:
        """Build the text representation used for embedding."""
        title = (article.title or "").strip()
        summary = (article.summary or "").strip()[:500]
        return f"{title}. {summary}" if summary else title

    def embed_and_cluster(self, articles: List[Article]) -> List[Group]:
        """Embed articles and cluster them by cosine similarity.

        Returns a list of Group objects, largest cluster first.
        Each article's ``vector`` attribute is populated as a side-effect.
        """
        if not articles:
            return []

        # 1. Embed
        texts = [self._article_text(a) for a in articles]
        vectors = self.llm.embed(texts, batch_size=self.embed_batch_size)
        for article, vec in zip(articles, vectors):
            article.vector = vec

        X = np.array(vectors)

        # 2. Cluster (single-article input is a special case)
        if len(articles) == 1:
            return [Group(text=articles[0].title, articles=[articles[0]])]

        dist_matrix = cosine_distances(X)

        clustering = AgglomerativeClustering(
            n_clusters=None,
            metric="precomputed",
            linkage="average",
            distance_threshold=self.distance_threshold,
        )
        labels = clustering.fit_predict(dist_matrix)

        # 3. Group articles by label
        buckets: dict[int, List[Article]] = defaultdict(list)
        for article, label in zip(articles, labels):
            buckets[int(label)].append(article)

        groups = []
        for label, arts in buckets.items():
            # Name the cluster after its first article's title
            group = Group(text=arts[0].title, articles=arts)
            groups.append(group)

        groups.sort(key=lambda g: len(g.articles), reverse=True)
        return groups

    def rank_clusters(self, groups: List[Group], top_k: int) -> List[Group]:
        """Rank clusters by importance/impact using the LLM.

        Returns the top_k most important clusters in ranked order.
        """
        if not groups or len(groups) <= top_k:
            return groups

        lines = []
        for i, g in enumerate(groups):
            titles = [a.title for a in (g.articles or [])[:3] if a.title]
            rep_str = "; ".join(titles)[:250]
            lines.append(f"[{i}] ({len(g.articles)} papers) {rep_str}")

        items = "\n".join(lines)

        prompt = f"""You are ranking clusters of research papers by importance and impact.

Select the TOP {top_k} most important clusters from the list below.
Consider: novelty, potential impact, breadth of interest, and practical relevance.

Clusters:
{items}

Respond with ONLY a JSON array of the {top_k} cluster indices (e.g., [2, 0, 5, 1, 3]).
No explanation, just the JSON array."""

        response = self.llm.generate(prompt)

        try:
            match = re.search(r"\[[\d,\s]+\]", response)
            if match:
                selected = json.loads(match.group())
                return [groups[i] for i in selected if i < len(groups)][:top_k]
        except Exception as e:
            print(f"ResearchClusterer.rank_clusters parse error: {e}")

        return groups[:top_k]

    def select_representatives(self, groups: List[Group]) -> List[Article]:
        """Select a single representative article from each cluster.

        For single-article clusters, returns the article directly.
        For multi-article clusters, asks the LLM to pick the best one.
        """
        representatives: List[Article] = []

        for group in groups:
            if not group.articles:
                continue
            if len(group.articles) == 1:
                representatives.append(group.articles[0])
                continue

            # Ask LLM to pick the most representative/impactful article
            lines = []
            for i, a in enumerate(group.articles):
                summary = (a.summary or "")[:200]
                lines.append(f"[{i}] {a.title}\n    {summary}")

            items = "\n".join(lines)

            prompt = f"""From these {len(group.articles)} related research papers, select the ONE most important and representative paper.

Papers:
{items}

Respond with ONLY the single index number (e.g., 3). No explanation."""

            response = self.llm.generate(prompt)

            try:
                match = re.search(r"\d+", response)
                if match:
                    idx = int(match.group())
                    if idx < len(group.articles):
                        representatives.append(group.articles[idx])
                        continue
            except Exception as e:
                print(f"ResearchClusterer.select_representatives parse error: {e}")

            # Fallback: pick first article
            representatives.append(group.articles[0])

        return representatives

    def process(self, articles: List[Article], max_papers: int = 10) -> List[Article]:
        """Full pipeline: embed → cluster → rank → select representatives.

        Args:
            articles: Research papers to process.
            max_papers: Maximum number of representative papers to return.

        Returns:
            List of representative articles, one per top cluster.
        """
        if not articles:
            return []

        if len(articles) <= max_papers:
            return articles

        print(f"ResearchClusterer: embedding {len(articles)} papers...")
        groups = self.embed_and_cluster(articles)
        print(f"ResearchClusterer: found {len(groups)} clusters")

        groups = self.rank_clusters(groups, top_k=max_papers)
        print(f"ResearchClusterer: ranked to top {len(groups)} clusters")

        representatives = self.select_representatives(groups)
        print(f"ResearchClusterer: selected {len(representatives)} representative papers")

        return representatives[:max_papers]
