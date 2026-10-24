# Thumbnail Studio

Animated portfolio thumbnails, 482 × 402. The logos stay still. Behind them, pink, peach, mauve, magenta and blue colour fields drift and blend in a seamless loop, with a soft white light moving through.

## Ready-made exports

| File | What it is |
| --- | --- |
| `exports/hitachi-x-bosch@2x.mp4` | 964 × 804, 6 s loop, 60 fps (2x, looks sharp on retina screens at 482 × 402) |
| `exports/hitachi-x-bosch.mp4` | 482 × 402, 6 s loop, 60 fps |
| `exports/hitachi-x-bosch@2x.png` / `.png` | The first frame of the loop as a still |

## Make or tweak a thumbnail in the browser

Open `index.html` in Chrome, Edge or Safari 17+. It works straight from disk, so you don't need a server.

- **Motion** sets how far the colours travel, **Vividness** sets colour saturation, and **White light** sets the strength of the glow.
- **Loop**, **FPS** and **Export size** control the video.
- **Export MP4 loop** renders the video frame by frame and downloads it. The last frame leads back into the first, so it loops seamlessly.
- **Export first frame as PNG** saves a still that matches the start of the video.

### A new thumbnail (another "Company × Company")

1. In Figma, hide the background, so only the white text and logos sit on a transparent 482 × 402 frame.
2. Export it as **PNG @2x** (964 × 804).
3. Either click **Load text PNG** in the studio, or save it to `assets/overlays/<name>.png` and run `node scripts/embed-assets.mjs` so it shows up in the dropdown.

The gradient colours and where they sit are set in the `blob(...)` lines of the shader in `index.html`.

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
- The background is a WebGL shader in `index.html`. Eight colour blobs, with colours sampled from the reference gradient, each travel on their own closed loop and blend smoothly. A flow field bends them into organic shapes. Two soft white glows move on looping paths, one in the upper half and one in the lower, so they mostly pass around the logos. Time only enters as whole turns of the loop, so the loop has no seam.
- `vendor/mp4-muxer.js` (MIT) writes the MP4 container for in-browser export.
