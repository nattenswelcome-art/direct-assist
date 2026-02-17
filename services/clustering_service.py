import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from collections import defaultdict
from utils.logger import get_logger

logger = get_logger("clustering_service")

class ClusteringService:
    def __init__(self, n_clusters=5):
        self.default_n_clusters = n_clusters

    def cluster_keywords(self, keywords: list[str], n_clusters: int = None) -> dict[int, list[str]]:
        """
        Clusters a list of keywords into groups based on semantic similarity (TF-IDF).
        Returns a dict mapping cluster_id to list of keywords.
        """
        if not keywords:
            return {}
        
        # If fewer keywords than clusters, adjust
        if n_clusters is None:
            n_clusters = self.default_n_clusters
            
        if len(keywords) < n_clusters:
            n_clusters = max(1, len(keywords) // 2)

        try:
            logger.info(f"Clustering {len(keywords)} keywords into {n_clusters} clusters")
            
            # vectorization
            vectorizer = TfidfVectorizer(max_df=0.8, min_df=0.0, stop_words='english') # 'english' is default, might need russian stop words
            X = vectorizer.fit_transform(keywords)

            # clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            kmeans.fit(X)
            
            # grouping
            clusters = defaultdict(list)
            for i, label in enumerate(kmeans.labels_):
                clusters[int(label)].append(keywords[i])
                
            return dict(clusters)
            
        except Exception as e:
            logger.error(f"Clustering error: {e}")
            # Fallback: return all in one cluster
            return {0: keywords}

clustering_service = ClusteringService()
