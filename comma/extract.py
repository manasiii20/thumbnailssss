"""Builds the sprite assets for the Comma show reel from the two design frames.

    python3 comma/extract.py

Reads comma/source/01-collapsed.webp and 02-expanded.webp (961 x 634, i.e. the
479 x 316 frame at 2x) and writes comma/assets/:

  f1.png, f2.png   the two frames, used as-is for the resting states
  f2new.png        frame 2 with the elements that morph from frame 1 painted
                   out, so the "new" parts can fade in without doubling up
  av-c-*.png       collapsed avatars (45 px circles), av-e-*.png expanded (31 px)
  embedded.js      everything above as data URIs, plus layout.js data, so
                   index.html runs straight from disk
"""
import base64
import io
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "source"
OUT = ROOT / "assets"
CARD = 51  # card fill, #333

f1 = np.asarray(Image.open(SRC / "01-collapsed.webp").convert("RGB")).copy()
f2 = np.asarray(Image.open(SRC / "02-expanded.webp").convert("RGB")).copy()

# Avatar circles (source pixel coordinates).
AV_C = [(569.5, 349.0), (606.5, 349.0), (643.5, 349.0), (680.5, 349.0)]
R_C = 22.5
AV_E = [(287.0, 493.0), (394.0, 493.0), (505.0, 493.0), (616.0, 493.0)]
R_E = 15.5


def circle_mask(size, cx, cy, r, ss=4):
    """Anti-aliased circle mask (0..1) of the given size, centre in pixel coords."""
    big = Image.new("L", (size[0] * ss, size[1] * ss), 0)
    ImageDraw.Draw(big).ellipse(
        ((cx - r) * ss, (cy - r) * ss, (cx + r) * ss, (cy + r) * ss), fill=255
    )
    return np.asarray(big.resize(size, Image.LANCZOS)).astype(float) / 255.0


def rgba(rgb, alpha):
    out = np.zeros(rgb.shape[:2] + (4,), np.uint8)
    out[..., :3] = rgb
    out[..., 3] = np.clip(np.round(alpha * 255), 0, 255)
    return Image.fromarray(out)


# Expanded avatars: plain circles cut from frame 2.
av_e = []
for i, (cx, cy) in enumerate(AV_E):
    n = int(np.ceil(R_E * 2)) + 4
    x0, y0 = int(round(cx - n / 2)), int(round(cy - n / 2))
    crop = f2[y0 : y0 + n, x0 : x0 + n]
    m = circle_mask((n, n), cx - x0, cy - y0, R_E + 0.3)
    img = rgba(crop, m)
    img.save(OUT / f"av-e-{i}.png")
    av_e.append({"img": f"av-e-{i}", "x": x0, "y": y0, "w": n, "h": n})

# Collapsed avatars: each one's visible part comes from frame 1; the slice that
# the next avatar hides is filled in from the (upscaled) expanded avatar, so the
# circle is whole when the row spreads apart.
av_c = []
for i, (cx, cy) in enumerate(AV_C):
    n = int(np.ceil(R_C * 2)) + 4
    x0, y0 = int(round(cx - n / 2)), int(round(cy - n / 2))
    crop = f1[y0 : y0 + n, x0 : x0 + n].astype(float)
    m = circle_mask((n, n), cx - x0, cy - y0, R_C + 0.3)
    if i < 3:
        nx, ny = AV_C[i + 1]
        hidden = circle_mask((n, n), nx - x0, ny - y0, R_C + 1.5)
        e = Image.open(OUT / f"av-e-{i}.png")
        s = R_C / R_E
        up = e.resize((int(round(e.width * s)), int(round(e.height * s))), Image.LANCZOS)
        fill = Image.new("RGBA", (n, n), (CARD, CARD, CARD, 255))
        ex, ey = AV_E[i]
        ox = cx - x0 - (ex - av_e[i]["x"]) * s
        oy = cy - y0 - (ey - av_e[i]["y"]) * s
        fill.alpha_composite(up, (int(round(ox)), int(round(oy))))
        fill = np.asarray(fill.convert("RGB")).astype(float)
        crop = crop * (1 - hidden[..., None]) + fill * hidden[..., None]
    img = rgba(crop.astype(np.uint8), m)
    img.save(OUT / f"av-c-{i}.png")
    av_c.append({"img": f"av-c-{i}", "x": x0, "y": y0, "w": n, "h": n})

# Frame 2 with the morphing elements painted out (bar, %, icons, chip avatars).
f2new = f2.copy()
for x0, y0, x1, y1 in [
    (362, 192, 470, 208),  # progress bar
    (474, 192, 505, 209),  # 78%
    (263, 382, 279, 402),  # priority flag
    (261, 426, 279, 446),  # status icon
]:
    f2new[y0:y1, x0:x1] = CARD
for cx, cy in AV_E:
    m = circle_mask((f2.shape[1], f2.shape[0]), cx, cy, R_E + 1.2)
    f2new = (f2new * (1 - m[..., None]) + CARD * m[..., None]).astype(np.uint8)

# Compression left the card at 50-52 in places; snap it to #333 so faded-in
# pieces sit seamlessly on the drawn card.
near = (np.abs(f2new.astype(int) - CARD) <= 2).all(axis=2)
f2new[near] = CARD

