# Comma show reel

479 × 316 (rendered at 2x, 958 × 632). The cursor rests on the collapsed **System Design** card, which opens into the expanded card. When the cursor moves off, the card closes again. The gradient background never changes. It's a 5-second seamless loop at 60 fps.

| File | What it is |
| --- | --- |
| `source/01-collapsed.webp`, `source/02-expanded.webp` | The design frames, exported at 2x |
| `exports/comma-system-design@2x.mp4` | The rendered loop |
| `index.html` | Live preview with a scrubber and an **Export MP4 loop** button |

## How the morph works

Both resting states are your frames, shown untouched. Every in-between frame is rebuilt from pieces of them:

- **The card** is drawn as a #333 rounded rectangle that grows from the collapsed size to the expanded one. Everything is clipped to it, so the new content is revealed as it grows.
- **Shared elements** glide from their collapsed spot to their expanded spot and cross-fade from one frame's pixels to the other's. These are the title and its pill, the progress bar, 78%, the flag and the status icon.
- **The four avatars** slide out of the stacked row into their name chips and shrink from 45 px to 31 px.
- **Collapsed-only labels** ("4 credits", "Testing") fade out as they travel with their icon.
- **Expanded-only content** fades in from top to bottom, sharpening out of a light blur: the 3-of-4 pill, the checklist, Priority/Status and the chips.
- **Timing:** hover-in starts the open (0.6 s) and hover-out starts the close (0.55 s). Both use a brisk-start, soft-settle curve.

## Re-render

```sh
python3 comma/extract.py      # after changing a source frame
node comma/render.mjs         # needs ffmpeg + Playwright
```

The cursor path, hover timing and durations are at the top of the script in `index.html`. Element boxes are in `extract.py`.
