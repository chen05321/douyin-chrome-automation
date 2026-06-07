"""
Chrome AppleScript 控制器
通过 AppleScript 执行 Chrome JavaScript，操控已登录的浏览器
"""

import subprocess
import json
import os
import time


class ChromeController:
    """通过 AppleScript 控制 Chrome 浏览器"""

    def __init__(self):
        self._ensure_chrome_running()

    def _ensure_chrome_running(self):
        """确保 Chrome 正在运行"""
        result = subprocess.run(
            ["pgrep", "-x", "Google Chrome"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            subprocess.run(["open", "-a", "Google Chrome"], capture_output=True)
            time.sleep(3)

    def execute_js(self, js_code: str, tab_index: str = None) -> dict:
        """
        在 Chrome 中执行 JavaScript

        Args:
            js_code: 要执行的 JS 代码
            tab_index: 标签页索引，如 "1:1"。None 则用当前活跃标签页

        Returns:
            dict: {"success": bool, "output": str, "error": str}
        """
        # 转义 JS 中的引号和反斜杠
        escaped_js = js_code.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")

        if tab_index:
            # 指定标签页: window 1, tab N
            parts = tab_index.split(":")
            window_idx = parts[0]
            tab_idx = parts[1]
            script = f'''
            tell application "Google Chrome"
                execute window {window_idx} tab {tab_idx} javascript "{escaped_js}"
            end tell
            '''
        else:
            # 当前活跃标签页
            script = f'''
            tell application "Google Chrome"
                execute active tab of front window javascript "{escaped_js}"
            end tell
            '''

        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return {"success": True, "output": result.stdout.strip(), "error": ""}
            else:
                return {"success": False, "output": "", "error": result.stderr.strip()}
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "", "error": "执行超时(30s)"}

    def navigate(self, url: str, tab_index: str = None) -> dict:
        """在指定标签页中导航到 URL"""
        js = f'window.location.href = "{url}"; "NAVIGATING";'
        return self.execute_js(js, tab_index)

    def open_new_tab(self, url: str) -> dict:
        """打开新标签页"""
        script = f'''
        tell application "Google Chrome"
            tell front window
                make new tab with properties {{URL:"{url}"}}
            end tell
        end tell
        '''
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=10
            )
            return {"success": result.returncode == 0, "error": result.stderr.strip()}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "超时"}

    def get_tabs(self) -> list:
        """获取所有标签页信息"""
        script = '''
        set output to ""
        tell application "Google Chrome"
            set windowCount to count windows
            repeat with w from 1 to windowCount
                set tabCount to count tabs of window w
                repeat with t from 1 to tabCount
                    set tabTitle to title of tab t of window w
                    set tabURL to URL of tab t of window w
                    set output to output & w & ":" & t & "|" & tabTitle & "|" & tabURL & "\\n"
                end repeat
            end repeat
        end tell
        return output
        '''
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=10
            )
            tabs = []
            for line in result.stdout.strip().split("\n"):
                if "|" in line:
                    parts = line.split("|", 2)
                    if len(parts) == 3:
                        tabs.append({
                            "index": parts[0],
                            "title": parts[1],
                            "url": parts[2]
                        })
            return tabs
        except Exception:
            return []

    def get_page_text(self, tab_index: str = None) -> str:
        """获取页面文本内容"""
        result = self.execute_js("document.body.innerText", tab_index)
        return result.get("output", "")

    def get_page_url(self, tab_index: str = None) -> str:
        """获取当前页面 URL"""
        result = self.execute_js("window.location.href", tab_index)
        return result.get("output", "").strip('"')

    def wait_for_element(self, selector: str, timeout: int = 10, tab_index: str = None) -> bool:
        """等待元素出现"""
        js = f"""
        (function() {{
            var el = document.querySelector('{selector}');
            return el ? 'FOUND' : 'NOT_FOUND';
        }})()
        """
        start = time.time()
        while time.time() - start < timeout:
            result = self.execute_js(js, tab_index)
            if "FOUND" in result.get("output", ""):
                return True
            time.sleep(0.5)
        return False

    def click_element(self, selector: str, tab_index: str = None) -> dict:
        """点击元素"""
        js = f"""
        (function() {{
            var el = document.querySelector('{selector}');
            if (el) {{ el.click(); return 'CLICKED'; }}
            return 'NOT_FOUND';
        }})()
        """
        return self.execute_js(js, tab_index)

    def type_text(self, text: str, tab_index: str = None) -> dict:
        """通过剪贴板粘贴输入文本"""
        # 先写入剪贴板
        subprocess.run(["pbcopy"], input=text.encode(), check=True)
        time.sleep(0.2)

        # 通过 AppleScript 粘贴
        script = '''
        tell application "System Events"
            keystroke "v" using {command down}
        end tell
        '''
        try:
            subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