Image.fromarray(f1).save(OUT / "f1.png")
Image.fromarray(f2).save(OUT / "f2.png")
Image.fromarray(f2new).save(OUT / "f2new.png")

# The backdrop is the separate gradient export (959 wide; it lines up with the
# frames 1 px in). The resting cards are cut out of their frames along the
# card's rounded edge, so they always sit on this one backdrop.
Image.open(SRC / "00-gradient.webp").convert("RGB").save(OUT / "bg.png")
CARD_RADIUS = 22
CARD_FROM = [232, 244, 728, 389]
CARD_TO = [232, 87, 728, 546]


def card_cutout(frame, box, name, ss=4):
    x0, y0, x1, y1 = box
    big = Image.new("L", ((x1 - x0) * ss, (y1 - y0) * ss), 0)
    ImageDraw.Draw(big).rounded_rectangle(
        (0.4 * ss, 0.4 * ss, (x1 - x0 - 0.4) * ss, (y1 - y0 - 0.4) * ss), radius=CARD_RADIUS * ss, fill=255
    )
    m = np.asarray(big.resize((x1 - x0, y1 - y0), Image.LANCZOS)).astype(float) / 255
    rgba(frame[y0:y1, x0:x1], m).save(OUT / f"{name}.png")


card_cutout(f1, CARD_FROM, "c1")
card_cutout(f2, CARD_TO, "c2")

# The dashboard window, with its own shadow, exactly as exported.
Image.open(SRC / "03-dashboard.png").convert("RGBA").save(OUT / "dash.png")

# Layout: boxes are [x0, y0, x1, y1] in source pixels.
layout = {
    "size": [961, 634],
    "bgOffset": [1, 0],
    "card": {"color": "#333333", "radius": CARD_RADIUS, "from": CARD_FROM, "to": CARD_TO},
    # Dashboard resting position (top-left of dashboard.png) in the final frame,
    # and the gap between the expanded card's bottom and the dashboard window's
    # top while they scroll up together (from the mid-way reference frame).
    "dash": {"x": 15, "y": 69, "windowTop": 3, "gap": 202},
    "pill": {"color": "#262626", "from": [259, 263, 456, 305, 10], "to": [265, 118, 500, 164, 11]},
    # Elements present in both frames: they glide from one box to the other,
    # cross-fading frame-1 pixels into frame-2 pixels. Drawn with "lighten".
    "shared": {
        "title": {"from": [276, 272, 438, 298], "to": [292, 129, 472, 156]},
        "bar": {"from": [492, 273, 645, 290], "to": [362, 194, 469, 207]},
        "pct": {"from": [665, 273, 698, 291], "to": [474, 193, 504, 209]},
        "flag": {"from": [256, 338, 272, 358], "to": [264, 383, 278, 401]},
        "status": {"from": [383, 338, 403, 358], "to": [262, 427, 278, 445]},
    },
    # Only in frame 1: fade out while travelling with their anchor.
    "old": {
        "credits": {"box": [277, 337, 363, 360], "anchor": "flag"},
        "testing": {"box": [407, 337, 479, 362], "anchor": "status"},
    },
    # Only in frame 2: fade in (staggered) while travelling with their anchor.
    "new": [
        {"name": "steps", "box": [260, 179, 521, 222], "anchor": "bar", "order": 0},
        {"name": "row1", "box": [284, 219, 540, 262], "anchor": None, "order": 1},
        {"name": "row2", "box": [284, 262, 540, 296], "anchor": None, "order": 2},
        {"name": "row3", "box": [284, 296, 540, 330], "anchor": None, "order": 3},
        {"name": "row4", "box": [284, 330, 540, 362], "anchor": None, "order": 4},
        {"name": "priority", "box": [281, 378, 333, 407], "anchor": "flag", "order": 5},
        {"name": "urgent", "box": [346, 377, 432, 410], "anchor": "flag", "order": 5},
        {"name": "statusLabel", "box": [281, 420, 331, 450], "anchor": "status", "order": 6},
        {"name": "inprogress", "box": [346, 419, 457, 451], "anchor": "status", "order": 6},
        {"name": "chip0", "box": [260, 467, 368, 520], "anchor": "av0", "order": 7},
        {"name": "chip1", "box": [368, 467, 479, 520], "anchor": "av1", "order": 7},
        {"name": "chip2", "box": [479, 467, 589, 520], "anchor": "av2", "order": 7},
        {"name": "chip3", "box": [589, 467, 700, 520], "anchor": "av3", "order": 7},
    ],
    "avatars": [
        {"from": {"cx": AV_C[i][0], "cy": AV_C[i][1], "r": R_C, **av_c[i]},
         "to": {"cx": AV_E[i][0], "cy": AV_E[i][1], "r": R_E, **av_e[i]}}
        for i in range(4)
    ],
}


def data_uri(p):
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()


images = {p.stem: data_uri(p) for p in sorted(OUT.glob("*.png"))}
(OUT / "embedded.js").write_text(
    "// Generated by comma/extract.py — do not edit by hand.\n"
    "window.COMMA_ASSETS = " + json.dumps({"images": images, "layout": layout}) + ";\n"
)
print("wrote", ", ".join(sorted(images)))
