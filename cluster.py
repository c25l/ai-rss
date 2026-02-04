#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Article clustering using an LLM (no embeddings).

Strategy: "topic-tag then group"
1) Batch articles and ask the LLM to assign each article a small set of topic tags.
2) Merge tags across batches (synonyms / near-duplicates).
3) Group articles by merged tag OR use Louvain community detection for refinement.

Optional Louvain refinement:
- Constructs a graph where articles are nodes and edges connect articles with shared tags
- Uses Louvain algorithm to detect communities based on tag overlap
- Results in more nuanced clustering that accounts for multi-tag relationships

This is designed to work with the Copilot CLI wrapper (see copilot.py).
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from datamodel import Article, Group
from copilot import Copilot

try:
    import networkx as nx
    from networkx.algorithms import community
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False


def _sanitize_json_blob(blob: str) -> str:
    """Best-effort cleanup for common LLM JSON breakage.

    The most common failure we see is literal newlines inside quoted strings.
    JSON forbids that, so we replace them with spaces while inside a string.
    """
    out = []
    in_str = False
    esc = False
    for ch in blob:
        if in_str:
            if esc:
                esc = False
                out.append(ch)
                continue
            if ch == "\\":
                esc = True
                out.append(ch)
                continue
            if ch == '"':
                in_str = False
                out.append(ch)
                continue
            if ch in "\r\n\t":
                out.append(" ")
                continue
            out.append(ch)
            continue

        if ch == '"':
            in_str = True
        out.append(ch)

    return "".join(out)


