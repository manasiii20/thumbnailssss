# Thumbnail Studio

Animated portfolio thumbnails, 482 × 402. The logos stay still, and the pastel gradient behind them flows in a seamless loop with a soft white light drifting through it.

## Ready-made exports

| File | What it is |
| --- | --- |
| `exports/hitachi-x-bosch@2x.mp4` | 964 × 804, 8 s loop, 60 fps (2x, looks sharp on retina screens at 482 × 402) |
| `exports/hitachi-x-bosch.mp4` | 482 × 402, 8 s loop, 60 fps |
| `exports/hitachi-x-bosch@2x.png` / `.png` | The still image, identical to the reference design |

## Make or tweak a thumbnail in the browser

Open `index.html` in Chrome, Edge or Safari 17+. It works straight from disk, so you don't need a server.

- **Motion** and **White light** set how strong the flow and the glow are (1.00 is the default look).
- **Loop**, **FPS** and **Export size** control the video.
- **Export MP4 loop** renders the video frame by frame and downloads it. The last frame leads back into the first, so it loops seamlessly.
- **Show still** / **Export still PNG** show and save the static design with no motion.

### A new thumbnail (another "Company × Company")

1. In Figma, hide the background, so only the white text and logos sit on a transparent 482 × 402 frame.
2. Export it as **PNG @2x** (964 × 804).
3. Either click **Load text PNG** in the studio, or save it to `assets/overlays/<name>.png` and run `node scripts/embed-assets.mjs` so it shows up in the dropdown.

The gradient is `assets/gradient.png`. Use **Load gradient** to try a different one.

## Command-line render (optional)

You need Node 18+ and ffmpeg on your PATH.

```sh
npm install
npx playwright install chromium
npm run render                                   # every overlay → exports/*@2x.mp4 + png
node scripts/render.mjs hitachi-x-bosch --scale 1 --duration 10 --fps 30
node scripts/render.mjs --motion 1.2 --light 0.8
```

The output is H.264 High, yuv420p, tagged BT.709, with faststart. It plays in browsers, Framer, Webflow and Notion.

## How it's built

- `assets/gradient.png` is the reference gradient with the logos removed. The gap behind the text was filled from the surrounding gradient.
- `assets/overlays/hitachi-x-bosch.png` is the text layer pulled from the same reference as white plus alpha. Gradient + text recombine to within 0.05/255 of the original, so the still matches it pixel for pixel.
- The animation is a WebGL shader in `index.html`. A smooth two-level flow field warps the gradient, so it stays in the original colours and doesn't slide or tile. Two soft white glows move on looping paths, one in the upper half and one in the lower, so they mostly pass around the logos. Time only enters as whole turns of the loop, so the loop has no seam.
- `vendor/mp4-muxer.js` (MIT) writes the MP4 container for in-browser export.
