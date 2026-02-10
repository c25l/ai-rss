import feedparser
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from datamodel import Article

class Feeds:
    @staticmethod
    def get_articles(feed_url, days=1, timeout=30):
        now_struct = time.gmtime()
        # 24 hours ago as struct_time
        cutoff_struct = time.gmtime(time.mktime(now_struct) - 86400*days)
        articles = []
        
        # Fetch the feed with timeout using requests, then parse with feedparser
        # This approach allows us to control the timeout for the network request
        try:
            # First fetch the feed with timeout using requests
            response = requests.get(
                feed_url, 
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
                    'Accept': 'application/rss+xml, application/xml, text/xml'
                }
            )
            response.raise_for_status()
            
            # Parse the response content with feedparser
            feed = feedparser.parse(response.content)
        except requests.exceptions.Timeout:
            print(f"Timeout fetching feed: {feed_url}")
            return []
        except requests.exceptions.RequestException as e:
            print(f"Error fetching feed {feed_url}: {e}")
            return []
        for entry in feed.entries:
            if ("published_parsed" in entry and entry.published_parsed < cutoff_struct) or ("updated_parsed" in entry and entry.updated_parsed < cutoff_struct):
                continue
            
            # Filter by ArXiv announce type - only process "new" papers
            announce_type = entry.get("arxiv_announce_type", "")
            if announce_type and announce_type != "new":
                continue  # Skip "replace" and "cross-list" entries
            
            summ = BeautifulSoup(entry.get("summary", ""), "html.parser").get_text(separator=" ", strip=True)
            if 'tldr' in feed_url:
                try:
                    summ = requests.get(entry.link, timeout=timeout).text
                    print(summ)
                except requests.exceptions.RequestException as e:
                    print(f"Error fetching tldr for {entry.link}: {e}")
                    # Keep the summary from BeautifulSoup parsing (assigned above)
            published = datetime.now().isoformat()
            if hasattr(entry, "published"):
                published = entry.published

            if summ.strip() == "":
                continue
            title = entry.title.replace("<", "_").replace(">", "_")
            article = Article(
                title=title,
                url=entry.link,
                source=feed_url,
                summary=summ,
                keywords=[],  # Convert keywords to ORM objects
                published_at=published
            )
            articles.append(article)
        return articles
    
    @staticmethod
    def fetch_articles(feeds, days=1):
        articles= [Feeds.get_articles(xx, days=days) for xx in feeds]
        
        # Deduplicate articles by title
        deduped = []
        seen_titles = set()
        for xx in articles:
            if xx.title in seen_titles:
                continue
            seen_titles.add(xx.title)
            deduped.append(xx)
        return deduped
