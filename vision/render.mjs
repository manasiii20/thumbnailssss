// Renders the Vision Health walkthrough reel to MP4 with headless Chromium + ffmpeg.
//
//   node vision/render.mjs                      # vision/exports/vision-health-walkthrough.mp4 (1920 x 1080, 60 fps)
//   node vision/render.mjs --stills 3 12.5 40   # PNG stills at those seconds, into vision/exports/stills/
//   node vision/render.mjs --from 20 --to 30    # render only part of the timeline (for checking)
//
// Needs: ffmpeg on PATH, and Playwright (npm install).
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const outDir = join(here, 'exports');
mkdirSync(outDir, { recursive: true });
const W = 1920, H = 1080;
const args = process.argv.slice(2);
const opt = (n) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : undefined; };

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
page.on('pageerror', (e) => console.error(e));
await page.goto(pathToFileURL(join(here, 'index.html')).href);
await page.evaluate(() => window.anim.ready);
const { duration, fps } = await page.evaluate(() => { window.anim.exportMode(true); return window.anim.timeline; });
const cdp = await page.context().newCDPSession(page);
const grab = async (t) => {
  await page.evaluate((t) => window.anim.renderAt(t), t);
  const { data } = await cdp.send('Page.captureScreenshot', { format: 'png', clip: { x: 0, y: 0, width: W, height: H, scale: 1 }, optimizeForSpeed: true });
  return Buffer.from(data, 'base64');
};

if (args[0] === '--stills') {
  const dir = join(outDir, 'stills');
  mkdirSync(dir, { recursive: true });
  for (const s of args.slice(1)) writeFileSync(join(dir, `t${Number(s).toFixed(2)}.png`), await grab(Number(s)));
  await browser.close();
  console.log(`wrote ${args.length - 1} stills to ${dir}`);
  process.exit(0);
}

const from = Number(opt('--from') ?? 0), to = Math.min(duration, Number(opt('--to') ?? duration));
const file = join(outDir, opt('--out') ?? (from === 0 && to === duration ? 'vision-health-walkthrough.mp4' : `part-${from}-${to}.mp4`));
const ff = spawn('ffmpeg', [
  '-y', '-loglevel', 'error',
  '-f', 'image2pipe', '-c:v', 'png', '-framerate', String(fps), '-i', '-',
  '-vf', 'scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int,format=yuv420p',
  '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-profile:v', 'high', '-g', String(fps * 2),
  '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
  '-movflags', '+faststart', '-an', file,
], { stdio: ['pipe', 'inherit', 'inherit'] });
const done = new Promise((res, rej) => ff.on('close', (c) => (c === 0 ? res() : rej(new Error('ffmpeg exited ' + c)))));

const first = Math.round(from * fps), last = Math.round(to * fps);
const started = Date.now();
for (let i = first; i < last; i++) {
  const png = await grab(i / fps);
  if (!ff.stdin.write(png)) await new Promise((r) => ff.stdin.once('drain', r));
  if ((i - first) % 600 === 0) console.log(`frame ${i - first}/${last - first} · ${((Date.now() - started) / 1000).toFixed(0)} s`);
}
ff.stdin.end();
await done;
await browser.close();
console.log(`wrote ${file} (${last - first} frames, ${W}x${H}, ${((last - first) / fps).toFixed(2)}s @ ${fps}fps)`);
