from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from datetime import datetime
from clarity.schemas.ml import FeatureSet, FeatureVector
import structlog

logger = structlog.get_logger()

class FeatureExtractor:
    """Extracts features from raw behavioral and activity data."""
    
    def __init__(self):
        self.time_features = [
            'hour', 'day_of_week', 'week_of_year',
            'is_weekend', 'is_work_hours'
        ]
        self.activity_features = [
            'duration', 'intensity', 'focus_score',
            'context_switches', 'app_category'
        ]
        self.behavioral_features = [
            'productivity_score', 'distraction_level',
            'task_completion_rate', 'communication_frequency'
        ]

    def extract_features(
        self,
        activities: pd.DataFrame,
        behavioral_data: Dict,
        include_time: bool = True
    ) -> FeatureSet:
        try:
            feature_vectors = []
            
            for _, activity in activities.iterrows():
                features = {}
                
                # Extract time features
                if include_time:
                    time_features = self._extract_time_features(
                        activity['timestamp']
                    )
                    features.update(time_features)
                
                # Extract activity features
                activity_features = self._extract_activity_features(activity)
                features.update(activity_features)
                
                # Extract behavioral features
                behavioral_features = self._extract_behavioral_features(
                    activity, behavioral_data
                )
                features.update(behavioral_features)
                
                # Create feature vector
                feature_vectors.append(FeatureVector(
                    timestamp=activity['timestamp'],
                    features=features,
                    metadata={
                        'activity_id': activity.get('id'),
                        'source': activity.get('source')
                    }
                ))
            
            return FeatureSet(
                vectors=feature_vectors,
                feature_names=list(features.keys())
            )
            
        except Exception as e:
            logger.error("feature_extraction.failed", error=str(e))
            raise

    def _extract_time_features(self, timestamp: datetime) -> Dict:
        """Extract temporal features from timestamp."""
        return {
            'hour': timestamp.hour,
            'day_of_week': timestamp.weekday(),
            'week_of_year': timestamp.isocalendar()[1],
            'is_weekend': 1 if timestamp.weekday() >= 5 else 0,
            'is_work_hours': 1 if 9 <= timestamp.hour <= 17 else 0
        }

    def _extract_activity_features(self, activity: pd.Series) -> Dict:
        """Extract features from activity data."""
        features = {
            'duration': activity.get('duration', 0),
            'intensity': self._calculate_intensity(activity),
            'focus_score': activity.get('focus_score', 0),
            'context_switches': activity.get('context_switches', 0)
        }
        
        # One-hot encode app category
        app_category = activity.get('app_category', 'unknown')
        features[f'app_category_{app_category}'] = 1
        
        return features

    def _extract_behavioral_features(
        self,
        activity: pd.Series,
        behavioral_data: Dict
    ) -> Dict:
        """Extract behavioral patterns and metrics."""
        activity_time = activity['timestamp']
        
        # Get behavioral metrics for the time window
        window_data = {
            k: v for k, v in behavioral_data.items()
            if isinstance(v, (int, float))
        }
        
        # Calculate derived metrics
        productivity = window_data.get('productivity_score', 0)
        distractions = window_data.get('distraction_count', 0)
        tasks_completed = window_data.get('tasks_completed', 0)
        tasks_total = window_data.get('tasks_total', 1)
        
        return {
            'productivity_score': productivity,
            'distraction_level': distractions / 3600,  # per hour
            'task_completion_rate': tasks_completed / tasks_total,
            'communication_frequency': window_data.get('communication_count', 0) / 3600
        }

    def _calculate_intensity(self, activity: pd.Series) -> float:
        """Calculate activity intensity score."""
        base_intensity = activity.get('intensity', 0)
        
        # Adjust intensity based on activity type
        modifiers = {
            'coding': 1.2,
            'meeting': 1.1,
            'reading': 0.8,
            'browsing': 0.6
        }
        
        activity_type = activity.get('type', 'unknown')
        modifier = modifiers.get(activity_type, 1.0)
        
        return base_intensity * modifier
