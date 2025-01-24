from typing import Dict, List, Optional
import torch
import numpy as np
from datetime import datetime, timedelta
from clarity.ml.models.sequence import BehaviorSequenceModel
from clarity.schemas.ml import PredictionResult, TimeSeriesPrediction
import structlog

logger = structlog.get_logger()

class BehaviorPredictor:
    """Predicts future behavior patterns."""
    
    def __init__(
        self,
        model: BehaviorSequenceModel,
        prediction_horizon: int = 24,  # hours
        uncertainty_estimation: bool = True,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.model = model.to(device)
        self.prediction_horizon = prediction_horizon
        self.uncertainty_estimation = uncertainty_estimation
        self.device = device
        
        self.model.eval()

    async def predict_future(
        self,
        current_sequence: torch.Tensor,
        timestamp: datetime
    ) -> PredictionResult:
        """Generate future behavior predictions."""
        try:
            current_sequence = current_sequence.to(self.device)
            
            with torch.no_grad():
                # Generate predictions
                predictions = []
                uncertainties = []
                current_input = current_sequence
                
                for hour in range(self.prediction_horizon):
                    # Get prediction
                    output = self.model(current_input)
                    next_step = output.predictions[:, -1:]
                    
                    # Calculate uncertainty if enabled
                    if self.uncertainty_estimation:
                        uncertainty = self._estimate_uncertainty(
                            current_input,
                            output
                        )
                        uncertainties.append(uncertainty)
                    
                    # Add to predictions
                    predictions.append(
                        TimeSeriesPrediction(
                            timestamp=timestamp + timedelta(hours=hour),
                            value=next_step.cpu().numpy(),
                            confidence=float(output.attention_weights.mean()),
                            uncertainty=uncertainty if uncertainties else None
                        )
                    )
                    
                    # Update input sequence
                    current_input = torch.cat(
                        [current_input[:, 1:], next_step],
                        dim=1
                    )
                
                return PredictionResult(
                    predictions=predictions,
                    metadata={
                        'model_version': getattr(self.model, 'version', 'unknown'),
                        'prediction_horizon': self.prediction_horizon,
                        'average_uncertainty': np.mean(uncertainties) if uncertainties else None
                    }
                )
                
        except Exception as e:
            logger.error("predictor.prediction_failed", error=str(e))
            raise

    def _estimate_uncertainty(
        self,
        sequence: torch.Tensor,
        output
    ) -> float:
        """Estimate prediction uncertainty using attention patterns."""
        attention_weights = output.attention_weights
        pattern_features = output.pattern_features
        
        # Calculate uncertainty from attention stability
        attention_stability = 1 - torch.std(attention_weights) / torch.mean(attention_weights)
        
        # Calculate uncertainty from pattern strength
        pattern_strength = torch.mean(torch.abs(pattern_features))
        
        # Combine uncertainties
        uncertainty = 1 - (attention_stability * pattern_strength)
        return float(uncertainty)
