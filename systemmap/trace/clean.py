"""Merge duplicate / broken detections into clean segments.

Reads segments.json, writes clean.json: [{id, c, d, off, t0, t1}]
where for direction d the line is parametrised as:
  v : x = off, y = t      (t0..t1)
  ur: y = -tan30*x + off, x = t
  dr: y =  tan30*x + off, x = t
"""
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
T = np.tan(np.radians(30))
segs = json.loads((HERE / "segments.json").read_text())

def param(s):
    if s["d"] == "v":
        return s["x0"], min(s["y0"], s["y1"]), max(s["y0"], s["y1"])
    slope = -T if s["d"] == "ur" else T
    off = s["y0"] - slope * s["x0"]
    return off, min(s["x0"], s["x1"]), max(s["x0"], s["x1"])

items = []
for s in segs:
    if s["c"] == "orange":
        continue
    off, t0, t1 = param(s)
    ys = (t0, t1) if s["d"] == "v" else ((-T if s["d"] == "ur" else T) * t0 + off, (-T if s["d"] == "ur" else T) * t1 + off)
    if max(ys) < 232 or min(ys) > 1048:
        continue
    items.append([s["c"], s["d"], off, t0, t1])

# Repeatedly merge: same colour + direction, offsets within 2.6px, extents overlapping or gap <= 7.
changed = True
while changed:
    changed = False
    items.sort(key=lambda r: (r[0], r[1], r[2], r[3]))
    out = []
    for r in items:
        merged = False
        for o in out[-60:]:
            if o[0] == r[0] and o[1] == r[1] and abs(o[2] - r[2]) <= 2.6 and r[3] <= o[4] + 7 and o[3] <= r[4] + 7:
                wo, wr = o[4] - o[3], r[4] - r[3]
                o[2] = (o[2] * wo + r[2] * wr) / max(wo + wr, 1e-6)
                o[3], o[4] = min(o[3], r[3]), max(o[4], r[4])
                merged = changed = True
                break
        if not merged:
            out.append(list(r))
    items = out

clean = [{"id": i, "c": c, "d": d, "off": round(off, 2), "t0": round(t0, 1), "t1": round(t1, 1)}
         for i, (c, d, off, t0, t1) in enumerate(items) if (t1 - t0) >= 18]
(HERE / "clean.json").write_text(json.dumps(clean))
print(len(clean), "segments;", {c: sum(1 for s in clean if s["c"] == c) for c in ("black", "green", "blue")})
