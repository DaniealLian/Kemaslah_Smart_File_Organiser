"""
classifier.py
-------------
The inference engine for KemasLah.
Loads the trained CNN model and classifies image files
returning a KemasLah sorting category + confidence score.

This is the component that the KemasLah application (Flask backend)
calls during the Smart Organise feature.

Usage:
    from src.inference.classifier import ImageClassifier
    classifier = ImageClassifier("models/trained/best_model.pth")

    result = classifier.classify("C:/Users/User/Downloads/photo.jpg")
    # → {"category": "Vacation_Travel", "confidence": 0.91, "top3": [...]}

    results = classifier.classify_batch(["img1.jpg", "img2.jpg"])
"""

import os
from pathlib import Path
from typing import Union

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

from src.data.augmentation import get_inference_transforms
from src.data.category_mapper import IDX_TO_LABEL, NUM_CLASSES, KEMASLAH_CATEGORIES
from src.models.model_builder import build_model


# File extensions this classifier will process
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".heic", ".tiff"}
VIDEO_EXTENSIONS     = {".mp4", ".mov", ".avi", ".mkv", ".wmv"}


class ImageClassifier:
    """
    Loads the trained CNN and classifies image files.
    Thread-safe for use in a Flask web server.
    """

    def __init__(
        self,
        model_path: str,
        device: str = "auto",
        confidence_threshold: float = 0.55,
        fallback_category: str = "Screenshots_Documents",
    ):
        self.confidence_threshold = confidence_threshold
        self.fallback_category    = fallback_category
        self.transform            = get_inference_transforms(image_size=224)

        # Device selection
        if device == "auto":
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        # Load checkpoint
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model checkpoint not found: {model_path}\n"
                f"Run train.py first to generate the model."
            )

        print(f"Loading model from: {model_path} (device: {self.device})")
        checkpoint = torch.load(model_path, map_location=self.device)

        config = checkpoint["config"]
        self.model = build_model(config)
        self.model.load_state_dict(checkpoint["model_state"])
        self.model.to(self.device)
        self.model.eval()

        print(f"Model loaded. Training val_acc: {checkpoint.get('val_acc', 'N/A'):.4f}")

    def _preprocess(self, image_path: str) -> torch.Tensor:
        """Load and preprocess a single image into a model-ready tensor."""
        try:
            img = Image.open(image_path).convert("RGB")
        except Exception as e:
            raise IOError(f"Cannot open image: {image_path} — {e}")

        img_np    = np.array(img)
        augmented = self.transform(image=img_np)
        tensor    = augmented["image"].unsqueeze(0)  # Add batch dimension → [1, 3, H, W]
        return tensor.to(self.device)

    @torch.no_grad()
    def classify(self, image_path: str) -> dict:
        """
        Classify a single image file.

        Returns:
            {
                "category":   "Vacation_Travel",
                "confidence": 0.91,
                "accepted":   True,    # False if below confidence_threshold
                "top3":       [("Vacation_Travel", 0.91), ("Nature_Outdoors", 0.06), ...]
            }
        """
        tensor  = self._preprocess(image_path)
        logits  = self.model(tensor)
        probs   = F.softmax(logits, dim=1)[0].cpu().numpy()

        top3_idx  = probs.argsort()[::-1][:3]
        top3      = [(IDX_TO_LABEL[i], float(probs[i])) for i in top3_idx]
        best_cat, best_conf = top3[0]

        # If confidence is below threshold, use fallback category
        accepted = best_conf >= self.confidence_threshold
        category = best_cat if accepted else self.fallback_category

        return {
            "category":    category,
            "confidence":  best_conf,
            "accepted":    accepted,
            "top3":        top3,
            "file_path":   str(image_path),
        }

    @torch.no_grad()
    def classify_batch(self, image_paths: list[str], batch_size: int = 32) -> list[dict]:
        """
        Classify a list of image files efficiently using batched inference.
        Skips unsupported file types.

        Returns:
            List of classification result dicts (same structure as classify()).
        """
        results = []
        valid   = [(p, Path(p).suffix.lower()) for p in image_paths
                   if Path(p).suffix.lower() in SUPPORTED_EXTENSIONS]

        print(f"Classifying {len(valid)}/{len(image_paths)} supported images...")

        for i in range(0, len(valid), batch_size):
            batch_paths = valid[i:i + batch_size]

            tensors     = []   # one tensor per successfully preprocessed image
            valid_paths = []   # paths that produced a tensor (same order)
            failed_paths = []  # paths that raised IOError

            for path, _ in batch_paths:
                try:
                    tensors.append(self._preprocess(path))
                    valid_paths.append(path)
                except IOError:
                    failed_paths.append(path)

            # Emit a fallback result for every file that could not be opened
            for path in failed_paths:
                print(f"[Classifier] Could not preprocess: {path}")
                results.append({
                    "category":   self.fallback_category,
                    "confidence": 0.0,
                    "accepted":   False,
                    "top3":       [(self.fallback_category, 0.0)],
                    "file_path":  path,
                    "error":      "Could not open file",
                })

            if not tensors:
                continue

            batch  = torch.cat(tensors, dim=0)  # [N, 3, 224, 224]
            logits = self.model(batch)
            probs  = F.softmax(logits, dim=1).cpu().numpy()  # [N, NUM_CLASSES]

            # probs[k] now correctly aligns with valid_paths[k]
            for k, path in enumerate(valid_paths):
                p     = probs[k]
                top3i = p.argsort()[::-1][:3]
                top3  = [(IDX_TO_LABEL[j], float(p[j])) for j in top3i]
                best_cat, best_conf = top3[0]
                accepted = best_conf >= self.confidence_threshold

                results.append({
                    "category":   best_cat if accepted else self.fallback_category,
                    "confidence": best_conf,
                    "accepted":   accepted,
                    "top3":       top3,
                    "file_path":  path,
                })

        return results

    def classify_folder(self, folder_path: str) -> dict[str, list[str]]:
        """
        Scan a folder and group image files by predicted KemasLah category.
        This is called directly by the Smart Organise feature in KemasLah.

        Returns:
            {
                "Vacation_Travel":    ["C:/img1.jpg", "C:/img2.jpg"],
                "Work_Professional":  ["C:/img3.png"],
                ...
            }
        """
        folder = Path(folder_path)
        image_files = [
            str(f) for f in folder.rglob("*")
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        ]

        print(f"Found {len(image_files)} image files in: {folder}")
        if not image_files:
            return {}

        results = self.classify_batch(image_files)

        grouped: dict[str, list[str]] = {cat: [] for cat in KEMASLAH_CATEGORIES}
        for r in results:
            grouped[r["category"]].append(r["file_path"])

        # Remove empty categories
        grouped = {k: v for k, v in grouped.items() if v}
        return grouped


# ─────────────────────────────────────────────────────────────
# Video keyframe extraction helper
# ─────────────────────────────────────────────────────────────
def extract_keyframe(video_path: str, output_dir: str = "outputs/keyframes") -> str | None:
    """
    Extract the middle keyframe from a video file for classification.
    Requires: pip install opencv-python

    Returns the path to the saved keyframe image, or None on failure.
    """
    try:
        import cv2
    except ImportError:
        print("[WARN] opencv-python not installed. Skipping video: {video_path}")
        return None

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    mid_frame    = total_frames // 2

    cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return None

    os.makedirs(output_dir, exist_ok=True)
    stem       = Path(video_path).stem
    out_path   = os.path.join(output_dir, f"{stem}_keyframe.jpg")
    cv2.imwrite(out_path, frame)
    return out_path