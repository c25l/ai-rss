#!/usr/bin/env /usr/bin/python3
from collections import defaultdict
from datetime import datetime
import numpy as np
from datamodel import Article,Group
from outputs import Outputs
import feeds 
from generator import Generator
from modules import Weather, Stocks
import os
from cluster import Cluster
import pickle
import time
import database
import smtplib
from email.message import EmailMessage
from markdown import markdown
from datetime import datetime

def now(short = True):
    fstring = '%Y-%m-%d %H:%M:%S' if not short else '%Y-%m-%d'
    return datetime.now().strftime(fstring)
def log(*inp):
    print(now(False), *inp)
def make_gps(g, keyfunc):
    t_gps = defaultdict(list)
    misc = defaultdict(list)
    for xx in g:
        realkey = keyfunc(xx)
        if len(g[xx]) < 2:
            misc[realkey].extend(g[xx])
    
        else:
            t_gps[realkey].extend(g[xx])
    for ii,xx in t_gps.items():
            keys =defaultdict(int)
            for aa in xx:
                for kk in aa.keywords:
                    keys[kk] += 1
            keys = sorted(keys.items(), key=lambda x: x[1], reverse=True)
            print(keys)
            t_gps[ii] = Group(text=", ".join([f"{ii}" for ii,jj in keys[:3]]) or xx[0].title, articles=xx)

    return t_gps, misc
def cluster(gen, arts):
    clust = Cluster(gen.embed, gen)
    claims = [gen.embed(aa.title + "\n" + aa.summary) for aa in arts]
    title_summary_clust = clust.cluster_vectors_kmeans(claims)
    tags = [
    'conflict', 'diplomacy', 'alliances', 'sanctions', 'elections', 'multipolarity',
    'Russia', 'Ukraine', 'NATO', 'Israel', 'Zionism', 'Antisemitism', 'Hamas', 'Gaza', 'Hezbollah',
    'China', 'Taiwan', 'Xi Jinping', 'PLA', 'Iran', 'IRGC', 'Houthis', "European Union",
    'United Kingdom', 'Germany', 'France', 'Japan', 'South Korea', 'Australia',
    'Canada', 'Mexico', 'Brazil', 'Argentina', 'Turkey', 'Saudi Arabia',
    'United States', 'Joe Biden', 'BRICS', 'India', 'Brazil',
    'South Africa', 'UN', 'ICC', 'ASEAN', 'AI', 'automation', 'regulation',
    'surveillance', 'semiconductors', 'OpenAI', 'ChatGPT',
    'Anthropic AI', 
    'NVIDIA', 'AMD', 'TSMC', 'TikTok', 'ByteDance', 'Alibaba', "Apple",
    'DOGE', 'FTC', 'US Congress', "FAA", "Air Traffic Control",
    'climate change', 'energy', 'disaster', 'policy', 'migration', 'biodiversity',
    'NOAA', 'NASA', 
    'justice', 'legislation', 'culture', 'civil rights', 'tech policy',
    'RFK Jr.', 'SCOTUS', 'DOJ', 'FEC', 'Florida', 'Texas', 'California',
    "Democrat","Republican","senate","congress",
    'Ron DeSantis', 'Gavin Newsom', 'AOC', 'TikTok ban', 'Section 230',
    'inflation', 'recession', 'employment', 'housing', 'finance', 
    'CHIPS Act', 'government reduction',
    'misinformation', 'freedom', 'protest', 'repression', 'identity',
    'UNHCR', 'Human Rights Watch', 'Trump', 'President', 
    "music","concert","artist","album","linux","open source","python","programming","hardware","physics","quantum","nuclear",]
    vtags = np.array([gen.embed(aa) for aa in tags])
    kwds = []
    tagvect = None
    for ii,xx in enumerate(claims):
        sims = vtags@xx
        use = np.argsort(sims)[::-1][:5]
        for uu in use:
            if sims[uu] < 0.65:
                continue
                use = use[:uu]
            if tagvect is None:
                tagvect = np.zeros_like(vtags[uu]) 
            tagvect += vtags[uu] * sims[uu]

        use = [tags[uu] for uu in use  if sims[uu]>=0.65]
        
        arts[ii].keywords = use
        arts[ii].vector=xx
        kwds.append(use)
    kwd_assigns = clust.cluster_vectors_kmeans([xx.vector for xx in arts])
    # Step 1: Jaccard similarity on keyword sets
    #claims = [bb.vector for bb in arts]
    #print(claims)

    # claims2 = clust.cluster_vectors_kmeans(claims)
    #kwd_assigns = clust.cluster_jaccard_similarity(kwds)
    # print(claims2, claims3, kwd_assigns)
    #claims2 = clust.cluster_double_trouble(claims, kwds)
    print(title_summary_clust, kwd_assigns)
    cl = []
    clc = defaultdict(int)
    for c2,kk in zip(title_summary_clust, kwd_assigns):#, claims3, kwd_assigns):
        tcl = c2 +1000*kk#c3 * 1000+c2
        cl.append(tcl)
        clc[tcl] += 1
    mhg = defaultdict(int)
    for _,ii in clc.items():
        mhg[ii] += 1
    print(cl,clc,mhg)
    for aa,cc in zip(arts, cl):
        aa.cluster = cc
    return arts
    
