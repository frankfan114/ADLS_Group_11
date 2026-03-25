"""
Quantization experiment configurations.

Defines signature models, datasets, bit-width sweep parameters, and helpers
to build quantization configs for `quantize_transform_pass`.

Image (vision) models only (CIFAR-10 from-scratch):
  - ResNet18, ResNet50   : CNN, Conv2d + Linear (classifier)
  - MobileNetV2, EfficientNet-B0 : lightweight CNN, Conv2d + Linear
  - VGG7                 : CNN (vgg7_cifar), Conv2d + Linear
  - DeiT-tiny, DeiT-small: Vision Transformer, Linear-only, 224x224
NLP (not image): BERT-base
"""

from dataclasses import dataclass, field
from copy import deepcopy


# ---------------------------------------------------------------------------
# Model / dataset pairings
# ---------------------------------------------------------------------------

# All image model names for filtering (use --models from this list for vision-only)
IMAGE_MODEL_NAMES = [
    "ResNet18", "ResNet50",
    "MobileNetV2", "EfficientNet-B0",
    "VGG7",
    "DeiT-tiny", "DeiT-small",
]

@dataclass
class ModelConfig:
    name: str
    checkpoint: str
    dataset: str
    task: str
    is_nlp: bool = False
    # For NLP models: HuggingFace tokenizer checkpoint
    tokenizer_checkpoint: str | None = None
    # For NLP models: list of input names for graph/tracing inputs
    hf_input_names: list[str] | None = None
    # Expected spatial input size (H, W) for vision models
    input_size: tuple[int, int] = (32, 32)
    # Layer types present (for reporting)
    layer_types: list[str] = field(default_factory=lambda: ["linear"])


# ---- Vision CNNs (Conv2d + Linear) ----

RESNET18 = ModelConfig(
    name="ResNet18",
    checkpoint="resnet18",
    dataset="cifar10",
    task="cls",
    input_size=(32, 32),
    layer_types=["linear", "conv2d"],
)

RESNET50 = ModelConfig(
    name="ResNet50",
    checkpoint="resnet50",
    dataset="cifar10",
    task="cls",
    input_size=(32, 32),
    layer_types=["linear", "conv2d"],
)

MOBILENETV2 = ModelConfig(
    name="MobileNetV2",
    checkpoint="mobilenetv2",
    dataset="cifar10",
    task="cls",
    input_size=(32, 32),
    layer_types=["linear", "conv2d"],
)

EFFICIENTNET_B0 = ModelConfig(
    name="EfficientNet-B0",
    checkpoint="efficientnet_b0",
    dataset="cifar10",
    task="cls",
    input_size=(32, 32),
    layer_types=["linear", "conv2d"],
)

VGG7 = ModelConfig(
    name="VGG7",
    checkpoint="vgg7_cifar",
    dataset="cifar10",
    task="cls",
    input_size=(32, 32),
    layer_types=["linear", "conv2d"],
)

# ---- Vision Transformers (Linear-heavy, need 224x224) ----

DEIT_TINY = ModelConfig(
    name="DeiT-tiny",
    checkpoint="deit_tiny_patch16_224",
    dataset="cifar10",
    task="cls",
    input_size=(224, 224),
    layer_types=["linear"],
)

DEIT_SMALL = ModelConfig(
    name="DeiT-small",
    checkpoint="deit_small_patch16_224",
    dataset="cifar10",
    task="cls",
    input_size=(224, 224),
    layer_types=["linear"],
)

# ---- NLP Transformers ----

BERT_BASE = ModelConfig(
    name="BERT-base",
    checkpoint="bert-base-uncased",
    dataset="imdb",
    task="cls",
    is_nlp=True,
    tokenizer_checkpoint="bert-base-uncased",
    hf_input_names=["input_ids", "attention_mask", "labels"],
    layer_types=["linear"],
)

# Small BERT (2 layers, 128 hidden) - same API as BERT, faster and lighter
BERT_TINY = ModelConfig(
    name="BERT-tiny",
    checkpoint="prajjwal1/bert-tiny",
    dataset="imdb",
    task="cls",
    is_nlp=True,
    tokenizer_checkpoint="prajjwal1/bert-tiny",
    hf_input_names=["input_ids", "attention_mask", "labels"],
    layer_types=["linear"],
)

MODEL_CONFIGS: list[ModelConfig] = [
    RESNET18,
    RESNET50,
    MOBILENETV2,
    EFFICIENTNET_B0,
    VGG7,
    DEIT_TINY,
    DEIT_SMALL,
    BERT_BASE,
    BERT_TINY,
]

# ---------------------------------------------------------------------------
# Bit-width sweep
# ---------------------------------------------------------------------------

BIT_WIDTHS = [4, 8, 12, 16]


# ---------------------------------------------------------------------------
# Quantization config builders
# ---------------------------------------------------------------------------

def build_uniform_quant_config(
    layer_types: list[str],
    bit_width: int,
    frac_width: int | None = None,
    scheme: str = "integer",
) -> dict:
    """Build a uniform (by-type) quantization config.

    All specified layer types get the same bit-width for data_in, weight, and bias.
    Precision format is strictly integer: frac_width defaults to 0 (no fractional bits).
    """
    if frac_width is None:
        frac_width = 0  # strict int: no fractional part

    config = {
        "by": "type",
        "default": {"config": {"name": None}},
    }

    layer_config = {
        "config": {
            "name": scheme,
            "data_in_width": bit_width,
            "data_in_frac_width": frac_width,
            "weight_width": bit_width,
            "weight_frac_width": frac_width,
            "bias_width": bit_width,
            "bias_frac_width": frac_width,
        }
    }

    for lt in layer_types:
        config[lt] = deepcopy(layer_config)

    return config


def build_mixed_precision_config(
    layer_types: list[str],
    sensitive_width: int = 8,
    aggressive_width: int = 4,
    sensitive_frac: int | None = None,
    aggressive_frac: int | None = None,
    scheme: str = "integer",
) -> dict:
    """Build a mixed-precision config where different layer types get different widths.

    Conv2d layers (closer to input, more sensitive) get `sensitive_width`,
    Linear layers get `aggressive_width`. Precision format is strictly integer (frac=0).
    """
    if sensitive_frac is None:
        sensitive_frac = 0
    if aggressive_frac is None:
        aggressive_frac = 0

    config = {
        "by": "type",
        "default": {"config": {"name": None}},
    }

    for lt in layer_types:
        if lt == "conv2d":
            w, f = sensitive_width, sensitive_frac
        else:
            w, f = aggressive_width, aggressive_frac
        config[lt] = {
            "config": {
                "name": scheme,
                "data_in_width": w,
                "data_in_frac_width": f,
                "weight_width": w,
                "weight_frac_width": f,
                "bias_width": w,
                "bias_frac_width": f,
            }
        }

    return config
