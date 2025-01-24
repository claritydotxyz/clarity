from typing import Dict, List, Optional
import torch
from datetime import datetime
from clarity.ml.models.sequence import BehaviorSequenceModel
from clarity.ml.features.extractors import FeatureExtractor
from clarity.ml.features.processors import FeatureProcessor
from clarity.schemas.ml import InferencePipeline, InferenceResult
import structlog

logger = structlog.get_logger()

class BehaviorInferencePipeline:
    """Pipeline for running inference on behavior data."""
    
    def __init__(
        self,
        model: BehaviorSequenceModel,
        feature_extractor: FeatureExtractor,
        feature_processor: FeatureProcessor,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.model = model.to(device)
        self.feature_extractor = feature_extractor
        self.feature_processor = feature_processor
        self.device = device
        
        self.model.eval()
        
    async def predict(
        self,
        activities: Dict,
        behavioral_data: Dict
    ) -> InferenceResult:
        """Run inference pipeline on new data."""
        try:
            # Extract features
            features = self.feature_extractor.extract_features(
                activities,
                behavioral_data
            )
            
            # Process features
            processed_features = self.feature_processor.process_features(
                features,
                fit=False
            )
            
            # Convert to tensor
            x = torch.FloatTensor(processed_features.features).unsqueeze(0)
            x = x.to(self.device)
            
            # Run inference
            with torch.no_grad():
                output = self.model(x)
                predictions = output.predictions.cpu().numpy()
                pattern_features = output.pattern_features.cpu().numpy()
                
                # Detect patterns
                patterns = self.model.detect_patterns(x)
            
            return InferenceResult(
                timestamp=datetime.utcnow(),
                predictions=predictions,
                patterns=patterns,
                feature_importance=self._calculate_feature_importance(
                    pattern_features
                ),
                metadata={
                    'model_version': getattr(self.model, 'version', 'unknown'),
                    'confidence_score': self._calculate_confidence(output)
                }
            )
            
        except Exception as e:
            logger.error("inference.pipeline_failed", error=str(e))
            raise

    def _calculate_feature_importance(
        self,
        pattern_features: np.ndarray
    ) -> Dict[str, float]:
        """Calculate feature importance scores."""
        try:
            # Use pattern features to determine importance
            importance_scores = np.mean(np.abs(pattern_features), axis=0)
            feature_names = self.feature_extractor.time_features + \
                          self.feature_extractor.activity_features + \
                          self.feature_extractor.behavioral_features
            
            return {
                name: float(score)
                for name, score in zip(feature_names, importance_scores)
            }
        except Exception:
            return {}

    def _calculate_confidence(self, output) -> float:
        """Calculate confidence score for predictions."""
        attention_weights = output.attention_weights
        pattern_strength = np.mean(output.pattern_features)
        
        # Combine attention and pattern strength
        confidence = (np.mean(attention_weights) + pattern_strength) / 2
        return float(confidence)
