"""
model_builder.py
----------------
Builds the CNN classification model with a choice of backbone.

Supported backbones:
    "resnet50_places365"   — ResNet50 pre-trained on Places365 (BEST for KemasLah)
    "efficientnet_b4"      — EfficientNet-B4 pre-trained on ImageNet (via timm)
    "mobilenetv3_large"    — Lightweight, fast inference (via timm)
    "convnext_tiny"        — Modern ConvNeXt-Tiny (via timm)

The classifier head is replaced with a custom 10-class head
matching KemasLah's sorting categories.

Usage:
    from src.models.model_builder import build_model
    model = build_model(config)
"""

import torch
import torch.nn as nn
import timm

from src.data.category_mapper import NUM_CLASSES


# ─────────────────────────────────────────────────────────────
# Places365 ResNet50 — custom loader (not in timm by default)
# ─────────────────────────────────────────────────────────────
def _load_places365_resnet50(num_classes: int, dropout: float) -> nn.Module:
    """
    Load ResNet50 pre-trained on Places365.

    The pre-trained weights file must be downloaded manually:
        URL: http://places2.csail.mit.edu/models_places365/resnet50_places365.pth.tar
        Save to: models/pretrained/resnet50_places365.pth.tar

    If the weight file is not found, falls back to ImageNet ResNet50 from torchvision.
    """
    import torchvision.models as tv_models
    import os

    weight_path = "models/pretrained/resnet50_places365.pth.tar"
    model = tv_models.resnet50(weights=None)

    if os.path.exists(weight_path):
        print(f"Loading Places365 weights from: {weight_path}")
        checkpoint = torch.load(weight_path, map_location="cpu")

        # Places365 checkpoint stores weights under the key 'state_dict'
        state_dict = checkpoint.get("state_dict", checkpoint)

        # Strip 'module.' prefix added by DataParallel training
        cleaned = {k.replace("module.", ""): v for k, v in state_dict.items()}

        # ── FIX: explicitly remove the fc (classifier) keys before loading ──
        # The checkpoint fc is shaped [365, 2048] (Places365 classes).
        # Our model fc is [1000, 2048] (default ImageNet init).
        # PyTorch 2.1+ raises RuntimeError on size mismatches even with
        # strict=False — so we strip the fc keys entirely and replace
        # the head ourselves in the next block below.
        backbone_weights = {
            k: v for k, v in cleaned.items()
            if not k.startswith("fc.")
        }

        # Load backbone-only weights — all keys present, no size mismatches
        missing, unexpected = model.load_state_dict(backbone_weights, strict=False)
        print(f"Places365 backbone weights loaded.")
        print(f"  Layers loaded : {len(backbone_weights)}")
        print(f"  Missing keys  : {len(missing)}  (fc head — expected, will be replaced)")
        print(f"  Unexpected    : {len(unexpected)}")
    else:
        print(
            f"[WARN] Places365 weights not found at '{weight_path}'.\n"
            f"       Falling back to ImageNet pretrained ResNet50.\n"
            f"       Download weights from:\n"
            f"       http://places2.csail.mit.edu/models_places365/resnet50_places365.pth.tar"
        )
        model = tv_models.resnet50(weights="IMAGENET1K_V2")

    # Replace the final fully-connected layer with our custom 10-class head
    # in_features is always 2048 for ResNet50 regardless of what fc was before
    in_features = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Dropout(p=dropout),
        nn.Linear(in_features, num_classes),
    )
    print(f"Custom classification head attached: 2048 → {num_classes} classes")
    return model


# ─────────────────────────────────────────────────────────────
# timm-based backbones
# ─────────────────────────────────────────────────────────────
def _load_timm_model(model_name: str, num_classes: int, dropout: float) -> nn.Module:
    """
    Load any timm model with a custom classification head.

    timm model names:
        EfficientNet-B4  → "efficientnet_b4"
        MobileNetV3-Large → "mobilenetv3_large_100"
        ConvNeXt-Tiny    → "convnext_tiny"
    """
    timm_name_map = {
        "efficientnet_b4":   "efficientnet_b4",
        "mobilenetv3_large": "mobilenetv3_large_100",
        "convnext_tiny":     "convnext_tiny",
    }
    resolved = timm_name_map.get(model_name, model_name)
    print(f"Loading timm model: {resolved} (pretrained=True)")

    model = timm.create_model(
        resolved,
        pretrained=True,
        num_classes=0,         # Remove the original head
        drop_rate=dropout,
    )

    # Get the output feature dimension
    with torch.no_grad():
        dummy = torch.zeros(1, 3, 224, 224)
        feat_dim = model(dummy).shape[-1]

    # Attach the KemasLah classification head
    model.head = nn.Sequential(
        nn.Dropout(p=dropout),
        nn.Linear(feat_dim, num_classes),
    )
    # Forward pass needs to use the new head
    original_forward = model.forward

    def new_forward(x):
        features = original_forward(x)
        return model.head(features)

    model.forward = new_forward
    return model


# ─────────────────────────────────────────────────────────────
# Backbone freezing
# ─────────────────────────────────────────────────────────────
def freeze_backbone(model: nn.Module, backbone_name: str) -> None:
    """
    Freeze all layers except the classification head.
    Call this for the first N epochs (as set in config freeze_backbone_epochs).
    This lets the new head stabilise before fine-tuning the whole network.
    """
    if backbone_name == "resnet50_places365":
        for name, param in model.named_parameters():
            if "fc" not in name:
                param.requires_grad = False
    else:
        # timm models: freeze everything except .head
        for name, param in model.named_parameters():
            if "head" not in name:
                param.requires_grad = False

    frozen = sum(1 for p in model.parameters() if not p.requires_grad)
    total  = sum(1 for p in model.parameters())
    print(f"Backbone frozen: {frozen}/{total} parameter groups locked.")


def unfreeze_all(model: nn.Module) -> None:
    """Unfreeze all layers for full fine-tuning."""
    for param in model.parameters():
        param.requires_grad = True
    print("All layers unfrozen — full fine-tuning enabled.")


# ─────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────
def build_model(config: dict) -> nn.Module:
    """
    Build and return the CNN model specified in config.

    Args:
        config: Parsed training_config.yaml dict

    Returns:
        nn.Module ready for training
    """
    backbone = config["model"]["backbone"]
    dropout  = config["model"]["dropout"]

    print(f"\nBuilding model: backbone={backbone}, num_classes={NUM_CLASSES}, dropout={dropout}")

    if backbone == "resnet50_places365":
        model = _load_places365_resnet50(NUM_CLASSES, dropout)
    elif backbone in ("efficientnet_b4", "mobilenetv3_large", "convnext_tiny"):
        model = _load_timm_model(backbone, NUM_CLASSES, dropout)
    else:
        raise ValueError(
            f"Unknown backbone: '{backbone}'. "
            f"Choose from: resnet50_places365, efficientnet_b4, mobilenetv3_large, convnext_tiny"
        )

    # Print parameter count
    total   = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Parameters: total={total:,} | trainable={trainable:,}")

    return model


def get_model_info(model: nn.Module) -> dict:
    """Return a summary dict of the model."""
    total     = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return {
        "total_params":     total,
        "trainable_params": trainable,
        "frozen_params":    total - trainable,
    }
