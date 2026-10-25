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
RED = 1.5                                      # overall amount of #D33C27 (1 = the first, lighter round)


def srgb_to_oklab(c):
    c = c / 255.0
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    m1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929],
                   [0.2119034982, 0.6806995451, 0.1073969566],
                   [0.0883024619, 0.2817188376, 0.6299787005]])
    lms = np.cbrt(lin @ m1.T)
    m2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468],
                   [1.9779984951, -2.4285922050, 0.4505937099],
                   [0.0259040371, 0.7827717662, -0.8086757660]])
    return lms @ m2.T


def oklab_to_srgb(lab):
    m2i = np.array([[1.0, 0.3963377774, 0.2158037573],
                    [1.0, -0.1055613458, -0.0638541728],
                    [1.0, -0.0894841775, -1.2914855480]])
    lms = (lab @ m2i.T) ** 3
    m1i = np.array([[4.0767416621, -3.3077115913, 0.2309699292],
                    [-1.2684380046, 2.6097574011, -0.3413193965],
                    [-0.0041960863, -0.7034186147, 1.7076147010]])
    lin = np.clip(lms @ m1i.T, 0, 1)
    c = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)
    return c * 255.0


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
        tint = 1 - (1 - tint) * (1 - min(1.0, strength * RED) * glow(xx, yy, cx, cy, rx, ry))   # soft union
    # Mix in OKLab so the lighter tints stay the same orange-red as #D33C27
    # instead of drifting towards pink the way a plain RGB mix does.
    lab = srgb_to_oklab(WHITE)[None, None, :] * (1 - tint[..., None]) + srgb_to_oklab(ACCENT)[None, None, :] * tint[..., None]
    img = oklab_to_srgb(lab)

    # Grain: monochrome, slightly soft, about the same as the Comma backdrop.
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, (h, w)).astype(np.float32)
    n = np.asarray(Image.fromarray(((n * 40) + 128).clip(0, 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(0.45 * scale))).astype(float)
    n = (n - n.mean()) / n.std()
    img += n[..., None] * 3.4
    return Image.fromarray(np.clip(np.round(img), 0, 255).astype(np.uint8))


VARIANTS = {
    # The red is spread over several soft glows with open white between them.
    # The bottom-right and top-left corners reach #D33C27 itself (0.67 x RED
    # caps at full strength). Strengths are before the RED multiplier.
    "corner-glow": [(1.0, 1.0, 0.43, 0.45, 0.67), (0.0, 0.0, 0.31, 0.33, 0.67),
                    (1.10, 0.30, 0.22, 0.26, 0.12), (0.12, 1.14, 0.28, 0.20, 0.10)],
    # A gentle diagonal wash, strongest along the bottom edge.
    "diagonal-wash": [(0.85, 1.25, 0.95, 0.65, 0.26), (0.10, 1.10, 0.55, 0.45, 0.14), (0.95, -0.15, 0.35, 0.35, 0.07)],
    # Soft haze hanging from the top, the centre stays clean white.
    "top-haze": [(0.50, -0.30, 0.85, 0.55, 0.24), (1.05, 0.10, 0.35, 0.45, 0.10), (-0.05, 0.15, 0.30, 0.40, 0.08)],
}

for name, spots in VARIANTS.items():
    for scale, suffix in ((1, ""), (2, "@2x")):
        render(spots, scale, seed=7 + scale).save(OUT / f"d33c27-{name}{suffix}.png")
    print("wrote", name)
