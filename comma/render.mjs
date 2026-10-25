// Renders the Comma show reel to MP4 with headless Chromium + ffmpeg.
//
//   node comma/render.mjs            # comma/exports/comma-system-design@2x.mp4 (958 x 632)
//
// Needs: ffmpeg on PATH, and Playwright (npm install).
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const outDir = join(here, 'exports');
mkdirSync(outDir, { recursive: true });
const W = 958, H = 632;

const browser = await chromium.launch({ args: ['--ignore-gpu-blocklist', '--enable-unsafe-swiftshader'] });
const page = await browser.newPage();
page.on('pageerror', (e) => console.error(e));
await page.goto(pathToFileURL(join(here, 'index.html')).href);
await page.evaluate(() => window.anim.ready);
const { duration, fps } = await page.evaluate(() => { window.anim.exportMode(true); return window.anim.timeline; });
const frames = Math.round(duration * fps);

const file = join(outDir, 'comma-system-design@2x.mp4');
const ff = spawn('ffmpeg', [
  '-y', '-loglevel', 'error',
  '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${W}x${H}`, '-r', String(fps), '-i', '-',
  '-vf', 'scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int,format=yuv420p',
  '-c:v', 'libx264', '-preset', 'slow', '-crf', '12', '-profile:v', 'high', '-g', String(fps * 2),
  '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
  '-movflags', '+faststart', '-an', file,
], { stdio: ['pipe', 'inherit', 'inherit'] });
const done = new Promise((res, rej) => ff.on('close', (c) => (c === 0 ? res() : rej(new Error('ffmpeg exited ' + c)))));

for (let i = 0; i < frames; i++) {
  const b64 = await page.evaluate((t) => { window.anim.renderAt(t); return window.anim.readPixels(); }, i / fps);
  if (!ff.stdin.write(Buffer.from(b64, 'base64'))) await new Promise((r) => ff.stdin.once('drain', r));
}
ff.stdin.end();
await done;
await browser.close();
console.log(`wrote ${file} (${frames} frames, ${W}x${H}, ${duration}s @ ${fps}fps)`);
