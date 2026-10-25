"""Freeform (mesh-style) gradients of #D33C27 with a little white, no grain.

    python3 backgrounds/make_red_mesh.py

Not linear and not radial: every shape is a stretched, rotated soft patch,
drawn in a warped space so its edges curve organically. #D33C27 is the main
colour; patches lift it towards a warm coral, sink it towards crimson, or let
a little soft white through. Mixed in OKLab so every tint stays the same red.
Writes backgrounds/red-mesh-<name>.png (481 x 379), @2x, and an overview.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from make_gradients import oklab_to_srgb, srgb_to_oklab

OUT = Path(__file__).resolve().parent
W, H = 481, 379

BASE = srgb_to_oklab(np.array([0xD3, 0x3C, 0x27], float))
TONES = {
    "coral": BASE + np.array([+0.085, -0.004, +0.012]),
    "deep": BASE + np.array([-0.075, +0.006, -0.012]),
    "white": srgb_to_oklab(np.array([252, 246, 243], float)),
}


def swirl(x, y, k):
    """Bend space in two layers so soft shapes come out freeform."""
    x1 = x + k * (0.16 * np.sin(2.1 * y + 0.7) + 0.07 * np.sin(4.3 * y - 1.7 * x + 1.9))
    y1 = y + k * (0.13 * np.cos(1.8 * x + 0.3) + 0.06 * np.cos(3.9 * x + 1.2 * y + 0.4))
    x2 = x1 + k * 0.08 * np.sin(3.1 * y1 + 2.4)
    y2 = y1 + k * 0.07 * np.cos(2.7 * x1 + 1.1)
    return x2, y2


def patch(x, y, cx, cy, length, width, angle, k=1.0):
    """A soft elongated patch, rotated: reads as a streak of light, not a circle."""
    c, s = np.cos(angle), np.sin(angle)
    u = (x - cx) * c + (y - cy) * s
    v = -(x - cx) * s + (y - cy) * c
    return k * np.exp(-((u / length) ** 2 + (v / width) ** 2) ** 0.85)


# Each design: warp strength and a list of (tone, cx, cy, length, width, angle, amount).
# x runs 0..1.27 (frame width in height units), y 0..1 top to bottom.
DESIGNS = {
    # A ribbon of soft white curling through the upper left, coral beside it,
    # crimson settling into the lower right.
    "silk": (1.5, [
        ("coral", 0.30, 0.30, 0.55, 0.24, -0.5, 0.85),
        ("white", 0.40, 0.22, 0.42, 0.08, -0.45, 0.60),
        ("deep", 1.10, 0.90, 0.60, 0.26, -0.6, 0.85),
        ("deep", 0.05, 0.95, 0.35, 0.16, 0.3, 0.45),
        ("coral", 1.05, 0.25, 0.35, 0.16, 0.8, 0.40),
    ]),
    # Warm light drifting in from the left with a faint white haze inside it,
    # deeper red folding in from the right edge.
    "drift": (1.7, [
        ("coral", 0.20, 0.60, 0.60, 0.30, 0.9, 0.85),
        ("white", 0.18, 0.55, 0.38, 0.17, 0.95, 0.50),
        ("deep", 1.20, 0.45, 0.55, 0.22, 1.3, 0.80),
        ("coral", 0.85, 0.05, 0.45, 0.14, 0.15, 0.45),
        ("deep", 0.55, 1.05, 0.50, 0.14, -0.1, 0.55),
    ]),
    # A soft white flare sweeping diagonally through the middle, wrapped in
    # coral, with crimson in two corners.
    "flare": (1.3, [
        ("coral", 0.65, 0.48, 0.75, 0.22, -0.7, 0.80),
        ("white", 0.62, 0.50, 0.55, 0.07, -0.72, 0.55),
        ("deep", 0.05, 0.05, 0.45, 0.25, 0.4, 0.70),
        ("deep", 1.22, 0.98, 0.50, 0.25, 0.4, 0.75),
        ("coral", 0.15, 0.90, 0.30, 0.14, -0.2, 0.35),
    ]),
}


def render(design, scale):
    k, patches = design
    w, h = W * scale, H * scale
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    x, y = swirl(xx / h, yy / h, k)
    lab = np.broadcast_to(BASE, (h, w, 3)).copy()
    for tone, cx, cy, length, width, angle, amount in patches:
        t = patch(x, y, cx, cy, length, width, angle, amount)[..., None]
        lab = lab + t * (TONES[tone] - lab)          # each patch blends over what's there
    img = oklab_to_srgb(lab) + np.random.default_rng(3).uniform(-0.5, 0.5, (h, w, 1))
    return Image.fromarray(np.clip(np.round(img), 0, 255).astype(np.uint8))


if __name__ == "__main__":
    thumbs = []
    for name, design in DESIGNS.items():
        for scale, suffix in ((1, ""), (2, "@2x")):
            img = render(design, scale)
            img.save(OUT / f"red-mesh-{name}{suffix}.png")
        thumbs.append((name, img.resize((W, H), Image.LANCZOS)))
        print("wrote", name)
    sheet = Image.new("RGB", (3 * (W + 16) + 16, H + 56), (245, 243, 241))
    d = ImageDraw.Draw(sheet)
    for i, (name, im) in enumerate(thumbs):
        x = 16 + i * (W + 16)
        d.text((x, 16), f"{i + 1}. {name}", fill=(60, 50, 48))
        sheet.paste(im, (x, 34))
    sheet.save(OUT / "red-mesh-overview.png")
