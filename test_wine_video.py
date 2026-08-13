#!/usr/bin/env python3
"""
酒主题视频生成测试脚本
调用三个已安装的 skill：seedance2-video-gen / media-generation / hyperframes
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).resolve().parent
SKILLS = ROOT / "skills"

# 酒主题 prompt（中英双语，适配不同模型）
WINE_PROMPT_CN = (
    "深红色葡萄酒缓缓倒入水晶高脚杯，液体在杯壁形成优雅的挂杯，"
    "暖色调灯光下酒液泛着宝石红光泽，背景是古朴的橡木酒窖，"
    "镜头从杯口特写缓慢下移展示酒液漩涡，电影级质感，慢动作"
)
WINE_PROMPT_EN = (
    "Cinematic close-up of deep red wine pouring into a crystal goblet, "
    "elegant legs forming on the glass walls, ruby red liquid glowing under warm lighting, "
    "vintage oak wine cellar background, camera slowly tilts down from rim to show swirling liquid, "
    "slow motion, premium commercial cinematography"
)

# ============================================================
# 1. Seedance 2.0 — AI 视频生成（文生视频）
# ============================================================
def call_seedance2():
    print("\n" + "=" * 60)
    print("【1/3】调用 seedance2-video-gen 技能（AI 文生视频）")
    print("=" * 60)

    api_key = os.environ.get("SEEDANCE_API_KEY", "").strip()
    skill_md = SKILLS / "@xk103295870-alt" / "seedance2-video-gen" / "SKILL.md"
    print(f"  技能路径: {skill_md}")

    # 构建 API 调用参数（根据 SKILL.md 规范）
    payload = {
        "model": "seedance-2.0-text-to-video",
        "prompt": WINE_PROMPT_EN,
        "duration": 5,
        "quality": "720p",
        "aspect_ratio": "16:9",
        "generate_audio": True,
    }
    print(f"  模型: {payload['model']}")
    print(f"  时长: {payload['duration']}s | 分辨率: {payload['quality']} | 比例: {payload['aspect_ratio']}")
    print(f"  Prompt: {payload['prompt'][:80]}...")

    if not api_key:
        print("\n  ⚠ SEEDANCE_API_KEY 未设置，跳过实际 API 调用")
        print("  已生成完整 API 参数（如需调用请设置环境变量后重试）:")
        print(json.dumps(payload, ensure_ascii=False, indent=2))

        # 保存参数到文件供后续使用
        params_file = ROOT / "wine-video" / "seedance2_params.json"
        params_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n  参数已保存: {params_file}")
        print("  状态: ✗ 跳过（无 API Key）")
        return False

    # 有 API Key 时执行实际调用
    print(f"\n  API Key 已配置，正在调用 EvoLink API...")
    import requests
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        resp = requests.post(
            "https://api.evolink.ai/v1/videos/generations",
            json=payload, headers=headers, timeout=30,
        )
        print(f"  HTTP {resp.status_code}")
        result = resp.json()

        if resp.ok:
            task_id = result.get("id") or result.get("task_id")
            print(f"  任务 ID: {task_id}")
            print("  正在轮询生成结果...")

            # 轮询查询
            for i in range(60):
                time.sleep(5)
                poll = requests.get(
                    f"https://api.evolink.ai/v1/tasks/{task_id}",
                    headers={"Authorization": f"Bearer {api_key}"}, timeout=30,
                ).json()
                status = str(poll.get("status", "")).lower()
                print(f"  轮询 {i+1}/60 — 状态: {status}")
                if status in ("succeeded", "completed", "success"):
                    video_url = poll.get("video_url") or poll.get("result_url")
                    print(f"  视频链接: {video_url}")
                    out = ROOT / "wine-video" / "seedance_wine.mp4"
                    if video_url:
                        dl = requests.get(video_url, timeout=120)
                        out.write_bytes(dl.content)
                        print(f"  已下载: {out}")
                    print("  状态: ✓ 成功")
                    return True
                if status in ("failed", "error"):
                    print(f"  生成失败: {poll}")
                    print("  状态: ✗ 失败")
                    return False
        else:
            print(f"  API 错误: {result}")
            print("  状态: ✗ 失败")
            return False
    except Exception as e:
        print(f"  异常: {e}")
        print("  状态: ✗ 失败")
        return False


# ============================================================
# 2. Media Generation — 烟雾测试 + 酒主题生成
# ============================================================
def call_media_generation():
    print("\n" + "=" * 60)
    print("【2/3】调用 media-generation 技能（媒体生成）")
    print("=" * 60)

    mg_scripts = SKILLS / "@lijiazhen0623" / "media-generation" / "scripts"
    print(f"  技能路径: {mg_scripts}")

    # Step A: 运行 smoke_test.py（内置测试脚本）
    print("\n  [A] 运行内置 smoke_test.py...")
    result = subprocess.run(
        [sys.executable, str(mg_scripts / "smoke_test.py")],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    if result.returncode == 0:
        print("  smoke_test 通过 ✓")
        try:
            summary = json.loads(result.stdout)
            for t in summary.get("tests", []):
                print(f"    · {t['name']}: {'✓' if t['ok'] else '✗'}")
        except json.JSONDecodeError:
            print(f"    {result.stdout.strip()}")
    else:
        print(f"  smoke_test 失败 ✗")
        print(f"    stderr: {result.stderr[:300]}")

    # Step B: 尝试用 generate_video.py 生成酒主题视频
    print("\n  [B] 调用 generate_video.py 生成酒主题视频...")
    out_dir = ROOT / "tmp" / "videos"
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, str(mg_scripts / "generate_video.py"),
        "--prompt", WINE_PROMPT_EN,
        "--size", "1280x720",
        "--seconds", "6",
        "--out-dir", str(out_dir),
        "--prefix", "wine-media-gen",
        "--print-json",
    ]
    print(f"  命令: {' '.join(cmd[:6])}...")

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))

    if result.returncode == 0:
        print("  视频生成成功 ✓")
        try:
            data = json.loads(result.stdout)
            downloaded = data.get("downloaded")
            if downloaded:
                print(f"  输出文件: {downloaded}")
            else:
                print(f"  响应: {json.dumps(data.get('response', {}), ensure_ascii=False)[:200]}")
        except json.JSONDecodeError:
            print(f"  {result.stdout[:300]}")
        print("  状态: ✓ 成功")
        return True
    else:
        # 检查失败原因
        stderr_lower = result.stderr.lower()
        if "provider not found" in stderr_lower or "config not found" in stderr_lower or "placeholder" in stderr_lower:
            print("  ⚠ OpenClaw 未配置媒体提供商，跳过实际生成")
            print("  状态: ✗ 跳过（无媒体 API 配置）")
        else:
            print(f"  生成失败 ✗")
            print(f"    stderr: {result.stderr[:400]}")
            print("  状态: ✗ 失败")
        return False


# ============================================================
# 3. HyperFrames — 渲染酒主题 HTML 合成视频
# ============================================================
def call_hyperframes():
    print("\n" + "=" * 60)
    print("【3/3】调用 hyperframes 技能（HTML 视频合成渲染）")
    print("=" * 60)

    comp_dir = ROOT / "wine-video"
    html_file = comp_dir / "index.html"
    output_mp4 = comp_dir / "wine-story.mp4"
    render_script = comp_dir / "render.py"
    print(f"  合成文件: {html_file}")
    print(f"  渲染脚本: {render_script}")
    print(f"  输出目标: {output_mp4}")

    if not html_file.exists():
        print("  ✗ index.html 不存在")
        return False

    # 使用 Python 渲染脚本（playwright + Edge 截帧 + imageio-ffmpeg 合成）
    print("\n  使用 playwright + Edge 截帧 + imageio-ffmpeg 合成...")
    result = subprocess.run(
        [sys.executable, str(render_script)],
        capture_output=True, text=True, cwd=str(comp_dir), timeout=600,
    )

    if result.returncode == 0 and output_mp4.exists():
        size_mb = output_mp4.stat().st_size / (1024 * 1024)
        print(f"\n  渲染成功 ✓ — {output_mp4} ({size_mb:.1f} MB)")
        print("  状态: ✓ 成功")
        return True
    else:
        print(f"  渲染失败 ✗")
        print(f"    stdout: {result.stdout[-500:]}")
        print(f"    stderr: {result.stderr[-500:]}")
        print("  状态: ✗ 失败")
        return False


def render_with_puppeteer(comp_dir, output_mp4):
    """备用渲染方案：用 puppeteer 逐帧截图 + ffmpeg 合成视频"""
    frame_script = comp_dir / "_render_frames.mjs"
    frames_dir = comp_dir / "frames"
    frames_dir.mkdir(exist_ok=True)

    frame_script.write_text("""
