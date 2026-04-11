"""
dataset_loader.py  (Kaggle-compatible version)
----------------------------------------------
Supports TWO download sources for each dataset:

  Source A — Kaggle (recommended for you):
      kagglehub downloads to a cache folder automatically.
      Run 00_kaggle_download.ipynb — it saves the paths to config for you.

  Source B — Official manual download (fallback):
      ~24 GB for Places365, ~19 GB for COCO.

Kaggle vs Official — what is actually different:
  ┌────────────────┬──────────────────────────────────────────────────┐
  │ Dataset        │ Difference                                       │
  ├────────────────┼──────────────────────────────────────────────────┤
  │ COCO 2017      │ IDENTICAL data. Kaggle wraps it inside a         │
  │                │ coco2017/ subfolder. Auto-detected here.         │
  ├────────────────┼──────────────────────────────────────────────────┤
  │ Places365      │ Kaggle is a SUBSET (~36,500 images, 100 per      │
  │                │ category). Images are in category folders with   │
  │                │ NO split text files. Loader auto-splits 80/10/10.│
  └────────────────┴──────────────────────────────────────────────────┘

The Kaggle Places365 subset is fine for KemasLah because you are
fine-tuning on top of Places365-pretrained ResNet50 weights, so
the model already understands scenes from its pretraining.
"""

import os
import json
import random
import numpy as np
from pathlib import Path
from PIL import Image

import torch
from torch.utils.data import Dataset, DataLoader, ConcatDataset, WeightedRandomSampler

from src.data.augmentation import get_train_transforms, get_val_transforms
from src.data.category_mapper import CategoryMapper, LABEL_TO_IDX, NUM_CLASSES

VALID_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


# ─────────────────────────────────────────────────────────────
# Path resolvers — handle Kaggle's wrapping subfolder
# ─────────────────────────────────────────────────────────────

def _resolve_coco_root(kaggle_path: str) -> str | None:
    """
    Kaggle COCO (awsaf49/coco-2017-dataset) puts files inside a
    coco2017/ subfolder. Find the folder that actually contains
    train2017/ and annotations/.
    """
    base = Path(kaggle_path)
    candidates = [base, base / "coco2017"] + list(base.iterdir())
    for p in candidates:
        if Path(p).is_dir() and (Path(p) / "train2017").exists() and (Path(p) / "annotations").exists():
            return str(p)
    return None


def _resolve_places365_kaggle_root(kaggle_path: str) -> str | None:
    """
    Kaggle Places365 (benjaminkz/places365) puts images in category
    sub-folders. Find the folder that contains those category folders.
    """
    known_cats = {"abbey", "airport_terminal", "bedroom", "office", "beach", "forest"}

    def _is_places365_root(folder: Path) -> bool:
        if not folder.is_dir():
            return False
        subdirs = {d.name.lower() for d in folder.iterdir() if d.is_dir()}
        return len(known_cats & subdirs) >= 2

    base = Path(kaggle_path)
    if _is_places365_root(base):
        return str(base)
    for child in base.iterdir():
        if _is_places365_root(child):
            return str(child)
    return None


# ─────────────────────────────────────────────────────────────
# 1. COCO 2017 Dataset
# ─────────────────────────────────────────────────────────────
class COCODataset(Dataset):
    """
    Works for both Kaggle and official COCO downloads.
    Labels each image by its dominant (largest-area) object.
    """

    def __init__(self, root: str, split: str = "train", transform=None):
        self.root      = Path(root)
        self.transform = transform
        self.mapper    = CategoryMapper()

        ann_file = self.root / "annotations" / f"instances_{split}2017.json"
        if not ann_file.exists():
            raise FileNotFoundError(f"COCO annotation file not found:\n  {ann_file}")

        print(f"  Loading COCO {split} annotations (~30 seconds)...")
        with open(ann_file) as f:
            coco_data = json.load(f)

        coco_cats  = {c["id"]: c["name"] for c in coco_data["categories"]}
        img_dir    = self.root / f"{split}2017"
        img_lookup = {img["id"]: img_dir / img["file_name"] for img in coco_data["images"]}

        ann_by_img: dict[int, list] = {}
        for ann in coco_data["annotations"]:
            ann_by_img.setdefault(ann["image_id"], []).append(ann)

        self.samples: list[tuple[Path, int]] = []
        for img_id, anns in ann_by_img.items():
            dominant = max(anns, key=lambda a: a["bbox"][2] * a["bbox"][3])
            cat_name = coco_cats.get(dominant["category_id"], "unknown")
            kemaslah = self.mapper.map_coco(cat_name)
            self.samples.append((img_lookup[img_id], LABEL_TO_IDX[kemaslah]))

        print(f"  COCO {split}: {len(self.samples):,} images.")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        try:
            image = np.array(Image.open(img_path).convert("RGB"))
        except Exception:
            image = np.zeros((224, 224, 3), dtype=np.uint8)
        if self.transform:
            image = self.transform(image=image)["image"]
        return image, label


