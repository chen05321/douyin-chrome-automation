#!/usr/bin/env python3
"""
Hermes 自动录屏器
录制自己的自动化操作过程，用于抖音/小红书内容生产

用法：
    python3 hermes_recorder.py start          # 开始录屏
    python3 hermes_recorder.py start --duration 60  # 录60秒
    python3 hermes_recorder.py stop           # 停止录屏
    python3 hermes_recorder.py list           # 列出已录制文件
"""

import subprocess
import os
import time
import sys
import signal
import json
from datetime import datetime
from pathlib import Path

RECORD_DIR = Path.home() / "hermes-records"
RECORD_DIR.mkdir(exist_ok=True)

# 当前录制进程
_record_process = None
_record_file = None


def get_screen_size():
    """获取屏幕分辨率"""
    script = 'tell application "Finder" to get bounds of window of desktop'
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode == 0:
        # 输出格式: "0, 0, 1920, 1080"
        parts = result.stdout.strip().split(", ")
        if len(parts) == 4:
            return int(parts[2]), int(parts[3])
    return 1920, 1080


def list_avfoundation_devices():
    """列出 ffmpeg avfoundation 可用设备"""
    result = subprocess.run(
        ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
        capture_output=True, text=True
    )
    # 从 stderr 中提取设备列表（ffmpeg 输出到 stderr）
    devices = []
    for line in result.stderr.split("\n"):
        if "AVFoundation" in line and "[" in line:
            devices.append(line.strip())
    return devices


def start_recording(duration=None, region=None, filename=None):
    """
    开始录屏

    Args:
        duration: 录制时长（秒），None 表示手动停止
        region: 录制区域 [x, y, width, height]，None 表示全屏
        filename: 输出文件名，None 自动生成
    """
    global _record_process, _record_file

    if _record_process and _record_process.poll() is None:
        print(f"⚠️ 已在录制中: {_record_file}")
        return _record_file

    # 生成文件名
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"hermes_{timestamp}.mp4"

    _record_file = RECORD_DIR / filename

    # 构建 ffmpeg 命令
    cmd = [
        "ffmpeg", "-y",
        "-f", "avfoundation",
        "-capture_cursor", "1",        # 录制鼠标光标
        "-capture_mouse_clicks", "1",   # 录制鼠标点击高亮
        "-framerate", "30",
        "-i", "0",                      # 屏幕0（Capture screen 0）
    ]

    # 裁剪区域
    if region:
        x, y, w, h = region
        cmd.extend(["-vf", f"crop={w}:{h}:{x}:{y}"])

    # 时长
    if duration:
        cmd.extend(["-t", str(duration)])

    # 编码参数
    cmd.extend([
        "-vcodec", "libx264",
        "-preset", "ultrafast",     # 最快速度编码
        "-pix_fmt", "yuv420p",
        "-crf", "23",
        str(_record_file)
    ])

    print(f"🎬 开始录制: {_record_file.name}")
    if duration:
        print(f"   时长: {duration}秒")
    if region:
        print(f"   区域: {region}")
    print(f"   停止: python3 hermes_recorder.py stop 或 Ctrl+C")

    _record_process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    return str(_record_file)


def stop_recording():
    """停止录屏"""
    global _record_process, _record_file

    if not _record_process or _record_process.poll() is not None:
        print("没有在录制中")
        return None

    # 发送 SIGINT 让 ffmpeg 正常结束（写入尾部元数据）
    _record_process.send_signal(signal.SIGINT)
    _record_process.wait(timeout=10)

    size = os.path.getsize(_record_file) if _record_file.exists() else 0
    print(f"✅ 录制完成: {_record_file.name} ({size/1024/1024:.1f}MB)")

    _record_process = None
    result = str(_record_file)
    _record_file = None
    return result


def list_records():
    """列出已录制文件"""
    files = sorted(RECORD_DIR.glob("*.mp4"), key=os.path.getmtime, reverse=True)
    if not files:
        print("暂无录制文件")
        return []

    print(f"📁 录制文件 ({len(files)} 个):")
    for f in files[:20]:
        size = os.path.getsize(f) / 1024 / 1024
        mtime = datetime.fromtimestamp(os.path.getmtime(f)).strftime("%m-%d %H:%M")
        print(f"  {mtime}  {size:6.1f}MB  {f.name}")

    return [str(f) for f in files]


def get_chrome_window_region():
    """获取 Chrome 窗口位置和大小（用于区域录制）"""
    script = '''
    tell application "Google Chrome"
        set winBounds to bounds of front window
        return (item 1 of winBounds) & "," & (item 2 of winBounds) & "," & (item 3 of winBounds) & "," & (item 4 of winBounds)
    end tell
    '''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode == 0:
        parts = result.stdout.strip().split(",")
        if len(parts) == 4:
            x, y, x2, y2 = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
            return [x, y, x2 - x, y2 - y]
    return None


def record_automation(task_name, func, *args, **kwargs):
    """
    录制一个自动化任务的执行过程

    用法：
        def my_task():
            dy = DouyinAutomation()
            dy.upload_video("video.mp4")

        record_automation("upload_video", my_task)
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{task_name}_{timestamp}.mp4"

    print(f"🎬 开始录制自动化任务: {task_name}")
    start_recording(filename=filename)

    time.sleep(1)  # 等录屏稳定

    try:
        result = func(*args, **kwargs)
        print(f"✅ 任务完成: {task_name}")
    except Exception as e:
        print(f"❌ 任务失败: {e}")
        result = None
    finally:
        time.sleep(2)  # 多录2秒
        stop_recording()

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 hermes_recorder.py [start|stop|list]")
        print("  start [--duration 60] [--chrome]  开始录制")
        print("  stop                              停止录制")
        print("  list                              列出录制文件")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "start":
        duration = None
        region = None

        if "--duration" in sys.argv:
            idx = sys.argv.index("--duration")
            duration = int(sys.argv[idx + 1])

        if "--chrome" in sys.argv:
            region = get_chrome_window_region()
            if region:
                print(f"📌 录制 Chrome 窗口: {region}")

        start_recording(duration=duration, region=region)

        if duration:
            time.sleep(duration + 1)
            print("⏱️ 录制时长到达，自动停止")
        else:
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                stop_recording()

    elif cmd == "stop":
        stop_recording()

    elif cmd == "list":
        list_records()

    else:
        print(f"未知命令: {cmd}")
