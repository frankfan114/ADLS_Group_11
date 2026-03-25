"""
Pure PyTorch quantization layers.
Integer quantization for Linear and Conv2d: PTQ and QAT with straight-through estimator.
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional


def _symmetric_quantize(
    x: torch.Tensor,
    bit_width: int,
    frac_width: int = 0,
) -> torch.Tensor:
    """Quantize to signed integer with bit_width bits; frac_width bits for fractional part (fixed-point). STE in backward."""
    n_levels = 2 ** bit_width
    half = n_levels // 2
    if frac_width <= 0:
        # Integer: scale so that max abs value maps to ±(half-1)
        scale = x.abs().max().clamp(min=1e-8) / (half - 1)
        x_scaled = x / scale
        x_int = torch.round(x_scaled).clamp(-half, half - 1)
        x_dequant = x_int * scale
    else:
        # Fixed-point: step = 2^(-frac_width)
        step = 2.0 ** (-frac_width)
        max_repr = (half - 1) * step
        scale = x.abs().max().clamp(min=1e-8) / max_repr
        x_scaled = x / scale
        x_int = torch.round(x_scaled / step).clamp(-half, half - 1)
        x_dequant = x_int * step * scale
    # STE: forward = x_dequant (quantized), backward = gradient flows as if identity (through x)
    return x + (x_dequant - x).detach()


class QuantLinear(nn.Module):
    """Linear with integer/fixed-point quantized weight and optional bias."""

    def __init__(
        self,
        in_features: int,
        out_features: int,
        bias: bool = True,
        bit_width: int = 8,
        frac_width: int = 0,
        device=None,
        dtype=None,
    ):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.bit_width = bit_width
        self.frac_width = frac_width
        self.weight = nn.Parameter(torch.empty(out_features, in_features, device=device, dtype=dtype or torch.float32))
        self.bias = nn.Parameter(torch.empty(out_features, device=device, dtype=dtype or torch.float32)) if bias else None
        self.reset_parameters()

    def reset_parameters(self):
        nn.init.kaiming_uniform_(self.weight, a=5**0.5)
        if self.bias is not None:
            fan_in, _ = nn.init._calculate_fan_in_and_fan_out(self.weight)
            bound = 1 / (fan_in**0.5) if fan_in > 0 else 0
            nn.init.uniform_(self.bias, -bound, bound)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        w = _symmetric_quantize(self.weight, self.bit_width, self.frac_width)
        b = _symmetric_quantize(self.bias, self.bit_width, self.frac_width) if self.bias is not None else None
        return F.linear(x, w, b)


class QuantConv2d(nn.Module):
    """Conv2d with integer-quantized weight and optional bias."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int | tuple[int, int],
        stride: int | tuple[int, int] = 1,
        padding: int | tuple[int, int] = 0,
        dilation: int | tuple[int, int] = 1,
        groups: int = 1,
        bias: bool = True,
        padding_mode: str = "zeros",
        bit_width: int = 8,
        frac_width: int = 0,
        device=None,
        dtype=None,
    ):
        super().__init__()
        self.bit_width = bit_width
        self.frac_width = frac_width
        self._conv = nn.Conv2d(
            in_channels,
            out_channels,
            kernel_size,
            stride=stride,
            padding=padding,
            dilation=dilation,
            groups=groups,
            bias=bias,
            padding_mode=padding_mode,
            device=device,
            dtype=dtype or torch.float32,
        )

    @property
    def weight(self):
        return self._conv.weight

    @property
    def bias(self):
        return self._conv.bias

    # Expose Conv2d attributes for toolchains (e.g., Ultralytics fuse_conv_and_bn).
    @property
    def in_channels(self):
        return self._conv.in_channels

    @property
    def out_channels(self):
        return self._conv.out_channels

    @property
    def kernel_size(self):
        return self._conv.kernel_size

    @property
    def stride(self):
        return self._conv.stride

    @property
    def padding(self):
        return self._conv.padding

    @property
    def dilation(self):
        return self._conv.dilation

    @property
    def groups(self):
        return self._conv.groups

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        w = _symmetric_quantize(self._conv.weight, self.bit_width, self.frac_width)
        b = _symmetric_quantize(self._conv.bias, self.bit_width, self.frac_width) if self._conv.bias is not None else None
        return F.conv2d(
            x, w, b,
            self._conv.stride,
            self._conv.padding,
            self._conv.dilation,
            self._conv.groups,
        )