import puppeteer from 'puppeteer';
import { pathToFileURL } from 'url';
import path from 'path';

const FPS = 30;
const DURATION = 13;
const WIDTH = 1920;
const HEIGHT = 1080;
const TOTAL_FRAMES = FPS * DURATION;

const browser = await puppeteer.launch({
  headless: 'new',
  args: ['--no-sandbox', '--disable-setuid-sandbox', '--force-device-scale-factor=1']
});
const page = await browser.newPage();
await page.setViewport({ width: WIDTH, height: HEIGHT, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(path.resolve('index.html')).href, { waitUntil: 'networkidle0' });
await page.waitForFunction('window.__timelines && Object.keys(window.__timelines).length > 0', { timeout: 5000 });
await page.evaluate(() => {
  const tl = window.__timelines['wine-root'];
  if (tl) tl.seek(0).pause();
});

for (let i = 0; i < TOTAL_FRAMES; i++) {
  const t = i / FPS;
  await page.evaluate((time) => {
    const tl = window.__timelines['wine-root'];
    if (tl) tl.seek(time);
  }, t);
  await page.screenshot({ path: path.join('frames', `frame_${String(i).padStart(5, '0')}.png`), type: 'png' });
  if (i % 30 === 0) console.error(`帧 ${i}/${TOTAL_FRAMES} (${(t).toFixed(1)}s)`);
}

await browser.close();
console.error('截帧完成');
""", encoding='utf-8');

    # 安装 puppeteer 并截帧
    print("  安装 puppeteer 并截帧...")
    subprocess.run(
        "npm install puppeteer",
        capture_output=True, text=True, cwd=str(comp_dir), timeout=120, shell=True,
    )
    subprocess.run(
        "npx puppeteer install chrome",
        capture_output=True, text=True, cwd=str(comp_dir), timeout=180, shell=True,
    )

    # 用 node 执行截帧脚本
    result = subprocess.run(
        f'node "{frame_script}"',
        capture_output=True, text=True, cwd=str(comp_dir), timeout=300, shell=True,
    )
    if result.returncode != 0:
        print(f"  截帧失败: {result.stderr[:300]}")
        print("  状态: ✗ 失败")
        return False

    print("  截帧完成，正在用 ffmpeg 合成视频...")

    # 用 ffmpeg 合成帧为 MP4
    ffmpeg_cmd = f'ffmpeg -y -framerate 30 -i "{frames_dir / "frame_%05d.png"}" -c:v libx264 -pix_fmt yuv420p -preset fast -crf 18 "{output_mp4}"'
    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=120, shell=True)

    if result.returncode == 0 and output_mp4.exists():
        size_mb = output_mp4.stat().st_size / (1024 * 1024)
        print(f"  渲染成功 ✓ — {output_mp4} ({size_mb:.1f} MB)")
        print("  状态: ✓ 成功（puppeteer + ffmpeg 备用方案）")
        return True
    else:
        print(f"  ffmpeg 合成失败: {result.stderr[:300]}")
        print("  状态: ✗ 失败")
        return False


# ============================================================
# 主函数
# ============================================================
def main():
    print("=" * 60)
    print("  酒主题视频生成 — 测试脚本")
    print("  调用技能: seedance2-video-gen + media-generation + hyperframes")
    print("=" * 60)
    print(f"  工作目录: {ROOT}")
    print(f"  技能目录: {SKILLS}")
    print(f"  Python:   {sys.executable}")

    results = {}

    # 1. Seedance 2.0
    results["seedance2"] = call_seedance2()

    # 2. Media Generation
    results["media-generation"] = call_media_generation()

    # 3. HyperFrames
    results["hyperframes"] = call_hyperframes()

    # 汇总
    print("\n" + "=" * 60)
    print("  汇总")
    print("=" * 60)
    for skill, ok in results.items():
        status = "✓ 成功" if ok else "✗ 未成功"
        print(f"  {skill:25s} {status}")

    success = any(results.values())
    if success:
        print(f"\n  视频输出目录: {ROOT / 'wine-video'}")
    print("=" * 60)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
