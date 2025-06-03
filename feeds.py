import feedparser
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from datamodel import Article
FEEDS = [
[1,"MF", "https://rss.metafilter.com/metafilter.rss", ["Culture"]],
[1,"LfaA", "https://heathercoxrichardson.substack.com/feed", ["US News", "History"]],
[1,"Quanta", "http://www.quantamagazine.org/feed/", ["Science"]],
[1,"Acoup", "https://acoup.blog/feed/", ["Culture", "Classics", "History", "Warfare"]],
[1,"NYT Sci.", "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml", ["Science"]],
[1,"MSR", "https://www.microsoft.com/en-us/research/feed/", ["Artificial Intelligence"]],
[1,"Wired Sci.", "https://www.wired.com/feed/category/science/latest/rss", ["Science"]],
[1,"Wired Ai.", "https://www.wired.com/feed/tag/ai/latest/rss", ["Artificial Intelligence"]],
[1,"Nature", "https://www.nature.com/nature.rss", ["Science"]],
[1,"Science news", "https://www.science.org/rss/news_current.xml", ["Science"]],
[1,"NYT US", "https://rss.nytimes.com/services/xml/rss/nyt/US.xml", ["US News"]],
[2,"hn-daily", "https://www.daemonology.net/hn-daily/index.rss", ["Technology"]],
[3,"TLDR AI", "https://tldr.tech/api/rss/ai", ["Artificial Intelligence"]],
[3,"TLDR", "https://tldr.tech/api/rss/tech", ["Technology"]],
[1,"Smithsonian", "https://www.smithsonianmag.com/rss/smithsonianmag/", ["Science"]],
[1,"The Atlantic", "https://www.theatlantic.com/feed/all/", ["US News"]],
[1,"Ars Technica", "https://feeds.arstechnica.com/arstechnica/index", ["Technology"]],
[1,"NYT Space", "https://rss.nytimes.com/services/xml/rss/nyt/Space.xml", ["Space"]],
[1,"NYT World", "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", ["World News"]],
[3,"TLDR Data", "https://tldr.tech/api/rss/data", ["Technology"]],
[1,"Vox", "https://www.vox.com/rss/index.xml", ["US News", "Politics"]],
[1,"Longmont Leader", "https://www.longmontleader.com/rss/",["Local News", "Colorado"]]
]

class Feeds:
    @staticmethod
    def fetch_articles(feeds):
        # Get current UTC time as struct_time
        now_struct = time.gmtime()
        # 24 hours ago as struct_time
        cutoff_struct = time.gmtime(time.mktime(now_struct) - 86400)
        articles = []
        for tt, ss, xx, kk in feeds:
            feed = feedparser.parse(xx)
            source = ss
            for entry in feed.entries:
                if ("published_parsed" in entry and entry.published_parsed < cutoff_struct) or ("updated_parsed" in entry and entry.updated_parsed < cutoff_struct):
                    continue
                summ = BeautifulSoup(entry.get("summary", ""), "html.parser").get_text(separator=" ", strip=True)
                published = datetime.now().isoformat()
                if hasattr(entry, "published"):
                    published = entry.published

                if tt == 1:  # Standard RSS feed
                    if summ.strip() == "":
                        continue
                    title = entry.title.replace("<", "_").replace(">", "_")
                    article = Article(
                        title=title,
                        url=entry.link,
                        source=source,
                        summary=summ,
                        keywords=kk,  # Convert keywords to ORM objects
                        published_at=published
                    )
                    articles.append(article)
                    continue
                elif tt == 2:  # HackerNews
                    links = BeautifulSoup(entry.get("summary", ""), "html.parser").find_all("a")
                    links = [
                        Article(
                            title=aa.text.replace("<", "_").replace(">", "_"),
                            url=aa["href"],
                            source=ss,
                            summary="",
                            keywords=kk,  # Convert keywords to ORM objects
                            published_at=published
                        )
                        for aa in links if "comments" not in aa.text
                    ]
                    links = [xx for xx in links if "hacker news" not in xx.title.lower()]
                    articles.extend(links)
                    continue
                elif tt == 3:  # TLDR
                    link = entry.get("links")[0].get("href")
                    inner = BeautifulSoup(requests.get(link).text, "html.parser")
                    inner = inner.find_all("h3")
                    for ii in inner:
                        ii = ii.parent.parent
                        content = ii.text
                        if "(Sponsor)" in content:
                            continue
                        summ = content
                        if "minute read)" in content.lower():
                            summ = content.split("read)")[1]
                        b = ii.find("a")
                        if b is None:
                            print(ii)
                            continue
                        url = b["href"]
                        title = b.text.replace("<", "_").replace(">", "_")
                        article = Article(
                            title=title,
                            url=url,
                            source=ss,
                            summary=summ,
                            keywords=kk,  # Convert keywords to ORM objects
                            published_at=published
                        )
                        articles.append(article)
                    continue

        # Deduplicate articles by title
        deduped = []
        seen_titles = set()
        for xx in articles:
            if xx.title in seen_titles:
                continue
            seen_titles.add(xx.title)
            deduped.append(xx)
        return deduped
