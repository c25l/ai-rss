import feeds
import datetime
from bs4 import BeautifulSoup
import requests
from datamodel import Article
from cluster import ArticleClusterer
from copilot import Copilot

def _load_news_sources():
    """Load RSS news sources from preferences.yaml, falling back to defaults."""
    defaults = [
        "https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://www.theatlantic.com/feed/all/",
        "https://heathercoxrichardson.substack.com/feed",
        "https://rss.metafilter.com/metafilter.rss",
        "https://acoup.blog/feed/",
        "https://www.longmontleader.com/rss/",
        "https://www.nature.com/nature.rss",
        "https://www.reddit.com/r/Longmont.rss",
    ]
    try:
        import yaml, os
        pref_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'preferences.yaml')
        if os.path.exists(pref_file):
            with open(pref_file, 'r') as f:
                prefs = yaml.safe_load(f) or {}
            configured = prefs.get('sources')
            if configured:
                # Extract RSS URLs that look like news sources (not tech/research)
                return [s['url'] for s in configured if s.get('type') == 'rss' and s.get('url')]
    except Exception as e:
        print(f"Warning: could not load sources from preferences.yaml: {e}")
    return defaults

class News:
    def __init__(self, use_clustering=True):
        self.use_clustering = use_clustering
        self.clusterer = ArticleClusterer() if use_clustering else None
        self.claude = Copilot()

    def rank_clusters(self, clusters, category_name, top_k=5):
        """
        Rank clusters by importance using Claude.

        Args:
            clusters: List of Group objects to rank
            category_name: Name of category (for prompt context): 'continuing', 'new', or 'dormant'
            top_k: Number of top clusters to return

        Returns:
            List of top_k ranked Group objects
        """
        if len(clusters) <= top_k:
            return clusters

        # Format clusters for ranking
        cluster_descriptions = []
        for i, group in enumerate(clusters):
            rep_title = group.articles[0].title if group.articles else getattr(group, 'representative_title', 'No title')
            article_count = len(group.articles)
            total_count = getattr(group, 'total_count', article_count)

            if category_name == 'continuing':
                desc = f"[{i}] {rep_title} ({article_count} new articles today, {total_count} total)"
            elif category_name == 'dormant':
                desc = f"[{i}] {rep_title} ({total_count} articles from previous days, none today)"
            else:  # new
                desc = f"[{i}] {rep_title} ({article_count} articles)"

            cluster_descriptions.append(desc)

        # Create prompt template
        items_str = '\n'.join(cluster_descriptions)

        if category_name == 'continuing':
            context = "CONTINUING STORIES - ongoing coverage from previous days"
        elif category_name == 'new':
            context = "NEW STORIES - appearing for the first time today"
        else:  # dormant
            context = "DORMANT STORIES - had coverage before but none today"

        prompt_template = f"""Rank these {category_name.upper()} news story clusters by importance and significance.
Focus on: major news impact, public interest, and relevance. Please suppress articles like "x killed by y in z" unless the number killed is over 1000, the location is colorado, or the people are famous. 

{context}

{{items}}

Respond with ONLY a JSON array of the top {{top_k}} indices (e.g., [3, 7, 12, 1, 18]).
No explanation, just the JSON array."""

        # Rank using Claude
        selected_indices = self.claude.rank_items(
            items=items_str,
            prompt_template=prompt_template,
            top_k=top_k
        )

        # Return ranked clusters
        return [clusters[i] for i in selected_indices if i < len(clusters)]

    def pull_data(self, return_clustered=None, corpus_days=3, show_days=1, return_structured=False):
        """
        Pull news articles from various sources

        Args:
            return_clustered: If True, returns clustered output. If False, returns flat list.
                            If None, uses self.use_clustering default.
            corpus_days: Number of days to fetch articles from (default: 3)
            show_days: Number of days to consider as "today" for categorization (default: 1)
            return_structured: If True, returns dict with Group objects. If False, returns formatted string.

        Returns:
            If return_structured=True: dict with keys 'new', 'continuing', 'dormant' containing Group objects
            If return_structured=False: String formatted output of articles or article clusters
        """
        if return_clustered is None:
            return_clustered = self.use_clustering

        articles = []
        content_sections = []
        sources = _load_news_sources()
        for src in sources:
            articles.extend([xx for xx in feeds.Feeds.get_articles(src, days=corpus_days)])
        
        # If clustering is enabled, cluster the articles
        if return_clustered and self.clusterer:
            print(f"Preparing {len(articles)} articles for clustering...")
            embedded_articles = self.clusterer.embed_articles(articles)

            print("Clustering articles...")
            groups = self.clusterer.cluster_articles_threshold(embedded_articles)
            print(f"Created {len(groups)} article clusters")

            # Categorize groups by date (new/continuing/dormant)
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=show_days)

            def parse_article_date(article):
                """Parse article date, return None if unparseable. Returns naive datetime."""
                try:
                    if article.published_at:
                        if isinstance(article.published_at, str):
                            try:
                                dt = datetime.datetime.fromisoformat(article.published_at.replace('Z', '+00:00'))
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

            new_stories = []  # Articles from today only (any count)
            continuing_stories = []  # Mix of old and new
            dormant_stories = []  # Had 2+ articles before but none today

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

                # Categorize based on strict rules
                if len(older_articles) == 0 and len(today_articles) > 0:
                    # NEW: only today's articles (any count)
                    group.articles = today_articles
                    group.total_count = len(today_articles)
                    group.today_count = len(today_articles)
                    new_stories.append(group)
                elif len(today_articles) > 0 and len(older_articles) > 0:
                    # CONTINUING: has history + today (only keep today's articles)
                    group.articles = today_articles
                    group.total_count = len(today_articles) + len(older_articles)
                    group.today_count = len(today_articles)
                    continuing_stories.append(group)
                elif len(today_articles) == 0 and len(older_articles) >= 2:
                    # DORMANT: was a story (2+ articles), now gone
                    # We don't need to keep the old articles
                    group.articles = []
                    group.total_count = len(older_articles)
                    group.today_count = 0
                    group.representative_title = older_articles[0].title if older_articles else ""
                    dormant_stories.append(group)
                # else: drop it (only 1 old article, not enough to be a story)

            # Sort continuing stories by (total_count × today_count)
            continuing_stories.sort(key=lambda g: g.total_count * g.today_count, reverse=True)

            # Return structured data if requested
            if return_structured:
                return {
                    'new': new_stories,
                    'continuing': continuing_stories,
                    'dormant': dormant_stories
                }

            # Format output by category
            output_parts = []

            # Continuing Stories
            if continuing_stories:
                output_parts.append("## CONTINUING STORIES (ongoing coverage from previous days)\n")
                for i, group in enumerate(continuing_stories, 1):
                    cluster_title = group.articles[0].title if group.articles else "Empty cluster"
                    output_parts.append(f"### Continuing Story {i}: {len(group.articles)} new articles today (total: {group.total_count} articles across {corpus_days} days)")
                    output_parts.append(f"**Representative headline:** {cluster_title}\n")
                    for article in group.articles:
                        output_parts.append(article.out_rich())
                    output_parts.append("")  # Blank line between clusters

            # New Stories
            if new_stories:
                output_parts.append("## NEW STORIES (appearing for the first time today)\n")
                for i, group in enumerate(new_stories, 1):
                    cluster_title = group.articles[0].title if group.articles else "Empty cluster"
                    output_parts.append(f"### New Story {i}: {len(group.articles)} articles")
                    output_parts.append(f"**Representative headline:** {cluster_title}\n")
                    for article in group.articles:
                        output_parts.append(article.out_rich())
                    output_parts.append("")  # Blank line between clusters

            # Dormant Stories
            if dormant_stories:
                output_parts.append("## DORMANT STORIES (had coverage before but none today - stories that have disappeared from the news)\n")
                for i, group in enumerate(dormant_stories, 1):
                    cluster_title = getattr(group, 'representative_title', '') or (group.articles[0].title if group.articles else "Empty cluster")
                    output_parts.append(f"### Dormant Story {i}: {group.total_count} articles from previous days")
                    output_parts.append(f"**Representative headline:** {cluster_title}\n")

            return "\n".join(output_parts)
        else:
            # Return flat list as before
            return "\n\n".join([xx.out_rich() for xx in articles])     
