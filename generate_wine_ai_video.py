#!/usr/bin/env python3
"""
酒主题 AI 视频生成 — 智谱 CogVideoX-3
使用 ZAI_API_KEY 调用智谱清影视频生成 API
"""

import os
import sys
import time
import json
import requests
from pathlib import Path

# 智谱 API 配置
API_KEY = os.environ.get("ZAI_API_KEY", "").strip()
API_BASE = "https://open.bigmodel.cn/api/paas/v4"
MODEL = "cogvideox-3"

# 输出目录
OUTPUT_DIR = Path(__file__).resolve().parent / "wine-video"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 酒主题 prompt
WINE_PROMPT = (
    "特写镜头：深红色葡萄酒缓缓倒入水晶高脚杯，酒液在杯壁形成优雅的挂杯，"
    "暖色调灯光下酒液泛着宝石红光泽，背景是古朴的橡木酒窖，"
    "镜头从杯口缓慢下移展示酒液漩涡，电影级质感，慢动作，高级商业广告风格"
)


def generate_video():
    """调用 CogVideoX-3 文生视频 API"""
    print("=" * 55)
    print("  酒主题 AI 视频生成 — 智谱 CogVideoX-3")
    print("=" * 55)
    print(f"  API Key: {API_KEY[:12]}...{API_KEY[-6:]}")
    print(f"  模型:    {MODEL}")
    print(f"  Prompt:  {WINE_PROMPT[:60]}...")
    print(f"  分辨率:  1920x1080 | 时长: 5s | 帧率: 30fps")
    print("-" * 55)

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "prompt": WINE_PROMPT,
        "quality": "quality",
        "with_audio": True,
        "size": "1920x1080",
        "fps": 30,
        "duration": 5,
    }

    # Step 1: 提交生成任务
    print("\n[1/3] 提交视频生成任务...")
    try:
        resp = requests.post(
            f"{API_BASE}/videos/generations",
            json=payload, headers=headers, timeout=30,
        )
        result = resp.json()

        if resp.status_code != 200:
            print(f"  API 错误 ({resp.status_code}): {json.dumps(result, ensure_ascii=False)}")
            return False

        task_id = result.get("id")
        task_status = result.get("task_status")
        print(f"  任务 ID: {task_id}")
        print(f"  初始状态: {task_status}")

    except Exception as e:
        print(f"  请求失败: {e}")
        return False

    if not task_id:
        print(f"  未获取到任务 ID: {result}")
        return False

    # Step 2: 轮询查询结果
    print("\n[2/3] 等待视频生成（通常需要 1-3 分钟）...")
    max_polls = 60
    for i in range(max_polls):
        time.sleep(5)
        try:
            poll_resp = requests.get(
                f"{API_BASE}/async-result/{task_id}",
                headers=headers, timeout=30,
            )
            poll_result = poll_resp.json()
        except Exception as e:
            print(f"  轮询异常: {e}")
            continue

        status = poll_result.get("task_status", "")
        elapsed = (i + 1) * 5
        print(f"  轮询 {i+1}/{max_polls} — {elapsed}s — 状态: {status}")

        if status == "SUCCESS":
            video_result = poll_result.get("video_result", [])
            if video_result:
                video_url = video_result[0].get("url")
                cover_url = video_result[0].get("cover_image_url")
                print(f"\n  生成成功!")
                print(f"  视频链接: {video_url}")
                if cover_url:
                    print(f"  封面链接: {cover_url}")

                # Step 3: 下载视频
                print("\n[3/3] 下载视频...")
                output_file = OUTPUT_DIR / "wine_cogvideox.mp4"
                try:
                    dl_resp = requests.get(video_url, timeout=120)
                    dl_resp.raise_for_status()
                    output_file.write_bytes(dl_resp.content)
                    size_mb = output_file.stat().st_size / (1024 * 1024)
                    print(f"  已下载: {output_file} ({size_mb:.1f} MB)")

                    # 保存元数据
                    meta_file = OUTPUT_DIR / "cogvideox_meta.json"
                    meta_file.write_text(json.dumps({
                        "task_id": task_id,
                        "model": MODEL,
                        "prompt": WINE_PROMPT,
                        "video_url": video_url,
                        "cover_url": cover_url,
                        "local_file": str(output_file),
                    }, ensure_ascii=False, indent=2), encoding="utf-8")

                    print("\n" + "=" * 55)
                    print(f"  AI 视频生成成功!")
                    print(f"  输出: {output_file}")
                    print("=" * 55)
                    return True
                except Exception as e:
                    print(f"  下载失败: {e}")
                    print(f"  手动下载: {video_url}")
                    return False
            else:
                print(f"  无视频结果: {poll_result}")
                return False

        elif status == "FAIL":
            print(f"  生成失败: {json.dumps(poll_result, ensure_ascii=False)}")
            return False

    print(f"\n  超时（{max_polls * 5}s），任务可能仍在处理中")
    print(f"  可手动查询: GET {API_BASE}/async-result/{task_id}")
    return False


def main():
    if not API_KEY:
        print("错误: ZAI_API_KEY 未设置")
        sys.exit(1)
    ok = generate_video()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
