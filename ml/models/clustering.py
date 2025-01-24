import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.mixture import GaussianMixture
from typing import Dict, List, Optional
from clarity.schemas.ml import ClusteringResult, ClusterStats
import structlog

logger = structlog.get_logger()

class BehaviorClusterer:
    def __init__(
        self,
        n_clusters: Optional[int] = None,
        method: str = "kmeans"
    ):
        self.n_clusters = n_clusters
        self.method = method
        self.model = None
        
        if method == "kmeans":
            self.model = KMeans(n_clusters=n_clusters)
        elif method == "dbscan":
            self.model = DBSCAN()
        elif method == "gmm":
            self.model = GaussianMixture(n_components=n_clusters)
        else:
            raise ValueError(f"Unsupported clustering method: {method}")

    def fit_predict(
        self,
        features: np.ndarray,
        timestamps: np.ndarray
    ) -> ClusteringResult:
        try:
            # Normalize features
            features_normalized = self._normalize_features(features)
            
            # Fit and predict clusters
            labels = self.model.fit_predict(features_normalized)
            
            # Calculate cluster statistics
            cluster_stats = self._calculate_cluster_stats(
                features_normalized,
                labels,
                timestamps
            )
            
            return ClusteringResult(
                labels=labels,
                cluster_stats=cluster_stats,
                n_clusters=len(np.unique(labels[labels >= 0])),
                silhouette_score=self._calculate_silhouette_score(
                    features_normalized,
                    labels
                )
            )
            
        except Exception as e:
            logger.error("clustering.fit_predict_failed", error=str(e))
            raise

    def _normalize_features(self, features: np.ndarray) -> np.ndarray:
        """Normalize features to zero mean and unit variance."""
        mean = np.mean(features, axis=0)
        std = np.std(features, axis=0)
        std[std == 0] = 1  # Prevent division by zero
        return (features - mean) / std

    def _calculate_cluster_stats(
        self,
        features: np.ndarray,
        labels: np.ndarray,
        timestamps: np.ndarray
    ) -> List[ClusterStats]:
        """Calculate statistics for each cluster."""
        unique_labels = np.unique(labels[labels >= 0])
        stats = []
        
        for label in unique_labels:
            mask = labels == label
            cluster_features = features[mask]
            cluster_times = timestamps[mask]
            
            stats.append(ClusterStats(
                cluster_id=int(label),
                size=int(np.sum(mask)),
                mean=np.mean(cluster_features, axis=0).tolist(),
                std=np.std(cluster_features, axis=0).tolist(),
                temporal_density=self._calculate_temporal_density(cluster_times),
                feature_importance=self._calculate_feature_importance(
                    cluster_features,
                    features
                )
            ))
        
        return stats

    def _calculate_temporal_density(
        self,
        timestamps: np.ndarray
    ) -> float:
        """Calculate temporal density of cluster points."""
        if len(timestamps) <= 1:
            return 0.0
        
        time_diffs = np.diff(sorted(timestamps))
        return 1.0 / (np.mean(time_diffs) + 1e-6)

    def _calculate_feature_importance(
        self,
        cluster_features: np.ndarray,
        all_features: np.ndarray
    ) -> List[float]:
        """Calculate importance of each feature for the cluster."""
        cluster_mean = np.mean(cluster_features, axis=0)
        overall_mean = np.mean(all_features, axis=0)
        overall_std = np.std(all_features, axis=0)
        
        # Calculate z-scores of cluster centroids
        importance = np.abs(cluster_mean - overall_mean) / (overall_std + 1e-6)
        return importance.tolist()

    def _calculate_silhouette_score(
        self,
        features: np.ndarray,
        labels: np.ndarray
    ) -> float:
        """Calculate silhouette score for clustering quality."""
        try:
            from sklearn.metrics import silhouette_score
            if len(np.unique(labels)) > 1:
                return float(silhouette_score(features, labels))
            return 0.0
        except Exception:
            return 0.0
