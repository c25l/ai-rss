#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fetch RSS articles and cluster them using embeddings
"""
import argparse
import json
import sys
from datetime import datetime, timedelta
from cluster import ArticleClusterer
from feeds import Feeds
from datamodel import Article


def main():
    parser = argparse.ArgumentParser(description="Fetch and cluster RSS articles")
    parser.add_argument("--method", choices=["dbscan", "threshold"], default="threshold",
                        help="Clustering method (default: threshold)")
    parser.add_argument("--eps", type=float, default=0.3,
                        help="DBSCAN eps parameter - max distance (default: 0.3)")
    parser.add_argument("--min-samples", type=int, default=2,
                        help="DBSCAN min_samples parameter (default: 2)")
    parser.add_argument("--threshold", type=float, default=0.575,
                        help="Threshold clustering similarity (default: 0.575)")
    parser.add_argument("--feed-type", default="main", choices=["research", "main"],
                        help="Feed type to fetch (default: main)")
    parser.add_argument("--summarize", action="store_true",
                        help="Generate LLM summaries for each cluster")
    parser.add_argument("--input", type=str,
                        help="JSON file containing articles (if not provided, fetches from RSS)")

    args = parser.parse_args()



    # Get articles - either from input file or RSS feeds
    if args.input:
        # Load articles from JSON file
        with open(args.input, 'r') as f:
            articles_data = json.load(f)

        articles = []
        for article_dict in articles_data:
            article = Article(
                title=article_dict.get('title'),
                url=article_dict.get('url'),
                summary=article_dict.get('summary', ''),
                source=article_dict.get('source', ''),
                published_at=article_dict.get('published_at')
            )
            articles.append(article)
    else:
        # Define feed configurations
        feed_configs = {
            "research": ["https://export.arxiv.org/rss/cs.DC+cs.SY+cs.PF+cs.AR"],
            "main": [
                "https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
                "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
                "https://www.theatlantic.com/feed/all/",
                "https://heathercoxrichardson.substack.com/feed",
                "https://rss.metafilter.com/metafilter.rss",
                "https://acoup.blog/feed/",
                "https://www.microsoft.com/en-us/research/feed/",
                "https://www.nature.com/nature.rss",
                "https://blog.google/technology/ai/rss/",
                "https://www.longmontleader.com/rss/",
                "https://www.reddit.com/r/Longmont.rss"
            ]
        }
        corpus_days=3
        # Fetch articles (suppressing output)
        feeds = feed_configs.get(args.feed_type, feed_configs["main"])
        articles = Feeds.fetch_articles(feeds, days=corpus_days)
        return cluster(articles)
def cluster(articles):
    
    corpus_days=3
    show_days=1
    if not articles:
        return

    # Initialize clusterer and embed articles (suppressing output)
    clusterer = ArticleClusterer()
    embedded_articles = clusterer.embed_articles(articles)

    if not embedded_articles:
        return

    # Cluster articles
    groups = clusterer.cluster_articles_threshold(
            embedded_articles,
            similarity_threshold=0.575
        )

    # Categorize groups by date
    cutoff_date = datetime.now() - timedelta(days=show_days)

    def parse_article_date(article):
        """Parse article date, return None if unparseable. Returns naive datetime."""
        try:
            if article.published_at:
                if isinstance(article.published_at, str):
                    try:
                        dt = datetime.fromisoformat(article.published_at.replace('Z', '+00:00'))
                    except:
                        from dateutil import parser
                        dt = parser.parse(article.published_at)
                else:
                    dt = article.published_at

                # Strip timezone info to make naive
                if dt.tzinfo is not None:
                    dt = dt.replace(tzinfo=None)
                return dt
        except:
            pass
        return None

    new_stories = []  # Only today's articles (2+ articles = story)
    continuing_stories = []  # Mix of old and new (2+ total = story)
    dormant_stories = []  # Had 2+ articles before but none today
    single_articles = []  # Single articles (not stories)

    for group in groups:
        today_articles = []
        older_articles = []

        for article in group.articles:
            article_date = parse_article_date(article)
            if article_date and article_date >= cutoff_date:
                today_articles.append(article)
            elif article_date:
                older_articles.append(article)
            else:
                # If no date, assume today
                today_articles.append(article)

        total_count = len(today_articles) + len(older_articles)

        # Skip empty groups
        if total_count == 0:
            continue

        if today_articles and not older_articles:
            # Only new articles
            group.articles = today_articles
            group.total_count = total_count
            group.today_count = len(today_articles)
            if total_count >= 2:
                new_stories.append(group)
            else:
                single_articles.append(group)
        elif today_articles and older_articles:
            # Continuing story (only count as story if 2+ total)
            group.articles = today_articles  # Only show today's
            group.total_count = total_count
            group.today_count = len(today_articles)
            if total_count >= 2:
                continuing_stories.append(group)
            else:
                single_articles.append(group)
        elif not today_articles and len(older_articles) >= 2:
            # Dormant: had 2+ articles before but none today
            group.articles = older_articles
            group.total_count = total_count
            group.today_count = 0
            dormant_stories.append(group)

    # Sort continuing stories by (total_count × today_count)
    continuing_stories.sort(key=lambda g: g.total_count * g.today_count, reverse=True)

    # Generate titles for all story clusters (2+ articles)
    all_stories = continuing_stories + new_stories + dormant_stories
    for group in all_stories:
        if len(group.articles) >= 2:
            # Generate better title using LLM
            generated_title = clusterer.generate_cluster_title(group)
            if generated_title:
                group.text = generated_title

    # Generate summaries only for groups with >1 article

    groups_to_summarize = [g for g in (new_stories + continuing_stories) if len(g.articles) > 1]
    if groups_to_summarize:
        clusterer.summarize_clusters(groups_to_summarize)

    # Build markdown output
    md_output = []
    md_output.append(f"# News Digest - {datetime.now().strftime('%Y-%m-%d')}\n")

    # Track reference links
    link_counter = 1
    reference_links = {}

    # Continuing Stories
    if continuing_stories:
        md_output.append("## Continuing Stories\n")
        md_output.append(f"Major stories with ongoing coverage ({len(continuing_stories)} stories)\n\n")

        for group in continuing_stories:
            article_refs = []
            for article in group.articles:
                reference_links[link_counter] = article.url
                article_refs.append(f"[{link_counter}]")
                link_counter += 1

            md_output.append(f"**{group.text}** " + " ".join(article_refs) + "\n")
            md_output.append(f"*{group.today_count} new article(s) today (total: {group.total_count} articles across {corpus_days} days)*\n\n")

    # New Stories
    if new_stories:
        md_output.append("## New Stories Today\n")
        md_output.append(f"Stories that appeared for the first time today ({len(new_stories)} stories, 2+ articles each)\n\n")

        for group in new_stories:
            article_refs = []
            for article in group.articles:
                reference_links[link_counter] = article.url
                article_refs.append(f"[{link_counter}]")
                link_counter += 1

            md_output.append(f"**{group.text}** " + " ".join(article_refs) + "\n")
            md_output.append(f"*{len(group.articles)} article(s)*\n\n")

    # Single Articles
    if single_articles:
        md_output.append("## Single Articles Today\n")
        md_output.append(f"Individual articles not part of a larger story ({len(single_articles)} articles)\n")

        for group in single_articles:
            article = group.articles[0]
            reference_links[link_counter] = article.url
            md_output.append(f"- {article.title} [{link_counter}]\n\n")
            link_counter += 1
        md_output.append("\n")

    # Dormant Stories
    if dormant_stories:
        md_output.append("## Dormant Stories\n")
        md_output.append(f"Stories with coverage in previous days but none today ({len(dormant_stories)} stories)\n")

        for group in dormant_stories:
            md_output.append(f"- {group.text} ({group.total_count} articles, last seen yesterday)\n")
        md_output.append("\n")

    # Summary
    md_output.append("---\n\n")
    md_output.append("## Summary\n")
    md_output.append(f"- Total articles analyzed: {len(embedded_articles)}\n")
    md_output.append(f"- Continuing stories (2+ articles): {len(continuing_stories)}\n")
    md_output.append(f"- New stories today (2+ articles): {len(new_stories)}\n")
    md_output.append(f"- Dormant stories (2+ articles): {len(dormant_stories)}\n")
    md_output.append(f"- Single articles: {len(single_articles)}\n\n")

    # Add reference links at the end
    md_output.append("---\n\n")
    md_output.append("## References\n\n")
    for ref_num in sorted(reference_links.keys()):
        md_output.append(f"[{ref_num}]: {reference_links[ref_num]}\n")
    return "".join(md_output)
    # Output only markdown to stdout
    print("".join(md_output))


if __name__ == "__main__":
    main()
