"""Re-arrange the gigamap's systems layer into the 480 x 463 thumbnail.

    python3 systemmap/compact.py            # render
    python3 systemmap/compact.py --profile  # print where each cut can run

Every pixel of the map is kept; nothing is redrawn except the stepping
tiles. The four corner subsystems are slid towards Spatial Dynamics along
isometric cut lines that run between the drawings: a cut never crosses an
illustration or a label, and only removes space where nothing sits. Any
connection line that crosses a cut is re-joined along the cut, so each line
keeps its route on the map's 30-degree grid. The stepping tiles are taken
off and laid again between the moved subsystems; the titles ride along with
their subsystem. The page grey becomes plain white.

Writes systemmap/exports/system-map@2x.png (960 x 926) and system-map.png.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
T = np.tan(np.radians(30))
PAGE = 246.0
PROFILE = "--profile" in sys.argv

SRC = np.asarray(Image.open(HERE / "source/gigamap.webp").convert("RGB")).astype(float)
H, W, _ = SRC.shape
STAMPS = json.loads((HERE / "trace/stamps.json").read_text())
SEGS = json.loads((HERE / "trace/clean.json").read_text())
STAMP_DIR = HERE / "trace/stamps"

FAM = {"ur": lambda x, y: y + T * x, "dr": lambda x, y: y - T * x}
DIRS = {"ur": np.array([0.866, -0.5]), "dr": np.array([0.866, 0.5]), "v": np.array([0.0, 1.0])}

# ------------------------------------------------------------------ the cuts
# (subsystem that moves, family, cut value, side that moves (+1 = values above), shift)
# Target centres (source px): Spatial Dynamics stays put; the other four sit
# around it 2-1-2. Each move is a slide along its cut plus, where needed, a
# step outward (always safe) or a small step inward (only through empty space).
TARGET = {
    "communication": (600, 410), "user-behaviour": (1370, 390),
    "material-flow": (483, 1068), "environmental-impact": (1370, 1050),
}
CUTS = [
    ("material-flow", "dr", 456, +1),
    ("environmental-impact", "ur", 1620, +1),
    ("user-behaviour", "dr", -268, -1),
    ("communication", "ur", 966, -1),
]
# Small nudges for the titles after they follow their subsystem (source px).
TITLE_NUDGE = {"spatial-dynamics": (-112, 26), "environmental-impact": (52, -22)}


def morph(mask, size, op):
    f = ImageFilter.MaxFilter(size) if op == "dilate" else ImageFilter.MinFilter(size)
    return np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).filter(f)) > 0


def stamp_mask(r):
    a = np.asarray(Image.open(STAMP_DIR / f"{r['name']}.png"))[..., 3] > 0
    m = np.zeros((H, W), bool)
    m[r["y"]:r["y"] + r["h"], r["x"]:r["x"] + r["w"]] = a
    return m


def seg_ends(s):
    if s["d"] == "v":
        return (s["off"], s["t0"]), (s["off"], s["t1"])
    k = -T if s["d"] == "ur" else T
    return (s["t0"], k * s["t0"] + s["off"]), (s["t1"], k * s["t1"] + s["off"])


def draw_lines(size, lines, ss=4):
    w, h = size
    layer = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for (x0, y0), (x1, y1), col, width in lines:
        d.line([(x0 * ss, y0 * ss), (x1 * ss, y1 * ss)], fill=tuple(int(c) for c in col) + (255,),
               width=max(1, int(round(width * ss))))
    a = np.asarray(layer.resize((w, h), Image.LANCZOS)).astype(float)
    return a[..., :3], a[..., 3:] / 255.0


# ------------------------------------------------------------------ 1. clean page
img = np.clip(SRC * 255.0 / PAGE, 0, 255)
dev = np.abs(SRC - PAGE).max(2)
EXCLUDE = np.zeros((H, W), bool)
for x0, y0, x1, y1 in [(110, 295, 350, 345), (40, 575, 280, 645), (1708, 365, 1950, 430), (1610, 685, 1850, 748),
                       (884, 965, 1110, 1036), (1480, 0, 2000, 270), (690, 0, 870, 252), (895, 0, 1195, 248)]:
    EXCLUDE[y0:y1, x0:x1] = True
EXCLUDE[:232] = True
EXCLUDE[1048:] = True
img[EXCLUDE] = 255

blocks = {r["name"]: r for r in STAMPS["stamps"] if r["kind"] == "block"}
labels = [r for r in STAMPS["stamps"] if r["kind"] == "label"]
titles = [r for r in STAMPS["stamps"] if r["kind"] == "title"]
tiles = [r for r in STAMPS["stamps"] if r["kind"] == "tile"]

block_id = np.zeros((H, W), np.int16)              # 1..5 per subsystem
for i, (n, r) in enumerate(blocks.items(), 1):
    block_id[stamp_mask(r)] = i
block_zone = block_id > 0
label_zone = np.zeros((H, W), bool)
for r in labels:
    label_zone |= stamp_mask(r)
title_zone = np.zeros((H, W), bool)
for r in titles:
    title_zone |= stamp_mask(r)

# Orange outside the subsystems belongs to the interventions (thin lines,
# arrowheads): remove it. Titles and tiles are handled separately below.
R, G, B = SRC[..., 0], SRC[..., 1], SRC[..., 2]
orange = (R - B > 28) & (R - G > 18) & (dev > 12)
orange = morph(orange, 3, "dilate")
img[orange & ~block_zone & ~title_zone] = 255
# thin orange lines that cross the platforms
thin = (R - B > 28) & (R - G > 18) & (dev > 12) & block_zone
thin &= ~morph(morph(thin, 3, "erode"), 7, "dilate")
thin = morph(thin, 3, "dilate") & block_zone & ~morph(morph((R - B > 90), 3, "erode"), 5, "dilate")
img[thin] = np.maximum(img[thin], 252)

# ------------------------------------------------------------------ 2. tiles off, titles off
TILE_W, TILE_SLAB = 70.0, 6.0
TILE_HH = TILE_W / 2 * T                            # half height of the top face
tile_info = []
tile_erase = np.zeros((H, W), bool)
for r in tiles:
    i = int(r["name"].split("-")[1])
    x0, x1 = r["x"], r["x"] + r["w"]
    if r["w"] < 66:                                 # partly hidden behind a block: keep its true width
        if i == 7:
            x1 = x0 + TILE_W
        else:
            x0 = x1 - TILE_W
    yb = r["y"] + r["h"]
    xc = (x0 + x1) / 2
    top_y = yb - TILE_SLAB - 2 * TILE_HH
    poly = [(x0, yb - TILE_SLAB - TILE_HH), (xc, top_y), (x1, yb - TILE_SLAB - TILE_HH),
            (x1, yb - TILE_HH), (xc, yb), (x0, yb - TILE_HH)]
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    tile_erase |= np.asarray(m) > 0
    tile_info.append({"i": i, "chain": "A" if i <= 7 else "B", "cx": xc, "cy": yb - TILE_SLAB - TILE_HH})
tile_erase = morph(tile_erase, 5, "dilate") & ~block_zone & ~label_zone
title_erase = morph(title_zone, 3, "dilate") & ~block_zone
label_erase = np.zeros((H, W), bool)
label_px = []
for r in labels:
    m = stamp_mask(r)
    label_erase |= m
    label_px.append((r, np.asarray(Image.open(STAMP_DIR / f"{r['name']}.png"))))
label_erase &= ~block_zone
gone = tile_erase | title_erase | morph(label_erase, 3, "dilate")
img[gone] = 255
COL = {"black": (42, 42, 41), "green": (120, 196, 124), "blue": (36, 70, 236)}
REAL = [s for s in STAMPS["segments"]]
rgb, a = draw_lines((W, H), [(tuple(s["a"]), tuple(s["b"]), COL[s["c"]], 1.35) for s in REAL])
fill = (tile_erase | title_erase)[..., None] * a     # never paint lines through lettering
img = img * (1 - fill) + rgb * fill

# lines parallel to each cut family: they must not sit inside removed space
par = {}
for fam in ("ur", "dr"):
    _, a = draw_lines((W, H), [(*seg_ends(s), (0, 0, 0), 3) for s in SEGS if s["d"] == fam and s["t1"] - s["t0"] >= 30])
    par[fam] = a[..., 0] > 0.3

# ------------------------------------------------------------------ 3. cuts
yy, xx = np.mgrid[0:H, 0:W].astype(float)
track = {n: np.array([r["cx"], r["cy"]]) for n, r in blocks.items()}
for r in labels:
    track[r["name"]] = np.array([r["cx"], r["cy"]])
moved = {n: np.zeros(2) for n in track}


def shift(arr, wx, wy, M, covered, fillv):
    out = arr.copy()
    out[M | covered] = fillv
    sy = np.clip(np.round(yy - wy).astype(int), 0, H - 1)
    sx = np.clip(np.round(xx - wx).astype(int), 0, W - 1)
    take = covered & M[sy, sx]
    out[take] = arr[sy[take], sx[take]]
    return out


def profile(fam, lo, hi):
    f = np.round(FAM[fam](xx, yy)).astype(int)
    obst = block_zone | label_zone | par[fam]
    vals = np.arange(lo, hi)
    counts = np.array([int((obst & (f == v)).sum()) for v in vals])
    free = vals[counts == 0]
    runs = np.split(free, np.nonzero(np.diff(free) > 1)[0] + 1) if len(free) else []
    return [(int(r[0]), int(r[-1])) for r in runs if len(r) >= 3]


for owner, fam, c, side in CUTS:
    wx, wy = np.array(TARGET[owner]) - track[owner]
    f = FAM[fam]
    fw = f(wx, wy) - f(0, 0)
    removal = -side * fw if side * fw < 0 else 0.0
    if PROFILE:
        lo = int(c - 260)
        print(f"{owner}: free {fam} bands near {c}:", profile(fam, lo, int(c + 260)),
              f"(this shift removes {removal:.0f})")
    M = side * (f(xx, yy) - c) > 0
    covered = side * (f(xx - wx, yy - wy) - c) > 0
    lost_zone = covered & ~M

    # lines crossing the cut: probe just inside the static side
    pf = c - side * 2.5
    px = np.arange(0, W - 1, 0.5)
    py = pf - T * px if fam == "ur" else pf + T * px
    ok = (py >= 0) & (py < H - 1)
    px, py = px[ok], py[ok]
    vals = 255 - img[np.round(py).astype(int), np.round(px).astype(int)].min(1)
    idx = np.nonzero(vals > 45)[0]
    runs = np.split(idx, np.nonzero(np.diff(idx) > 2)[0] + 1) if len(idx) else []
    joins, blocked = [], 0
    for grp in runs:
        if len(grp) > 16:
            blocked += 1
            continue
        k = grp[len(grp) // 2]
        P = np.array([px[k], py[k]])
        best, bestd = 0, None
        for dname, d in DIRS.items():
            if dname == fam:
                continue
            hits = 0
            for s_ in (1, -1):
                for t in range(3, 12):
                    q = P + s_ * t * d
                    qi, qj = int(round(q[1])), int(round(q[0]))
                    if 0 <= qi < H and 0 <= qj < W and (255 - img[qi, qj].min()) > 40:
                        hits += 1
            if hits > best:
                best, bestd = hits, d
        if bestd is None or best < 10:
            continue
        cols = img[np.round(py[grp]).astype(int), np.round(px[grp]).astype(int)]
        col = cols[cols.mean(1).argmin()]
        fd = f(*bestd) - f(0, 0)
        P0 = P + ((c - f(*P)) / fd) * bestd
        Bp = P0 + (fw / fd) * bestd
        if side * fw > 0:
            joins.append((tuple(P0), tuple(Bp), col, 1.5))
        joins.append((tuple(Bp), tuple(P0 + np.array([wx, wy])), col, 1.5))

    lost = int((lost_zone & ((255 - img.min(2)) > 40) & (block_zone | par[fam])).sum())
    img = shift(img, wx, wy, M, covered, 255)
    block_id = shift(block_id, wx, wy, M, covered, 0)
    block_zone = block_id > 0
    label_zone = shift(label_zone, wx, wy, M, covered, False)
    for fam2 in par:
        par[fam2] = shift(par[fam2], wx, wy, M, covered, False)
    if joins:
        rgb, a = draw_lines((W, H), joins)
        img = img * (1 - a) + rgb * a
    for n, p in track.items():
        if side * (f(*p) - c) > 0:
            track[n] = p + np.array([wx, wy])
            moved[n] += np.array([wx, wy])
    print(f"{owner:22s} {fam}={c}: {len(joins)} joins, {blocked} drawings on the cut, "
          f"{lost} px of drawings/labels/parallel lines under removed space")

if PROFILE:
    sys.exit()

# ------------------------------------------------------------------ 4. tiles back on
OWN = {"A": ("communication", "spatial-dynamics"), "B": ("spatial-dynamics", "user-behaviour")}
layer = Image.new("RGBA", (W * 4, H * 4), (0, 0, 0, 0))
d = ImageDraw.Draw(layer)
S = 4
placed = []
STEP = 47.0                                      # centre-to-centre spacing of the original stones
for chain, (a_, b_) in OWN.items():
    ts = sorted([t for t in tile_info if t["chain"] == chain], key=lambda t: t["cx"])
    p0 = np.array([ts[0]["cx"], ts[0]["cy"]]) + moved[a_]
    p1 = np.array([ts[-1]["cx"], ts[-1]["cy"]]) + moved[b_]
    n = max(2, int(round(np.linalg.norm(p1 - p0) / STEP)) + 1)
    v = (p1 - p0) / np.linalg.norm(p1 - p0)
    side = np.array([-v[1], v[0]])
    steep = abs(v[1]) > 0.8                       # a near-vertical run: stagger the stones like the original
    for j in range(n):
        u = j / (n - 1)
        wob = (9 if j % 2 else -9) if steep and 0 < j < n - 1 else 0
        placed.append(tuple(p0 + u * (p1 - p0) + wob * side))
for cx, cy in sorted(placed, key=lambda p: p[1]):
    hw, hh, sl = TILE_W / 2, TILE_HH, TILE_SLAB
    Lp, Tp, Rp, Bp = (cx - hw, cy), (cx, cy - hh), (cx + hw, cy), (cx, cy + hh)
    sc = lambda pts: [(x * S, y * S) for x, y in pts]
    d.polygon(sc([Lp, Bp, (Bp[0], Bp[1] + sl), (Lp[0], Lp[1] + sl)]), fill=(218, 70, 26, 255))
    d.polygon(sc([Bp, Rp, (Rp[0], Rp[1] + sl), (Bp[0], Bp[1] + sl)]), fill=(206, 62, 22, 255))
    d.polygon(sc([Lp, Tp, Rp, Bp]), fill=(255, 255, 255, 255))
    d.line(sc([Lp, Tp, Rp]), fill=(150, 150, 150, 255), width=int(1.2 * S))
    d.line(sc([Lp, Bp, Rp]), fill=(120, 60, 40, 140), width=int(0.8 * S))
tl = np.asarray(layer.resize((W, H), Image.LANCZOS)).astype(float)
ta = tl[..., 3:] / 255.0
tile_rgb = 255 * (1 - ta) + tl[..., :3] * ta
# tiles sit under the lines and labels (multiply), and behind the subsystems
mult = tile_rgb * img / 255.0
img = np.where(block_zone[..., None], img, mult)

# ------------------------------------------------------------------ 5. titles back on
canvas = Image.fromarray(np.clip(np.round(img), 0, 255).astype(np.uint8)).convert("RGBA")
for r, rgba in label_px:
    dlt = moved[r["name"]]
    canvas.alpha_composite(Image.fromarray(rgba, "RGBA"), (int(round(r["x"] + dlt[0])), int(round(r["y"] + dlt[1]))))
for r in titles:
    owner = r["name"].replace("title-", "")
    dlt = moved[owner] + np.array(TITLE_NUDGE.get(owner, (0, 0)))
    rgba = Image.open(STAMP_DIR / f"{r['name']}.png")
    canvas.alpha_composite(rgba, (int(round(r["x"] + dlt[0])), int(round(r["y"] + dlt[1]))))

# ------------------------------------------------------------------ 6. fit the frame
arr = np.asarray(canvas.convert("RGB")).astype(int)
nz = np.nonzero((255 - arr.min(2)) > 30)
y0, y1, x0, x1 = nz[0].min(), nz[0].max() + 1, nz[1].min(), nz[1].max() + 1
crop = canvas.convert("RGB").crop((x0, y0, x1, y1))
CW, CH, PAD = 960, 926, 24
k = min((CW - 2 * PAD) / crop.width, (CH - 2 * PAD) / crop.height)
crop = crop.resize((int(round(crop.width * k)), int(round(crop.height * k))), Image.LANCZOS)
frame = Image.new("RGB", (CW, CH), (255, 255, 255))
frame.paste(crop, ((CW - crop.width) // 2, (CH - crop.height) // 2))
(HERE / "exports").mkdir(exist_ok=True)
frame.save(HERE / "exports/system-map@2x.png")
frame.resize((480, 463), Image.LANCZOS).save(HERE / "exports/system-map.png")
canvas.convert("RGB").save(HERE / "trace/compacted-full.png")
print(f"content {x1 - x0} x {y1 - y0} px, scaled {k:.3f} into 960 x 926")
