from typing import Dict, Optional, Tuple
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm
from clarity.ml.models.sequence import BehaviorSequenceModel
from clarity.utils.monitoring.metrics import (
    training_loss_gauge,
    validation_loss_gauge,
    training_duration_histogram
)
import structlog

logger = structlog.get_logger()

class SequenceTrainer:
    """Trainer for behavior sequence models."""
    
    def __init__(
        self,
        model: BehaviorSequenceModel,
        learning_rate: float = 1e-3,
        weight_decay: float = 1e-5,
        clip_grad_norm: float = 1.0,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.model = model.to(device)
        self.device = device
        self.clip_grad_norm = clip_grad_norm
        
        self.criterion = nn.MSELoss()
        self.optimizer = torch.optim.Adam(
            model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )
        
        self.best_val_loss = float('inf')
        self.best_model_state = None

    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        num_epochs: int = 100,
        patience: int = 10,
        checkpoint_dir: Optional[str] = None
    ) -> Dict:
        """Train the model."""
        train_losses = []
        val_losses = []
        epochs_without_improvement = 0
        
        try:
            for epoch in range(num_epochs):
                # Training phase
                self.model.train()
                train_loss = self._train_epoch(train_loader)
                train_losses.append(train_loss)
                training_loss_gauge.set(train_loss)
                
                # Validation phase
                self.model.eval()
                val_loss = self._validate(val_loader)
                val_losses.append(val_loss)
                validation_loss_gauge.set(val_loss)
                
                # Log progress
                logger.info(
                    "training.epoch_completed",
                    epoch=epoch,
                    train_loss=train_loss,
                    val_loss=val_loss
                )
                
                # Check for improvement
                if val_loss < self.best_val_loss:
                    self.best_val_loss = val_loss
                    self.best_model_state = self.model.state_dict()
                    epochs_without_improvement = 0
                    
                    # Save checkpoint
                    if checkpoint_dir:
                        self._save_checkpoint(checkpoint_dir, epoch, val_loss)
                else:
                    epochs_without_improvement += 1
                
                # Early stopping
                if epochs_without_improvement >= patience:
                    logger.info(
                        "training.early_stopping",
                        epoch=epoch,
                        best_val_loss=self.best_val_loss
                    )
                    break
            
            # Restore best model
            if self.best_model_state is not None:
                self.model.load_state_dict(self.best_model_state)
            
            return {
                'train_losses': train_losses,
                'val_losses': val_losses,
                'best_val_loss': self.best_val_loss,
                'epochs_completed': epoch + 1
            }
            
        except Exception as e:
            logger.error("training.failed", error=str(e))
            raise

    def _train_epoch(self, train_loader: DataLoader) -> float:
        """Train for one epoch."""
        epoch_loss = 0.0
        num_batches = len(train_loader)
        
        for batch_idx, (x, y) in enumerate(tqdm(train_loader)):
            x = x.to(self.device)
            y = y.to(self.device)
            
            # Forward pass
            self.optimizer.zero_grad()
            output = self.model(x)
            loss = self.criterion(output.predictions, y)
            
            # Backward pass
            loss.backward()
            
            # Gradient clipping
            if self.clip_grad_norm > 0:
                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(),
                    self.clip_grad_norm
                )
            
            self.optimizer.step()
            epoch_loss += loss.item()
        
        return epoch_loss / num_batches

    def _validate(self, val_loader: DataLoader) -> float:
        """Validate the model."""
        val_loss = 0.0
        num_batches = len(val_loader)
        
        with torch.no_grad():
            for x, y in val_loader:
                x = x.to(self.device)
                y = y.to(self.device)
                
                output = self.model(x)
                loss = self.criterion(output.predictions, y)
                val_loss += loss.item()
        
        return val_loss / num_batches

    def _save_checkpoint(
        self,
        checkpoint_dir: str,
        epoch: int,
        val_loss: float
    ):
        """Save model checkpoint."""
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'val_loss': val_loss,
            'model_config': {
                'input_dim': self.model.input_dim,
                'hidden_dim': self.model.hidden_dim,
                'num_layers': self.model.num_layers
            }
        }
        
        path = f"{checkpoint_dir}/model_epoch{epoch}_loss{val_loss:.4f}.pt"
        torch.save(checkpoint, path)
        logger.info("checkpoint.saved", path=path)

class OnlineTrainer(SequenceTrainer):
    """Trainer for online learning and model updates."""
    
    def __init__(self, *args, update_frequency: int = 100, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_frequency = update_frequency
        self.samples_since_update = 0
        self.accumulated_loss = 0.0

    def update(self, new_data: DataLoader) -> Dict:
        """Update model with new data."""
        self.samples_since_update += len(new_data.dataset)
        
        if self.samples_since_update >= self.update_frequency:
            update_loss = self._train_epoch(new_data)
            self.accumulated_loss += update_loss
            
            # Reset counters
            self.samples_since_update = 0
            accumulated_loss = self.accumulated_loss
            self.accumulated_loss = 0.0
            
            return {
                'updated': True,
                'loss': accumulated_loss,
                'samples_processed': self.update_frequency
            }
        
        return {
            'updated': False,
            'samples_pending': self.update_frequency - self.samples_since_update
        }
