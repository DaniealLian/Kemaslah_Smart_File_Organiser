"""
trainer.py
----------
Full training loop for the KemasLah CNN model.

Features:
  - Cosine annealing LR scheduler
  - Backbone freeze → unfreeze strategy
  - Early stopping
  - Mixed-precision (AMP) training
  - Gradient clipping
  - TensorBoard logging
  - Per-class accuracy reporting
  - Best model checkpointing

Usage:
    from src.training.trainer import Trainer
    trainer = Trainer(model, train_loader, val_loader, config)
    trainer.train()
"""

import os
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.tensorboard import SummaryWriter
from torch.cuda.amp import GradScaler, autocast
from tqdm import tqdm

from src.models.model_builder import freeze_backbone, unfreeze_all
from src.data.category_mapper import IDX_TO_LABEL, NUM_CLASSES


class EarlyStopping:
    """Stop training when validation loss stops improving."""

    def __init__(self, patience: int = 7, min_delta: float = 0.001):
        self.patience   = patience
        self.min_delta  = min_delta
        self.best_loss  = float("inf")
        self.counter    = 0
        self.stop       = False

    def step(self, val_loss: float) -> bool:
        if val_loss < self.best_loss - self.min_delta:
            self.best_loss = val_loss
            self.counter   = 0
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.stop = True
        return self.stop