# ─────────────────────────────────────────────────────────────
# 2A. Places365 — Official download
# ─────────────────────────────────────────────────────────────
class Places365OfficialDataset(Dataset):
    """Uses split .txt files + data_256/ folder from official download."""

    def __init__(self, root: str, split: str = "train", transform=None):
        self.root      = Path(root)
        self.transform = transform
        self.mapper    = CategoryMapper()

        list_file = self.root / f"places365_{split}_standard.txt"
        if not list_file.exists():
            raise FileNotFoundError(f"Places365 split file not found:\n  {list_file}")

        idx_map: dict[int, str] = {}
        cat_file = self.root / "categories_places365.txt"
        if cat_file.exists():
            with open(cat_file) as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        scene = parts[0].lstrip("/").split("/")[-1]
                        idx_map[int(parts[1])] = scene

        self.samples: list[tuple[Path, int]] = []
        with open(list_file) as f:
            for line in f:
                img_rel, class_idx = line.strip().split()
                scene    = idx_map.get(int(class_idx), "unknown")
                kemaslah = self.mapper.map_places365(scene)
                self.samples.append(
                    (self.root / "data_256" / img_rel.lstrip("/"), LABEL_TO_IDX[kemaslah])
                )

        print(f"  Places365 official {split}: {len(self.samples):,} images.")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        try:
            image = np.array(Image.open(img_path).convert("RGB"))
        except Exception:
            image = np.zeros((224, 224, 3), dtype=np.uint8)
        if self.transform:
            image = self.transform(image=image)["image"]
        return image, label


# ─────────────────────────────────────────────────────────────
# 2B. Places365 — Kaggle download (category folders, no split files)
# ─────────────────────────────────────────────────────────────
class Places365KaggleDataset(Dataset):
    """
    Kaggle Places365 (benjaminkz/places365) — ~36,500 images in category folders.

    Structure inside the Kaggle download:
        <root>/
            abbey/          ← scene name = folder name
                00000001.jpg
            airport_terminal/
            bedroom/
            ...

    No split files exist, so this class creates an 80/10/10
    train/val/test split with a fixed random seed for reproducibility.
    """

    def __init__(
        self,
        root: str,
        split: str = "train",
        transform=None,
        val_split: float = 0.10,
        test_split: float = 0.10,
        seed: int = 42,
    ):
        self.root      = Path(root)
        self.transform = transform
        self.mapper    = CategoryMapper()

        category_dirs = sorted([d for d in self.root.iterdir() if d.is_dir()])
        if not category_dirs:
            raise FileNotFoundError(
                f"No category folders found in: {self.root}\n"
                f"Expected sub-folders like 'abbey/', 'bedroom/', etc.\n"
                f"Check that your kaggle_places365_path is correct."
            )

        all_samples: list[tuple[Path, int]] = []
        for cat_dir in category_dirs:
            scene    = cat_dir.name.lower()
            kemaslah = self.mapper.map_places365(scene)
            target   = LABEL_TO_IDX[kemaslah]
            for img_file in cat_dir.iterdir():
                if img_file.suffix.lower() in VALID_EXTS:
                    all_samples.append((img_file, target))

        if not all_samples:
            raise RuntimeError(f"No images found under: {self.root}")

        # Reproducible shuffle + split
        rng = random.Random(seed)
        rng.shuffle(all_samples)
        n       = len(all_samples)
        n_test  = int(n * test_split)
        n_val   = int(n * val_split)
        n_train = n - n_test - n_val

        splits = {
            "train": all_samples[:n_train],
            "val":   all_samples[n_train: n_train + n_val],
            "test":  all_samples[n_train + n_val:],
        }
        self.samples = splits[split]

        print(f"  Places365 Kaggle — total: {n:,} images across {len(category_dirs)} scene categories")
        print(f"  Split '{split}': {len(self.samples):,} images  "
              f"(train {n_train:,} / val {n_val:,} / test {n_test:,})")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        try:
            image = np.array(Image.open(img_path).convert("RGB"))
        except Exception:
            image = np.zeros((224, 224, 3), dtype=np.uint8)
        if self.transform:
            image = self.transform(image=image)["image"]
        return image, label


