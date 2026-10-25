"""Red gradients built from #D33C27 itself, no grain.

    python3 backgrounds/make_red.py

#D33C27 stays the main colour; each design moves gently towards a lighter,
warmer coral and a deeper crimson made from the same red in OKLab, so it all
reads as one colour catching light. Writes backgrounds/red-<name>.png
(481 x 379) and @2x (962 x 758), plus red-overview.png. A sub-step dither
(at most one colour step) only prevents banding.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from make_gradients import oklab_to_srgb, srgb_to_oklab
from make_natural import warp

OUT = Path(__file__).resolve().parent
W, H = 481, 379
AR = W / H

BASE = srgb_to_oklab(np.array([0xD3, 0x3C, 0x27], float))
# Same red, lifted and warmed (a soft coral) / lowered and cooled (crimson).
LIGHT = BASE + np.array([+0.085, -0.004, +0.012])
DEEP = BASE + np.array([-0.075, +0.006, -0.012])


def soft(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def blob(qx, qy, cx, cy, rx, ry, p=1.7):
    return np.exp(-(np.sqrt(((qx - cx) / rx) ** 2 + ((qy - cy) / ry) ** 2)) ** p)


# Each design returns (lift, deepen): how far each pixel moves towards the
# light coral and towards the deep crimson (0..1). Where both are 0 it is
# exactly #D33C27. x runs 0..1.27, y 0..1 (top to bottom).
DESIGNS = {
    # Light falls from the top left; the red deepens towards the bottom right.
    "glow": lambda x, y: (blob(x, y, 0.05, -0.05, 0.75, 0.65) * 0.9,
                          blob(x, y, AR + 0.05, 1.08, 0.70, 0.60) * 0.8),
    # A soft bloom of light in the middle, edges sinking a little deeper.
    "bloom": lambda x, y: (blob(x, y, AR * 0.5, 0.45, 0.55, 0.45) * 0.75,
                           soft(np.sqrt(((x / AR - 0.5) / 0.62) ** 2 + ((y - 0.5) / 0.62) ** 2) - 0.35) * 0.7),
    # Warm and bright across the top, richer red pooling at the bottom.
    "dusk": lambda x, y: (soft((0.62 - y) / 0.62) * 0.8, soft((y - 0.45) / 0.55) * 0.75),
    # Organic: lighter and deeper patches of the red drifting into each other.
    "mesh": lambda x, y: (lambda q: (
        np.clip(blob(q[0], q[1], 0.25, 0.20, 0.45, 0.38) * 0.85 + blob(q[0], q[1], 1.05, 0.55, 0.30, 0.28) * 0.45, 0, 1),
        np.clip(blob(q[0], q[1], 1.15, 1.00, 0.50, 0.40) * 0.85 + blob(q[0], q[1], 0.15, 1.05, 0.35, 0.25) * 0.45, 0, 1)))(warp(x, y, 1.4)),
}


def render(design, scale):
    w, h = W * scale, H * scale
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    lift, deep = design(xx / h, yy / h)
    lift, deep = np.clip(lift, 0, 1)[..., None], np.clip(deep, 0, 1)[..., None]
    lab = BASE + lift * (LIGHT - BASE) + deep * (DEEP - BASE)
    img = oklab_to_srgb(lab) + np.random.default_rng(3).uniform(-0.5, 0.5, (h, w, 1))
    return Image.fromarray(np.clip(np.round(img), 0, 255).astype(np.uint8))


if __name__ == "__main__":
    thumbs = []
    for name, design in DESIGNS.items():
        for scale, suffix in ((1, ""), (2, "@2x")):
            img = render(design, scale)
            img.save(OUT / f"red-{name}{suffix}.png")
        thumbs.append((name, img.resize((W, H), Image.LANCZOS)))
        print("wrote", name)
    sheet = Image.new("RGB", (2 * (W + 16) + 16, 2 * (H + 40) + 16), (245, 243, 241))
    d = ImageDraw.Draw(sheet)
    for i, (name, im) in enumerate(thumbs):
        x, y = 16 + (i % 2) * (W + 16), 16 + (i // 2) * (H + 40)
        d.text((x, y), f"{i + 1}. {name}", fill=(60, 50, 48))
        sheet.paste(im, (x, y + 18))
    sheet.save(OUT / "red-overview.png")
