import feedparser
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from datamodel import Article


class Feeds:
    @staticmethod
    def fetch_articles(feeds, days=1):
        # Get current UTC time as struct_time
        now_struct = time.gmtime()
        # 24 hours ago as struct_time
        cutoff_struct = time.gmtime(time.mktime(now_struct) - 86400*days)
        articles = []
        for xx in feeds:
            feed = feedparser.parse(xx)
            for entry in feed.entries:
                if ("published_parsed" in entry and entry.published_parsed < cutoff_struct) or ("updated_parsed" in entry and entry.updated_parsed < cutoff_struct):
                    continue
                
                # Filter by ArXiv announce type - only process "new" papers
                announce_type = entry.get("arxiv_announce_type", "")
                if announce_type and announce_type != "new":
                    continue  # Skip "replace" and "cross-list" entries
                
                summ = BeautifulSoup(entry.get("summary", ""), "html.parser").get_text(separator=" ", strip=True)
                published = datetime.now().isoformat()
                if hasattr(entry, "published"):
                    published = entry.published

                if summ.strip() == "":
                    continue
                title = entry.title.replace("<", "_").replace(">", "_")
                article = Article(
                    title=title,
                    url=entry.link,
                    source=xx,
                    summary=summ,
                    keywords=[],  # Convert keywords to ORM objects
                    published_at=published
                )
                articles.append(article)

        # Deduplicate articles by title
        deduped = []
        seen_titles = set()
        for xx in articles:
            if xx.title in seen_titles:
                continue
            seen_titles.add(xx.title)
            deduped.append(xx)
        return deduped
