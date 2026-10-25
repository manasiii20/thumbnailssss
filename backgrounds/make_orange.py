"""Light, playful white + #F24B18 gradients for the 4th thumbnail (480 x 463).

    python3 backgrounds/make_orange.py

Mostly white so a system map can sit on top. The orange comes in as soft
silk-like folds: each fold has one crisp edge (the "sharp" part) and fades
out smoothly on the other side, and the folds curve so nothing is linear or
radial. The middle of the frame is kept the lightest. No grain; a sub-step
dither (at most one colour step) only prevents banding. Mixed in OKLab so
every tint stays the same orange. Writes orange-<name>.png, @2x, and an overview.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from make_gradients import oklab_to_srgb, srgb_to_oklab

OUT = Path(__file__).resolve().parent
W, H = 480, 463
WHITE = srgb_to_oklab(np.array([253, 251, 249], float))
ORANGE = srgb_to_oklab(np.array([0xF2, 0x4B, 0x18], float))


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def fold(x, y, p0, p1, bend, side, edge, fade, k):
    """A curved fold line from p0 to p1 (bowed by `bend`).

    On `side` (+1/-1) the orange starts at a crisp edge (`edge` wide) and
    fades out over `fade`; the other side stays white.
    """
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    L = np.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    s = ((x - x0) * ux + (y - y0) * uy) / L          # 0..1 along the line
    d = (x - x0) * -uy + (y - y0) * ux                 # signed distance from it
    d = d - bend * np.sin(np.pi * np.clip(s, -0.3, 1.3)) - 0.025 * np.sin(7 * s + 1.3)
    d = d * side
    rise = smooth(-edge, edge, d)                      # the crisp edge
    fall = np.exp(-np.clip(d, 0, None) / fade)         # the smooth tail
    along = smooth(-0.15, 0.25, s) * smooth(1.15, 0.75, s)   # fade at the ends
    return k * rise * fall * along


def union(*ts):
    out = np.zeros_like(ts[0])
    for t in ts:
        out = 1 - (1 - out) * (1 - np.clip(t, 0, 1))
    return out


# x runs 0..1.04 (width in height units), y 0..1 top to bottom.
DESIGNS = {
    # Two silk folds sweeping in from opposite corners, crisp edges facing the centre.
    "silk": lambda x, y: union(
        fold(x, y, (-0.1, 0.42), (0.62, -0.1), 0.06, -1, 0.006, 0.20, 0.42),
        fold(x, y, (0.40, 1.12), (1.16, 0.50), -0.07, +1, 0.006, 0.22, 0.46),
        fold(x, y, (0.70, 1.10), (1.15, 0.80), 0.03, +1, 0.004, 0.10, 0.22)),
    # Petals: three curved shapes tucked into the edges, like paper layered behind.
    "petals": lambda x, y: union(
        fold(x, y, (0.50, -0.1), (1.15, 0.45), 0.08, -1, 0.005, 0.18, 0.42),
        fold(x, y, (0.78, -0.1), (1.15, 0.18), 0.03, -1, 0.004, 0.08, 0.30),
        fold(x, y, (-0.12, 0.55), (0.50, 1.12), -0.08, +1, 0.005, 0.18, 0.44),
        fold(x, y, (-0.12, 0.82), (0.22, 1.12), -0.02, +1, 0.004, 0.07, 0.28)),
    # One long crisp crease running corner to corner with a soft glow behind it,
    # plus a whisper of orange top left.
    "crease": lambda x, y: union(
        fold(x, y, (-0.1, 1.02), (1.16, 0.18), -0.10, +1, 0.005, 0.26, 0.38),
        fold(x, y, (0.15, 1.12), (1.16, 0.62), -0.05, +1, 0.004, 0.10, 0.30),
        fold(x, y, (-0.12, 0.30), (0.35, -0.12), 0.04, -1, 0.008, 0.12, 0.18)),
}


def render(field, scale):
    w, h = W * scale, H * scale
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    t = np.clip(field(xx / h, yy / h), 0, 1)[..., None]
    lab = WHITE * (1 - t) + ORANGE * t
    img = oklab_to_srgb(lab) + np.random.default_rng(3).uniform(-0.5, 0.5, (h, w, 1))
    return Image.fromarray(np.clip(np.round(img), 0, 255).astype(np.uint8))


if __name__ == "__main__":
    thumbs = []
    for name, field in DESIGNS.items():
        for scale, suffix in ((1, ""), (2, "@2x")):
            img = render(field, scale)
            img.save(OUT / f"orange-{name}{suffix}.png")
        thumbs.append((name, img.resize((W, H), Image.LANCZOS)))
        print("wrote", name)
    sheet = Image.new("RGB", (3 * (W + 16) + 16, H + 56), (60, 58, 56))
    d = ImageDraw.Draw(sheet)
    for i, (name, im) in enumerate(thumbs):
        x = 16 + i * (W + 16)
        d.text((x, 16), f"{i + 1}. {name}", fill=(235, 232, 228))
        sheet.paste(im, (x, 34))
    sheet.save(OUT / "orange-overview.png")
