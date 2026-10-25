"""Cut the gigamap into the pieces the re-layout moves around, pixel-exact.

    python3 systemmap/trace/stamps.py

  blocks  each subsystem with everything drawn on it (line ends included);
          the grey page around it is transparent, its platform, illustration
          and paper underside stay opaque.
  tiles   the stepping tiles between subsystems.
  labels  the connection labels: their text and small arrow glyphs only.
  titles  the subsystem titles (optional in the layout).

The page grey (246) is lifted to white, so on a white background every piece
looks exactly as it did on the map. Also writes the corridor line segments
(those outside blocks, tiles and labels) for the graph step.

Writes systemmap/trace/stamps/*.png and stamps.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from extract import BLOCKS, grow, morph, poly_mask  # noqa: E402

SRC = np.asarray(Image.open(HERE.parent / "source/gigamap.webp").convert("RGB")).astype(float)
H, W, _ = SRC.shape
OUT = HERE / "stamps"
OUT.mkdir(exist_ok=True)
PAGE = 246.0
T = np.tan(np.radians(30))

V = SRC.mean(2)
SAT = SRC.max(2) - SRC.min(2)
DEV = np.abs(SRC - PAGE).max(2)
INK = DEV > 14


def lift(rgb):
    """Page grey -> white, everything else scaled the same way."""
    return np.clip(np.round(rgb * 255.0 / PAGE), 0, 255).astype(np.uint8)


def full_poly(pts):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return np.asarray(m) > 0


def save_stamp(name, mask, kind, extra=None):
    ys, xs = np.nonzero(mask)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    m = mask[y0:y1, x0:x1]
    rgb = lift(SRC[y0:y1, x0:x1])
    a = np.where(m, 255, 0).astype(np.uint8)
    Image.fromarray(np.dstack([rgb, a]), "RGBA").save(OUT / f"{name}.png")
    rec = {"name": name, "kind": kind, "x": int(x0), "y": int(y0), "w": int(x1 - x0), "h": int(y1 - y0),
           "cx": float(xs.mean()), "cy": float(ys.mean())}
    if extra:
        rec.update(extra)
    return rec


# Text boxes, the top section and the bottom (intervention) section are not part of the systems map.
EXCLUDE = np.zeros((H, W), bool)
for x0, y0, x1, y1 in [(110, 295, 350, 345), (40, 575, 280, 645), (1708, 365, 1950, 430), (1610, 685, 1850, 748),
                       (884, 965, 1110, 1036)]:
    EXCLUDE[y0:y1, x0:x1] = True
EXCLUDE[:232] = True
for x0, y0, x1, y1 in [(1480, 0, 2000, 270), (690, 0, 870, 252), (895, 0, 1195, 248)]:
    EXCLUDE[y0:y1, x0:x1] = True
EXCLUDE[1048:] = True

records = []

# ---------------------------------------------------------------- blocks
block_masks = {}
for name, b in BLOCKS.items():
    inside = full_poly(b["poly"])
    for cut in b.get("cut", []):
        inside &= ~full_poly(cut)
    pagelike = (SAT <= 6) & (np.abs(V - PAGE) <= 4)
    outside = ~inside
    ys, xs = np.nonzero(inside)
    bx0, bx1, by0, by1 = xs.min() - 6, xs.max() + 7, ys.min() - 6, ys.max() + 7
    sub_in = inside[by0:by1, bx0:bx1]
    sub_page = pagelike[by0:by1, bx0:bx1]
    transparent = grow(~sub_in, ~sub_in | sub_page)
    opaque = sub_in & ~transparent
    # paper underside: from the platform's thick orange edge down to its outline
    crop = SRC[by0:by1, bx0:bx1]
    edge = morph((crop.max(2) - crop.min(2)) > 80, 3, "erode") & sub_in
    neutral = (crop.max(2) - crop.min(2)) <= 6
    outline = neutral & (crop.mean(2) < 241) & (crop.mean(2) > 150) & sub_in
    h, w = sub_in.shape
    bottoms = np.full(w, -1)
    depth = np.full(w, np.nan)
    for x in range(w):
        ey = np.nonzero(edge[:, x])[0]
        if len(ey):
            e = ey.max()
            bottoms[x] = e
            oy = np.nonzero(outline[e + 6:e + 52, x])[0]
            if len(oy):
                depth[x] = 6 + oy.max()
    valid = bottoms >= 0
    if valid.any():
        d = depth.copy()
        good = ~np.isnan(d)
        d[~good] = np.interp(np.nonzero(~good)[0], np.nonzero(good)[0], d[good]) if good.any() else 28
        sm = np.array([np.median(d[max(0, x - 12):x + 13]) for x in range(w)])
        sm = np.clip(sm, 14, 40)
        sm = np.convolve(np.pad(sm, 4, mode="edge"), np.ones(9) / 9, mode="valid")
        tops = np.array([np.nonzero(edge[:, x])[0].min() if valid[x] else h for x in range(w)])
        yy = np.arange(h)[:, None]
        opaque |= valid[None, :] & (yy >= tops[None, :]) & (yy <= (bottoms + sm)[None, :]) & sub_in
        opaque &= ~(valid[None, :] & (yy > (bottoms + sm + 1)[None, :]))
    full = np.zeros((H, W), bool)
    full[by0:by1, bx0:bx1] = opaque
    block_masks[name] = full
    top = [list(p) for p in b["top"]]
    records.append(save_stamp(name, full, "block", {"top": top, "poly": [list(p) for p in b["poly"]]}))
    print("block", name)

BLOCK_ZONE = np.zeros((H, W), bool)
for name, b in BLOCKS.items():
    z = full_poly(b["poly"])
    for cut in b.get("cut", []):
        z &= ~full_poly(cut)
    BLOCK_ZONE |= z

# ---------------------------------------------------------------- titles
TITLES = {
    "title-communication": [(355, 335), (545, 245), (545, 300), (365, 400)],
    "title-user-behaviour": [(1398, 345), (1478, 292), (1548, 286), (1550, 345), (1404, 400)],
    "title-spatial-dynamics": [(815, 510), (935, 455), (940, 515), (820, 580)],
    "title-material-flow": [(115, 730), (305, 635), (310, 680), (120, 765)],
    "title-environmental-impact": [(1375, 700), (1565, 600), (1565, 650), (1380, 765)],
}
TITLE_ZONE = np.zeros((H, W), bool)
for name, pts in TITLES.items():
    z = full_poly(pts) & (SRC[..., 0] - SRC[..., 2] > 40) & ~BLOCK_ZONE
    z = morph(z, 3, "dilate") & INK
    TITLE_ZONE |= morph(full_poly(pts), 5, "dilate")
    records.append(save_stamp(name, z, "title"))

# ---------------------------------------------------------------- tiles
thick_orange = morph((SAT > 80) & (SRC[..., 0] - SRC[..., 2] > 90), 3, "erode")
thick_orange &= ~BLOCK_ZONE & ~EXCLUDE & ~TITLE_ZONE
tm = morph(thick_orange, 3, "dilate")
lab = np.zeros((H, W), int)
from collections import deque  # noqa: E402
n = 0
tiles = []
for y, x in zip(*np.nonzero(tm)):
    if lab[y, x]:
        continue
    n += 1
    q = deque([(y, x)])
    lab[y, x] = n
    pts = []
    while q:
        cy, cx = q.popleft()
        pts.append((cy, cx))
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                yy, xx = cy + dy, cx + dx
                if 0 <= yy < H and 0 <= xx < W and tm[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = n
                    q.append((yy, xx))
    if len(pts) > 120:
        tiles.append(np.array(pts))
TILE_ZONE = np.zeros((H, W), bool)
for i, pts in enumerate(sorted(tiles, key=lambda p: (p[:, 1].mean(), p[:, 0].mean()))):
    # the orange edge is the tile's front; its white top sits above it
    ey0, ey1 = pts[:, 0].min(), pts[:, 0].max()
    ex0, ex1 = pts[:, 1].min(), pts[:, 1].max()
    box = np.zeros((H, W), bool)
    box[max(0, ey0 - 44):ey1 + 2, ex0 - 2:ex1 + 3] = True
    # the tile: anything not page that is connected to its orange edge, within the box
    cand = box & (DEV > 3)
    seed = np.zeros((H, W), bool)
    seed[pts[:, 0], pts[:, 1]] = True
    t = grow(seed, cand | seed)
    t = morph(morph(t, 3, "dilate"), 3, "erode") | t
    # drop thin line pixels that leaked in (keep the solid top + edge)
    solid = morph(morph(t, 5, "erode"), 5, "dilate")
    t &= morph(solid, 5, "dilate")
    TILE_ZONE |= morph(t, 3, "dilate")
    records.append(save_stamp(f"tile-{i:02d}", t, "tile"))
print("tiles", len(tiles))

# ---------------------------------------------------------------- corridor segments
segs = json.loads((HERE / "clean.json").read_text())


def seg_points(s, step=1.0):
    if s["d"] == "v":
        t = np.arange(s["t0"], s["t1"] + 1e-6, step)
        return np.stack([np.full_like(t, s["off"]), t], 1)
    k = -T if s["d"] == "ur" else T
    x = np.arange(s["t0"], s["t1"] + 1e-6, step * np.cos(np.radians(30)))
    return np.stack([x, k * x + s["off"]], 1)


def textiness(s):
    """Share of points along the segment with ink 3-6 px to the side: high for
    lettering written along the same angle, low for a thin connection line."""
    p = seg_points(s, 2.0)
    if s["d"] == "v":
        nx, ny = 1.0, 0.0
    else:
        k = -T if s["d"] == "ur" else T
        nx, ny = -k / np.hypot(1, k), 1 / np.hypot(1, k)
    hits = 0
    for sign in (1, -1):
        for off in (3.5, 5.0):
            q = p + sign * off * np.array([nx, ny])
            xi = np.clip(np.round(q[:, 0]).astype(int), 0, W - 1)
            yi = np.clip(np.round(q[:, 1]).astype(int), 0, H - 1)
            hits = np.maximum(hits, INK[yi, xi].astype(int)) if isinstance(hits, np.ndarray) else INK[yi, xi].astype(int)
    return float(np.mean(hits))


def coverage(s):
    """Share of points along the segment that sit on ink: ~1 for a drawn line,
    lower for dashed arrows and lettering that only line up by chance."""
    p = seg_points(s, 1.0)
    ok = np.zeros(len(p), bool)
    for dx in (-0.6, 0.6):
        for dy in (-0.6, 0.6):
            xi = np.clip(np.round(p[:, 0] + dx).astype(int), 0, W - 1)
            yi = np.clip(np.round(p[:, 1] + dy).astype(int), 0, H - 1)
            ok |= DEV[yi, xi] > 30
    return float(ok.mean())


for s in segs:
    s["tx"] = textiness(s)
    s["text"] = s["tx"] > 0.30 or coverage(s) < 0.86
segs = [s for s in segs if not s["text"]]

LINE = np.zeros((H, W), bool)
long_segs = [s for s in segs if s["t1"] - s["t0"] >= 40]
lm = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(lm)
for s in long_segs:
    p = seg_points(s, 4)
    d.line([tuple(p[0]), tuple(p[-1])], fill=255, width=4)
LINE = np.asarray(lm) > 0

# ---------------------------------------------------------------- labels
text = INK & ~BLOCK_ZONE & ~TILE_ZONE & ~TITLE_ZONE & ~EXCLUDE & (SAT < 140)
text &= ~(SRC[..., 0] - SRC[..., 2] > 22)                     # no orange (intervention) lines


def components(mask, conn8=True):
    lab = np.zeros(mask.shape, np.int32)
    comps = []
    nb = [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy or dx)] if conn8 else [(1, 0), (-1, 0), (0, 1), (0, -1)]
    for y, x in zip(*np.nonzero(mask)):
        if lab[y, x]:
            continue
        lab[y, x] = len(comps) + 1
        q = deque([(y, x)])
        pts = []
        while q:
            cy, cx = q.popleft()
            pts.append((cy, cx))
            for dy, dx in nb:
                yy, xx = cy + dy, cx + dx
                if 0 <= yy < H and 0 <= xx < W and mask[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = len(comps) + 1
                    q.append((yy, xx))
        comps.append(np.array(pts))
    return comps


# Lettering = small marks once the long lines are taken away. Letters touching
# a line are found again by peeling the line pixels off first.
small = np.zeros((H, W), bool)
for pts in components(text & ~LINE):
    h_ = pts[:, 0].max() - pts[:, 0].min() + 1
    w_ = pts[:, 1].max() - pts[:, 1].min() + 1
    span = max(h_, w_)
    if len(pts) >= 5 and (span <= 22 or len(pts) / span >= 3.0):
        small[pts[:, 0], pts[:, 1]] = True
grp = morph(small, 11, "dilate")
labels = []
for pts in components(grp, conn8=False):
    comp = np.zeros((H, W), bool)
    comp[pts[:, 0], pts[:, 1]] = True
    ink = comp & small
    if ink.sum() < 40:
        continue
    # put back stroke pixels a crossing line had taken out of the lettering
    ink |= morph(ink, 3, "dilate") & INK & ~BLOCK_ZONE & ~TILE_ZONE & text
    labels.append(ink)
LABEL_ZONE = np.zeros((H, W), bool)
for i, m in enumerate(sorted(labels, key=lambda m: tuple(np.argwhere(m).mean(0)))):
    LABEL_ZONE |= morph(m, 7, "dilate")
    records.append(save_stamp(f"label-{i:02d}", m, "label"))
print("labels", len(labels))

# Corridor segments: the parts of long-enough segments outside blocks, tiles and excluded areas.
corr = []
blocked = BLOCK_ZONE | EXCLUDE | TILE_ZONE
for s in segs:
    p = seg_points(s, 1.0)
    xi = np.clip(np.round(p[:, 0]).astype(int), 0, W - 1)
    yi = np.clip(np.round(p[:, 1]).astype(int), 0, H - 1)
    free = ~blocked[yi, xi]
    in_label = LABEL_ZONE[yi, xi]
    # runs of free points
    idx = np.nonzero(free)[0]
    if not len(idx):
        continue
    runs = np.split(idx, np.nonzero(np.diff(idx) > 1)[0] + 1)
    for r in runs:
        if len(r) < 10:
            continue
        if in_label[r].mean() > 0.6 and len(r) < 60:      # strokes of label text
            continue
        a, b = p[r[0]], p[r[-1]]
        corr.append({"c": s["c"], "d": s["d"], "a": [round(float(a[0]), 2), round(float(a[1]), 2)],
                     "b": [round(float(b[0]), 2), round(float(b[1]), 2)]})
print("corridor segments", len(corr))

(HERE / "stamps.json").write_text(json.dumps({"stamps": records, "segments": corr}))
