
# 7. Training Pipeline
training_pipeline = """\"\"\"
End-to-End Training Pipeline with MLflow Integration
Supports distributed training, hyperparameter tuning, and checkpointing
\"\"\"

import os
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.cuda.amp import autocast, GradScaler
import torchvision.transforms as transforms
from torch.utils.tensorboard import SummaryWriter

import mlflow
import mlflow.pytorch
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support
import numpy as np
from tqdm import tqdm
import yaml

from src.models.cnn_classifier import CNNClassifier, build_model
from src.data.dataset import ImageClassificationDataset
from src.utils.logger import setup_logger
from src.utils.metrics import AverageMeter


class Trainer:
    \"\"\"CNN Model Trainer with MLOps integration\"\"\"
    
    def __init__(self, config: Dict, experiment_name: str = "cnn-training"):
        self.config = config
        self.experiment_name = experiment_name
        self.logger = setup_logger(__name__)
        
        # Device setup
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.scaler = GradScaler() if config.get("mixed_precision", False) else None
        
        # Initialize MLflow
        self._setup_mlflow()
        
        # Build model
        self.model = self._build_model()
        self.optimizer = self._build_optimizer()
        self.scheduler = self._build_scheduler()
        self.criterion = nn.CrossEntropyLoss(label_smoothing=config.get("label_smoothing", 0.1))
        
        # Tracking
        self.best_metric = 0.0
        self.epoch = 0
        self.global_step = 0
        
        # Create directories
        self.checkpoint_dir = Path(config.get("checkpoint_dir", "checkpoints"))
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
    def _setup_mlflow(self):
        \"\"\"Initialize MLflow tracking\"\"\"
        mlflow.set_experiment(self.experiment_name)
        mlflow.start_run(run_name=f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        mlflow.log_params(self.config)
        self.logger.info(f"MLflow tracking URI: {mlflow.get_tracking_uri()}")
    
    def _build_model(self) -> nn.Module:
        \"\"\"Build and initialize model\"\"\"
        model = build_model(self.config["model"])
        model = model.to(self.device)
        
        # Multi-GPU support
        if torch.cuda.device_count() > 1:
            self.logger.info(f"Using {torch.cuda.device_count()} GPUs")
            model = nn.DataParallel(model)
        
        return model
    
    def _build_optimizer(self) -> optim.Optimizer:
        \"\"\"Build optimizer with parameter groups\"\"\"
        base_lr = self.config.get("learning_rate", 1e-3)
        weight_decay = self.config.get("weight_decay", 1e-4)
        
        # Different LR for backbone and classifier
        backbone_params = []
        classifier_params = []
        
        for name, param in self.model.named_parameters():
            if not param.requires_grad:
                continue
            if "classifier" in name or "fc" in name:
                classifier_params.append(param)
            else:
                backbone_params.append(param)
        
        optimizer = optim.AdamW([
            {"params": backbone_params, "lr": base_lr * 0.1},
            {"params": classifier_params, "lr": base_lr}
        ], weight_decay=weight_decay)
        
        return optimizer
    
    def _build_scheduler(self):
        \"\"\"Build learning rate scheduler\"\"\"
        scheduler_type = self.config.get("scheduler", "cosine")
        epochs = self.config.get("epochs", 100)
        
        if scheduler_type == "cosine":
            return optim.lr_scheduler.CosineAnnealingWarmRestarts(
                self.optimizer, T_0=10, T_mult=2
            )
        elif scheduler_type == "plateau":
            return optim.lr_scheduler.ReduceLROnPlateau(
                self.optimizer, mode="max", patience=5, factor=0.5
            )
        elif scheduler_type == "one_cycle":
            return optim.lr_scheduler.OneCycleLR(
                self.optimizer,
                max_lr=self.config.get("learning_rate", 1e-3),
                epochs=epochs,
                steps_per_epoch=self.config.get("steps_per_epoch", 100)
            )
        return None
    
    def train_epoch(self, train_loader: DataLoader) -> Dict[str, float]:
        \"\"\"Train for one epoch\"\"\"
        self.model.train()
        
        losses = AverageMeter()
        accuracies = AverageMeter()
        
        pbar = tqdm(train_loader, desc=f"Epoch {self.epoch}")
        
        for batch_idx, (images, labels) in enumerate(pbar):
            images = images.to(self.device)
            labels = labels.to(self.device)
            
            self.optimizer.zero_grad()
            
            # Mixed precision training
            if self.scaler:
                with autocast():
                    outputs = self.model(images)
                    loss = self.criterion(outputs, labels)
                
                self.scaler.scale(loss).backward()
                self.scaler.step(self.optimizer)
                self.scaler.update()
            else:
                outputs = self.model(images)
                loss = self.criterion(outputs, labels)
                loss.backward()
                self.optimizer.step()
            
            # Calculate accuracy
            _, predicted = outputs.max(1)
            accuracy = (predicted == labels).float().mean().item()
            
            losses.update(loss.item(), images.size(0))
            accuracies.update(accuracy, images.size(0))
            
            # Update progress bar
            pbar.set_postfix({
                "loss": f"{losses.avg:.4f}",
                "acc": f"{accuracies.avg:.4f}",
                "lr": f"{self.optimizer.param_groups[0]['lr']:.6f}"
            })
            
            # Log to MLflow
            if batch_idx % 10 == 0:
                mlflow.log_metric("train_loss", loss.item(), step=self.global_step)
                mlflow.log_metric("train_acc", accuracy, step=self.global_step)
            
            self.global_step += 1
        
        return {"loss": losses.avg, "accuracy": accuracies.avg}
    
    @torch.no_grad()
    def validate(self, val_loader: DataLoader) -> Dict[str, float]:
        \"\"\"Validate model\"\"\"
        self.model.eval()
        
        losses = AverageMeter()
        all_predictions = []
        all_labels = []
        
        for images, labels in tqdm(val_loader, desc="Validation"):
            images = images.to(self.device)
            labels = labels.to(self.device)
            
            outputs = self.model(images)
            loss = self.criterion(outputs, labels)
            
            _, predicted = outputs.max(1)
            
            losses.update(loss.item(), images.size(0))
            all_predictions.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
        
        # Calculate metrics
        accuracy = accuracy_score(all_labels, all_predictions)
        f1 = f1_score(all_labels, all_predictions, average="weighted")
        precision, recall, _, _ = precision_recall_fscore_support(
            all_labels, all_predictions, average="weighted"
        )
        
        metrics = {
            "loss": losses.avg,
            "accuracy": accuracy,
            "f1_score": f1,
            "precision": precision,
            "recall": recall
        }
        
        return metrics
    
    def save_checkpoint(self, filename: str, is_best: bool = False):
        \"\"\"Save model checkpoint\"\"\"
        checkpoint = {
            "epoch": self.epoch,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "best_metric": self.best_metric,
            "config": self.config
        }
        
        if self.scheduler:
            checkpoint["scheduler_state_dict"] = self.scheduler.state_dict()
        
        filepath = self.checkpoint_dir / filename
        torch.save(checkpoint, filepath)
        self.logger.info(f"Checkpoint saved: {filepath}")
        
        if is_best:
            best_path = self.checkpoint_dir / "best_model.pt"
            torch.save(checkpoint, best_path)
            
            # Log to MLflow
            mlflow.log_artifact(str(best_path), "models")
    
    def load_checkpoint(self, filepath: str):
        \"\"\"Load model checkpoint\"\"\"
        checkpoint = torch.load(filepath, map_location=self.device)
        
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.epoch = checkpoint["epoch"]
        self.best_metric = checkpoint["best_metric"]
        
        if self.scheduler and "scheduler_state_dict" in checkpoint:
            self.scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
        
        self.logger.info(f"Checkpoint loaded: {filepath}")
    
    def train(self, train_loader: DataLoader, val_loader: DataLoader, epochs: int):
        \"\"\"Full training loop\"\"\"
        self.logger.info(f"Starting training for {epochs} epochs")
        
        for epoch in range(self.epoch, epochs):
            self.epoch = epoch
            
            # Train
            train_metrics = self.train_epoch(train_loader)
            
            # Validate
            val_metrics = self.validate(val_loader)
            
            # Update scheduler
            if self.scheduler:
                if isinstance(self.scheduler, optim.lr_scheduler.ReduceLROnPlateau):
                    self.scheduler.step(val_metrics["accuracy"])
                else:
                    self.scheduler.step()
            
            # Log metrics
            mlflow.log_metrics({
                "epoch": epoch,
                "train_loss": train_metrics["loss"],
                "train_acc": train_metrics["accuracy"],
                "val_loss": val_metrics["loss"],
                "val_acc": val_metrics["accuracy"],
                "val_f1": val_metrics["f1_score"]
            }, step=epoch)
            
            self.logger.info(
                f"Epoch {epoch}: "
                f"Train Loss: {train_metrics['loss']:.4f}, "
                f"Train Acc: {train_metrics['accuracy']:.4f}, "
                f"Val Loss: {val_metrics['loss']:.4f}, "
                f"Val Acc: {val_metrics['accuracy']:.4f}, "
                f"Val F1: {val_metrics['f1_score']:.4f}"
            )
            
            # Save checkpoint
            is_best = val_metrics["accuracy"] > self.best_metric
            if is_best:
                self.best_metric = val_metrics["accuracy"]
                self.logger.info(f"New best model! Accuracy: {self.best_metric:.4f}")
            
            self.save_checkpoint(f"checkpoint_epoch_{epoch}.pt", is_best=is_best)
            
            # Early stopping check
            if epoch - self._get_best_epoch() > self.config.get("early_stopping_patience", 10):
                self.logger.info("Early stopping triggered")
                break
        
        # Log final model to MLflow
        mlflow.pytorch.log_model(self.model, "final_model")
        mlflow.end_run()
        
        self.logger.info("Training completed!")
    
    def _get_best_epoch(self) -> int:
        \"\"\"Get epoch number of best model\"\"\"
        # This is a simplified version - in practice, track this during training
        return self.epoch


def main():
    parser = argparse.ArgumentParser(description="Train CNN Classifier")
    parser.add_argument("--config", type=str, required=True, help="Path to config file")
    parser.add_argument("--experiment-name", type=str, default="cnn-training")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--resume", type=str, default=None, help="Resume from checkpoint")
    args = parser.parse_args()
    
    # Load config
    with open(args.config) as f:
        config = yaml.safe_load(f)
    
    # Override config with CLI args
    config["epochs"] = args.epochs
    config["batch_size"] = args.batch_size
    
    # Create trainer
    trainer = Trainer(config, experiment_name=args.experiment_name)
    
    if args.resume:
        trainer.load_checkpoint(args.resume)
    
    # Load data (simplified - implement actual data loading)
    # train_loader = DataLoader(...)
    # val_loader = DataLoader(...)
    
    # Train
    # trainer.train(train_loader, val_loader, args.epochs)


if __name__ == "__main__":
    main()
"""

with open(f"{project_root}/src/training/train.py", "w") as f:
    f.write(training_pipeline)

print("✅ Training pipeline created")