class Trainer:
    def __init__(self, model: nn.Module, train_loader, val_loader, config: dict):
        self.model        = model
        self.train_loader = train_loader
        self.val_loader   = val_loader
        self.config       = config
        self.device       = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.use_amp      = config["training"]["mixed_precision"] and self.device.type == "cuda"

        print(f"Training on: {self.device} | AMP: {self.use_amp}")

        self.model.to(self.device)

        # Loss: label smoothing improves generalisation
        self.criterion = nn.CrossEntropyLoss(label_smoothing=0.1)

        # Optimiser — AdamW is better than vanilla Adam for fine-tuning
        self.optimizer = optim.AdamW(
            filter(lambda p: p.requires_grad, model.parameters()),
            lr=config["training"]["learning_rate"],
            weight_decay=config["training"]["weight_decay"],
        )

        total_epochs = config["training"]["epochs"]
        if config["training"]["scheduler"] == "cosine":
            self.scheduler = optim.lr_scheduler.CosineAnnealingLR(
                self.optimizer, T_max=total_epochs, eta_min=1e-6
            )
        elif config["training"]["scheduler"] == "step":
            self.scheduler = optim.lr_scheduler.StepLR(
                self.optimizer, step_size=10, gamma=0.5
            )
        else:  # plateau
            self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
                self.optimizer, mode="min", patience=3, factor=0.5
            )

        self.scaler        = GradScaler(enabled=self.use_amp)
        self.early_stop    = EarlyStopping(patience=config["training"]["early_stopping_patience"])
        self.grad_clip     = config["training"]["gradient_clip"]
        self.freeze_epochs = config["model"]["freeze_backbone_epochs"]
        self.backbone_name = config["model"]["backbone"]

        # Paths
        self.best_model_path = Path(config["paths"]["best_model"])
        self.best_model_path.parent.mkdir(parents=True, exist_ok=True)

        log_dir = Path(config["paths"]["logs"]) / f"run_{int(time.time())}"
        self.writer = SummaryWriter(log_dir=str(log_dir))
        print(f"TensorBoard logs: {log_dir}  (run: tensorboard --logdir={config['paths']['logs']})")

        self.best_val_acc = 0.0

    # ─────────────────────────────────────────────────────────────
    # One epoch
    # ─────────────────────────────────────────────────────────────
    def _run_epoch(self, loader, is_train: bool) -> tuple[float, float]:
        self.model.train(is_train)
        total_loss, correct, total = 0.0, 0, 0

        prefix = "Train" if is_train else "Val"
        bar = tqdm(loader, desc=f"  {prefix}", leave=False, ncols=90)

        for images, labels in bar:
            images = images.to(self.device, non_blocking=True)
            labels = labels.to(self.device, non_blocking=True)

            with autocast(enabled=self.use_amp):
                outputs = self.model(images)
                loss    = self.criterion(outputs, labels)

            if is_train:
                self.optimizer.zero_grad(set_to_none=True)
                self.scaler.scale(loss).backward()
                self.scaler.unscale_(self.optimizer)
                nn.utils.clip_grad_norm_(self.model.parameters(), self.grad_clip)
                self.scaler.step(self.optimizer)
                self.scaler.update()

            total_loss += loss.item() * images.size(0)
            preds      = outputs.argmax(dim=1)
            correct    += (preds == labels).sum().item()
            total      += images.size(0)

            bar.set_postfix(loss=f"{loss.item():.3f}", acc=f"{correct/total:.3f}")

        bar.close()
        return total_loss / total, correct / total

    # ─────────────────────────────────────────────────────────────
    # Per-class accuracy (run on val set after each epoch)
    # ─────────────────────────────────────────────────────────────
    @torch.no_grad()
    def _per_class_accuracy(self) -> dict[str, float]:
        class_correct = [0] * NUM_CLASSES
        class_total   = [0] * NUM_CLASSES
        self.model.eval()
        for images, labels in self.val_loader:
            images = images.to(self.device)
            labels = labels.to(self.device)
            preds  = self.model(images).argmax(dim=1)
            for pred, label in zip(preds, labels):
                class_total[label.item()]   += 1
                class_correct[label.item()] += (pred == label).item()
        return {
            IDX_TO_LABEL[i]: (class_correct[i] / class_total[i] if class_total[i] else 0.0)
            for i in range(NUM_CLASSES)
        }

    # ─────────────────────────────────────────────────────────────
    # Main training loop
    # ─────────────────────────────────────────────────────────────
    def train(self) -> None:
        epochs = self.config["training"]["epochs"]

        # Phase 1: freeze backbone for faster head warm-up
        freeze_backbone(self.model, self.backbone_name)

        for epoch in range(1, epochs + 1):
            epoch_start = time.time()

            # Phase transition: unfreeze at freeze_backbone_epochs
            if epoch == self.freeze_epochs + 1:
                print(f"\nEpoch {epoch}: Unfreezing backbone for full fine-tuning...")
                unfreeze_all(self.model)

                # Rebuild optimizer with differential LRs:
                # backbone gets 10x smaller LR to avoid destroying pretrained features
                # head gets full LR to continue learning fast
                self.optimizer = optim.AdamW([
                    {"params": [p for n, p in self.model.named_parameters()
                                if "fc" not in n and "head" not in n],
                     "lr": self.config["training"]["learning_rate"] * 0.1},
                    {"params": [p for n, p in self.model.named_parameters()
                                if "fc" in n or "head" in n],
                     "lr": self.config["training"]["learning_rate"]},
                ], weight_decay=self.config["training"]["weight_decay"])

                # ── CRITICAL FIX: rebuild the scheduler with the new optimizer ──
                # Without this the old scheduler tracked the old optimizer object,
                # so the new optimizer's LR never decayed — causing the flat LR
                # at 1.00e-05 seen in the previous training run.
                remaining_epochs = epochs - epoch
                scheduler_type   = self.config["training"]["scheduler"]
                if scheduler_type == "cosine":
                    self.scheduler = optim.lr_scheduler.CosineAnnealingLR(
                        self.optimizer, T_max=remaining_epochs, eta_min=1e-6
                    )
                elif scheduler_type == "step":
                    self.scheduler = optim.lr_scheduler.StepLR(
                        self.optimizer, step_size=5, gamma=0.5
                    )
                else:
                    self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
                        self.optimizer, mode="min", patience=3, factor=0.5
                    )
                print(f"  Scheduler rebuilt for remaining {remaining_epochs} epochs.")
                print(f"  Backbone LR: {self.config['training']['learning_rate'] * 0.1:.2e}")
                print(f"  Head LR    : {self.config['training']['learning_rate']:.2e}")

            train_loss, train_acc = self._run_epoch(self.train_loader, is_train=True)
            val_loss,   val_acc   = self._run_epoch(self.val_loader,   is_train=False)

            # Scheduler step
            if isinstance(self.scheduler, optim.lr_scheduler.ReduceLROnPlateau):
                self.scheduler.step(val_loss)
            else:
                self.scheduler.step()

            elapsed = time.time() - epoch_start
            current_lr = self.optimizer.param_groups[0]["lr"]

            print(
                f"Epoch {epoch:03d}/{epochs} | "
                f"Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} | "
                f"Val Loss: {val_loss:.4f} Acc: {val_acc:.4f} | "
                f"LR: {current_lr:.2e} | {elapsed:.0f}s"
            )

            # TensorBoard logging
            self.writer.add_scalars("Loss",     {"train": train_loss, "val": val_loss}, epoch)
            self.writer.add_scalars("Accuracy", {"train": train_acc,  "val": val_acc},  epoch)
            self.writer.add_scalar("LearningRate", current_lr, epoch)

            # Per-class accuracy every 5 epochs
            if epoch % 5 == 0:
                class_accs = self._per_class_accuracy()
                print("  Per-class accuracy:")
                for cat, acc in class_accs.items():
                    print(f"    {cat:<30} {acc:.3f}")
                    self.writer.add_scalar(f"ClassAcc/{cat}", acc, epoch)

            # Save best model
            if val_acc > self.best_val_acc:
                self.best_val_acc = val_acc
                torch.save({
                    "epoch":        epoch,
                    "model_state":  self.model.state_dict(),
                    "val_acc":      val_acc,
                    "config":       self.config,
                }, self.best_model_path)
                print(f"  ✓ Best model saved (val_acc={val_acc:.4f})")

            # Early stopping
            if self.early_stop.step(val_loss):
                print(f"Early stopping triggered at epoch {epoch}.")
                break

        self.writer.close()
        print(f"\nTraining complete. Best val accuracy: {self.best_val_acc:.4f}")
        print(f"Best model saved to: {self.best_model_path}")
