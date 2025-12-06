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

    def pull_data(self, return_clustered=None):
        """
        Pull news articles from various sources

        Args:
            return_clustered: If True, returns clustered output. If False, returns flat list.
                            If None, uses self.use_clustering default.

        Returns:
            String formatted output of articles or article clusters
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
            articles.extend([xx for xx in feeds.Feeds.get_articles(src, days=3)])
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

            # Format output by cluster
            output_parts = []
            for i, group in enumerate(groups, 1):
                cluster_title = group.articles[0].title if group.articles else "Empty cluster"
                output_parts.append(f"### Cluster {i}: {len(group.articles)} articles")
                output_parts.append(f"**Representative headline:** {cluster_title}\n")
                for article in group.articles:
                    output_parts.append(article.out_rich())
                output_parts.append("")  # Blank line between clusters

            return "\n".join(output_parts)
        else:
            # Return flat list as before
            return "\n\n".join([xx.out_rich() for xx in articles])     
