from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import structlog

logger = structlog.get_logger()

class DataNormalizer:
    def __init__(self, method: str = 'standard'):
        self.method = method
        self.scalers: Dict[str, Any] = {}

    def normalize_data(
        self,
        data: pd.DataFrame,
        columns: Optional[List[str]] = None,
        fit: bool = True
    ) -> pd.DataFrame:
        try:
            # Determine columns to normalize
            if columns is None:
                columns = data.select_dtypes(include=[np.number]).columns
                
            normalized_data = data.copy()
            
            for col in columns:
                if fit or col not in self.scalers:
                    scaler = (StandardScaler() if self.method == 'standard' 
                            else MinMaxScaler())
                    normalized_data[col] = scaler.fit_transform(
                        data[col].values.reshape(-1, 1)
                    )
                    self.scalers[col] = scaler
                else:
                    normalized_data[col] = self.scalers[col].transform(
                        data[col].values.reshape(-1, 1)
                    )
            
            return normalized_data
        
        except Exception as e:
            logger.error("data_normalization.failed", error=str(e))
            raise

    def denormalize(
        self,
        data: pd.DataFrame,
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        try:
            if columns is None:
                columns = [col for col in data.columns if col in self.scalers]
                
            denormalized_data = data.copy()
            
            for col in columns:
                if col in self.scalers:
                    denormalized_data[col] = self.scalers[col].inverse_transform(
                        data[col].values.reshape(-1, 1)
                    )
            
            return denormalized_data
            
        except Exception as e:
            logger.error("data_denormalization.failed", error=str(e))
            raise

    def save_scalers(self, path: str):
        """Save scalers to file."""
        import joblib
        joblib.dump(self.scalers, path)
        logger.info("scalers.saved", path=path)

    def load_scalers(self, path: str):
        """Load scalers from file."""
        import joblib
        self.scalers = joblib.load(path)
        logger.info("scalers.loaded", path=path)
