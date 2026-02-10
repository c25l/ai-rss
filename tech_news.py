import feeds
import datetime
from bs4 import BeautifulSoup
import requests
from datamodel import Article
from copilot import Copilot

def _load_tech_sources():
    """Load tech source config from preferences.yaml, falling back to defaults."""
    default_rss = [
        "https://www.microsoft.com/en-us/research/feed/",
        "https://blog.google/technology/ai/rss/",
    ]
    default_tldr = True
    default_hn = True
    try:
        import yaml, os
        pref_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'preferences.yaml')
        if os.path.exists(pref_file):
            with open(pref_file, 'r') as f:
                prefs = yaml.safe_load(f) or {}
            configured = prefs.get('sources')
            if configured:
                rss = [s['url'] for s in configured
                       if s.get('type') == 'rss' and s.get('url')]
                tldr = any(s.get('type') == 'tldr' for s in configured)
                hn = any(s.get('type') == 'hn-daily' for s in configured)
                return rss, tldr, hn
    except Exception as e:
        print(f"Warning: could not load sources from preferences.yaml: {e}")
    return default_rss, default_tldr, default_hn

class TechNews:
    def __init__(self):
        self.llm = Copilot()

    def rank_articles(self, articles, top_k=5):
        """
        Rank tech articles by importance using the LLM.

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

        # Rank using LLM
        selected_indices = self.llm.rank_items(
            items=items_str,
            prompt_template=prompt_template,
            top_k=top_k,
            batch_size=50
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

        # Load sources from preferences
        tech_rss, use_tldr, use_hn = _load_tech_sources()

        for src in tech_rss:
            articles.extend([xx for xx in feeds.Feeds.get_articles(src, days=days)])

        # Add tldr.tech AI newsletter
        now = datetime.datetime.now()
        if use_tldr:
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


        if use_hn:
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
