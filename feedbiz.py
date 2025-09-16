import feeds
from typing import Sequence
def feedbiz(feed: str,whitelist=None, blacklist=None) -> Sequence[str]:
    """
    Fetches news feed and returns a list of news items.
    """

    feed_configs = {"news":["https://rss.nytimes.com/services/xml/rss/nyt/US.xml", "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "https://www.theatlantic.com/feed/all/", "https://heathercoxrichardson.substack.com/feed"],
                "culture":["https://rss.metafilter.com/metafilter.rss", "https://acoup.blog/feed/"],
                "ai":["https://www.microsoft.com/en-us/research/feed/", "https://www.nature.com/nature.rss", "https://tldr.tech/api/rss/ai"],
                "local":["https://www.longmontleader.com/rss/", "https://www.reddit.com/r/Longmont.rss"],
                    "research":["https://export.arxiv.org/rss/cs.DC+cs.SY+cs.PF+cs.AR"]}# old ones: "https://export.arxiv.org/rss/cs.Ai+cs.Lg+stat.ML"]}

    articles = feeds.Feeds.fetch_articles(feed_configs.get(feed, feed_configs["news"]), days=1)
    print(f"Fetched {len(articles)} articles")

    little_news = [
        {
            "title": article.title,
            "url": article.url,
            "summary": article.summary[:500] + ("..." if len(article.summary) > 500 else "")
        } for article in articles
    ]
    print("little_news:",feed, len(little_news))
    little_news = [f"- [{item['title']}]({item['url']})\n\t - {item['summary']}" for item in little_news if item['summary']]
    if whitelist:
        little_news = [xx for xx in little_news if any(word.lower() in xx.lower() for word in whitelist)]
    if blacklist:
        little_news = [xx for xx in little_news if not any(word.lower() in xx.lower() for word in blacklist)]
    print("little_news:",feed, len(little_news))

    return little_news
