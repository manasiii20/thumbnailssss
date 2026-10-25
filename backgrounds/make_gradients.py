"""Soft white backgrounds tinted with #D33C27, with a fine film grain.

    python3 backgrounds/make_gradients.py

Writes backgrounds/d33c27-<variant>.png (481 x 379) and @2x (962 x 758).
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

OUT = Path(__file__).resolve().parent
W, H = 481, 379
ACCENT = np.array([0xD3, 0x3C, 0x27], float)
WHITE = np.array([252, 250, 248], float)      # a warm white, not a flat #fff


def glow(xx, yy, cx, cy, rx, ry):
    """Very wide, soft falloff (no visible edge)."""
    d2 = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
    return np.exp(-d2)


def render(spots, scale, seed):
    w, h = W * scale, H * scale
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    xx /= w
    yy /= h
    tint = np.zeros((h, w))
    for cx, cy, rx, ry, strength in spots:
        tint = 1 - (1 - tint) * (1 - strength * glow(xx, yy, cx, cy, rx, ry))   # soft union
    img = WHITE[None, None, :] * (1 - tint[..., None]) + ACCENT[None, None, :] * tint[..., None]

    # Grain: monochrome, slightly soft, about the same as the Comma backdrop.
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, (h, w)).astype(np.float32)
    n = np.asarray(Image.fromarray(((n * 40) + 128).clip(0, 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(0.45 * scale))).astype(float)
    n = (n - n.mean()) / n.std()
    img += n[..., None] * 3.4
    return Image.fromarray(np.clip(np.round(img), 0, 255).astype(np.uint8))


VARIANTS = {
    # Warm glow rising from the bottom-right corner, a faint echo top-left.
    "corner-glow": [(1.05, 1.08, 0.62, 0.70, 0.30), (-0.08, -0.10, 0.45, 0.50, 0.12)],
    # A gentle diagonal wash, strongest along the bottom edge.
    "diagonal-wash": [(0.85, 1.25, 0.95, 0.65, 0.26), (0.10, 1.10, 0.55, 0.45, 0.14), (0.95, -0.15, 0.35, 0.35, 0.07)],
    # Soft haze hanging from the top, the centre stays clean white.
    "top-haze": [(0.50, -0.30, 0.85, 0.55, 0.24), (1.05, 0.10, 0.35, 0.45, 0.10), (-0.05, 0.15, 0.30, 0.40, 0.08)],
}

for name, spots in VARIANTS.items():
    for scale, suffix in ((1, ""), (2, "@2x")):
        render(spots, scale, seed=7 + scale).save(OUT / f"d33c27-{name}{suffix}.png")
    print("wrote", name)
