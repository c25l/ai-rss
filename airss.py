#!/usr/bin/env /usr/bin/python3
from collections import defaultdict
from datetime import datetime
import numpy as np
from datamodel import Article, Group
from database import Database
from outputs import AzureOut, Outputs
from feeds import Feeds
from generator import Generator
from modules import Weather, Stocks
import pickle
import os
from cluster import Cluster

import time
db = Database("./airss.db")

def now(short = True):
	fstring = '%Y-%m-%d %H:%M:%S' if not short else '%Y-%m-%d'
	return datetime.now().strftime(fstring)
def log(*inp):
	print(now(False), *inp)



def main():
	today = now()
	gen = Generator(db.get_secret("openai-endpt"),db.get_secret("openai-key"))
	db.setup_db()
	clust = Cluster(gen.embed, gen)
	feeds = db.get_feeds()
	feeds = [[tt,ss,xx,kk] for tt,ss,xx,kk in feeds if xx is not None]
	log("Feeds", "\n".join([", ".join([str(yy) for yy in xx]) for xx in feeds]))
	articles = Feeds.fetch_articles(feeds)
	db.set_articles(articles)

	updated_articles = []
	for article in articles:
		updated_article = gen.get_article_keywords(article)
		# Ensure the `keywords` field is updated with the combined keywords
		updated_article.keywords = list(set((updated_article.keywords or [])))# + (updated_article.source_keywords.split(" / "	) or [])))
		updated_articles.append(updated_article)
		db.set_article(updated_article)
	
	t_gps = clust.cluster(updated_articles)
	##db.set_groups(t_gps)
	Outputs.send_email("\n".join([Weather.info(gen.generate), Stocks.quotes(),"# Articles"] + [tgp.out() for tgp in t_gps]),db.get_secret('airss-email-sender'),db.get_secret('airss-email-receiver'),db.get_secret('airss-email-password'))
#	Outputs.md_fileout("\n".join([Weather.info(gen.generate), Stocks.quotes(),"# Articles"] + [tgp.out() for tgp in t_gps]),"./")
	#AzureOut(db).write_d3_bundle_to_azure(now(), [article.json() for article in use_articles])

if __name__ == "__main__":
	main()
