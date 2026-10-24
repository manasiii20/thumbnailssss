// Renders seamless MP4 loops (and a PNG of the first frame) for every text layer in
// assets/overlays, using the same shader as index.html in headless Chromium.
//
//   node scripts/render.mjs                       # all thumbnails, 2x, 8s, 60fps
//   node scripts/render.mjs hitachi-x-bosch --scale 1 --duration 10 --fps 30
//   node scripts/render.mjs --motion 1.2 --light 0.8 --vivid 1.3
//
// Needs: ffmpeg on PATH, and Playwright (npm install).
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const outDir = join(root, 'exports');

const args = process.argv.slice(2);
const opts = { scale: 2, duration: 8, fps: 60, motion: 1, light: 1, vivid: 1.0, crf: 12 };
const names = [];
for (let i = 0; i < args.length; i++) {
  if (args[i].startsWith('--')) opts[args[i].slice(2)] = Number(args[++i]);
  else names.push(args[i]);
}

function ffmpeg(file, width, height, fps) {
  const p = spawn('ffmpeg', [
    '-y', '-loglevel', 'error',
    '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${width}x${height}`, '-r', String(fps), '-i', '-',
    // WebGL rows come bottom-up; convert RGB -> BT.709 YUV and tag it so browsers show the right colours.
    '-vf', 'vflip,scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int,format=yuv420p',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', String(opts.crf), '-profile:v', 'high',
    '-g', String(fps * 2),
    '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
    '-movflags', '+faststart', '-an', file,
  ], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((res, rej) => p.on('close', (c) => (c === 0 ? res() : rej(new Error('ffmpeg exited ' + c)))));
  return { stdin: p.stdin, done };
}

const browser = await chromium.launch({ args: ['--ignore-gpu-blocklist', '--enable-unsafe-swiftshader'] });
const page = await browser.newPage();
page.on('pageerror', (e) => console.error(e));
await page.goto(pathToFileURL(join(root, 'index.html')).href);
await page.evaluate(() => window.thumb.ready);

const all = await page.evaluate(() => window.thumb.overlays());
const targets = names.length ? names : all;
mkdirSync(outDir, { recursive: true });

for (const name of targets) {
  if (!all.includes(name)) { console.error(`No overlay "${name}". Available: ${all.join(', ')}`); continue; }
  const suffix = opts.scale === 2 ? '@2x' : '';
  const [width, height] = [482 * opts.scale, 402 * opts.scale];
  await page.evaluate(async ({ name, opts }) => {
    const t = window.thumb;
    Object.assign(t.config, { motion: opts.motion, light: opts.light, vivid: opts.vivid });
    t.exportMode(true);
    t.setSize(opts.scale);
    await t.setOverlay(name);
  }, { name, opts });

  // First frame of the loop as a still.
  const png = await page.evaluate(() => {
    window.thumb.render(0);
    return document.getElementById('stage').toDataURL('image/png').split(',')[1];
  });
  writeFileSync(join(outDir, `${name}${suffix}.png`), Buffer.from(png, 'base64'));

  const frames = Math.round(opts.duration * opts.fps);
  const file = join(outDir, `${name}${suffix}.mp4`);
  const enc = ffmpeg(file, width, height, opts.fps);
  for (let i = 0; i < frames; i++) {
    const b64 = await page.evaluate((phase) => { window.thumb.render(phase); return window.thumb.readPixels(); }, i / frames);
    if (!enc.stdin.write(Buffer.from(b64, 'base64'))) await new Promise((r) => enc.stdin.once('drain', r));
    if (i % 60 === 0) process.stdout.write(`\r${name}: frame ${i + 1}/${frames}`);
  }
  enc.stdin.end();
  await enc.done;
  console.log(`\r${name}: wrote ${file} (${frames} frames, ${width}x${height}, ${opts.duration}s @ ${opts.fps}fps)`);
}

await browser.close();
