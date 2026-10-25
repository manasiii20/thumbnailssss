"""Natural, organic gradients of #D33C27 on white, with fine grain.

    python3 backgrounds/make_natural.py

Writes backgrounds/natural-<variant>.png (481 x 379) and @2x (962 x 758).
The red reaches #D33C27 itself only in the heart of each shape and melts
into white through lighter tints of the same orange-red (mixed in OKLab).
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from make_gradients import ACCENT, WHITE, oklab_to_srgb, srgb_to_oklab

OUT = Path(__file__).resolve().parent
W, H = 481, 379


def warp(x, y, amount=1.0):
    """A gentle, smooth bend so shapes come out organic rather than geometric."""
    wx = 0.13 * np.sin(2.3 * y + 1.1) + 0.06 * np.sin(4.1 * y + 2.0 * x + 2.0)
    wy = 0.11 * np.cos(1.9 * x + 0.4) + 0.05 * np.cos(3.7 * x - 1.3 * y + 1.0)
    return x + amount * wx, y + amount * wy


def wave(x, y):
    """Red rising softly from the lower edge, its top edge a slow wave."""
    qx, qy = warp(x, y)
    crest = 0.58 + 0.10 * np.sin(2.2 * qx + 0.5) + 0.05 * np.sin(4.6 * qx + 2.1)
    t = np.clip((qy - crest) / 0.42, 0, 1) ** 0.9
    haze = 0.22 * np.exp(-(((qx - 1.15) / 0.35) ** 2 + ((qy - 0.05) / 0.30) ** 2))   # faint warmth top right
    return 1 - (1 - t) * (1 - haze)


def bloom(x, y):
    """One organic cloud of red off-centre, with a smaller, paler echo."""
    qx, qy = warp(x, y, 1.6)
    d = np.sqrt(((qx - 0.98) / 0.48) ** 2 + ((qy - 0.88) / 0.40) ** 2)
    a = np.exp(-d ** 1.6)                      # wide, slow falloff: no visible rim
    e = np.sqrt(((qx - 0.18) / 0.32) ** 2 + ((qy - 0.10) / 0.26) ** 2)
    b = 0.30 * np.exp(-e ** 1.6)
    return 1 - (1 - np.clip(a * 1.05, 0, 1)) * (1 - b)


def sweep(x, y):
    """A broad, soft diagonal sweep of red, white above and below it."""
    qx, qy = warp(x, y, 1.3)
    d = (qx * 0.62 + qy * 0.78) - (1.02 + 0.08 * np.sin(3.0 * qx - 1.2 * qy + 0.8))
    core = 0.95 * np.exp(-(d / 0.19) ** 2)
    glow = 0.22 * np.exp(-(d / 0.42) ** 2)
    return np.clip(1 - (1 - core) * (1 - glow), 0, 1)


def clouds(x, y):
    """Several soft clouds of red at different strengths, drifting into each other."""
    qx, qy = warp(x, y, 1.5)
    t = np.zeros_like(qx)
    for cx, cy, rx, ry, k in [(1.08, 0.92, 0.42, 0.36, 1.0), (0.32, 1.00, 0.30, 0.22, 0.50),
                              (0.85, 0.02, 0.32, 0.22, 0.45), (0.02, 0.22, 0.22, 0.26, 0.28)]:
        d = np.sqrt(((qx - cx) / rx) ** 2 + ((qy - cy) / ry) ** 2)
        t = 1 - (1 - t) * (1 - k * np.exp(-d ** 1.6))
    return t


VARIANTS = {"wave": wave, "bloom": bloom, "sweep": sweep, "clouds": clouds}


def render(field, scale, seed):
    w, h = W * scale, H * scale
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    x = xx / h          # keep shapes round: both axes in frame-height units
    y = yy / h
    t = np.clip(field(x, y), 0, 1)
    lab = srgb_to_oklab(WHITE)[None, None] * (1 - t[..., None]) + srgb_to_oklab(ACCENT)[None, None] * t[..., None]
    img = oklab_to_srgb(lab)
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, (h, w)).astype(np.float32)
    n = np.asarray(Image.fromarray(((n * 40) + 128).clip(0, 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(0.45 * scale))).astype(float)
    n = (n - n.mean()) / n.std()
    img += n[..., None] * 3.4
    return Image.fromarray(np.clip(np.round(img), 0, 255).astype(np.uint8))


if __name__ == "__main__":
    for name, field in VARIANTS.items():
        for scale, suffix in ((1, ""), (2, "@2x")):
            render(field, scale, seed=11 + scale).save(OUT / f"natural-{name}{suffix}.png")
        print("wrote", name)
