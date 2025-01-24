from typing import Dict, List, Any
import pandas as pd
import numpy as np
from datetime import datetime
import structlog

logger = structlog.get_logger()

class DataCleaner:
    def __init__(self):
        self.outlier_threshold = 3
        self.missing_threshold = 0.3

    def clean_activity_data(self, data: pd.DataFrame) -> pd.DataFrame:
        try:
            # Remove duplicates
            data = data.drop_duplicates()
            
            # Handle missing values
            data = self._handle_missing_values(data)
            
            # Remove outliers
            data = self._remove_outliers(data)
            
            # Validate data types
            data = self._validate_types(data)
            
            return data
        except Exception as e:
            logger.error("data_cleaning.failed", error=str(e))
            raise

    def _handle_missing_values(self, data: pd.DataFrame) -> pd.DataFrame:
        # Calculate missing ratio
        missing_ratio = data.isnull().sum() / len(data)
        
        # Drop columns with too many missing values
        drop_cols = missing_ratio[missing_ratio > self.missing_threshold].index
        data = data.drop(columns=drop_cols)
        
        # Fill remaining missing values
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        categorical_cols = data.select_dtypes(exclude=[np.number]).columns
        
        data[numeric_cols] = data[numeric_cols].fillna(data[numeric_cols].median())
        data[categorical_cols] = data[categorical_cols].fillna(data[categorical_cols].mode().iloc[0])
        
        return data

    def _remove_outliers(self, data: pd.DataFrame) -> pd.DataFrame:
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            mean = data[col].mean()
            std = data[col].std()
            data = data[abs(data[col] - mean) <= (self.outlier_threshold * std)]
        
        return data

    def _validate_types(self, data: pd.DataFrame) -> pd.DataFrame:
        # Convert timestamp columns
        timestamp_cols = [col for col in data.columns if 'time' in col.lower()]
        for col in timestamp_cols:
            data[col] = pd.to_datetime(data[col])
            
        # Convert numeric columns
        numeric_cols = [col for col in data.columns if any(t in col.lower() for t in ['count', 'duration', 'score'])]
        for col in numeric_cols:
            data[col] = pd.to_numeric(data[col], errors='coerce')
            
        return data
