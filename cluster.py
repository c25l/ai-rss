import numpy as np
from collections import defaultdict
import networkx as nx
from sklearn.metrics import pairwise_distances
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import MultiLabelBinarizer
from datamodel import Group

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
    

    def cluster_jaccard_similarity(self, arts):
        keywords_sets = [list(aa.keys()) for aa in arts]
        tf=MultiLabelBinarizer()
        ks2=tf.fit_transform(keywords_sets)
        distances = pairwise_distances(ks2, metric="jaccard")
        # distances = np.zeros((len(arts), len(arts)))
        # for ii,k1 in enumerate(arts):
        #     keyset1 = k1.keys()
        #     for jj,k2 in enumerate(arts):
        #         if ii<jj:
        #             continue
        #         if ii == jj:
        #             distances[ii, jj] = 0.0
        #             continue
        #         keyset2 = k2.keys()
        #         num=0
        #         den=0
        #         for kk in set(keyset1)|set(keyset2):
        #             t1 = 0
        #             t2 = 0
        #             if kk in keyset2:
        #                 t1=k2.get(kk,0.5)
        #                 t2=k2.get(kk,0.5)
        #                 if kk not in keyset1:
        #                     t1=min(k1.get(kk,0.5),t1)
        #                     t2=max(k1.get(kk,0.5),t2)
                    
                    
        #             num+=(t1+1)/2
        #             den+=(t2+1)/2 
        #             distances[ii, jj] = 1 - (num / den) if den > 0 else 1.0
        #             distances[ii, jj] = distances[jj, ii]
        best_k = 0
        best_score = 0
        clusters_for_best_score = []
        print(distances.mean())
        print(distances.shape, "embeddings shape")
        for k in range(1, 31):
            dbs = DBSCAN(metric='precomputed', eps=0.03*k, min_samples=2)
            labels = dbs.fit_predict(distances)
            
            for ii,xx in enumerate(labels):
                if xx<0:
                    labels[ii] = 1000-ii
            try:
                score = silhouette_score(distances, labels,metric="precomputed")
            except:
                continue
            if score > best_score:
                best_k = k
                best_score = score
                clusters_for_best_score = labels
            print(k,score,best_k, best_score)
        return clusters_for_best_score

    def cluster_jaccard_agglom(self, arts):
        keywords_sets = arts
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
        return clusters_for_best_score
    def cluster_double_trouble(self, embeddings, kwds):
        tf=MultiLabelBinarizer()
        ks2=tf.fit_transform(kwds)
        jaccard_matrix = pairwise_distances(ks2, metric="jaccard")
        embeddings = np.array(embeddings)
        embeddings /= np.linalg.norm(embeddings, axis=1, keepdims=True)
        distances = embeddings@(embeddings.T)
        distances = np.abs(1 - distances)
        distances= 1-(1-distances)*(1-jaccard_matrix)
        print(distances.mean(), distances.std())
        best_k = 0
        best_score = 0
        clusters_for_best_score = []
        for k in range(1, 31):
            dbs = DBSCAN(metric='precomputed', eps=0.03*k, min_samples=2)
            labels = dbs.fit_predict(distances)
            
            labelcts = defaultdict(int)
            for ii,xx in enumerate(labels):
                if xx<0:
                    labels[ii] = 999-ii
                labelcts[labels[ii]] += 1
            if len(labelcts) < 2:
                continue
            if len(labelcts) > len(labels)-1:
                continue
            score = silhouette_score(distances, labels,metric="precomputed")
            if score > best_score:
                best_k = k
                best_score = score
                clusters_for_best_score = labels
            print(k,score,best_k, best_score)
        return clusters_for_best_score
        
    def cluster_vectors_similarity(self, embeddings):
        embeddings = np.array(embeddings)
        embeddings /= np.linalg.norm(embeddings, axis=1, keepdims=True)
        distances = embeddings@(embeddings.T)
        distances = np.abs(1 - distances)

        best_k = 0
        best_score = 0
        clusters_for_best_score = []
        for k in range(1, 31):
            dbs = DBSCAN(metric='precomputed', eps=0.01*k, min_samples=2)
            labels = dbs.fit_predict(distances)
            
            for ii,xx in enumerate(labels):
                if xx<0:
                    labels[ii] = 999-ii
            try:
                score = silhouette_score(distances, labels,metric="precomputed")
            except:
                continue
            if score > best_score:
                best_k = k
                best_score = score
                clusters_for_best_score = labels
            print(k,score,best_k, best_score)
        return clusters_for_best_score
        ### WE need to make the full similarity matrix here and use that
        ### to make a distance matrix
    
    def cluster_vectors_kmeans(self, embeddings):
        # Optimal k-means clustering on embeddings
        best_k = 2
        best_score = -1
        clusters_for_best_score = []
        ### WE need to make the full similarity matrix here and use that
        ### to make a distance matrix
        for k in range(4, len(embeddings)-1):
            kmeans = KMeans(n_clusters=k, random_state=42)
            labels = kmeans.fit_predict(embeddings)
            score = silhouette_score(embeddings, labels)
            if score > best_score:
                best_k = k
                best_score = score
                clusters_for_best_score = labels
        return clusters_for_best_score
    
