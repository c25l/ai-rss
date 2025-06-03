#!/usr/bin/env /usr/bin/python3
from collections import defaultdict
from datetime import datetime
import numpy as np
from datamodel import Article,Group
import feeds 
import smtplib
from email.message import EmailMessage
from markdown import markdown
from datetime import datetime
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import requests

def now(short = True):
    fstring = '%Y-%m-%d %H:%M:%S' if not short else '%Y-%m-%d'
    return datetime.now().strftime(fstring)
def log(*inp):
    print(now(False), *inp)

def embed(text, pq = 'p',norm=True):
    payload = {
        "model": "nomic-embed-text",
        "prompt": ("passage: " if pq=='p' else "query: ") + text,
    }
    try:
        response = requests.post("http://localhost:11434/api/embeddings", json=payload)
        response.raise_for_status()
        data = response.json()
        vect = np.array(data.get("embedding",[]))
        if norm:
            vect /= np.linalg.norm(vect)
        return vect
    except Exception as e:
        print(f"[ERROR] Model call failed: {e}")
        return []

###
#  Clustering happens here.
# ###    
def make_labelled_groups(t_gps):
    for ii,xx in t_gps.items():
            keys =defaultdict(int)
            for aa in xx:
                for kk in aa.keywords:
                    keys[kk] += 1
            keys = sorted(keys.items(), key=lambda x: x[1], reverse=True)
            print(keys)
            headline =  ", ".join([f"{ii}" for ii,jj in keys[:3]])
            t_gps[ii] = Group(text=headline, articles=xx)

    return t_gps


def make_gps(g, keyfunc):
    t_gps = defaultdict(list)
    misc = defaultdict(list)
    for xx in g:
        realkey = keyfunc(xx)
        if len(g[xx]) < 2:
            misc[realkey].extend(g[xx])
    
        else:
            t_gps[realkey].extend(g[xx])
    return make_labelled_groups(t_gps),misc

def cluster_vectors_kmeans(embeddings):
        # Optimal k-means clustering on embeddings
        best_k = 2
        best_score = -1
        clusters_for_best_score = []
        for k in range(4, len(embeddings)-1):
            kmeans = KMeans(n_clusters=k, random_state=42)
            labels = kmeans.fit_predict(embeddings)
            score = silhouette_score(embeddings, labels)
            if score > best_score:
                best_k = k
                best_score = score
                clusters_for_best_score = labels
        return clusters_for_best_score

def cluster(arts):
    claims = [embed(aa.title + "\n" + aa.summary) for aa in arts]
    title_summary_clust = cluster_vectors_kmeans(claims)
    tags = [
    'Conflict', 'Diplomacy', 'Alliances', 'Sanctions', 'Elections', 'Multipolarity',
    'Russia', 'Ukraine', 'Nato', 'Israel', 'Zionism', 'Antisemitism', 'Hamas', 'Gaza', 'Hezbollah',
    'China', 'Taiwan', 'Iran', 'Houthis', "European Union",
    'United Kingdom', 'Germany', 'France', 'Japan', 'South Korea', 'Australia',
    'Canada', 'Mexico', 'Brazil', 'Argentina', 'Turkey', 'Saudi Arabia',
    'United States', 'Joe Biden', 'India', 'Brazil',
    'South Africa', 'United Nations' 'Artificial Intelligence', 'Automation', 'Regulation',
    'Surveillance', 'Semiconductors', 'Openai', 'Chatgpt',
    'Conspiracy','Misinformation','Disinformation','Propaganda','Censorship',
    'Nvidia', 'Bytedance', 'Alibaba', "Apple", 
    'Doge', 'Us Congress', "Air Traffic Control",
    'Climate Change', 'Energy', 'Disaster', 'Policy', 'Migration', 'Biodiversity',
    'Noaa', 'Nasa', 
    'Justice', 'Legislation', 'Culture', 'Civil Rights', 'Tech Policy',
    'Robert F Kennedy Jr.', 'Scotus', 'Florida', 'Texas', 'California',
    "Democrat","Republican","Senate",
    'Inflation', 'Recession', 'Employment', 'Housing', 'Finance', 
    'Misinformation', 'Freedom', 'Protest', 'Repression', 'Identity',
    'Human Rights Watch', 'Trump', 'President', 
    'Sports','Geology','Space','Technology','Science','Chemistry','Biology','Physics',
    "Music","Concert","Artist","Album","Linux","Open Source","Python","Programming","Hardware","Physics","Quantum","Nuclear",]
    vtags = np.array([embed(aa) for aa in tags])
    kwds = []
    tagvect = None
    for ii,xx in enumerate(claims):
        sims = vtags@xx
        use = np.argsort(sims)[::-1][:5]
        for uu in use:
            if sims[uu] < 0.65:
                continue
            if tagvect is None:
                tagvect = np.zeros_like(vtags[uu]) 
            tagvect += vtags[uu] * sims[uu]

        use = [tags[uu] for uu in use  if sims[uu]>=0.5]
        
        arts[ii].keywords = use
        arts[ii].vector=xx
        kwds.append(use)
    kwd_assigns = cluster_vectors_kmeans([xx.vector for xx in arts])
    print(title_summary_clust, kwd_assigns)
    cl = []
    clc = defaultdict(int)
    for c2,kk in zip(title_summary_clust, kwd_assigns):
        tcl = c2 +1000*kk
        cl.append(tcl)
        clc[tcl] += 1
    mhg = defaultdict(int)
    for _,ii in clc.items():
        mhg[ii] += 1
    print(cl,clc,mhg)
    for aa,cc in zip(arts, cl):
        aa.cluster = cc
    return arts
###
# Main control flow.
###
def main():
    today = now()
    articles = feeds.Feeds.fetch_articles(feeds.FEEDS)

    print(len(articles), "articles")
    updated_articles = cluster(articles)

    g = defaultdict(list)
    old_clusts = set([aa.cluster for aa in updated_articles[len(articles):]])
    for aa in updated_articles[:len(articles)]:
        g[aa.cluster].append(aa)
    t_gps, misc = make_gps(g, lambda x: x)
    t_gps[-1] = Group(text="Misc.", articles=[xx[0] for yy, xx in misc.items() if yy not in t_gps])
    print("group ct: ", len(t_gps))
    text = "\n".join([tgp.out() for _, tgp in t_gps.items()])
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


if __name__ == "__main__":
    main()