def main():
    today = now()

    gen = Generator()
    articles = feeds.Feeds.fetch_articles(feeds.FEEDS)

    print(len(articles), "articles")
    # for article in articles:
    #     updated_article = gen.get_article_keywords(article)
    #     updated_article.keywords = list(set((updated_article.keywords or [])))
    #     updated_articles.append(updated_article)

    updated_articles = cluster(gen, articles)#updated_articles)
    # maxt = max([xx.published_at for xx in updated_articles]) 
    # print(len(updated_articles), "updated articles")
    # updated_articles = [aa for aa in updated_articles if aa.published_at > maxt - 60*60*24*7]
    # print(len(updated_articles), "updated articles today.")
    
    #db = database.Database()

    g = defaultdict(list)
    for aa in updated_articles:
        g[aa.cluster].append(aa)
    database.setup_db()
    database.add_articles(updated_articles)
    t_gps, misc = make_gps(g, lambda x: x)
    print(t_gps)
    t_gps2, misc2 = make_gps(misc, lambda x: 999 + (x % 1000))
    t_gps.update(t_gps2)
    print(t_gps)
    t_gps3, misc3 = make_gps(misc2, lambda x: (x%1000)+500)
    t_gps.update(t_gps3)
    t_gps[-1] = Group(text="Misc.", articles=[xx[0] for _, xx in misc3.items()])
    
    print(t_gps)

    #outgps= {g2[xx][0].articles[0].section: Group(text=g2[xx][0].articles[0].section,articles=g2[xx]) for xx in g2}
    outgps=t_gps

    

    #  try:
    #     if os.path.exists(f"{today}-annotated.pkl"):
    #         with open(f"{today}-annotated.pkl", "r") as f:
    #             print("Loading previous annotations")
    #             updated_articles = pickle.load(f)
    #     else:
    #         print("No previous annotations")
    # except:
    #     print("Error loading previous annotations, annotating new articles")
    #     for article in articles:
    #         updated_article = gen.get_article_keywords(article)
    #         updated_article.keywords = list(set((updated_article.keywords or [])))
    #         updated_articles.append(updated_article)

    # try:
    #     with open(f"{today}-annotated.pkl", "w") as f:
    #         pickle.dump(updated_articles, f)
    # except:
    #     pass
    # print(updated_articles)
    # print(t_gps)
    # for group in t_gps:
    #     # Add group to the database
    #     db_group = Group([]
    #         text=group.text,
    #         created_at=datetime.now()
    #     )

    text = "\n".join([tgp.out() for _, tgp in outgps.items()])
    sender = "christopherpbonnell@icloud.com"
    receiver = "christopherpbonnell@gmail.com"
    password="vqxh-oqrp-wjln-eagl"

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = f"Morning News for {datetime.now().strftime('%Y-%m-%d')}"
    msg.set_content(markdown(text), subtype="html")
    with smtplib.SMTP("smtp.mail.me.com", 587) as server:
        server.starttls()
        server.login(msg['From'], password)
        server.send_message(msg)

    # Outputs.md_fileout(
    #     "\n".join(tmp + ["# Articles"] + [tgp.out() for _, tgp in outgps.items()]),
    #     "./"
    # )

if __name__ == "__main__":
    main()
