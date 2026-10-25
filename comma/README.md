# Comma show reel

479 × 316, rendered at 2x (958 × 632), 60 fps. It's a 6.25 s seamless loop: the last frame is identical to the first. The gradient backdrop (`source/00-gradient.webp`) stays the same in every frame.

| Time | What happens |
| --- | --- |
| 0 – 0.85 s | The cursor glides in from the right, at about centre height, onto the **System Design** pill |
| 0.85 s | Click: the cursor squeezes and a soft ring spreads from the click point |
| 0.93 – 1.38 s | The card morphs open into the expanded card |
| 1.5 – 1.95 s | The cursor leaves off the right edge |
| 1.95 – 2.3 s | The expanded card holds |
| 2.3 – 3.55 s | The expanded card scrolls up and away while the Queue2 dashboard rises into the centre |
| 3.55 – 4.75 s | The dashboard holds |
| 4.75 – 6.05 s | The dashboard sinks out while the collapsed card comes down from the top. They keep the gap from the return storyboard, and the card lands on its starting spot |
| 6.05 – 6.25 s | The collapsed card rests, then the loop starts again |

| File | What it is |
| --- | --- |
| `source/` | Your frames: gradient, collapsed card, expanded card, dashboard, plus reference frames for the scroll |
| `exports/comma-show-reel@2x.mp4` | The rendered video |
| `index.html` | Live preview with a scrubber and an **Export MP4 loop** button |

## How it's built

- **Resting states are your artwork, untouched.** The collapsed and expanded cards are cut out of your frames along the card's rounded edge. The dashboard is your PNG, with its own shadow. All of them sit on the one gradient image.
- **The card morph** rebuilds only the in-between frames, from pieces of your two card frames:
  - The card grows, and the title, bar, 78% and icons glide and cross-fade into their new spots.
  - The avatars spread into chips.
  - "4 credits" and "Testing" fade out, and the new content fades in from top to bottom out of a light blur.
- **The scrolls** keep the gaps from your storyboard: 202 px at 2x going up and about 400 px coming back down. Whatever is leaving eases back slightly, and whatever is arriving grows from 93% to 100% as it lands.

## Re-render

```sh
python3 comma/extract.py      # after changing a source image
node comma/render.mjs         # needs ffmpeg + Playwright
```

Timings and the cursor path are at the top of the script in `index.html`. Element boxes and positions are in `extract.py`.
