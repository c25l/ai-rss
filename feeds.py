import feedparser
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from datamodel import Article


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
				if (("published_parsed" in entry and entry.published_parsed < cutoff_struct)
				or ("updated_parsed" in entry and entry.updated_parsed < cutoff_struct)):
					continue
				summ = BeautifulSoup(entry.get("summary", ""), "html.parser").get_text(separator=" ", strip=True)
				published = datetime.now().isoformat()
				if hasattr(entry, "published"):
					published = entry.published

				if tt == 1:  # Standard RSS feed
					if summ.strip() == "":
						continue
					title = entry.title.replace("<", "_").replace(">", "_")
					od = Article(title, entry.link, source, summ, keywords=kk.split(" / ")) 
					od.published = published
					articles.append(od)
					continue
				elif tt == 2:  # HackerNews
					links = BeautifulSoup(entry.get("summary", ""), "html.parser").find_all("a")
					links = [
						Article(aa.text.replace("<", "_").replace(">", "_"), aa["href"], ss, "", keywords=kk.split(" / "))
						for aa in links
						if "comments" not in aa.text
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
						articles.append(Article(title, url, ss, summ, keywords=kk.split(" / ")))
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
