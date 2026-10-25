"""Blended white + #F24B18 gradients for the 4th thumbnail (480 x 463), no grain.

    python3 backgrounds/make_orange_blend.py

The two colours melt into each other through a warped (freeform, not linear
or radial) field. Mostly light, the centre kept lightest for the system map;
in a few spots the blend tightens so it feels lively. OKLab mix, sub-step
dither only. Writes orange-blend-<name>.png, @2x, and an overview.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from make_gradients import oklab_to_srgb, srgb_to_oklab

OUT = Path(__file__).resolve().parent
W, H = 480, 463
AR = W / H
WHITE = srgb_to_oklab(np.array([253, 251, 249], float))
ORANGE = srgb_to_oklab(np.array([0xF2, 0x4B, 0x18], float))


def swirl(x, y, k):
    x1 = x + k * (0.14 * np.sin(2.2 * y + 0.6) + 0.06 * np.sin(4.4 * y - 1.6 * x + 2.0))
    y1 = y + k * (0.12 * np.cos(1.9 * x + 0.2) + 0.05 * np.cos(4.0 * x + 1.1 * y + 0.5))
    return x1 + k * 0.06 * np.sin(3.2 * y1 + 2.3), y1 + k * 0.05 * np.cos(2.8 * x1 + 1.0)


def glow(x, y, cx, cy, rx, ry, angle=0.0, p=1.6):
    c, s = np.cos(angle), np.sin(angle)
    u, v = (x - cx) * c + (y - cy) * s, -(x - cx) * s + (y - cy) * c
    return np.exp(-(np.sqrt((u / rx) ** 2 + (v / ry) ** 2)) ** p)


def union(*ts):
    out = np.zeros_like(ts[0])
    for t in ts:
        out = 1 - (1 - out) * (1 - np.clip(t, 0, 1))
    return out


def keep_centre_light(x, y, t, amount=0.55):
    c = glow(x, y, AR * 0.5, 0.5, 0.42, 0.38, 0, 2.2)
    return t * (1 - amount * c)


# Each: (warp strength, function of warped x, y). p > 2 tightens a blend (livelier), p < 2 softens it.
DESIGNS = {
    # Warm orange melting in from the bottom right and top left, white between.
    "glow": (1.4, lambda x, y: union(
        0.70 * glow(x, y, 1.10, 1.05, 0.55, 0.42, -0.5, 2.4),
        0.45 * glow(x, y, -0.05, -0.05, 0.42, 0.34, 0.6, 1.8),
        0.25 * glow(x, y, 1.05, 0.10, 0.30, 0.22, 0.4, 1.5))),
    # Orange washes in along the bottom and right edges and curls upward.
    "tide": (1.7, lambda x, y: union(
        0.62 * glow(x, y, 0.55, 1.12, 0.75, 0.30, 0.15, 2.6),
        0.50 * glow(x, y, 1.12, 0.45, 0.25, 0.55, 0.2, 2.2),
        0.22 * glow(x, y, 0.05, 0.25, 0.25, 0.30, 0.0, 1.6))),
    # Several soft clouds of orange of different strengths drifting into the white.
    "clouds": (1.5, lambda x, y: union(
        0.55 * glow(x, y, 0.95, 0.95, 0.40, 0.32, -0.4, 2.0),
        0.42 * glow(x, y, 0.10, 0.12, 0.35, 0.26, 0.5, 2.0),
        0.30 * glow(x, y, 1.02, 0.12, 0.26, 0.20, 0.0, 1.8),
        0.30 * glow(x, y, 0.05, 0.92, 0.28, 0.22, 0.0, 1.8))),
}


def render(design, scale):
    k, f = design
    w, h = W * scale, H * scale
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    x, y = xx / h, yy / h
    qx, qy = swirl(x, y, k)
    t = np.clip(keep_centre_light(x, y, f(qx, qy)), 0, 1)[..., None]
    lab = WHITE * (1 - t) + ORANGE * t
    img = oklab_to_srgb(lab) + np.random.default_rng(3).uniform(-0.5, 0.5, (h, w, 1))
    return Image.fromarray(np.clip(np.round(img), 0, 255).astype(np.uint8))


if __name__ == "__main__":
    thumbs = []
    for name, design in DESIGNS.items():
        for scale, suffix in ((1, ""), (2, "@2x")):
            img = render(design, scale)
            img.save(OUT / f"orange-blend-{name}{suffix}.png")
        thumbs.append((name, img.resize((W, H), Image.LANCZOS)))
        print("wrote", name)
    sheet = Image.new("RGB", (3 * (W + 16) + 16, H + 56), (60, 58, 56))
    d = ImageDraw.Draw(sheet)
    for i, (name, im) in enumerate(thumbs):
        x = 16 + i * (W + 16)
        d.text((x, 16), f"{i + 1}. {name}", fill=(235, 232, 228))
        sheet.paste(im, (x, 34))
    sheet.save(OUT / "orange-blend-overview.png")