def _extract_json(text: str) -> Optional[object]:
    """Extract the first JSON object/array from model output."""
    # Prefer fenced blocks if present
    fence = re.search(r"```json\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        blob = fence.group(1)
        blob = _sanitize_json_blob(blob)
        try:
            return json.loads(blob)
        except Exception:
            pass

    # Fall back to first {...} or [...]
    match = re.search(r"(\{.*\}|\[.*\])", text, flags=re.DOTALL)
    if not match:
        return None

    blob = _sanitize_json_blob(match.group(1))
    try:
        return json.loads(blob)
    except Exception:
        return None


def _normalize_tag(tag: str) -> str:
    tag = (tag or "").strip().lower()
    tag = re.sub(r"\s+", " ", tag)
    tag = tag.replace("/", " ")
    tag = re.sub(r"\s+", " ", tag).strip()
    return tag[:120] or "misc"


def _safe_slug(tag: str) -> str:
    tag = _normalize_tag(tag)
    tag = re.sub(r"[^a-z0-9\-\s]", "", tag)
    tag = re.sub(r"\s+", "-", tag).strip("-")
    return tag[:80] or "misc"


class ArticleClusterer:
    """Cluster articles by LLM-assigned topic tags.

    Optionally performs a macro-merge pass to consolidate many small topic clusters
    into a smaller set of higher-level stories.
    """

    def __init__(self, llm: Optional[Copilot] = None, macro_target: int = 10, use_louvain: bool = False):
        self.llm = llm or Copilot()
        self.macro_target = macro_target
        self.use_louvain = use_louvain and HAS_NETWORKX

    def embed_article(self, article: Article):  # kept for API compatibility
        return None

    def embed_articles(self, articles: List[Article]) -> List[Article]:  # compatibility
        return articles

    def _format_article_for_tagging(self, idx: int, article: Article) -> str:
        title = (article.title or "").strip()
        summary = (article.summary or "").strip()
        source = (article.source or "").strip()
        url = (article.url or "").strip()
        # Keep this compact to reduce tokens, but include enough disambiguation.
        return (
            f"[{idx}] Title: {title}\n"
            f"Source: {source}\n"
            f"URL: {url}\n"
            f"Summary: {summary[:400]}\n"
        )

    def _tag_batch(self, batch: List[Article], start_index: int) -> Dict[int, List[str]]:
        items = "\n".join(
            self._format_article_for_tagging(start_index + i, a) for i, a in enumerate(batch)
        )

        prompt = f"""You are clustering news articles into STORY TOPICS.

For each article, assign 1-3 short topic tags.
Tags must be:
- lowercase
- 2-5 words max
- not publisher names
- stable across similar stories (prefer canonical phrasing)
- MUST be valid JSON strings: do not include literal newlines; keep tags on one line

Return ONLY MINIFIED JSON of this form (no extra text):
{{"tags": {{"<index>": ["tag one", "tag two"]}}}}

Articles:
{items}
"""

        resp = self.llm.generate(prompt)
        data = _extract_json(resp)
        if not isinstance(data, dict) or "tags" not in data or not isinstance(data["tags"], dict):
            # Hard fallback: everything in one bucket
            return {start_index + i: ["misc"] for i in range(len(batch))}

        out: Dict[int, List[str]] = {}
        for k, v in data["tags"].items():
            try:
                idx = int(k)
            except Exception:
                continue
            if not isinstance(v, list):
                continue
            tags = [_normalize_tag(str(t)) for t in v if str(t).strip()]
            tags = [t for t in tags if t]
            out[idx] = tags[:3] if tags else ["misc"]

        # Ensure every article has tags
        for i in range(len(batch)):
            idx = start_index + i
            out.setdefault(idx, ["misc"])

        return out

    def _merge_tag_vocab(self, tags: List[str]) -> Dict[str, str]:
        """Ask the LLM to merge near-duplicate tags into canonical ones."""
        counts: Dict[str, int] = {}
        for t in tags:
            tt = (t or "").strip().lower()
            if not tt:
                continue
            counts[tt] = counts.get(tt, 0) + 1

        # Prefer tags that recur; cap to keep prompt bounded.
        uniq = sorted(counts.keys(), key=lambda t: (-counts[t], t))
        uniq = uniq[:250]
        if not uniq:
            return {}

        items = "\n".join(f"- {t} ({counts.get(t,1)}x)" for t in uniq)

        prompt = f"""You are normalizing topic tags for clustering.

Given this list of tags, merge synonyms / near-duplicates into a smaller set of canonical tags.
Rules:
- canonical tags should be lowercase, 2-5 words
- avoid overly broad tags like "politics" unless necessary
- keep at most ~40 canonical tags
- MUST be valid JSON strings: do not include literal newlines inside strings

Return ONLY MINIFIED JSON of this form (no extra text):
{{"map": {{"original tag": "canonical tag"}}}}

Tags:
{items}
"""

        resp = self.llm.generate(prompt)
        data = _extract_json(resp)
        if not isinstance(data, dict) or "map" not in data or not isinstance(data["map"], dict):
            return {t: t for t in uniq}

        mapping: Dict[str, str] = {}
        for k, v in data["map"].items():
            kk = _normalize_tag(str(k))
            vv = _normalize_tag(str(v)) if str(v).strip() else kk
            mapping[kk] = vv

        # Fill any missing
        for t in uniq:
            mapping.setdefault(t, t)

        return mapping

    def _macro_merge_clusters(self, groups: List[Group]) -> List[Group]:
        """Merge many small groups into ~macro_target higher-level stories."""
        if not groups:
            return []
        if len(groups) <= self.macro_target:
            return groups

        # Summarize each group with a few representative headlines.
        lines = []
        for i, g in enumerate(groups):
            reps = [a.title for a in (g.articles or [])[:3] if a.title]
            rep_str = "; ".join(reps)[:220]
            lines.append(f"[{i}] {g.text} :: {len(g.articles)} articles :: {rep_str}")

        items = "\n".join(lines[:120])  # cap for token safety

        prompt = f"""You are merging news STORY CLUSTERS into higher-level MACRO STORIES.

Goal: merge these clusters into about {self.macro_target} macro stories.
Rules:
- Each input cluster must map to exactly one macro story.
- Macro story titles should be short, specific, and stable (lowercase, 2-6 words).
- Avoid generic buckets like "world news".
- Return ONLY MINIFIED JSON, no extra text.

JSON schema:
{{"map": {{"<cluster_index>": "<macro_title>"}}}}

Clusters:
{items}
"""

        resp = self.llm.generate(prompt)
        data = _extract_json(resp)
        if not isinstance(data, dict) or "map" not in data or not isinstance(data["map"], dict):
            return groups

        mapping: Dict[int, str] = {}
        for k, v in data["map"].items():
            try:
                idx = int(str(k).strip())
            except Exception:
                continue
            title = _normalize_tag(str(v))
            if title:
                mapping[idx] = title

        merged: Dict[str, List[Article]] = defaultdict(list)
        for i, g in enumerate(groups):
            macro = mapping.get(i, _normalize_tag(g.text))
            merged[macro].extend(g.articles)

        out = [Group(text=title, articles=arts) for title, arts in merged.items()]
        out.sort(key=lambda g: len(g.articles), reverse=True)
        return out

    def _louvain_refine_clusters(
        self,
        articles: List[Article],
        tag_by_index: Dict[int, List[str]],
        mapping: Dict[str, str]
    ) -> List[Group]:
        """Use Louvain community detection to refine clusters based on tag overlap.
        
        Constructs a graph where:
        - Nodes are articles
        - Edges connect articles with shared canonical tags
        - Edge weights are proportional to number of shared tags
        
        Args:
            articles: List of articles to cluster
            tag_by_index: Mapping from article index to assigned tags
            mapping: Mapping from original tags to canonical tags
            
        Returns:
            List of Group objects with articles clustered by community detection
        """
        if not HAS_NETWORKX:
            # Fallback to simple tag-based grouping
            buckets: Dict[str, List[Article]] = defaultdict(list)
            for i, article in enumerate(articles):
                tags = tag_by_index.get(i, ["misc"])
                canon_tag = mapping.get(_normalize_tag(tags[0]), tags[0])
                buckets[canon_tag].append(article)
            groups = [Group(text=tag, articles=arts) for tag, arts in buckets.items()]
            groups.sort(key=lambda g: len(g.articles), reverse=True)
            return groups
        
        # Build graph
        G = nx.Graph()
        
        # Add all articles as nodes
        for i in range(len(articles)):
            G.add_node(i)
        
        # Get canonical tags for each article
        article_canon_tags: Dict[int, set] = {}
        for i, article in enumerate(articles):
            tags = tag_by_index.get(i, ["misc"])
            canon_tags = set()
            for t in tags:
                tt = _normalize_tag(t)
                ct = mapping.get(tt, tt)
                canon_tags.add(ct)
            article_canon_tags[i] = canon_tags
        
        # Add edges between articles with shared tags
        for i in range(len(articles)):
            for j in range(i + 1, len(articles)):
                tags_i = article_canon_tags.get(i, set())
                tags_j = article_canon_tags.get(j, set())
                
                # Calculate overlap
                shared = tags_i & tags_j
                if shared:
                    # Weight by number of shared tags
                    weight = len(shared)
                    G.add_edge(i, j, weight=weight)
        
        # Run Louvain community detection
        communities = community.louvain_communities(G, weight='weight', resolution=1.0)
        
        # Build groups from communities
        groups = []
        for comm in communities:
            if not comm:
                continue
                
            # Get articles in this community
            comm_articles = [articles[i] for i in comm]
            
            # Determine best representative tag for the community
            # Count tag frequencies across all articles in community
            tag_counts: Dict[str, int] = defaultdict(int)
            for i in comm:
                for tag in article_canon_tags.get(i, set()):
                    tag_counts[tag] += 1
            
            # Use most common tag as group name
            if tag_counts:
                best_tag = max(tag_counts.items(), key=lambda x: (x[1], x[0]))[0]
            else:
                best_tag = "misc"
            
            groups.append(Group(text=best_tag, articles=comm_articles))
        
        # Sort by size
        groups.sort(key=lambda g: len(g.articles), reverse=True)
        return groups

    def find_similar_articles(
        self,
        article: Article,
        candidates: List[Article],
        threshold: float = 0.0,
        top_k: int = 10,
    ) -> List[Tuple[Article, float]]:
        """Not supported for LLM clustering; kept for compatibility."""
        return []

    def cluster_articles_threshold(
        self,
        articles: List[Article],
        similarity_threshold: float = 0.0,
    ) -> List[Group]:
        """Cluster using LLM topic tags; similarity_threshold is ignored."""

        if not articles:
            return []

        # 1) Tag in batches
        batch_size = 20
        tag_by_index: Dict[int, List[str]] = {}
        for start in range(0, len(articles), batch_size):
            batch = articles[start : start + batch_size]
            tag_by_index.update(self._tag_batch(batch, start))

        # 2) Merge tag vocab
        all_tags = [t for tags in tag_by_index.values() for t in tags]
        mapping = self._merge_tag_vocab(all_tags)

        # 3) Group articles
        if self.use_louvain:
            # Use Louvain community detection for grouping
            groups = self._louvain_refine_clusters(articles, tag_by_index, mapping)
        else:
            # Use simple tag-based grouping (original approach)
            # Count canonical tag frequencies across all tags
            canon_counts: Dict[str, int] = {}
            for t in all_tags:
                tt = _normalize_tag(t)
                ct = mapping.get(tt, tt)
                canon_counts[ct] = canon_counts.get(ct, 0) + 1

            # Group by canonical tag chosen by global frequency (not per-article specificity)
            buckets: Dict[str, List[Article]] = defaultdict(list)
            for i, article in enumerate(articles):
                tags = tag_by_index.get(i, ["misc"])
                canon_tags = []
                for t in tags:
                    tt = _normalize_tag(t)
                    canon_tags.append(mapping.get(tt, tt))

                # Pick the most common canonical tag for this article; tie-break by earliest
                best = None
                best_score = -1
                for ct in canon_tags:
                    score = canon_counts.get(ct, 0)
                    if score > best_score:
                        best = ct
                        best_score = score
                buckets[best or "misc"].append(article)

            # If we collapsed too much, re-split using the 2nd tag when available.
            # (Prevents a single vague canonical tag from absorbing everything.)
            if buckets and (max(len(v) for v in buckets.values()) / len(articles)) > 0.35:
                refined: Dict[str, List[Article]] = defaultdict(list)
                for i, article in enumerate(articles):
                    tags = tag_by_index.get(i, ["misc"])
                    canon_tags = []
                    for t in tags:
                        tt = _normalize_tag(t)
                        canon_tags.append(mapping.get(tt, tt))

                    canon_primary = canon_tags[0] if canon_tags else "misc"
                    canon_secondary = canon_tags[1] if len(canon_tags) > 1 else ""

                    key = canon_primary
                    if canon_secondary and canon_secondary != canon_primary:
                        key = f"{canon_primary} / {canon_secondary}"
                    refined[key].append(article)
                buckets = refined

            # Build Groups, largest first
            groups = [Group(text=tag, articles=arts) for tag, arts in buckets.items()]
            groups.sort(key=lambda g: len(g.articles), reverse=True)

        # 4) Macro-merge pass (optional, skip if using Louvain which already does refinement)
        if not self.use_louvain:
            groups = self._macro_merge_clusters(groups)
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
