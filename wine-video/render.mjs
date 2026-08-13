/**
 * 酒主题 HyperFrames 渲染脚本
 * 使用 puppeteer 逐帧截图 + ffmpeg-static 合成 MP4
 */
import puppeteer from 'puppeteer';
import ffmpegStatic from 'ffmpeg-static';
import { execFileSync } from 'child_process';
import { pathToFileURL } from 'url';
import path from 'path';
import fs from 'fs';

const FPS = 30;
const DURATION = 13;
const WIDTH = 1920;
const HEIGHT = 1080;
const TOTAL_FRAMES = FPS * DURATION;
const FRAMES_DIR = path.join(path.resolve('.'), 'frames');
const OUTPUT = path.join(path.resolve('.'), 'wine-story.mp4');

// 清理旧帧
if (fs.existsSync(FRAMES_DIR)) {
  fs.rmSync(FRAMES_DIR, { recursive: true });
}
fs.mkdirSync(FRAMES_DIR, { recursive: true });

console.log(`渲染参数: ${WIDTH}x${HEIGHT} @ ${FPS}fps, ${DURATION}s (${TOTAL_FRAMES} 帧)`);
console.log(`ffmpeg 路径: ${ffmpegStatic}`);

const browser = await puppeteer.launch({
  headless: 'new',
  args: ['--no-sandbox', '--disable-setuid-sandbox', '--force-device-scale-factor=1'],
});
const page = await browser.newPage();
await page.setViewport({ width: WIDTH, height: HEIGHT, deviceScaleFactor: 1 });

const htmlUrl = pathToFileURL(path.resolve('index.html')).href;
console.log(`加载: ${htmlUrl}`);
await page.goto(htmlUrl, { waitUntil: 'networkidle0', timeout: 30000 });

// 等待 GSAP timeline 就绪
await page.waitForFunction(
  'window.__timelines && Object.keys(window.__timelines).length > 0 && typeof window.gsap !== "undefined"',
  { timeout: 10000 }
);

// 初始化到第 0 帧
await page.evaluate(() => {
  const tl = window.__timelines['wine-root'];
  if (tl) tl.seek(0).pause();
});

console.log('开始截帧...');

for (let i = 0; i < TOTAL_FRAMES; i++) {
  const t = i / FPS;
  await page.evaluate((time) => {
    const tl = window.__timelines['wine-root'];
    if (tl) tl.seek(time);
  }, t);
  await page.screenshot({
    path: path.join(FRAMES_DIR, `frame_${String(i).padStart(5, '0')}.png`),
    type: 'png',
  });
  if (i % 30 === 0) {
    console.log(`  帧 ${i}/${TOTAL_FRAMES} (${t.toFixed(1)}s)`);
  }
}

console.log('截帧完成，正在合成视频...');
await browser.close();

// 用 ffmpeg-static 合成 MP4
const framePattern = path.join(FRAMES_DIR, 'frame_%05d.png');
try {
  execFileSync(ffmpegStatic, [
    '-y', '-framerate', String(FPS),
    '-i', framePattern,
    '-c:v', 'libx264',
    '-pix_fmt', 'yuv420p',
    '-preset', 'fast',
    '-crf', '18',
    OUTPUT,
  ], { stdio: 'inherit' });

  const sizeMB = (fs.statSync(OUTPUT).size / (1024 * 1024)).toFixed(1);
  console.log(`\n渲染成功: ${OUTPUT} (${sizeMB} MB)`);
} catch (e) {
  console.error('ffmpeg 合成失败:', e.message);
  process.exit(1);
}
