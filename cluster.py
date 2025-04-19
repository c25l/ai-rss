import numpy as np
from collections import defaultdict
import networkx as nx
from datamodel import Group
import hdbscan

class Cluster:
    def __init__(self, embed, gen):
        self.embed = embed
        self.gen = gen
    def keycounts(self, arts):
        keys = defaultdict(int)
        for xx in arts:
            for kk in xx.keywords:
                keys[kk]+=1
        return keys
    
    def article_hdbscan(self, arts):
        for kk,cc in self.keycounts(arts).items():
            if cc <= 1:
                continue
            aas = [aa for aa in arts if kk in aa.keywords]
            vas = np.array(self.embed([aa.big_no_links() for aa in aas],norm=True))
            clusters = hdbscan.hdbscan(vas,min_cluster_size=2,cluster_selection_method='leaf',metric='euclidean',min_samples=1,allow_single_cluster=True)[0]
            for ii,aa in enumerate(aas):
                clust =  clusters[ii]
                if clust == -1:
                    aa.keywords = [k for k in aa.keywords if k != kk]
                else:
                    aa.keywords = [k for k in aa.keywords if k != kk] + [f"{kk}{clust}"]

        # Now we've chipped a lot apart, let's see if the rubble holds signal.
        singles = [aa for aa in arts for kk in [kk for kk,cc in self.keycounts(arts).items() if cc==1] if kk in aa.keywords]
        vss = np.array(self.embed([aa.big_no_links() for aa in singles],norm=True))
        clusters = hdbscan.hdbscan(vss,min_cluster_size=2,cluster_selection_method='leaf',metric='euclidean')[0]
        for ii,aa in enumerate(singles):
            clust =  clusters[ii]
            if clust == -1:
                continue
            aa.keywords = aa.keywords + [f"{clust}"]
        return arts 

    def build_kwd_graph(self, processed):
        edges = defaultdict(int)
        for xx in processed:
            kw = xx.keywords
            kw.sort()
            for ii in range(len(kw)):
                for jj in range(ii+1, len(kw)):
                    edges[(kw[ii], kw[jj])]+=1
        
        G=nx.Graph()
        for (xx,yy),cc in edges.items():
            G.add_edge(xx, yy, weight=cc)
        return G
    
    def cluster(self, articles):
        # maychaps this should do groups natively.
        articles = self.article_hdbscan(articles)
        # must derive components to group..
        G = self.build_kwd_graph(articles)
        gps= list(nx.connected_components(G))
        gps =[Group("",[aa for aa in articles if set(gp).intersection(aa.keywords)]) for gp in list(gps)]
        gps2=[]
        for local in gps:
            if local.text=="" and len(local.articles)==1:
                temp=Group(local.articles[0].title,local.articles)
            else:
                summ=self.gen.summary_arts(local)
                temp=Group(summ,local)
            gps2.append(temp)
            
        topics = [xx.strip(" -:").split(" — ")[0]+"\n" for xx in self.gen.news_blocks.split("\n")]
        news_topics = np.array(self.embed([xx for xx in self.gen.news_blocks.split("\n")]))
        t_gps = [Group("## "+topic,[]) for topic in topics] + [Group("## Other",[])]
        for xx in gps2:
            cluster = self.embed(xx.big_no_links())
            sims = cluster @ news_topics.T
            print(sims)
            val = np.argmax(sims)
            if sims[0][val] > 0.2:
                t_gps[val].add(xx)
            else:
                t_gps[-1].add(xx)
        t_gps = [xx for xx in t_gps if len(xx.articles)>0]
        return t_gps