def replace_with_quant(
    model: nn.Module,
    bit_width: int,
    layer_types: list[str],
    frac_width: int | None = None,
) -> nn.Module:
    """
    Replace nn.Linear and/or nn.Conv2d in model with QuantLinear/QuantConv2d.
    Modifies model in place; copies weight/bias from original to quant layer.
    frac_width: fractional bits (fixed-point). If None, uses bit_width // 2.
    """
    if frac_width is None:
        frac_width = bit_width // 2
    want_linear = "linear" in layer_types
    want_conv2d = "conv2d" in layer_types

    to_replace: list[tuple[nn.Module, str, nn.Module]] = []  # (parent, attr_name, new_module)

    for name, module in list(model.named_modules()):
        if want_linear and isinstance(module, nn.Linear):
            q = QuantLinear(
                module.in_features,
                module.out_features,
                bias=module.bias is not None,
                bit_width=bit_width,
                frac_width=frac_width,
                device=module.weight.device,
                dtype=module.weight.dtype,
            )
            with torch.no_grad():
                q.weight.copy_(module.weight)
                if module.bias is not None:
                    q.bias.copy_(module.bias)
            parts = name.split(".")
            parent = model
            for p in parts[:-1]:
                parent = getattr(parent, p)
            to_replace.append((parent, parts[-1], q))

        elif want_conv2d and isinstance(module, nn.Conv2d):
            q = QuantConv2d(
                module.in_channels,
                module.out_channels,
                module.kernel_size,
                stride=module.stride,
                padding=module.padding,
                dilation=module.dilation,
                groups=module.groups,
                bias=module.bias is not None,
                padding_mode=module.padding_mode,
                bit_width=bit_width,
                frac_width=frac_width,
                device=module.weight.device,
                dtype=module.weight.dtype,
            )
            with torch.no_grad():
                q._conv.weight.copy_(module.weight)
                if module.bias is not None:
                    q._conv.bias.copy_(module.bias)
            parts = name.split(".")
            parent = model
            for p in parts[:-1]:
                parent = getattr(parent, p)
            to_replace.append((parent, parts[-1], q))

    for parent, attr_name, new_module in to_replace:
        setattr(parent, attr_name, new_module)

    return model


def replace_one_layer_with_quant(
    model: nn.Module,
    layer_name: str,
    bit_width: int,
) -> nn.Module:
    """
    Replace only the module at `layer_name` with QuantLinear (or QuantConv2d) at given bit_width.
    Used for sensitivity: "accuracy drop when only this layer is quantized to bit_width".
    Modifies model in place. Handles nn.Linear, QuantLinear, nn.Conv2d, QuantConv2d.
    """
    parts = layer_name.split(".")
    parent = model
    for p in parts[:-1]:
        parent = getattr(parent, p)
    attr_name = parts[-1]
    module = getattr(parent, attr_name)

    fw = bit_width // 2
    if isinstance(module, nn.Linear):
        q = QuantLinear(
            module.in_features,
            module.out_features,
            bias=module.bias is not None,
            bit_width=bit_width,
            frac_width=fw,
            device=module.weight.device,
            dtype=module.weight.dtype,
        )
        with torch.no_grad():
            q.weight.copy_(module.weight)
            if module.bias is not None:
                q.bias.copy_(module.bias)
        setattr(parent, attr_name, q)
    elif isinstance(module, QuantLinear):
        q = QuantLinear(
            module.in_features,
            module.out_features,
            bias=module.bias is not None,
            bit_width=bit_width,
            frac_width=fw,
            device=module.weight.device,
            dtype=module.weight.dtype,
        )
        with torch.no_grad():
            q.weight.copy_(module.weight)
            if module.bias is not None:
                q.bias.copy_(module.bias)
        setattr(parent, attr_name, q)
    elif isinstance(module, nn.Conv2d):
        q = QuantConv2d(
            module.in_channels,
            module.out_channels,
            module.kernel_size,
            stride=module.stride,
            padding=module.padding,
            dilation=module.dilation,
            groups=module.groups,
            bias=module.bias is not None,
            padding_mode=module.padding_mode,
            bit_width=bit_width,
            frac_width=fw,
            device=module.weight.device,
            dtype=module.weight.dtype,
        )
        with torch.no_grad():
            q._conv.weight.copy_(module.weight)
            if module.bias is not None:
                q._conv.bias.copy_(module.bias)
        setattr(parent, attr_name, q)
    elif isinstance(module, QuantConv2d):
        q = QuantConv2d(
            module._conv.in_channels,
            module._conv.out_channels,
            module._conv.kernel_size,
            stride=module._conv.stride,
            padding=module._conv.padding,
            dilation=module._conv.dilation,
            groups=module._conv.groups,
            bias=module._conv.bias is not None,
            padding_mode=module._conv.padding_mode,
            bit_width=bit_width,
            frac_width=fw,
            device=module._conv.weight.device,
            dtype=module._conv.weight.dtype,
        )
        with torch.no_grad():
            q._conv.weight.copy_(module._conv.weight)
            if module._conv.bias is not None:
                q._conv.bias.copy_(module._conv.bias)
        setattr(parent, attr_name, q)
    else:
        raise TypeError(f"Layer {layer_name} is {type(module)}; only Linear/QuantLinear/Conv2d/QuantConv2d supported.")
    return model
