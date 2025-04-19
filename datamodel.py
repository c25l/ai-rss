
class Article(object):
	keys = ["id","title", "url", "summary", "source",  "published", "vector","keywords"]
	json_keys = ["title", "url", "summary", "source",  "published","keywords"]
	unique = ["url"]
	table = ["articles"]
	def __init__(self, title, url, source, summary="", keywords=[], published_at=None, vector=[],id=None,hashed_summary=None):
		self.title = title.encode('ascii', 'ignore').decode('ascii')
		self.url = url
		self.summary = summary.encode('ascii', 'ignore').decode('ascii')
		self.source = source
		self.published_at = published_at
		self.vector = vector
		self.keywords=keywords
		self.hashed_summary=hashed_summary
		self.id=id
	def json(self):
		return {xx:getattr(self,xx) for xx in self.json_keys}
	def big_no_links(self):
		return "- " + self.title + " "+ self.source +": "+self.summary
	def big(self):
		return "- " + self.title + self.str_small()+" ".join(self.keywords)+"\n\t- "+self.summary
	def limited(self):
		return self.medium() +": "+" ".join(self.summary.split(" ")[:30])
	def medium(self,lev=0):
		return "- " + self.title + self.str_small()
	def out(self,lev=0):
		return self.str_small()
	def __str__(self):
		return self.big()
	def __repr__(self):
		return self.medium()
	def str_small(self):
		return f"[{self.source}]({self.url})"
	def __getitem__(self, key):
		if key in self.keys:
			return getattr(self, key)
		else:
			raise KeyError(f"{key} not found in Article")
	def todict(self):
		return {xx:getattr(self,xx) for xx in self.keys}
class Group(object):
	keys = ["text","articles"]
	table = ["groups"]
	def __init__(self, text, articles):
		self.text = text
		self.articles = articles
	def __iter__(self):
		return iter(self.articles)
	def add(self, art):
		self.articles.append(art)
	def limited(self):
		return "\n".join([xx.limited() for xx in self.articles])
	def big_no_links(self):
		return  "".join([f"{self.text}: "] + [xx.big_no_links() for xx in self.articles])
	def big(self):
		return  "".join([f"{self.text}: "] + [xx.big() for xx in self.articles])
	def medium(self,lev=1):
		return  "\n".join([f"{self.text}: "] + [xx.medium() for xx in self.articles])
	def out(self):
		pfx = ""
		sfx = ""
		if self.text.startswith("#"):
			sfx = "\n"
		else:
			pfx = "- "
		return "".join([f"{pfx}{self.text}{sfx}"] + [xx.out() for xx in self.articles])+"\n"
	def __str__(self):
		return self.out()
