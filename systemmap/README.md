# System map thumbnail

480 × 463, built at 2x (960 × 926) on plain white. It's the systems layer of the gigamap, rearranged so the five subsystems sit 2–1–2:

| Position | Subsystem |
| --- | --- |
| Top left | Communication System |
| Top right | User Behaviour |
| Centre | Spatial Dynamics |
| Bottom left | Material Flow |
| Bottom right | Environmental Impact |

The stakeholder mapping on top, the text boxes and the interventions underneath (the thin orange lines) are left out.

## How it stays true to the map

Nothing is redrawn except the stepping stones. The thumbnail is the gigamap's own pixels: every connection line, label, arrow and illustration is kept.

`compact.py` does this in five steps:

1. It lifts the labels, the titles and the stepping stones off the map.
2. It slides each corner subsystem towards Spatial Dynamics along an isometric cut line that runs between the illustrations. A cut only removes space where nothing sits.
3. Wherever a connection line crosses a cut, the line is joined again along the cut. Every line keeps its route and stays on the map's 30° grid.
4. It puts each label and title back with its own subsystem.
5. It lays the stepping stones again between the moved subsystems, in the original stone's size and colours.

The run prints a check for each cut: how many lines were joined, and how many pixels of drawings, labels or parallel lines fell in removed space. All four read 0.

## Files

| File | What it is |
| --- | --- |
| `source/gigamap.webp` | The original gigamap |
| `trace/detect.py`, `trace/clean.py` | Find the connection lines (vertical and ±30°) |
| `trace/stamps.py` | Cuts the gigamap into subsystems, labels, titles and stones |
| `extract.py` | The outline of each subsystem |
| `compact.py` | Builds the thumbnail |
| `exports/system-map@2x.png` / `system-map.png` | The result |

```sh
python3 systemmap/trace/detect.py && python3 systemmap/trace/clean.py
python3 systemmap/trace/stamps.py
python3 systemmap/compact.py
```

The positions of the four corner subsystems are set by `TARGET` in `compact.py`, and title nudges by `TITLE_NUDGE`.