# ─────────────────────────────────────────────────────────────
# 3. Custom / WhatsApp images (optional)
# ─────────────────────────────────────────────────────────────
class CustomDataset(Dataset):
    """
    Your own labelled images for fine-tuning.
    Place images in datasets/custom/train/<CategoryName>/ etc.
    This is optional — training works without it.
    """

    def __init__(self, root: str, split: str = "train", transform=None):
        self.root      = Path(root) / split
        self.transform = transform
        self.samples: list[tuple[Path, int]] = []

        if not self.root.exists():
            return  # Optional — skip silently

        for label_dir in sorted(self.root.iterdir()):
            if not label_dir.is_dir() or label_dir.name not in LABEL_TO_IDX:
                continue
            label_idx = LABEL_TO_IDX[label_dir.name]
            for img_file in label_dir.iterdir():
                if img_file.suffix.lower() in VALID_EXTS:
                    self.samples.append((img_file, label_idx))

        if self.samples:
            print(f"  Custom {split}: {len(self.samples):,} images.")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        try:
            image = np.array(Image.open(img_path).convert("RGB"))
        except Exception:
            image = np.zeros((224, 224, 3), dtype=np.uint8)
        if self.transform:
            image = self.transform(image=image)["image"]
        return image, label


# ─────────────────────────────────────────────────────────────
# Helper: proportional subsample across multiple datasets
# ─────────────────────────────────────────────────────────────
def _subsample_datasets(
    dataset_list: list[Dataset],
    max_total: int,
    seed: int,
) -> list[Dataset]:
    """
    Reduce a list of datasets so their combined length is at most max_total,
    preserving the original proportion of each dataset.

    Example: COCO (117K) + Places365 (1.35M) → 500K total
        COCO keeps    :  117K × (500K / 1.47M) ≈  40K  (8%)
        Places365 keeps: 1.35M × (500K / 1.47M) ≈ 460K (92%)

    Uses torch.utils.data.Subset so no data is copied — only indices change.
    """
    from torch.utils.data import Subset

    total = sum(len(ds) for ds in dataset_list)
    if total <= max_total:
        return dataset_list   # Already small enough, nothing to do

    rng = random.Random(seed)
    result = []
    for ds in dataset_list:
        proportion   = len(ds) / total
        n_keep       = max(1, round(max_total * proportion))
        all_indices  = list(range(len(ds)))
        rng.shuffle(all_indices)
        chosen = all_indices[:n_keep]
        result.append(Subset(ds, chosen))

    actual_total = sum(len(ds) for ds in result)
    print(f"  Subsampled: {total:,} → {actual_total:,} images "
          f"({actual_total/total*100:.1f}% of full dataset)")
    return result


