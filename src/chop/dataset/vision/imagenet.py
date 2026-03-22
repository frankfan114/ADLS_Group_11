"""
ImageNet dataset (ILSVRC). Cannot be auto-downloaded: license and size require
manual registration/download. Use --data-dir to point to your local copy.
For quick testing without ImageNet, use dataset=cifar10 (auto-downloads).
"""

import os
from pathlib import Path
import torchvision as tv
from ..utils import add_dataset_info


@add_dataset_info(
    name="imagenet",
    dataset_source="others",
    available_splits=("train", "validation"),
    image_classification=True,
    num_classes=1000,
    image_size=(3, 224, 224),
)
class ImageNetMase(tv.datasets.ImageFolder):
    info = {
        "num_classes": 1000,
        "image_size": (3, 224, 224),
    }

    test_dataset_available: bool = False
    pred_dataset_available: bool = False

    def __init__(self, root: os.PathLike, transform: callable, subset=False) -> None:
        if subset:
            root = self._create_subset_dataset(root)
        super().__init__(root, transform=transform)

    def prepare_data(self) -> None:
        pass

    def setup(self) -> None:
        pass

    # If the user requests a subset version of ImageNet, then sample only 10 images
    # from each class.
    def _create_subset_dataset(self, root: os.PathLike) -> os.PathLike:
        # Check if the root directory points to the validation or train folder
        root = Path(root)
        subset_root = root.parent.parent / "imagenet_subset"
        if subset_root.exists():
            return subset_root / root.name

        # Create a tiny dataset with only 100 samples per class for each split
        sizes = [100, 20]
        dataset_dir = root.parent
        for i, split in enumerate(["train", "val"]):
            # Get all the class directories from the original dataset
            class_dirs = [d for d in (dataset_dir / split).iterdir() if d.is_dir()]

            for class_dir in class_dirs:
                subset_class_dir = subset_root / split / class_dir.name
                subset_class_dir.mkdir(parents=True, exist_ok=True)

                # NOTE: We don't pick randomly. We just go in the order they're listed.
                for j, img in enumerate(class_dir.iterdir()):
                    if j >= sizes[i]:
                        break
                    os.symlink(img, subset_class_dir / img.name)

        return subset_root / root.name


def _looks_like_imagenet_root(root: Path) -> bool:
    """True if root contains subdirs (class folders). Accepts WordNet IDs (n01440764), numeric (0,1,...), or any named subdirs."""
    if not root.is_dir():
        return False
    try:
        subdirs = [d for d in root.iterdir() if d.is_dir()]
    except OSError:
        return False
    return len(subdirs) > 0


def _resolve_imagenet_root(imagenet_dir: Path, train: bool):
    """Resolve train or val/validation folder; try common naming and fallback to data-dir as val root. Returns Path or None if not found."""
    if train:
        candidates = ["train", "Train"]
    else:
        candidates = ["val", "validation", "ILSVRC2012_img_val"]
    for name in candidates:
        root = imagenet_dir / name
        if root.exists():
            return root
    # Fallback for validation: if --data-dir itself contains class subfolders (e.g. D:\datasets\imagenet\n01440764\...), use it as val root
    if not train and _looks_like_imagenet_root(imagenet_dir):
        return imagenet_dir
    return None


def get_imagenet_dataset(
    name: str, path: os.PathLike, train: bool, transform: callable, subset=False
) -> tv.datasets.ImageFolder | None:
    match name.lower():
        case "imagenet":
            imagenet_dir = Path(path)
            root = _resolve_imagenet_root(imagenet_dir, train)
            if root is None:
                if train:
                    # Allow run without train (e.g. PTQ-only with val); QAT will fail later at train_dataloader()
                    return None
                tried_paths = [str(imagenet_dir / c) for c in ["val", "validation", "ILSVRC2012_img_val"]]
                # Always show whether path exists and what's inside (for debugging)
                resolved = imagenet_dir.resolve()
                exists = resolved.exists()
                is_dir = resolved.is_dir() if exists else False
                contents = ""
                if exists and is_dir:
                    try:
                        entries = list(resolved.iterdir())[:12]
                        contents = f"; contents ({len(entries)} shown): {[e.name for e in entries]}"
                    except OSError as e:
                        contents = f"; listdir failed: {e}"
                else:
                    contents = f"; path exists={exists}, is_dir={is_dir}"
                raise RuntimeError(
                    f"ImageNet validation not found. data-dir={resolved}{contents}. "
                    f"The directory does not exist from this process. Check: (1) Path is correct and the drive (e.g. D:) is available. "
                    f"(2) In PowerShell run: Test-Path '{resolved}' to verify. "
                    f"(3) If your data is elsewhere (e.g. on F:), use that path: --data-dir F:\\path\\to\\imagenet. "
                    f"Expected layout: <data-dir>/val/ or <data-dir>/validation/ with class subfolders, "
                    f"or <data-dir> containing class subfolders (e.g. n01440764/, 0/, 1/, ...)."
                )
            dataset = ImageNetMase(root, transform=transform, subset=subset)
        case _:
            raise ValueError(f"Unknown dataset {name}")
    return dataset
