import feeds
import datetime
from bs4 import BeautifulSoup
import requests
from datamodel import Article
from claude import Claude

class TechNews:
    def __init__(self):
        self.claude = Claude()

    def rank_articles(self, articles, top_k=5):
        """
        Rank tech articles by importance using Claude.

        Args:
            articles: List of Article objects to rank
            top_k: Number of top articles to return

        Returns:
            List of top_k ranked Article objects
        """
        if len(articles) <= top_k:
            return articles

        # Format articles for ranking
        article_descriptions = []
        for i, article in enumerate(articles):
            desc = f"[{i}] {article.title}"
            article_descriptions.append(desc)

        # Create prompt template
        items_str = '\n'.join(article_descriptions)

        prompt_template = """Rank these tech articles by importance and significance.
Focus on: AI/ML developments, hardware/chips, datacenter tech, software releases, tech industry impact.

{items}

Respond with ONLY a JSON array of the top {top_k} indices (e.g., [3, 7, 12, 1, 18]).
No explanation, just the JSON array."""

        # Rank using Claude
        selected_indices = self.claude.rank_items(
            items=items_str,
            prompt_template=prompt_template,
            top_k=top_k
        )

        # Return ranked articles
        return [articles[i] for i in selected_indices if i < len(articles)]

    def pull_data(self, days=1, top_k=5, use_ranking=True):
        """
        Pull tech news articles from tech-focused sources

        Args:
            days: Number of days to fetch articles from (default: 1)
            top_k: Number of top articles to return (default: 5)
            use_ranking: If True, rank articles by importance. If False, return chronologically (default: True)

        Returns:
            String formatted output of tech articles
        """
        articles = []

        # Tech-focused RSS feeds
        tech_sources = [
            #"https://techcrunch.com/feed/",
            #"https://www.theverge.com/rss/index.xml",
            #"https://feeds.arstechnica.com/arstechnica/index",
            #"https://www.wired.com/feed/rss",
            #"https://www.reddit.com/r/technology/.rss",
            #"https://www.daemonology.net/hn-daily/index.rss",
            "https://www.microsoft.com/en-us/research/feed/",
            "https://blog.google/technology/ai/rss/",
        ]

        for src in tech_sources:
            articles.extend([xx for xx in feeds.Feeds.get_articles(src, days=days)])

        # Add tldr.tech AI newsletter
        now = datetime.datetime.now()
        try:
            text = BeautifulSoup(requests.get(f"https://tldr.tech/ai/{now:%Y-%m-%d}").text, "html.parser")
            text = text.find_all("article")
            print(len(text), "articles from tldrai")
            articles.extend([Article(title=str(xx), summary="", published_at=now, source="tldr.tech/ai") for xx in text])
        except:
            print("error for tldr.tech/ai")
            pass  # Skip if tldr.tech is unavailable

        try:
            text = BeautifulSoup(requests.get(f"https://tldr.tech/tech/{now:%Y-%m-%d}").text, "html.parser")
            text = text.find_all("article")
            print(len(text), "articles from tldr")
            articles.extend([Article(title=str(xx), summary="", published_at=now, source="tldr.tech") for xx in text])
        except:
            print("error for tldr.tech")
            pass  # Skip if tldr.tech is unavailable


        try:
            text = BeautifulSoup(requests.get(f"https://www.daemonology.net/hn-daily/{now-datetime.timedelta(days=1):%Y-%m-%d}.html").text, "html.parser")
            text = text.find_all("span", class_="storylink")
            print(len(text), "articles from hndaily")
            articles.extend([Article(title=str(xx), published_at=now, source="hacker news daily", summary="") for xx in text])
        except:
            print("error for hn-daily")
            pass

        self.articles = articles
        print(f"Found {len(articles)} tech articles")

        # Rank articles if requested
        if use_ranking and len(articles) > top_k:
            print(f"Ranking top {top_k} articles...")
            articles = self.rank_articles(articles, top_k=top_k)
        else:
            articles = articles[:top_k]

        # Format output
        output = []
        for art in articles:
            output.append(f"- **[{art.title}]({art.url})**")

        return "\n".join(output)
