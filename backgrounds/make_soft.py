"""The light corner glow (white + #D33C27), clean with no grain.

    python3 backgrounds/make_soft.py

Same composition as the corner glow you picked (a warm glow from the bottom
right with a faint echo top left, plain RGB blend), with less red so more
white comes through. Writes backgrounds/soft-corner.png (481 x 379) and @2x.
A sub-step dither (never more than one colour step) stops 8-bit banding; it
isn't visible as texture.
"""
from pathlib import Path

import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent
W, H = 481, 379
ACCENT = np.array([0xD3, 0x3C, 0x27], float)
WHITE = np.array([252, 250, 248], float)
RED = 1.2          # was 1.5 in the version you picked; lower = whiter
SPOTS = [(1.05, 1.08, 0.62, 0.70, 0.30), (-0.08, -0.10, 0.45, 0.50, 0.12)]


def render(scale):
    w, h = W * scale, H * scale
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    xx /= w
    yy /= h
    tint = np.zeros((h, w))
    for cx, cy, rx, ry, k in SPOTS:
        g = np.exp(-(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2))
        tint = 1 - (1 - tint) * (1 - min(1.0, k * RED) * g)
    img = WHITE * (1 - tint[..., None]) + ACCENT * tint[..., None]
    img += np.random.default_rng(3).uniform(-0.5, 0.5, (h, w, 1))   # anti-banding only
    return Image.fromarray(np.clip(np.round(img), 0, 255).astype(np.uint8))


for scale, suffix in ((1, ""), (2, "@2x")):
    render(scale).save(OUT / f"soft-corner{suffix}.png")
print("wrote soft-corner")
