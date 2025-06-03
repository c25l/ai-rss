import psycopg2
from psycopg2.extras import RealDictCursor
from datamodel import Article, Group
import os

connection_string = os.getenv("PGVECTOR_URL", "postgresql://postgres:yourpassword@localhost:5432/rss")

def get_connection():
    try:
        conn = psycopg2.connect(connection_string, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"Failed to connect to PostgreSQL: {e}")
        raise e

def setup_db():
    """
    Create tables for feeds, articles, and keyword mapping if they don't exist.
    """
    create_feeds_table = """
    CREATE TABLE IF NOT EXISTS feeds (
        id SERIAL PRIMARY KEY,
        type INT NOT NULL,
        source TEXT NOT NULL,
        url TEXT NOT NULL UNIQUE
    );
    """
    create_secrets_table = """
    CREATE TABLE IF NOT EXISTS secrets (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        value TEXT NOT NULL
    );
    """
    create_topics_table = """
    CREATE TABLE IF NOT EXISTS topics (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    create_articles_table = """
    CREATE TABLE IF NOT EXISTS articles (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        url TEXT NOT NULL UNIQUE,
        source TEXT NOT NULL,
        summary TEXT,
        keywords TEXT, -- delimited by " / "
        groupid INTEGER,
        published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute(create_feeds_table)
            cur.execute(create_secrets_table)
            cur.execute(create_topics_table)
            cur.execute(create_articles_table)
        conn.commit()
    print("Database setup complete.")

def get_feeds():
    """
    Fetch feeds from the database.
    """
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT type, source, url FROM feeds;")
            feeds = cur.fetchall()
    return feeds

def set_feed(type, source, url):
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO feeds (type, source, url) 
                VALUES (%s, %s, %s) 
                ON CONFLICT (url) 
                DO UPDATE SET type = EXCLUDED.type, source = EXCLUDED.source;
                """,
                (type, source, url)
            )
        conn.commit()

def get_secret(name):
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT value FROM secrets WHERE name = %s;", (name,))
            result = cur.fetchone()
    return result["value"] if result else None

def set_secret(name, value):
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO secrets (name, value) 
                VALUES (%s, %s) 
                ON CONFLICT (name) 
                DO UPDATE SET value = EXCLUDED.value;
                """,
                (name, value)
            )
        conn.commit()

def get_articles(query=None):
    conn = get_connection()
    cols = ["title", "url", "source", "summary", "keywords", "published_at"]
    select = ",".join(cols)
    if query is not None:
        if not query.startswith("WHERE"):
            query = "WHERE " + query
    query_str = f"SELECT {select} FROM articles  {query};"
    with conn:
        with conn.cursor() as cur:
            cur.execute(query_str, ())
            result = cur.fetchall()
    arts= [
        Article(
            title=res["title"],
            url=res["url"],
            source=res["source"],
            summary=res["summary"],
            keywords=res["keywords"].split(" / "),
            published_at=res["published_at"]
        )
        for res in result
    ] 
    return arts
def get_recent_articles(days=3):
    return get_articles("(published_at >= NOW() - INTERVAL '%s days') AND (published_at <= NOW()-Interval '1 days') " % days)

def add_articles(articles):
    if not isinstance(articles, list):
        articles = [articles]
    for article in articles:
        add_article(article)

def add_article(article):
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO articles (title, url, source, summary, keywords, published_at) 
                VALUES (%s, %s, %s, %s, %s, %s) 
                ON CONFLICT (url) 
                DO UPDATE SET 
                    title = EXCLUDED.title,
                    source = EXCLUDED.source,
                    summary = EXCLUDED.summary,
                    keywords = EXCLUDED.keywords,
                    groupid = EXCLUDED.groupid,
                    published_at = EXCLUDED.published_at;
                """,
                (
                    article.title,
                    article.url,
                    article.source,
                    article.summary,
                    " / ".join(article.keywords),
                    article.published_at
                )
            )
        conn.commit()
