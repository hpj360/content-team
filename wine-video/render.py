#!/usr/bin/env python3
"""
酒主题 HyperFrames 渲染脚本（Python 版）
使用 playwright + Edge 截帧，imageio-ffmpeg 合成 MP4
"""

import sys
from pathlib import Path

COMP_DIR = Path(__file__).resolve().parent
HTML_FILE = COMP_DIR / "index.html"
OUTPUT_MP4 = COMP_DIR / "wine-story.mp4"
FRAMES_DIR = COMP_DIR / "frames"

FPS = 30
DURATION = 13
WIDTH = 1920
HEIGHT = 1080
TOTAL_FRAMES = FPS * DURATION


def capture_frames():
    """用 playwright + Edge 逐帧截图"""
    from playwright.sync_api import sync_playwright

    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    # 清理旧帧
    for f in FRAMES_DIR.glob("*.png"):
        f.unlink()

    print(f"渲染参数: {WIDTH}x{HEIGHT} @ {FPS}fps, {DURATION}s ({TOTAL_FRAMES} 帧)")

    with sync_playwright() as p:
        # 尝试用系统 Edge，失败则用 playwright 自带 chromium
        try:
            browser = p.chromium.launch(channel="msedge", headless=True)
            print("使用系统 Edge 浏览器")
        except Exception:
            print("Edge 不可用，尝试安装 playwright chromium...")
            import subprocess
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"],
                         capture_output=True, timeout=120)
            browser = p.chromium.launch(headless=True)
            print("使用 playwright chromium")

        page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT})
        page.goto(HTML_FILE.as_uri(), wait_until="networkidle")

        # 等待 GSAP timeline 就绪
        page.wait_for_function(
            'window.__timelines && Object.keys(window.__timelines).length > 0',
            timeout=10000
        )

        # 初始化到第 0 帧
        page.evaluate("""() => {
            const tl = window.__timelines['wine-root'];
            if (tl) tl.seek(0).pause();
        }""")

        print("开始截帧...")

        for i in range(TOTAL_FRAMES):
            t = i / FPS
            page.evaluate(f"""() => {{
                const tl = window.__timelines['wine-root'];
                if (tl) tl.seek({t});
            }}""")
            page.screenshot(path=str(FRAMES_DIR / f"frame_{i:05d}.png"), type="png")

            if i % 30 == 0:
                print(f"  帧 {i}/{TOTAL_FRAMES} ({t:.1f}s)")

        browser.close()

    print("截帧完成")


def encode_video():
    """用 imageio-ffmpeg 合成 MP4"""
    import imageio_ffmpeg
    import subprocess

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    print(f"ffmpeg 路径: {ffmpeg_exe}")

    frame_pattern = str(FRAMES_DIR / "frame_%05d.png")

    print("正在合成视频...")
    result = subprocess.run([
        ffmpeg_exe, "-y",
        "-framerate", str(FPS),
        "-i", frame_pattern,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-crf", "18",
        str(OUTPUT_MP4),
    ], capture_output=True, text=True, timeout=120)

    if result.returncode == 0 and OUTPUT_MP4.exists():
        size_mb = OUTPUT_MP4.stat().st_size / (1024 * 1024)
        print(f"\n渲染成功: {OUTPUT_MP4} ({size_mb:.1f} MB)")
        return True
    else:
        print(f"合成失败: {result.stderr[:500]}")
        return False


def main():
    print("=" * 50)
    print("  酒主题视频渲染 (playwright + imageio-ffmpeg)")
    print("=" * 50)

    try:
        capture_frames()
    except Exception as e:
        print(f"截帧失败: {e}")
        return False

    return encode_video()


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