# ─────────────────────────────────────────────────────────────
# 4. Main entry point
# ─────────────────────────────────────────────────────────────
def build_dataloaders(config: dict) -> tuple[DataLoader, DataLoader, DataLoader]:
    """
    Build train / val / test DataLoaders.
    Automatically uses Kaggle paths if set in config, otherwise
    falls back to the manual download paths.

    If config['training']['max_train_samples'] is set and greater than 0,
    the training set is randomly subsampled to that size while keeping
    the proportion of each dataset the same (COCO vs Places365 ratio preserved).
    Val and test sets are NOT subsampled — they always use all available data.
    """
    image_size       = config["dataset"]["image_size"]
    batch_size       = config["training"]["batch_size"]
    num_workers      = config["dataset"]["num_workers"]
    pin_memory       = config["dataset"]["pin_memory"]
    seed             = config["training"]["seed"]
    val_split        = config["training"]["val_split"]
    test_split       = config["training"]["test_split"]
    max_train        = config["training"].get("max_train_samples", 0)

    train_tf = get_train_transforms(image_size)
    val_tf   = get_val_transforms(image_size)

    tr, va, te = [], [], []

    # ── COCO 2017 ──────────────────────────────────────────
    coco_root = None
    kg_coco   = config["dataset"].get("kaggle_coco_path", "").strip()

    if kg_coco and os.path.exists(kg_coco):
        resolved = _resolve_coco_root(kg_coco)
        if resolved:
            coco_root = resolved
            print(f"Using COCO from Kaggle cache: {coco_root}")
        else:
            print(f"[WARN] Could not find COCO structure inside {kg_coco}")

    if not coco_root:
        manual = config["dataset"]["coco_root"]
        if os.path.exists(manual):
            coco_root = manual

    if coco_root:
        print("Loading COCO 2017...")
        try:
            tr.append(COCODataset(coco_root, "train", train_tf))
            va.append(COCODataset(coco_root, "val",   val_tf))
            te.append(COCODataset(coco_root, "val",   val_tf))
        except Exception as e:
            print(f"[ERROR] COCO failed: {e}")
    else:
        print("[SKIP] COCO not found. Set kaggle_coco_path in config.")

    # ── Places365 ──────────────────────────────────────────
    p365_loaded = False
    kg_p365     = config["dataset"].get("kaggle_places365_path", "").strip()

    if kg_p365 and os.path.exists(kg_p365):
        resolved = _resolve_places365_kaggle_root(kg_p365)
        if resolved:
            print(f"Using Places365 from Kaggle cache: {resolved}")
            print("Loading Places365 Kaggle dataset...")
            kwargs = dict(val_split=val_split, test_split=test_split, seed=seed)
            try:
                tr.append(Places365KaggleDataset(resolved, "train", train_tf, **kwargs))
                va.append(Places365KaggleDataset(resolved, "val",   val_tf,   **kwargs))
                te.append(Places365KaggleDataset(resolved, "test",  val_tf,   **kwargs))
                p365_loaded = True
            except Exception as e:
                print(f"[ERROR] Places365 Kaggle failed: {e}")
        else:
            print(f"[WARN] Could not find Places365 category folders inside {kg_p365}")

    if not p365_loaded:
        manual = config["dataset"]["places365_root"]
        if os.path.exists(manual):
            print("Loading Places365 (official)...")
            try:
                tr.append(Places365OfficialDataset(manual, "train", train_tf))
                va.append(Places365OfficialDataset(manual, "val",   val_tf))
                te.append(Places365OfficialDataset(manual, "val",   val_tf))
            except Exception as e:
                print(f"[ERROR] Places365 official failed: {e}")
        else:
            print("[SKIP] Places365 not found. Set kaggle_places365_path in config.")

    # ── Custom images ──────────────────────────────────────
    custom = config["dataset"]["custom_root"]
    if os.path.exists(os.path.join(custom, "train")):
        tr.append(CustomDataset(custom, "train", train_tf))
        va.append(CustomDataset(custom, "val",   val_tf))
        te.append(CustomDataset(custom, "test",  val_tf))

    if not tr:
        raise RuntimeError(
            "\n❌ No datasets loaded!\n"
            "Make sure you ran 00_kaggle_download.ipynb and the paths\n"
            "were saved to configs/training_config.yaml"
        )

    # ── Apply training sample cap (val/test are never capped) ──
    total_before = sum(len(ds) for ds in tr)
    if max_train and max_train > 0 and total_before > max_train:
        print(f"\nApplying training sample cap: {total_before:,} → {max_train:,} images")
        print("Subsampling each dataset proportionally to preserve COCO/Places365 balance...")
        tr = _subsample_datasets(tr, max_train, seed)
    else:
        if max_train and max_train > 0:
            print(f"\nmax_train_samples={max_train:,} but dataset only has {total_before:,} — no cap needed.")

    def _join(lst):
        return ConcatDataset(lst) if len(lst) > 1 else lst[0]

    train_ds, val_ds, test_ds = _join(tr), _join(va), _join(te)

    print(f"\n{'='*55}")
    print(f"  Final dataset sizes:")
    print(f"    Train : {len(train_ds):,} images")
    print(f"    Val   : {len(val_ds):,} images")
    print(f"    Test  : {len(test_ds):,} images")
    if max_train and max_train > 0:
        print(f"  Sample cap applied: {max_train:,}")
    print(f"{'='*55}")

    g = torch.Generator().manual_seed(seed)
    kw = dict(num_workers=num_workers, pin_memory=pin_memory, persistent_workers=False)

    # ── Weighted sampler for balanced training ──────────────────
    # Instead of shuffle=True (which would still over-represent large
    # classes), we assign each sample a weight = 1/class_count so that
    # every category is seen equally often per epoch regardless of size.
    #
    # This is the standard fix for class imbalance — it does NOT remove
    # any data. It just changes how frequently each sample is drawn.
    # Val and test loaders are never weighted — they use all data as-is.
    use_weighted = config.get("training", {}).get("use_weighted_sampler", True)

    if use_weighted:
        print("\nBuilding weighted sampler for balanced training...")
        print("(Each category will be seen equally often per epoch)")

        # Collect labels from the training dataset
        # We access .samples from each sub-dataset directly to avoid
        # loading all images just to get labels
        all_labels: list[int] = []

        def _collect_labels(ds) -> list[int]:
            """Recursively collect labels from ConcatDataset or Subset."""
            if isinstance(ds, ConcatDataset):
                result = []
                for sub in ds.datasets:
                    result.extend(_collect_labels(sub))
                return result
            elif isinstance(ds, torch.utils.data.Subset):
                parent_labels = _collect_labels(ds.dataset)
                return [parent_labels[i] for i in ds.indices]
            elif hasattr(ds, "samples"):
                return [label for _, label in ds.samples]
            else:
                return []

        all_labels = _collect_labels(train_ds)

        if all_labels:
            from collections import Counter

            label_counts = Counter(all_labels)
            n_classes    = NUM_CLASSES
            total        = len(all_labels)

            # Weight per class = 1 / count  (rare classes get higher weight)
            class_weights = {
                cls: 1.0 / count for cls, count in label_counts.items()
            }

            # Weight per sample
            sample_weights = torch.tensor(
                [class_weights.get(lbl, 1.0 / total) for lbl in all_labels],
                dtype=torch.float
            )

            sampler = WeightedRandomSampler(
                weights     = sample_weights,
                num_samples = len(sample_weights),
                replacement = True,
                generator   = g,
            )

            # Print the effective class balance
            from src.data.category_mapper import IDX_TO_LABEL
            print(f"\n  Class weights (higher = sampled more often):")
            for cls_idx in sorted(label_counts.keys()):
                cat   = IDX_TO_LABEL.get(cls_idx, str(cls_idx))
                count = label_counts[cls_idx]
                w     = class_weights[cls_idx]
                print(f"    {cat:<30} {count:>8,} images  weight={w:.6f}")

            train_loader = DataLoader(
                train_ds,
                batch_size = batch_size,
                sampler    = sampler,     # replaces shuffle=True
                **kw
            )
            print("\n✅ Weighted sampler active — all categories balanced during training.")
        else:
            print("[WARN] Could not collect labels for weighting — falling back to shuffle.")
            train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, generator=g, **kw)
    else:
        train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, generator=g, **kw)

    val_loader  = DataLoader(val_ds,  batch_size=batch_size * 2, shuffle=False, **kw)
    test_loader = DataLoader(test_ds, batch_size=batch_size * 2, shuffle=False, **kw)

    return train_loader, val_loader, test_loader
    