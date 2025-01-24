from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from clarity.schemas.ml import FeatureSet, ProcessedFeatures
import structlog

logger = structlog.get_logger()

class FeatureProcessor:
    """Processes and transforms extracted features."""
    
    def __init__(
        self,
        scaling_method: str = 'standard',
        handle_missing: bool = True
    ):
        self.scaling_method = scaling_method
        self.handle_missing = handle_missing
        
        self.scaler = StandardScaler() if scaling_method == 'standard' else MinMaxScaler()
        self.feature_statistics = {}

    def process_features(
        self,
        feature_set: FeatureSet,
        fit: bool = True
    ) -> ProcessedFeatures:
        try:
            # Convert to DataFrame
            df = self._features_to_df(feature_set)
            
            # Handle missing values
            if self.handle_missing:
                df = self._handle_missing_values(df)
            
            # Calculate feature statistics
            if fit:
                self.feature_statistics = self._calculate_statistics(df)
            
            # Scale features
            features_scaled = self._scale_features(df, fit)
            
            # Create temporal features
            temporal_features = self._create_temporal_features(
                features_scaled,
                feature_set.vectors
            )
            
            return ProcessedFeatures(
                features=features_scaled,
                temporal_features=temporal_features,
                statistics=self.feature_statistics,
                scaler=self.scaler
            )
            
        except Exception as e:
            logger.error("feature_processing.failed", error=str(e))
            raise

    def _features_to_df(self, feature_set: FeatureSet) -> pd.DataFrame:
        """Convert feature vectors to DataFrame."""
        data = []
        for vector in feature_set.vectors:
            row = vector.features.copy()
            row['timestamp'] = vector.timestamp
            data.append(row)
        
        return pd.DataFrame(data)

    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values in features."""
        # Fill numeric columns with median
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
        
        # Fill categorical columns with mode
        categorical_cols = df.select_dtypes(include=['object']).columns
        df[categorical_cols] = df[categorical_cols].fillna(df[categorical_cols].mode().iloc[0])
        
        return df

    def _calculate_statistics(self, df: pd.DataFrame) -> Dict:
        """Calculate feature statistics."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        stats = {
            'mean': df[numeric_cols].mean().to_dict(),
            'std': df[numeric_cols].std().to_dict(),
            'min': df[numeric_cols].min().to_dict(),
            'max': df[numeric_cols].max().to_dict(),
            'missing_ratio': (df.isnull().sum() / len(df)).to_dict()
        }
        
        # Calculate correlations
        correlations = df[numeric_cols].corr()
        threshold = 0.7
        high_correlations = []
        
        for i in range(len(correlations.columns)):
            for j in range(i+1, len(correlations.columns)):
                if abs(correlations.iloc[i, j]) > threshold:
                    high_correlations.append({
                        'features': (correlations.columns[i], correlations.columns[j]),
                        'correlation': correlations.iloc[i, j]
                    })
        
        stats['high_correlations'] = high_correlations
        return stats

    def _scale_features(
        self,
        df: pd.DataFrame,
        fit: bool = True
    ) -> np.ndarray:
        """Scale numerical features."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        non_numeric_cols = df.select_dtypes(exclude=[np.number]).columns
        
        if fit:
            scaled_features = self.scaler.fit_transform(df[numeric_cols])
        else:
            scaled_features = self.scaler.transform(df[numeric_cols])
        
        # Combine with non-numeric features
        result = pd.DataFrame(scaled_features, columns=numeric_cols)
        for col in non_numeric_cols:
            result[col] = df[col]
        
        return result.values

    def _create_temporal_features(
        self,
        features: np.ndarray,
        vectors: List[FeatureVector]
    ) -> np.ndarray:
        """Create temporal features from time series data."""
        timestamps = np.array([v.timestamp.timestamp() for v in vectors])
        n_samples = len(timestamps)
        
        # Calculate time differences
        time_diffs = np.diff(timestamps)
        time_diffs = np.insert(time_diffs, 0, 0)
        
        # Calculate rolling statistics
        window_size = min(10, n_samples)
        rolling_mean = np.zeros((n_samples, features.shape[1]))
        rolling_std = np.zeros((n_samples, features.shape[1]))
        
        for i in range(n_samples):
            start_idx = max(0, i - window_size)
            window = features[start_idx:i+1]
            rolling_mean[i] = np.mean(window, axis=0)
            rolling_std[i] = np.std(window, axis=0)
        
        # Combine features
        temporal_features = np.column_stack([
            features,
            time_diffs.reshape(-1, 1),
            rolling_mean,
            rolling_std
        ])
        
        return temporal_features
