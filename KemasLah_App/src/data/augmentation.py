import albumentations as A
from albumentations.pytorch import ToTensorV2


def get_train_transforms(image_size: int = 224) -> A.Compose:

    return A.Compose([
        A.RandomResizedCrop(height=image_size, width=image_size, scale=(0.6, 1.0), ratio=(0.75, 1.33), p=1.0),
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.05),
        A.RandomRotate90(p=0.2),

        # Colour augmentations
        A.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3, hue=0.1, p=0.7),
        A.ToGray(p=0.05),               # Some files are greyscale
        A.RandomGamma(gamma_limit=(80, 120), p=0.3),

        # Noise & compression — important for messenger images
        A.GaussNoise(var_limit=(10, 50), p=0.3),
        A.ImageCompression(quality_lower=60, quality_upper=100, p=0.4),
        A.Blur(blur_limit=3, p=0.2),

        # Occlusion
        A.CoarseDropout(max_holes=8, max_height=32, max_width=32, p=0.3),

        # Normalise using ImageNet mean/std (standard for all pretrained models)
        A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        ToTensorV2(),
    ])


def get_val_transforms(image_size: int = 224) -> A.Compose:
    return A.Compose([
        A.Resize(int(image_size * 1.14), int(image_size * 1.14)),
        A.CenterCrop(height=image_size, width=image_size),
        A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        ToTensorV2(),
    ])


def get_inference_transforms(image_size: int = 224) -> A.Compose:

    return A.Compose([
        A.LongestMaxSize(max_size=int(image_size * 1.14)),
        A.PadIfNeeded(
            min_height=int(image_size * 1.14),
            min_width=int(image_size * 1.14),
            border_mode=0,        # Black padding
            value=0,
        ),
        A.CenterCrop(height=image_size, width=image_size),
        A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        ToTensorV2(),
    ])
