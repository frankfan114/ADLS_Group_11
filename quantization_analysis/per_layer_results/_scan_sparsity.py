"""One-off: scan *_linear_per_layer.json and *_conv_per_layer.json for sparsity rankings."""
import json
import pathlib

root = pathlib.Path(__file__).parent
rows = []
for p in sorted(root.glob("*.json")):
    if p.name.startswith("five_layers") or p.parent.name == "weights":
        continue
    if "_linear_per_layer" not in p.name and "_conv_per_layer" not in p.name:
        continue
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        continue
    key = "linear_layers" if "linear_layers" in d else "conv_layers" if "conv_layers" in d else None
    if not key:
        continue
    kind = "linear" if key == "linear_layers" else "conv"
    for L in d[key]:
        w0 = L.get("weight_sparsity_zero") or 0.0
        wnz = L.get("weight_sparsity_near_zero") or 0.0
        a0 = L.get("activation_sparsity_zero")
        anz = L.get("activation_sparsity_near_zero")
        a0f = a0 if a0 is not None else 0.0
        anzf = anz if anz is not None else 0.0
        mx = max(w0, wnz, a0f, anzf)
        rows.append(
            {
                "file": p.name,
                "kind": kind,
                "name": L.get("name", ""),
                "w0": w0,
                "wnz": wnz,
                "a0": a0,
                "anz": anz,
                "max": mx,
            }
        )

rows.sort(key=lambda r: r["max"], reverse=True)
print("=== Top 30 layers by max(weight_sparsity_*, activation_sparsity_*) ===\n")
for r in rows[:30]:
    print(
        f"max={r['max']:.6f} | {r['kind']:5} | "
        f"w0={r['w0']:.6f} wnz={r['wnz']:.6f} | "
        f"a0={r['a0']} anz={r['anz']} | "
        f"{r['name'][:70]}"
    )
    print(f"         file: {r['file']}\n")

# Summary: how many have any metric > 1e-4
hi = [r for r in rows if r["max"] > 1e-4]
print(f"Layers with max sparsity > 1e-4: {len(hi)} / {len(rows)}")
if not hi:
    print("(No structurally sparse layers; values are mostly near-zero float noise.)")
