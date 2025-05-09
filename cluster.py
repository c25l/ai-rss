import numpy as np
from collections import defaultdict
import networkx as nx
from datamodel import Group
import hdbscan
from sklearn.metrics import pairwise_distances
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import MultiLabelBinarizer

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
    

    def cluster_jaccard_agglom(self, arts):
        keywords_sets = [set(aa.keywords) for aa in arts]
        tf=MultiLabelBinarizer()
        ks2=tf.fit_transform(keywords_sets)
        jaccard_matrix = pairwise_distances(ks2, metric="jaccard")
        
        # Optimal k-means clustering on Jaccard similarity
        best_k = 2
        best_score = -1
        clusters_for_best_score = []
        for k in range(2, len(arts)-1):  # Limit k to a reasonable range
            kmeans = AgglomerativeClustering(n_clusters=k, metric='precomputed', linkage='average')
            labels = kmeans.fit_predict(jaccard_matrix)
            score = silhouette_score(jaccard_matrix, labels, metric="precomputed")
            if score > best_score:
                best_k = k
                best_score = score
                clusters_for_best_score = labels
        out = defaultdict(list)
        for ii,xx in enumerate(clusters_for_best_score):
            out[xx].append(arts[ii])
        return out.values()
    
    def cluster_vectors_kmeans(self, arts):
        # Optimal k-means clustering on embeddings
        embeddings= [aa.vector for aa in arts]
        best_k = 2
        best_score = -1
        clusters_for_best_score = []
        for k in range(2, len(arts)):
            kmeans = KMeans(n_clusters=k, random_state=42)
            labels = kmeans.fit_predict(embeddings)
            score = silhouette_score(embeddings, labels)
            if score > best_score:
                best_k = k
                best_score = score
                clusters_for_best_score = labels
        out = defaultdict(list)
        for ii,xx in enumerate(clusters_for_best_score):
            out[xx].append(arts[ii])
        return out.values()
    
    def annotate_vectors(self, arts):
        for aa in arts:
             aa.vector = self.embed(aa.big_no_links())
        return arts
    
    def cluster(self, articles):
        arts = self.annotate_vectors(articles)
        # Step 1: Jaccard similarity on keyword sets
        groups_1 = self.cluster_jaccard_agglom(articles)
        
        outgps = [] 
        singletons = []
        for cluster in groups_1:
            labels_2 = self.cluster_vectors_kmeans(cluster)
            for zz in labels_2:
                if len(zz) <= 1:
                    singletons.extend(zz)
                else:
                    outgps.append(zz)
        outgps.extend(self.cluster_vectors_kmeans(singletons))
        
        gps = [Group("",zz) for zz in outgps]
        # must derive components to group..
        gps2=[]
        for local in gps:
            if local.text=="" and len(local.articles)==1:
                temp=Group(local.articles[0].title,local.articles)
            else:
                summ=self.gen.summary_arts(local)
                temp=Group(summ,local)
            gps2.append(temp)
            
        topics = [xx.strip(" -:").split(" — ")[0]+"\n" for xx in self.gen.news_blocks.split("\n")]
        news_topics = np.array([self.embed(xx) for xx in self.gen.news_blocks.split("\n")])
        t_gps = [Group("## "+topic,[]) for topic in topics] + [Group("## Other",[])]
        for xx in gps2:
            cluster = self.embed(xx.big_no_links())
            sims = cluster @ news_topics.T
            print(sims)
            val = np.argmax(sims)
            if sims[val] > 0.2:
                t_gps[val].add(xx)
            else:
                t_gps[-1].add(xx)
        t_gps = [xx for xx in t_gps if len(xx.articles)>0]
        return t_gps
