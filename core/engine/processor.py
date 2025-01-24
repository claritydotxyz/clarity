from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
import numpy as np
from clarity.data.transforms.cleaners import DataCleaner
from clarity.data.transforms.normalizers import DataNormalizer
import structlog

logger = structlog.get_logger()

class DataProcessor:
    """Processes collected data for analysis."""
    
    def __init__(self):
        self.cleaner = DataCleaner()
        self.normalizer = DataNormalizer()
        
        # Processing settings
        self.min_data_points = 10
        self.outlier_threshold = 3
        self.moving_average_window = 5

    async def process_data(
        self,
        data: Dict,
        normalize: bool = True,
        remove_outliers: bool = True
    ) -> Dict:
        """Process raw data for analysis."""
        try:
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Clean data
            df = self.cleaner.clean_activity_data(df)
            
            # Remove outliers if requested
            if remove_outliers:
                df = self._remove_outliers(df)
            
            # Normalize if requested
            if normalize:
                df = self.normalizer.normalize_data(df)
            
            # Calculate derived metrics
            metrics = self._calculate_metrics(df)
            
            # Prepare processed data
            processed_data = {
                "timestamp": datetime.utcnow(),
                "data": df.to_dict("records"),
                "metrics": metrics,
                "metadata": {
                    "original_points": len(data),
                    "processed_points": len(df),
                    "missing_ratio": df.isnull().mean().to_dict()
                }
            }
            
            return processed_data
            
        except Exception as e:
            logger.error("processor.processing_failed", error=str(e))
            raise

    def _remove_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove outliers using Z-score method."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            mean = df[col].mean()
            std = df[col].std()
            df = df[abs(df[col] - mean) <= (self.outlier_threshold * std)]
        
        return df

    def _calculate_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate various metrics from processed data."""
        metrics = {}
        
        try:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            
            # Basic statistics
            metrics["statistics"] = {
                col: {
                    "mean": float(df[col].mean()),
                    "median": float(df[col].median()),
                    "std": float(df[col].std()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "q1": float(df[col].quantile(0.25)),
                    "q3": float(df[col].quantile(0.75))
                }
                for col in numeric_cols
            }
            
            # Time-based metrics
            if 'timestamp' in df.columns:
                df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
                df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek
                
                metrics["temporal"] = {
                    "hourly_patterns": df.groupby('hour')[numeric_cols]
                        .mean().to_dict(),
                    "daily_patterns": df.groupby('day_of_week')[numeric_cols]
                        .mean().to_dict(),
                    "peak_hours": {
                        col: int(df.groupby('hour')[col].mean().idxmax())
                        for col in numeric_cols
                    }
                }
            
            # Correlation analysis
            correlations = df[numeric_cols].corr()
            strong_correlations = []
            
            for i in range(len(correlations.columns)):
                for j in range(i+1, len(correlations.columns)):
                    if abs(correlations.iloc[i, j]) > 0.7:
                        strong_correlations.append({
                            "variables": (
                                correlations.columns[i],
                                correlations.columns[j]
                            ),
                            "correlation": float(correlations.iloc[i, j])
                        })
            
            metrics["correlations"] = strong_correlations
            
            # Trend analysis
            metrics["trends"] = {}
            for col in numeric_cols:
                trend = self._analyze_trend(df[col])
                if trend["is_significant"]:
                    metrics["trends"][col] = trend
            
            # Volatility analysis
            metrics["volatility"] = {
                col: float(df[col].std() / df[col].mean())
                for col in numeric_cols
                if df[col].mean() != 0
            }
            
            return metrics
            
        except Exception as e:
            logger.error("processor.metrics_calculation_failed", error=str(e))
            return {}

    def _analyze_trend(self, series: pd.Series) -> Dict:
        """Analyze trend in time series data."""
        try:
            # Calculate rolling statistics
            rolling_mean = series.rolling(window=self.moving_average_window).mean()
            rolling_std = series.rolling(window=self.moving_average_window).std()
            
            # Calculate trend
            x = np.arange(len(series))
            slope, intercept = np.polyfit(x, series, 1)
            
            # Calculate R-squared
            trend_line = slope * x + intercept
            r_squared = 1 - (np.sum((series - trend_line) ** 2) / 
                           np.sum((series - series.mean()) ** 2))
            
            return {
                "slope": float(slope),
                "intercept": float(intercept),
                "r_squared": float(r_squared),
                "is_significant": abs(r_squared) > 0.6,
                "direction": "increasing" if slope > 0 else "decreasing",
                "volatility": float(rolling_std.mean() / rolling_mean.mean())
                if rolling_mean.mean() != 0 else 0
            }
            
        except Exception as e:
            logger.error("processor.trend_analysis_failed", error=str(e))
            return {
                "slope": 0,
                "intercept": 0,
                "r_squared": 0,
                "is_significant": False,
                "direction": "stable",
                "volatility": 0
            }

    async def process_batch(
        self,
        data_list: List[Dict],
        batch_size: int = 1000
    ) -> List[Dict]:
        """Process multiple data points in batches."""
        processed_data = []
        
        try:
            # Process in batches
            for i in range(0, len(data_list), batch_size):
                batch = data_list[i:i + batch_size]
                
                # Process batch
                processed_batch = await self.process_data(batch)
                processed_data.extend(processed_batch["data"])
                
                logger.debug(
                    "processor.batch_processed",
                    batch_index=i//batch_size,
                    batch_size=len(batch)
                )
            
            return processed_data
            
        except Exception as e:
            logger.error("processor.batch_processing_failed", error=str(e))
            raise

    def get_data_quality_score(self, data: Dict) -> float:
        """Calculate a quality score for the processed data."""
        try:
            df = pd.DataFrame(data)
            
            # Calculate various quality metrics
            completeness = 1 - df.isnull().mean().mean()
            
            # Check for outliers
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            z_scores = df[numeric_cols].apply(
                lambda x: np.abs((x - x.mean()) / x.std())
            )
            outlier_ratio = (z_scores > self.outlier_threshold).mean().mean()
            
            # Check for consistency
            consistency_score = 1 - df.duplicated().mean()
            
            # Combine scores with weights
            quality_score = (
                0.4 * completeness +
                0.3 * (1 - outlier_ratio) +
                0.3 * consistency_score
            )
            
