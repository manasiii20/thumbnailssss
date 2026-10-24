# Thumbnail Studio

Animated portfolio thumbnails, 482 × 402. The logos stay still. Behind them, blush, pink, mauve, lilac, lavender and pale blue flow and fold into each other in a seamless loop, with soft white haze swirling through.

## Ready-made exports

| File | What it is |
| --- | --- |
| `exports/hitachi-x-bosch@2x.mp4` | 964 × 804, 6 s loop, 60 fps (2x, looks sharp on retina screens at 482 × 402) |
| `exports/hitachi-x-bosch.mp4` | 482 × 402, 6 s loop, 60 fps |
| `exports/hitachi-x-bosch@2x.png` / `.png` | The first frame of the loop as a still |

## Make or tweak a thumbnail in the browser

Open `index.html` in Chrome, Edge or Safari 17+. It works straight from disk, so you don't need a server.

- **Motion** sets how strongly the colours flow and fold, **Vividness** sets colour saturation (1.00 = the reference colours), and **White light** sets how strong the white haze is.
- **Loop**, **FPS** and **Export size** control the video.
- **Export MP4 loop** renders the video frame by frame and downloads it. The last frame leads back into the first, so it loops seamlessly.
- **Export first frame as PNG** saves a still that matches the start of the video.

### A new thumbnail (another "Company × Company")

1. In Figma, hide the background, so only the white text and logos sit on a transparent 482 × 402 frame.
2. Export it as **PNG @2x** (964 × 804).
3. Either click **Load text PNG** in the studio, or save it to `assets/overlays/<name>.png` and run `node scripts/embed-assets.mjs` so it shows up in the dropdown.

The colours are set in `ramp()` in the shader in `index.html`.

## Command-line render (optional)

You need Node 18+ and ffmpeg on your PATH.

```sh
npm install
npx playwright install chromium
npm run render                                   # every overlay → exports/*@2x.mp4 + png
node scripts/render.mjs hitachi-x-bosch --scale 1 --duration 10 --fps 30
node scripts/render.mjs --motion 1.2 --light 0.8 --vivid 1.4
```

The output is H.264 High, yuv420p, tagged BT.709, with faststart. It plays in browsers, Framer, Webflow and Notion.

## How it's built

- `assets/overlays/hitachi-x-bosch.png` is the text layer pulled from the reference thumbnail as white plus alpha, so the logos match it pixel for pixel.
- The background is a WebGL shader in `index.html`. A smooth field runs diagonally from blush (bottom left) to pale blue (top right), with travelling ripples on top. A two-level flow field folds it, so the colours keep mixing into new shapes. The field is coloured through a ramp of colours sampled from the reference gradient. The white haze is a second pattern in the same folded space, swirled a little more, so it mixes in with the colours. Near the logos, the brightest areas ease slightly towards mauve in a soft oval, so the white text always reads. The oval is found automatically from each text layer. Time only enters as whole turns of the loop, so the loop has no seam.
- `vendor/mp4-muxer.js` (MIT) writes the MP4 container for in-browser export.
