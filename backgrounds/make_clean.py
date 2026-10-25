"""Clean gradients of #D33C27 and white, no grain.

    python3 backgrounds/make_clean.py

Writes backgrounds/clean-<name>.png (481 x 379) and @2x (962 x 758), plus
clean-overview.png. Colours are mixed in OKLab so every tint stays the same
orange-red as #D33C27. A sub-step dither (at most one colour step) only
prevents 8-bit banding; there is no visible texture.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from make_gradients import ACCENT, WHITE, oklab_to_srgb, srgb_to_oklab
from make_natural import warp

OUT = Path(__file__).resolve().parent
W, H = 481, 379
AR = W / H


def soft(x):
    return x * x * (3 - 2 * x)


def blob(qx, qy, cx, cy, rx, ry, k=1.0, p=1.6):
    d = np.sqrt(((qx - cx) / rx) ** 2 + ((qy - cy) / ry) ** 2)
    return k * np.exp(-d ** p)


def union(*ts):
    out = np.zeros_like(ts[0])
    for t in ts:
        out = 1 - (1 - out) * (1 - np.clip(t, 0, 1))
    return out


# Coordinates: x runs 0..1.27 (frame width in height units), y runs 0..1 top to bottom.
DESIGNS = {
    # Red pooled low, fading up into white: like warm light from below.
    "dawn": lambda x, y: 0.88 * soft(np.clip((y - 0.25) / 0.85, 0, 1)) ** 1.3
    + 0.10 * blob(x, y, AR * 0.5, 1.15, 0.9, 0.5),
    # A glow rising from below the bottom edge, white all around it.
    "sunrise": lambda x, y: blob(x, y, AR * 0.55, 1.18, 0.62, 0.55, 1.0, 1.8),
    # Clean diagonal: white top left, the red gathering bottom right.
    "diagonal": lambda x, y: 0.92 * soft(np.clip((x / AR * 0.55 + y * 0.6 - 0.35) / 0.8, 0, 1)) ** 1.4,
    # A soft band of warmth across the lower third, white above and a lighter tint below.
    "horizon": lambda x, y: union(blob(x, y, AR * 0.5, 0.78, 1.6, 0.20, 0.85, 2.0),
                                  0.25 * soft(np.clip((y - 0.6) / 0.4, 0, 1))),
    # Light from the right edge, white on the left.
    "side": lambda x, y: union(blob(x, y, AR + 0.12, 0.62, 0.55, 0.75, 0.95, 1.7),
                               blob(x, y, AR + 0.05, 0.05, 0.25, 0.25, 0.35, 1.7)),
    # Organic: a few soft shapes of red drifting into each other, plenty of white.
    "mesh": lambda x, y: (lambda q: union(
        blob(q[0], q[1], 1.08, 0.92, 0.42, 0.36, 1.0),
        blob(q[0], q[1], 0.32, 1.00, 0.30, 0.22, 0.45),
        blob(q[0], q[1], 0.85, 0.02, 0.32, 0.22, 0.40),
        blob(q[0], q[1], 0.02, 0.22, 0.22, 0.26, 0.25)))(warp(x, y, 1.5)),
    # Red rising from the bottom with a slow wavy top edge.
    "wave": lambda x, y: (lambda q: union(
        np.clip((q[1] - (0.58 + 0.10 * np.sin(2.2 * q[0] + 0.5) + 0.05 * np.sin(4.6 * q[0] + 2.1))) / 0.42, 0, 1) ** 0.9,
        0.22 * np.exp(-(((q[0] - 1.15) / 0.35) ** 2 + ((q[1] - 0.05) / 0.30) ** 2))))(warp(x, y)),
    # A broad soft curve of red sweeping up through the frame.
    "sweep": lambda x, y: (lambda q: (lambda d: union(0.95 * np.exp(-(d / 0.19) ** 2), 0.22 * np.exp(-(d / 0.42) ** 2)))(
        (q[0] * 0.62 + q[1] * 0.78) - (1.02 + 0.08 * np.sin(3.0 * q[0] - 1.2 * q[1] + 0.8))))(warp(x, y, 1.3)),
}


def render(field, scale):
    w, h = W * scale, H * scale
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    t = np.clip(field(xx / h, yy / h), 0, 1)
    lab = srgb_to_oklab(WHITE)[None, None] * (1 - t[..., None]) + srgb_to_oklab(ACCENT)[None, None] * t[..., None]
    img = oklab_to_srgb(lab) + np.random.default_rng(3).uniform(-0.5, 0.5, (h, w, 1))
    return Image.fromarray(np.clip(np.round(img), 0, 255).astype(np.uint8))


if __name__ == "__main__":
    thumbs = []
    for name, field in DESIGNS.items():
        for scale, suffix in ((1, ""), (2, "@2x")):
            img = render(field, scale)
            img.save(OUT / f"clean-{name}{suffix}.png")
        thumbs.append((name, img.resize((W, H), Image.LANCZOS)))
        print("wrote", name)
    cols = 4
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (W + 16) + 16, rows * (H + 40) + 16), (245, 243, 241))
    d = ImageDraw.Draw(sheet)
    for i, (name, im) in enumerate(thumbs):
        x, y = 16 + (i % cols) * (W + 16), 16 + (i // cols) * (H + 40)
        d.text((x, y), f"{i + 1}. {name}", fill=(60, 50, 48))
        sheet.paste(im, (x, y + 18))
    sheet.save(OUT / "clean-overview.png")
