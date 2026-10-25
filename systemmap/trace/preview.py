"""Draw the stamps + corridor segments at their ORIGINAL positions on white,
to check the decomposition reproduces the map.  python3 preview.py out.png"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "stamps.json").read_text())
im = Image.new("RGBA", (2000, 1415), (255, 255, 255, 255))
d = ImageDraw.Draw(im)
COL = {"black": (43, 43, 42, 255), "green": (60, 180, 85, 255), "blue": (13, 52, 240, 255)}
for s in data["segments"]:
    d.line([tuple(s["a"]), tuple(s["b"])], fill=COL[s["c"]], width=1)
order = {"tile": 1, "label": 2, "title": 3, "block": 0}
for r in sorted(data["stamps"], key=lambda r: order[r["kind"]]):
    im.alpha_composite(Image.open(HERE / "stamps" / f"{r['name']}.png"), (r["x"], r["y"]))
im.convert("RGB").crop((0, 220, 2000, 1060)).save(sys.argv[1])
