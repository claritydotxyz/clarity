import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple
from clarity.schemas.ml import SequenceOutput, SequencePrediction
import structlog

logger = structlog.get_logger()

class BehaviorSequenceModel(nn.Module):
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        num_layers: int = 2,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # Input projection
        self.input_projection = nn.Linear(input_dim, hidden_dim)
        
        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True
        )
        
        # Output layers
        self.output_projection = nn.Linear(hidden_dim, input_dim)
        self.pattern_classifier = nn.Linear(hidden_dim, hidden_dim)
        self.dropout = nn.Dropout(dropout)
        
        # Pattern attention
        self.pattern_attention = nn.MultiheadAttention(
            embed_dim=hidden_dim,
            num_heads=4,
            dropout=dropout
        )

    def forward(
        self,
        x: torch.Tensor,
        hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None
    ) -> SequenceOutput:
        batch_size, seq_length, _ = x.size()
        
        # Project input
        projected = self.input_projection(x)
        projected = self.dropout(projected)
        
        # LSTM forward pass
        lstm_out, hidden = self.lstm(projected, hidden)
        
        # Apply pattern attention
        attended, attention_weights = self.pattern_attention(
            lstm_out,
            lstm_out,
            lstm_out
        )
        
        # Generate predictions
        predictions = self.output_projection(attended)
        
        # Classify patterns
        pattern_features = self.pattern_classifier(attended)
        
        return SequenceOutput(
            predictions=predictions,
            hidden_states=hidden,
            attention_weights=attention_weights,
            pattern_features=pattern_features
        )

    def predict_next(
        self,
        sequence: torch.Tensor,
        n_steps: int = 1
    ) -> List[SequencePrediction]:
        self.eval()
        predictions = []
        current_sequence = sequence
        hidden = None
        
        with torch.no_grad():
            for _ in range(n_steps):
                # Get prediction for next step
                output = self.forward(current_sequence, hidden)
                next_step = output.predictions[:, -1:]
                hidden = output.hidden_states
                
                # Calculate prediction confidence
                attention_scores = output.attention_weights[:, -1]
                confidence = torch.mean(attention_scores).item()
                
                predictions.append(SequencePrediction(
                    value=next_step.squeeze().cpu().numpy(),
                    confidence=confidence,
                    attention_weights=attention_scores.cpu().numpy()
                ))
                
                # Update sequence for next prediction
                current_sequence = torch.cat([current_sequence[:, 1:], next_step], dim=1)
        
        return predictions

    def detect_patterns(
        self,
        sequence: torch.Tensor,
        pattern_threshold: float = 0.7
    ) -> Dict[str, List[int]]:
        self.eval()
        patterns = {
            "repetitive": [],
            "unusual": [],
            "trending": []
        }
        
        with torch.no_grad():
            # Forward pass through the sequence
            output = self.forward(sequence)
            
            # Analyze pattern features
            pattern_features = output.pattern_features.squeeze()
            attention_weights = output.attention_weights.squeeze()
            
            # Detect repetitive patterns
            for i in range(1, len(pattern_features)):
                similarity = torch.cosine_similarity(
                    pattern_features[i:i+1],
                    pattern_features[i-1:i],
                    dim=0
                )
                if similarity > pattern_threshold:
                    patterns["repetitive"].append(i)
            
            # Detect unusual patterns
            mean_features = torch.mean(pattern_features, dim=0)
            for i, features in enumerate(pattern_features):
                distance = torch.norm(features - mean_features)
                if distance > pattern_threshold:
                    patterns["unusual"].append(i)
            
            # Detect trending patterns
            for i in range(2, len(pattern_features)):
                if (torch.all(pattern_features[i] > pattern_features[i-1]) and
                    torch.all(pattern_features[i-1] > pattern_features[i-2])):
                    patterns["trending"].append(i)
        
        return patterns

    def encode_sequence(self, sequence: torch.Tensor) -> torch.Tensor:
        """Encode sequence into latent representation."""
        self.eval()
        with torch.no_grad():
            output = self.forward(sequence)
            return output.pattern_features
