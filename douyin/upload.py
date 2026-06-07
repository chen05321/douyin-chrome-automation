"""
视频上传模块
通过 Base64 编码 + DataTransfer 注入实现 Chrome 中的文件上传
"""

import base64
import os
import time
from typing import Optional


def upload_file(chrome, file_path: str, selector: str = 'input[type="file"]',
                tab_index: Optional[str] = None) -> dict:
    """
    上传文件到 Chrome 中的 input[type=file]

    原理：
    1. Python 读取文件 → Base64 编码
    2. AppleScript 执行 Chrome JS
    3. JS 中 atob() 解码 → Uint8Array → File 对象
    4. DataTransfer 注入到 input.files
    5. 触发 change 事件

    Args:
        chrome: ChromeController 实例
        file_path: 文件绝对路径
        selector: CSS 选择器，默认 input[type="file"]
        tab_index: 标签页索引

    Returns:
        dict: {"success": bool, "output": str, "error": str}
    """
    if not os.path.exists(file_path):
        return {"success": False, "error": f"文件不存在: {file_path}"}

    filename = os.path.basename(file_path)
    filesize = os.path.getsize(file_path)

    # 读取文件并 Base64 编码
    with open(file_path, "rb") as f:
        b64_data = base64.b64encode(f.read()).decode("ascii")

    # 根据文件大小选择注入方式
    if filesize < 5 * 1024 * 1024:
        # 小文件：直接通过 JS eval 注入
        return _inject_via_eval(chrome, b64_data, filename, selector, tab_index)
    else:
        # 大文件：通过 AppleScript 直接执行
        return _inject_via_applescript(chrome, file_path, filename, selector, tab_index)


def _inject_via_eval(chrome, b64_data: str, filename: str,
                     selector: str, tab_index: Optional[str]) -> dict:
    """小文件：通过 chrome.execute_js 注入"""
    js_code = f"""
    (function() {{
        var b64 = '{b64_data}';
        var bin = atob(b64);
        var arr = new Uint8Array(bin.length);
        for (var i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
        var file = new File([arr], '{filename}', {{type: 'video/mp4'}});
        var input = document.querySelector('{selector}');
        if (!input) return 'INPUT_NOT_FOUND';
        var dt = new DataTransfer();
        dt.items.add(file);
        input.files = dt.files;
        input.dispatchEvent(new Event('change', {{bubbles: true}}));
        return 'INJECTED: ' + file.name + ' (' + file.size + ' bytes)';
    }})()
    """
    return chrome.execute_js(js_code, tab_index)


def _inject_via_applescript(chrome, file_path: str, filename: str,
                            selector: str, tab_index: Optional[str]) -> dict:
    """大文件：通过 AppleScript 直接执行 base64 + JS"""
    import subprocess

    # 构造 AppleScript：用 openssl base64 编码文件，然后注入 JS
    escaped_path = file_path.replace('"', '\\"')
    escaped_selector = selector.replace('"', '\\"')

    applescript = f'''
    set filePath to "{escaped_path}"
    set base64Data to do shell script "openssl base64 -in " & quoted form of filePath & " | tr -d '\\n'"

    set jsCode to "(function() {{ var b64 = '" & base64Data & "'; var bin = atob(b64); var arr = new Uint8Array(bin.length); for (var i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i); var file = new File([arr], '{filename}', {{type: \\\"video/mp4\\\"}}); var input = document.querySelector('{escaped_selector}'); if (!input) return \\\"INPUT_NOT_FOUND\\\"; var dt = new DataTransfer(); dt.items.add(file); input.files = dt.files; input.dispatchEvent(new Event(\\\"change\\\", {{bubbles: true}})); return \\\"INJECTED: \\\" + file.name + \\\" (\\\" + file.size + \\\" bytes)\\\"; }})()"

    tell application "Google Chrome"
        execute active tab of front window javascript jsCode
    end tell
    '''

    try:
        result = subprocess.run(
            ["osascript", "-e", applescript],
            capture_output=True, text=True, timeout=300
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout.strip(),
            "error": result.stderr.strip()
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "上传超时(300s)"}


def wait_upload_complete(chrome, timeout: int = 120, tab_index: Optional[str] = None) -> dict:
    """
    等待视频上传完成

    通过检测页面上的进度条消失或成功提示来判断
    """
    start = time.time()
    while time.time() - start < timeout:
        result = chrome.execute_js("""
        (function() {
            var body = document.body.innerText;
            if (body.includes('上传成功') || body.includes('作品描述')) return 'COMPLETE';
            if (body.includes('上传中') || body.includes('转码中')) return 'UPLOADING';
            if (body.includes('上传失败')) return 'FAILED';
            return 'UNKNOWN';
        })()
        """, tab_index)

        status = result.get("output", "").strip().strip('"')
        if status == "COMPLETE":
            return {"success": True, "status": "上传完成"}
        elif status == "FAILED":
            return {"success": False, "status": "上传失败"}

        time.sleep(2)

    return {"success": False, "status": "上传超时"}
