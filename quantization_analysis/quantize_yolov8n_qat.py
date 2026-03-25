#!/usr/bin/env python3
"""
Quantize YOLOv8n to integer precision, then run short QAT.

Pipeline:
1) Load yolov8n.pt
2) Replace nn.Conv2d / nn.Linear with QuantConv2d / QuantLinear (fake-quant STE)
3) Save PTQ-like quantized checkpoint
4) Run QAT with Ultralytics trainer on a dataset (default: coco8.yaml)
5) Save QAT quantized checkpoint
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import torch
import torch.nn as nn
from ultralytics import YOLO
from ultralytics.models.yolo.detect import DetectionTrainer

from quant_layers import QuantConv2d, QuantLinear, replace_with_quant


def count_layers(model: nn.Module) -> tuple[int, int, int, int]:
    conv = sum(isinstance(m, nn.Conv2d) for m in model.modules())
    lin = sum(isinstance(m, nn.Linear) for m in model.modules())
    qconv = sum(isinstance(m, QuantConv2d) for m in model.modules())
    qlin = sum(isinstance(m, QuantLinear) for m in model.modules())
    return conv, lin, qconv, qlin


class QuantizedDetectionTrainer(DetectionTrainer):
    """Inject a pre-quantized model so Ultralytics won't rebuild/load original Conv keys."""

    injected_model: nn.Module | None = None

    def get_model(self, cfg=None, weights=None, verbose: bool = True):
        if self.injected_model is not None:
            return self.injected_model
        return super().get_model(cfg=cfg, weights=weights, verbose=verbose)


def main():
    parser = argparse.ArgumentParser(description="Quantize YOLOv8n to int and run QAT")
    parser.add_argument("--weights", type=str, default="yolov8n.pt")
    parser.add_argument("--bit-width", type=int, default=8, help="Integer quant bit width")
    parser.add_argument("--frac-width", type=int, default=0, help="Fraction bits (0 = strict int)")
    parser.add_argument("--epochs", type=int, default=1, help="QAT epochs")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--data", type=str, default="coco8.yaml")
    parser.add_argument("--project", type=str, default="results")
    parser.add_argument("--name", type=str, default="yolov8n_int_qat")
    parser.add_argument("--device", type=str, default="0" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()

    out_dir = Path(__file__).parent / "checkpoints"
    out_dir.mkdir(parents=True, exist_ok=True)

    model = YOLO(args.weights)
    base = model.model
    conv, lin, qconv, qlin = count_layers(base)
    print(f"[Before] Conv={conv}, Linear={lin}, QuantConv={qconv}, QuantLinear={qlin}")

    replace_with_quant(
        base,
        bit_width=args.bit_width,
        frac_width=args.frac_width,
        layer_types=["conv2d", "linear"],
    )

    conv, lin, qconv, qlin = count_layers(base)
    print(f"[After ] Conv={conv}, Linear={lin}, QuantConv={qconv}, QuantLinear={qlin}")

    ptq_ckpt = out_dir / f"yolov8n_int{args.bit_width}_ptq.pt"
    torch.save(base.state_dict(), ptq_ckpt)
    print(f"[Saved] PTQ quantized state_dict -> {ptq_ckpt}")

    QuantizedDetectionTrainer.injected_model = base
    train_res = None
    try:
        train_res = model.train(
            trainer=QuantizedDetectionTrainer,
            data=args.data,
            epochs=args.epochs,
            imgsz=args.imgsz,
            batch=args.batch,
            device=args.device,
            workers=args.workers,
            project=args.project,
            name=args.name,
        )
        print(f"[QAT] train result: {train_res}")
    except Exception as e:
        # Ultralytics may fail in final validation/fuse for custom quant modules
        # while training already finished and best/last checkpoints are written.
        print(f"[WARN] QAT train finished with post-train validation error: {e}")

    run_dir = Path(args.project) / args.name / "weights"
    best_ckpt = run_dir / "best.pt"
    last_ckpt = run_dir / "last.pt"

    if best_ckpt.exists():
        qat_ckpt = out_dir / f"yolov8n_int{args.bit_width}_qat_best.pt"
        shutil.copy2(best_ckpt, qat_ckpt)
        print(f"[Saved] QAT best checkpoint -> {qat_ckpt}")
    elif last_ckpt.exists():
        qat_ckpt = out_dir / f"yolov8n_int{args.bit_width}_qat_last.pt"
        shutil.copy2(last_ckpt, qat_ckpt)
        print(f"[Saved] QAT last checkpoint -> {qat_ckpt}")
    else:
        print("[WARN] No best.pt/last.pt found under training run directory.")


if __name__ == "__main__":
    main()
