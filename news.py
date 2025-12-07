import feeds
import datetime
from bs4 import BeautifulSoup
import requests
from datamodel import Article
from cluster import ArticleClusterer

class News:
    def __init__(self, use_clustering=True):
        self.use_clustering = use_clustering
        self.clusterer = ArticleClusterer() if use_clustering else None

    def pull_data(self, return_clustered=None, corpus_days=3, show_days=1):
        """
        Pull news articles from various sources

        Args:
            return_clustered: If True, returns clustered output. If False, returns flat list.
                            If None, uses self.use_clustering default.
            corpus_days: Number of days to fetch articles from (default: 3)
            show_days: Number of days to consider as "today" for categorization (default: 1)

        Returns:
            String formatted output of articles or article clusters, categorized by new/continuing/dormant
        """
        if return_clustered is None:
            return_clustered = self.use_clustering

        articles = []
        content_sections = []
        sources = ["https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
                   "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
                   "https://www.theatlantic.com/feed/all/",
                   "https://heathercoxrichardson.substack.com/feed",
                   "https://rss.metafilter.com/metafilter.rss",
                     "https://acoup.blog/feed/",
                     "https://www.microsoft.com/en-us/research/feed/",
                       "https://www.nature.com/nature.rss",
                       "https://www.daemonology.net/hn-daily/index.rss",
                       "https://blog.google/technology/ai/rss/",
                       "https://www.longmontleader.com/rss/",
                         "https://www.reddit.com/r/Longmont.rss"]
        for src in sources:
            articles.extend([xx for xx in feeds.Feeds.get_articles(src, days=corpus_days)])
        now=datetime.datetime.now()
        text=BeautifulSoup(requests.get(f"https://tldr.tech/ai/{now:%Y-%m-%d}").text, "html.parser")
        text=text.find_all("article")
        articles.extend([Article(title=str(xx),summary="", published_at=now,source="tldr.tech/ai") for xx in text])
        text=BeautifulSoup(requests.get(f"https://www.daemonology.net/hn-daily/{now-datetime.timedelta(days=1):%Y-%m-%d}.html").text, "html.parser")
        text= text.find_all("span", class_="storylink")
        articles.extend([Article(title=str(xx), published_at=now, source="hacker news daily",summary="")  for xx in text])
        self.articles=articles

        # If clustering is enabled, cluster the articles
        if return_clustered and self.clusterer:
            print(f"Generating embeddings for {len(articles)} articles...")
            embedded_articles = self.clusterer.embed_articles(articles)
            print(f"Successfully embedded {len(embedded_articles)} articles")

            print("Clustering articles...")
            groups = self.clusterer.cluster_articles_threshold(
                embedded_articles,
                similarity_threshold=0.75
            )
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
                    # Continuing story (only show today's articles)
                    group.articles = today_articles
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

            # Single Articles
            if single_articles:
                output_parts.append("## SINGLE ARTICLES (standalone articles not part of a larger story)\n")
                for i, group in enumerate(single_articles, 1):
                    article = group.articles[0]
                    output_parts.append(f"### Single Article {i}")
                    output_parts.append(article.out_rich())
                    output_parts.append("")

            # Dormant Stories
            if dormant_stories:
                output_parts.append("## DORMANT STORIES (had coverage before but none today - stories that have disappeared from the news)\n")
                for i, group in enumerate(dormant_stories, 1):
                    cluster_title = group.articles[0].title if group.articles else "Empty cluster"
                    output_parts.append(f"### Dormant Story {i}: {group.total_count} articles from previous days")
                    output_parts.append(f"**Representative headline:** {cluster_title}\n")

            return "\n".join(output_parts)
        else:
            # Return flat list as before
            return "\n\n".join([xx.out_rich() for xx in articles])     
