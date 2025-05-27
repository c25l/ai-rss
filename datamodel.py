from datetime import datetime
import uuid

class Article:
    def __init__(self, id=None, title=None, url=None, summary=None, source=None, published_at=None, vector=None, hashed_summary=None, claims=None, keywords=None, cluster=None, age=None):
        self.id = id
        self.title = title
        self.url = url
        self.summary = summary
        self.source = source
        self.published_at = published_at
        self.section="Other"
        self.vector = vector
        self.hashed_summary = hashed_summary
        self.claims = claims if claims is not None else []
        self.keywords = keywords if keywords is not None else []
        self.cluster = cluster
        self.age=age

    def out(self,d=0):
        return f"- [{self.title}]({self .url})"

    def json(self):
        return {
            'id': self.id,
            'title': self.title,
            'url': self.url,
            'summary': self.summary,
            'source': self.source,
            'published_at': self.published_at,
            'keywords': self.keywords,
            'hashed_summary': self.hashed_summary
        }

class Group:
    def __init__(self, id=None, text=None, created_at=None, parent_id=None, articles=None):
        self.id = id
        self.text = text
        self.created_at = created_at
        self.parent_id = parent_id
        self.articles = articles if articles is not None else []


    def out(self,d=1):
        """Generate a string representation of the group with its title and associated articles."""
        article_list = "\n".join([xx.out(d+1) for xx in self.articles])
        hashes = "".join(["#" for _ in range(d)])
        return f"{hashes} {self.text}\n{article_list}"


