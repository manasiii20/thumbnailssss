"""Cuts the five subsystem illustrations out of the gigamap, untouched.

    python3 systemmap/extract.py

Each block is cut along a hand-placed outline. Inside it, the grey page that
can be reached from outside becomes transparent; the platform, the
illustration and its white fills stay exactly as drawn. Thin connection-line
stubs and labels left around the block are trimmed off. Writes
systemmap/assets/<block>.png (RGBA, source pixels) and blocks.json.
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent
SRC = np.asarray(Image.open(ROOT / "source/gigamap.webp").convert("RGB")).astype(int)
PAGE = 246

# Outline of each block (source pixels): platform, illustration above it and
# the paper underside below. "seed" is a point on the platform top.
BLOCKS = {
    "communication": {"poly": [(356, 498), (424, 398), (456, 342), (522, 342), (548, 358), (552, 408), (700, 500),
                               (702, 512), (610, 590), (530, 650), (445, 612), (372, 562), (356, 545)], "seed": (600, 520), "hot": (540, 520),
                      "top": [(361, 500), (527, 600), (696, 502), (530, 402)], "black": True,
                      "cut": [[(668, 520), (714, 520), (714, 562), (668, 562)]],
                      "protect": [[(424, 420), (460, 345), (545, 345), (572, 470), (568, 488), (560, 532), (495, 538),
                                   (468, 534), (424, 506)]],
                      "erase": [((392, 452), (392, 556)), ((529, 518), (529, 592)), ((497, 336), (497, 364))]},
    "user-behaviour": {"poly": [(1418, 502), (1438, 418), (1470, 385), (1530, 370), (1580, 375), (1620, 400), (1650, 420),
                                (1690, 405), (1712, 420), (1752, 490), (1752, 505), (1597, 625), (1414, 540)], "seed": (1700, 485), "hot": (1690, 487),
                       "top": [(1422, 498), (1597, 575), (1747, 492), (1572, 415)],
                       "cut": [[(1405, 500), (1446, 518), (1446, 545), (1405, 545)]],
                       "erase": [((1532, 548), (1532, 578))]},
    "spatial-dynamics": {"poly": [(818, 717), (822, 632), (860, 618), (930, 575), (985, 578), (1030, 585), (1095, 618),
                                  (1110, 630), (1130, 640), (1165, 655), (1190, 738), (1190, 752), (995, 860), (816, 760)], "seed": (1060, 770), "hot": (965, 705),
                         "cut": [[(852, 602), (893, 578), (926, 578), (931, 596), (931, 612), (926, 626), (866, 627)],
                                 [(890, 611), (933, 630), (943, 640), (943, 656), (930, 656), (886, 632)]],
                         "top": [(822, 717), (995, 812), (1120, 737), (947, 642)],
                         "erase": [((1159, 738), (1159, 775))]},
    "material-flow": {"poly": [(120, 852), (126, 778), (198, 743), (230, 758), (268, 737), (318, 742), (340, 770), (388, 768),
                               (438, 792), (440, 840), (462, 852), (462, 868), (290, 998), (116, 900)], "seed": (250, 900), "hot": (355, 880),
                      "top": [(123, 852), (290, 948), (458, 852), (291, 756)],
                      "erase": [((187, 744), (187, 762)), ((254, 746), (254, 774))]},
    "environmental-impact": {"poly": [(1378, 887), (1420, 860), (1470, 820), (1500, 785), (1580, 775), (1600, 800), (1640, 810),
                                      (1665, 812), (1700, 830), (1720, 890), (1720, 905), (1547, 1030), (1374, 925)], "seed": (1600, 940), "hot": (1437, 880),
                            "top": [(1381, 887), (1547, 985), (1715, 890), (1549, 792)],
                            "erase": [((1475, 810), (1475, 866))]},
}


def line_pixels(rgb):
    v = rgb.mean(2)
    sat = rgb.max(2) - rgb.min(2)
    return (v < 205) | ((sat > 40) & (v < 235))


def erase_segments(rgb, segs, keep, half=1.8, side=4):
    """Paint over line pixels near each segment where both sides are bare platform."""
    h, w = keep.shape
    yy, xx = np.mgrid[0:h, 0:w]
    out = rgb.copy()
    lp = line_pixels(rgb)
    for (ax, ay), (bx, by) in segs:
        dx, dy = bx - ax, by - ay
        L = np.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        nx, ny = -uy, ux
        t = (xx - ax) * ux + (yy - ay) * uy
        d = (xx - ax) * nx + (yy - ay) * ny
        band = (np.abs(d) <= half) & (t >= -2) & (t <= L + 2) & keep & lp
        for y, x in zip(*np.nonzero(band)):
            sd = d[y, x]
            pa = (int(round(x - (sd + side) * nx)), int(round(y - (sd + side) * ny)))
            pb = (int(round(x - (sd - side) * nx)), int(round(y - (sd - side) * ny)))
            if not (0 <= pa[0] < w and 0 <= pa[1] < h and 0 <= pb[0] < w and 0 <= pb[1] < h):
                continue
            ca, cb = rgb[pa[1], pa[0]], rgb[pb[1], pb[0]]
            if min(ca.mean(), cb.mean()) > 236 and (ca.max() - ca.min()) < 15 and (cb.max() - cb.min()) < 15:
                out[y, x] = (ca + cb) / 2
    return out


def poly_mask(shape, pts, ox, oy):
    m = Image.new("L", (shape[1], shape[0]), 0)
    ImageDraw.Draw(m).polygon([(x - ox, y - oy) for x, y in pts], fill=255)
    return np.asarray(m) > 0


def erase_thin(rgb, region, colored_only):
    """Paint out lines at most 3px wide whose two sides are bare platform."""
    out = rgb.copy()
    v = rgb.mean(2)
    sat = rgb.max(2) - rgb.min(2)
    bright = (v > 236) & (sat < 15)
    cand = region & ~bright & ((sat > 12) if colored_only else ((v < 243) & (sat < 25)))
    h, w = v.shape
    for y, x in zip(*np.nonzero(cand)):
        for ux, uy in ((1, 0), (0, 1), (0.87, 0.5), (0.87, -0.5)):
            for k in (2, 3):
                ax, ay = int(round(x - k * ux)), int(round(y - k * uy))
                bx, by = int(round(x + k * ux)), int(round(y + k * uy))
                if 0 <= ax < w and 0 <= ay < h and 0 <= bx < w and 0 <= by < h and bright[ay, ax] and bright[by, bx]:
                    out[y, x] = (rgb[ay, ax] + rgb[by, bx]) / 2
                    break
            else:
                continue
            break
    return out


def grow(seed, allowed, step=3):
    """Geodesic reconstruction: grow `seed` through `allowed` until stable."""
    seed = seed & allowed
    while True:
        img = Image.fromarray((seed * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(step))
        nxt = (np.asarray(img) > 0) & allowed
        if (nxt == seed).all():
            return seed
        seed = nxt


def morph(mask, size, op):
    f = ImageFilter.MaxFilter(size) if op == "dilate" else ImageFilter.MinFilter(size)
    return np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).filter(f)) > 0


def main():
    meta = {}
    for name, b in BLOCKS.items():
        xs, ys = zip(*b["poly"])
        x0, y0, x1, y1 = min(xs) - 4, min(ys) - 4, max(xs) + 5, max(ys) + 5
        crop = SRC[y0:y1, x0:x1].copy()
        h, w = crop.shape[:2]
        inside = poly_mask((h, w), b["poly"], x0, y0)

        # 1. Paint out the map's connection lines that cross the block.
        sat = crop.max(2) - crop.min(2)
        thick_orange = morph(morph(sat > 80, 3, "erode"), 9, "dilate")       # platform edges, hotspots
        protect = thick_orange.copy()
        for pr in b.get("protect", []):
            protect |= poly_mask((h, w), pr, x0, y0)
        segs = [((p1[0] - x0, p1[1] - y0), (p2[0] - x0, p2[1] - y0)) for p1, p2 in b.get("erase", [])]
        for _ in range(2):
            crop = erase_segments(crop, segs, inside)
            crop = erase_thin(crop, morph(inside, 9, "erode") & ~protect, colored_only=True)
            if b.get("black"):
                crop = erase_thin(crop, morph(inside, 9, "erode") & ~protect, colored_only=False)

        # 2. Grey page reachable from outside becomes transparent.
        v = crop.mean(2)
        neutral = (crop.max(2) - crop.min(2)) <= 6
        pagelike = neutral & (np.abs(v - PAGE) <= 4)
        outside = ~inside
        transparent = grow(outside, outside | pagelike)
        opaque = inside & ~transparent
        # The torn-paper underside is almost the page colour, so rebuild it per
        # column: from the orange platform edge down to the lowest drawn outline.
        edge = morph(crop.max(2) - crop.min(2) > 80, 3, "erode") & inside      # the thick platform edge only
        outline = neutral & (v < 241) & (v > 150) & inside      # the paper's light grey outline, not black map lines
        bottoms = np.full(w, -1)
        depth = np.full(w, np.nan)
        for x in range(w):
            ey = np.nonzero(edge[:, x])[0]
            if len(ey) == 0:
                continue
            e = ey.max()
            bottoms[x] = e
            oy = np.nonzero(outline[e + 6:e + 52, x])[0]
            if len(oy):
                depth[x] = 6 + oy.max()
        valid = bottoms >= 0
        if valid.any():
            # Robust, smooth depth: wide median, clipped to the paper's usual size.
            d = depth.copy()
            good = ~np.isnan(d)
            if good.any():
                d[~good] = np.interp(np.nonzero(~good)[0], np.nonzero(good)[0], d[good])
            else:
                d[:] = 28
            sm = np.array([np.median(d[max(0, x - 12):x + 13]) for x in range(w)])
            sm = np.clip(sm, 14, 40)
            sm = np.convolve(np.pad(sm, 4, mode="edge"), np.ones(9) / 9, mode="valid")
            tops = np.array([np.nonzero(edge[:, x])[0].min() if valid[x] else h for x in range(w)])
            yy = np.arange(h)[:, None]
            paper = valid[None, :] & (yy >= tops[None, :]) & (yy <= (bottoms + sm)[None, :]) & inside
            opaque |= paper
            opaque &= ~(valid[None, :] & (yy > (bottoms + sm + 1)[None, :]))   # nothing hangs below the paper
        for cut in b.get("cut", []):
            opaque &= ~poly_mask((h, w), cut, x0, y0)

        # 3. Trim thin stubs: keep only what lies near solid areas of the block.
        core = morph(morph(opaque, 5, "erode"), 5, "dilate")
        opaque &= morph(core, 11, "dilate")
        sx, sy = b["seed"][0] - x0, b["seed"][1] - y0
        seed = np.zeros_like(opaque)
        seed[sy - 2:sy + 3, sx - 2:sx + 3] = True
        opaque = grow(seed, opaque)

        alpha = np.asarray(Image.fromarray((opaque * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.5)))
        alpha = np.where(opaque, 255, alpha)
        out = np.dstack([np.clip(np.round(crop), 0, 255).astype(np.uint8), alpha.astype(np.uint8)])
        Image.fromarray(out, "RGBA").save(ROOT / f"assets/{name}.png")
        meta[name] = {"x": x0, "y": y0, "w": w, "h": h, "top": b.get("top"), "hot": b.get("hot")}
        print(name, w, h)

    (ROOT / "assets/blocks.json").write_text(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
