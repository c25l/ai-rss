import sqlite3
from datamodel import Article, Group
class Database:
	def __init__(self, path):
		self._db_path = path
		#self.setup_db()

	def get_connection(self):
		try:
			conn = sqlite3.connect(self._db_path)
			conn.row_factory = sqlite3.Row
			return conn
		except Exception as e:
			print(f"Failed to connect to SQLite: {e}")
			raise

	def setup_db(self):
		"""
		Create tables for feeds, articles, and keyword mapping if they don't exist.
		"""
		create_feeds_table = """
		CREATE TABLE IF NOT EXISTS feeds (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			type INT NOT NULL,
			source TEXT NOT NULL,
			url TEXT NOT NULL UNIQUE,
			keywords TEXT
		);
		"""
		create_secrets_table = """
		CREATE TABLE IF NOT EXISTS secrets (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT NOT NULL UNIQUE,
			value TEXT NOT NULL
		);
		"""
		create_articles_table ="""
		CREATE TABLE IF NOT EXISTS articles (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			title TEXT NOT NULL,
			url TEXT NOT NULL UNIQUE,
			source text NOT NULL,
			summary TEXT,
			keywords TEXT, -- delim by " / "
			published_at DATE DEFAULT (CURRENT_TIMESTAMP)
		);
		"""
		create_groups_table = """
		CREATE TABLE IF NOT EXISTS groups (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			title TEXT NOT NULL UNIQUE,
			keywords TEXT NOT NULL,
			sources TEXT NOT NULL,
			urls TEXT NOT NULL,
			published_at Date DEFAULT (CURRENT_TIMESTAMP)
		);
		"""
		conn = self.get_connection()
		with conn:
			conn.execute(create_feeds_table)
			conn.execute(create_secrets_table)
			conn.execute(create_articles_table)
			conn.execute(create_groups_table)
		print("Database setup complete.")

	def get_feeds(self):
		"""
		Fetch feeds from the database.
		"""
		conn = self.get_connection()
		with conn:
			feeds = conn.execute("SELECT type, source, url, keywords FROM feeds;").fetchall()
		return feeds
	
	def set_feed(self, type, source, url, keywords):
		conn = self.get_connection()
		with conn:
			conn.execute(
				"INSERT INTO feeds (type, source, url, keywords) VALUES (?, ?, ?,?) ON CONFLICT(url) DO UPDATE SET type=EXCLUDED.type, source=EXCLUDED.source, keywords=EXCLUDED.keywords;",
				(type, source, url, keywords)
			)
	def get_secret(self, name):
		conn = self.get_connection()
		with conn:
			result = conn.execute("SELECT value FROM secrets WHERE name = ?;", (name,)).fetchone()
		return result["value"] if result else None

	def set_secret(self, name, value):
		conn = self.get_connection()
		with conn:
			conn.execute(
				"INSERT INTO secrets (name, value) VALUES (?, ?) ON CONFLICT(name) DO UPDATE SET value = excluded.value;",
				(name, value)
			)
	def get_articles(self, query=None):
		conn = self.get_connection()
		cols = ["title", "url", "source", "summary", "keywords", "published_at"]
		select = ",".join(cols)
		query = ' AND \n'.join([f"{xx} ='{query[xx]}" for xx in cols if xx in query] or ['true'])
		querystr=f"SELECT ({select}) FROM articles WHERE {query} ;  "
		with conn:
			result = conn.execute(querystr).fetchall()
		return [Article(title, url, square, summary, keywords.split(" / "), published_at) for title,url, square, summary, keywords, published_at in[res["value"] for res in result]]  if result else None

	def set_articles(self, articles):
		if type(articles) is not list:
			articles = [articles]
		for article in articles:
			self.set_article(article)
	
	def set_article(self, article):
		conn = self.get_connection()
		with conn:
			conn.execute(
				"""INSERT INTO articles (title,url,source,summary,keywords,published_at) VALUES (?,?,?,?,?,?) 
				ON CONFLICT(url) 
				DO UPDATE SET 
				title = EXCLUDED.title,
				source = EXCLUDED.source,
				summary = EXCLUDED.summary,
				keywords = EXCLUDED.keywords,
				published_at = EXCLUDED.published_at
				;""",
				(article.title,article.url,article.source,article.summary, " / ".join(article.keywords),article.published_at)
			)

	def get_groups(self, day_query=None):
		conn = self.get_connection()
		cols = ["title", "url", "source", "summary", "keywords", "published_at"]
		select = ",".join(cols)
		querystr=f"SELECT ({select}) FROM articles {day_query} ;  "
		with conn:
			result = conn.execute(querystr).fetchall()
		return [Group(title, url, source, summary, keywords, published_at) for title, url, source, summary, keywords, published_at in [res["value"] for res in result]]  if result else None

	def set_groups(self, groups):
		if type(groups) is not list:
			groups = [groups]
		for article in groups:
			self.set_group(self, article)
	
	def set_group(self,group):
		conn = self.get_connection()
		with conn:
			conn.execute(
				"""INSERT INTO articles (title,keywords,sources,urls,published_at) VALUES (?,?,?,?,?) 

				;""",
				(group.title,group.keywords,group.sources,group.urls,group.published_at))
