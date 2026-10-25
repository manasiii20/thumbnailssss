"""Find the straight line segments of the gigamap's connection network.

Lines run vertically or at +-30 degrees. For each colour class and direction
we sample along every candidate line and keep long runs of line pixels.
Writes segments.json: [{c, d, x0, y0, x1, y1}] in gigamap pixels.
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
A = np.asarray(Image.open(ROOT / "source/gigamap.webp").convert("RGB")).astype(float)
H, W, _ = A.shape
R, G, B = A[..., 0], A[..., 1], A[..., 2]
V = A.mean(2)
SAT = A.max(2) - A.min(2)

INK = np.abs(A - 246).max(2) > 18
CLASSES = {
    "black": INK & (SAT < 22) & (V < 232),
    "green": INK & (G - R > 15) & (G - B > 10),
    "blue": INK & (B - R > 15) & (B - G > 6),
    "orange": INK & (R - B > 30) & (R - G > 20),
}
T = np.tan(np.radians(30))
DIRS = {"v": None, "ur": -T, "dr": T}   # slope dy/dx for the 30 degree families


def bilin(mask, xs, ys):
    xi = np.clip(np.round(xs).astype(int), 0, W - 1)
    yi = np.clip(np.round(ys).astype(int), 0, H - 1)
    ok = (xs >= 0) & (xs < W) & (ys >= 0) & (ys < H)
    return mask[yi, xi] & ok


def runs(on, min_len, max_gap):
    idx = np.nonzero(on)[0]
    if len(idx) == 0:
        return []
    out, s, p = [], idx[0], idx[0]
    for i in idx[1:]:
        if i - p > max_gap:
            if p - s >= min_len:
                out.append((s, p))
            s = i
        p = i
    if p - s >= min_len:
        out.append((s, p))
    return out


segs = []
for cname, m in CLASSES.items():
    # widen by one pixel so anti-aliased lines read as continuous
    mm = m.copy()
    mm[1:, :] |= m[:-1, :]
    mm[:, 1:] |= m[:, :-1]
    for d, slope in DIRS.items():
        found = []
        if d == "v":
            for x in range(W):
                col = mm[:, x]
                for a, b in runs(col, 22, 3):
                    found.append((x, a, x, b, x))
        else:
            xs = np.arange(W, dtype=float)
            # lines y = slope*x + c ; step c by 0.5
            cs = np.arange(-W * abs(slope) - 5, H + W * abs(slope) + 5, 0.5)
            for c in cs:
                ys = slope * xs + c
                on = bilin(mm, xs, ys)
                for a, b in runs(on, 22, 3):
                    found.append((a, slope * a + c, b, slope * b + c, c))
        # non-maximum suppression: neighbouring offsets give the same line
        found.sort(key=lambda f: (f[4], f[0]))
        keep = []
        for f in found:
            dup = False
            for k in keep[-40:]:
                if abs(k[4] - f[4]) <= 2.2 and min(k[2], f[2]) - max(k[0], f[0]) > -2 and (
                        d != "v" or min(k[3], f[3]) - max(k[1], f[1]) > -2):
                    # merge into the longer one
                    if (f[2] - f[0]) + (f[3] - f[1]) > (k[2] - k[0]) + (k[3] - k[1]):
                        keep[keep.index(k)] = f
                    dup = True
                    break
            if not dup:
                keep.append(f)
        for x0, y0, x1, y1, _ in keep:
            segs.append({"c": cname, "d": d, "x0": round(float(x0), 1), "y0": round(float(y0), 1),
                         "x1": round(float(x1), 1), "y1": round(float(y1), 1)})
    print(cname, sum(1 for s in segs if s["c"] == cname))

(Path(__file__).parent / "segments.json").write_text(json.dumps(segs))
