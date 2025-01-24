from typing import Dict, List, Optional, Tuple
import torch
from torch.utils.data import Dataset, DataLoader
import numpy as np
from clarity.schemas.ml import ProcessedFeatures
import structlog

logger = structlog.get_logger()

class BehaviorDataset(Dataset):
    """Dataset for behavior sequence data."""
    
    def __init__(
        self,
        features: ProcessedFeatures,
        sequence_length: int = 50,
        stride: int = 1
    ):
        self.features = torch.FloatTensor(features.features)
        self.temporal_features = torch.FloatTensor(features.temporal_features)
        self.sequence_length = sequence_length
        self.stride = stride
        
        # Create sequences
        self.sequences = self._create_sequences()

    def __len__(self) -> int:
        return len(self.sequences)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        seq = self.sequences[idx]
        
        # Input sequence and target
        x = seq[:-1]
        y = seq[1:]
        
        return x, y

    def _create_sequences(self) -> List[torch.Tensor]:
        """Create sequences from features."""
        sequences = []
        n_samples = len(self.features)
        
        for i in range(0, n_samples - self.sequence_length, self.stride):
            # Get sequence slice
            sequence = self.features[i:i + self.sequence_length]
            
            # Add temporal features
            temporal = self.temporal_features[i:i + self.sequence_length]
            sequence = torch.cat([sequence, temporal], dim=-1)
            
            sequences.append(sequence)
        
        return sequences

class BehaviorDataLoader:
    """Data loader for behavior data with preprocessing."""
    
    def __init__(
        self,
        batch_size: int = 32,
        sequence_length: int = 50,
        stride: int = 1,
        validation_split: float = 0.2
    ):
        self.batch_size = batch_size
        self.sequence_length = sequence_length
        self.stride = stride
        self.validation_split = validation_split

    def create_dataloaders(
        self,
        features: ProcessedFeatures
    ) -> Tuple[DataLoader, DataLoader]:
        """Create training and validation dataloaders."""
        try:
            # Create dataset
            dataset = BehaviorDataset(
                features,
                self.sequence_length,
                self.stride
            )
            
            # Split into train/val
            train_size = int((1 - self.validation_split) * len(dataset))
            val_size = len(dataset) - train_size
            
            train_dataset, val_dataset = torch.utils.data.random_split(
                dataset, [train_size, val_size]
            )
            
            # Create dataloaders
            train_loader = DataLoader(
                train_dataset,
                batch_size=self.batch_size,
                shuffle=True,
                num_workers=2,
                pin_memory=True
            )
            
            val_loader = DataLoader(
                val_dataset,
                batch_size=self.batch_size,
                shuffle=False,
                num_workers=2,
                pin_memory=True
            )
            
            logger.info(
                "dataloaders.created",
                train_size=len(train_dataset),
                val_size=len(val_dataset),
                batch_size=self.batch_size
            )
            
            return train_loader, val_loader
            
        except Exception as e:
            logger.error("dataloaders.creation_failed", error=str(e))
            raise

    def create_inference_loader(
        self,
        features: ProcessedFeatures
    ) -> DataLoader:
        """Create dataloader for inference."""
        try:
            dataset = BehaviorDataset(
                features,
                self.sequence_length,
                stride=self.sequence_length  # Non-overlapping sequences for inference
            )
            
            return DataLoader(
                dataset,
                batch_size=self.batch_size,
                shuffle=False,
                num_workers=1,
                pin_memory=True
            )
            
        except Exception as e:
            logger.error("inference_loader.creation_failed", error=str(e))
            raise
