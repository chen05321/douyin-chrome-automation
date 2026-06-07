"""
抖音自动化核心模块
整合 Chrome 控制、上传、发布、评论、数据监控
"""

import time
from typing import Optional, List
from .chrome import ChromeController
from .upload import upload_file, wait_upload_complete


class DouyinAutomation:
    """
    抖音创作者平台自动化控制器

    使用方法：
        dy = DouyinAutomation()
        dy.upload_video("/path/to/video.mp4", title="标题", topics=["话题"])
        dy.publish()
    """

    # 抖音创作者平台 URL
    CREATOR_HOME = "https://creator.douyin.com/creator-micro/home"
    UPLOAD_PAGE = "https://creator.douyin.com/creator-micro/content/upload"
    COMMENTS_PAGE = "https://creator.douyin.com/creator-micro/content/manage"
    ANALYTICS_PAGE = "https://creator.douyin.com/creator-micro/data"

    def __init__(self, tab_index: Optional[str] = None):
        """
        初始化

        Args:
            tab_index: 指定 Chrome 标签页，如 "1:1"。None 则自动查找抖音标签页
        """
        self.chrome = ChromeController()
        self.tab_index = tab_index or self._find_douyin_tab()

    def _find_douyin_tab(self) -> Optional[str]:
        """自动查找抖音标签页"""
        tabs = self.chrome.get_tabs()
        for tab in tabs:
            if "douyin.com" in tab.get("url", ""):
                return tab["index"]
        return None

    def _eval(self, js_code: str) -> dict:
        """执行 JS 并返回结果"""
        return self.chrome.execute_js(js_code, self.tab_index)

    def _eval_value(self, js_code: str):
        """执行 JS 并返回解析后的值"""
        result = self._eval(js_code)
        output = result.get("output", "")
        try:
            import json
            return json.loads(output)
        except (json.JSONDecodeError, TypeError):
            return output.strip('"')

    # ========== 账号信息 ==========

    def get_stats(self) -> dict:
        """
        获取账号数据

        Returns:
            dict: {"followers": int, "following": int, "likes": int, "username": str}
        """
        # 先导航到首页
        if not self.tab_index:
            return {"error": "未找到抖音标签页"}

        self.chrome.navigate(self.CREATOR_HOME, self.tab_index)
        time.sleep(3)

        return self._eval_value("""
        (function() {
            var text = document.body.innerText;
            var result = {};

            // 提取用户名
            var nameMatch = text.match(/抖音号：(\\S+)/);
            if (nameMatch) result.douyin_id = nameMatch[1];

            // 提取关注/粉丝/获赞
            var followMatch = text.match(/关注\\s*(\\d+)/);
            var fanMatch = text.match(/粉丝\\s*(\\d+)/);
            var likeMatch = text.match(/获赞\\s*(\\d+)/);

            if (followMatch) result.following = parseInt(followMatch[1]);
            if (fanMatch) result.followers = parseInt(fanMatch[1]);
            if (likeMatch) result.likes = parseInt(likeMatch[1]);

            return JSON.stringify(result);
        })()
        """)

    # ========== 视频上传 ==========

    def upload_video(self, video_path: str, title: str = "",
                     topics: List[str] = None) -> dict:
        """
        上传视频到抖音

        Args:
            video_path: 视频文件绝对路径
            title: 视频标题/描述
            topics: 话题标签列表，如 ["AI", "自动化"]

        Returns:
            dict: {"success": bool, "status": str}
        """
        # 导航到上传页
        self.chrome.navigate(self.UPLOAD_PAGE, self.tab_index)
        time.sleep(5)

        # 上传文件
        result = upload_file(self.chrome, video_path, tab_index=self.tab_index)
        if not result.get("success"):
            return result

        # 等待上传完成
        upload_result = wait_upload_complete(self.chrome, tab_index=self.tab_index)
        if not upload_result.get("success"):
            return upload_result

        # 填写标题
        if title:
            self._fill_title(title)

        # 添加话题
        if topics:
            self._add_topics(topics)

        return {"success": True, "status": "上传完成，已填写信息"}

    def _fill_title(self, title: str):
        """填写视频标题"""
        # 抖音的标题输入框通常是 contenteditable 的 div
        js = f"""
        (function() {{
            // 查找作品描述输入框
            var editors = document.querySelectorAll('[contenteditable="true"]');
            for (var ed of editors) {{
                if (ed.closest('[class*="desc"]') || ed.closest('[class*="title"]') || ed.innerText.length < 100) {{
                    ed.focus();
                    ed.innerText = '{title}';
                    ed.dispatchEvent(new Event('input', {{bubbles: true}}));
                    return 'TITLE_FILLED';
                }}
            }}
            // 备选：找 placeholder 包含"描述"的输入框
            var inputs = document.querySelectorAll('textarea, input[type="text"]');
            for (var inp of inputs) {{
                if (inp.placeholder && inp.placeholder.includes('描述')) {{
                    inp.value = '{title}';
                    inp.dispatchEvent(new Event('input', {{bubbles: true}}));
                    return 'TITLE_FILLED_INPUT';
                }}
            }}
            return 'TITLE_NOT_FOUND';
        }})()
        """
        self._eval(js)

    def _add_topics(self, topics: List[str]):
        """添加话题标签"""
        for topic in topics:
            js = f"""
            (function() {{
                // 点击添加话题按钮
                var btns = document.querySelectorAll('span, div, button');
                for (var btn of btns) {{
                    if (btn.innerText && btn.innerText.includes('添加话题')) {{
                        btn.click();
                        return 'TOPIC_BTN_CLICKED';
                    }}
                }}
                return 'TOPIC_BTN_NOT_FOUND';
            }})()
            """
            self._eval(js)
            time.sleep(1)

            # 输入话题关键词
            js_type = f"""
            (function() {{
                var input = document.querySelector('input[placeholder*="话题"], input[placeholder*="搜索"]');
                if (input) {{
                    input.focus();
                    input.value = '{topic}';
                    input.dispatchEvent(new Event('input', {{bubbles: true}}));
                    return 'TOPIC_TYPED';
                }}
                return 'TOPIC_INPUT_NOT_FOUND';
            }})()
            """
            self._eval(js_type)
            time.sleep(1)

            # 选择第一个搜索结果
            self._eval("""
            (function() {
                var items = document.querySelectorAll('[class*="topic"] [class*="item"], [class*="suggest"] [class*="item"]');
                if (items.length > 0) { items[0].click(); return 'TOPIC_SELECTED'; }
                return 'NO_TOPIC_RESULT';
            })()
            """)
            time.sleep(0.5)

    def publish(self) -> dict:
        """
        点击发布按钮

        Returns:
            dict: {"success": bool, "status": str}
        """
        result = self._eval("""
        (function() {
            var btns = document.querySelectorAll('button');
            for (var btn of btns) {
                if (btn.innerText && btn.innerText.includes('发布') && !btn.innerText.includes('定时')) {
                    btn.click();
                    return 'PUBLISHED';
                }
            }
            return 'PUBLISH_BTN_NOT_FOUND';
        })()
        """)
        output = result.get("output", "").strip().strip('"')
        return {"success": "PUBLISHED" in output, "status": output}

    # ========== 评论管理 ==========

    def get_comments(self, limit: int = 10) -> list:
        """获取最新评论"""
        self.chrome.navigate(self.COMMENTS_PAGE, self.tab_index)
        time.sleep(3)

        return self._eval_value(f"""
        (function() {{
            var comments = [];
            var items = document.querySelectorAll('[class*="comment"], [class*="Comment"]');
            for (var i = 0; i < Math.min(items.length, {limit}); i++) {{
                var text = items[i].innerText;
                if (text.length > 5) {{
                    comments.push(text.substring(0, 200));
                }}
            }}
            return JSON.stringify(comments);
        }})()
        """)

    def reply_comment(self, text: str, comment_index: int = 0) -> dict:
        """回复评论"""
        js = f"""
        (function() {{
            var replyBtns = document.querySelectorAll('[class*="reply"], [class*="Reply"]');
            if (replyBtns.length > {comment_index}) {{
                replyBtns[{comment_index}].click();
                return 'REPLY_CLICKED';
            }}
            return 'NO_REPLY_BTN';
        }})()
        """
        self._eval(js)
        time.sleep(1)

        # 输入回复内容
        js_type = f"""
        (function() {{
            var textarea = document.querySelector('textarea, [contenteditable="true"]');
            if (textarea) {{
                textarea.focus();
                if (textarea.tagName === 'TEXTAREA') {{
                    textarea.value = '{text}';
                }} else {{
                    textarea.innerText = '{text}';
                }}
                textarea.dispatchEvent(new Event('input', {{bubbles: true}}));
                return 'REPLY_TYPED';
            }}
            return 'NO_INPUT';
        }})()
        """
        return self._eval(js_type)

    # ========== 数据监控 ==========

    def get_analytics(self) -> dict:
        """获取数据分析"""
        self.chrome.navigate(self.ANALYTICS_PAGE, self.tab_index)
        time.sleep(3)

        return self._eval_value("""
        (function() {
            var text = document.body.innerText;
            var result = {};

            var viewMatch = text.match(/播放量[\\s\\n]*(\\d+)/);
            var likeMatch = text.match(/点赞[\\s\\n]*(\\d+)/);
            var commentMatch = text.match(/评论[\\s\\n]*(\\d+)/);
            var shareMatch = text.match(/分享[\\s\\n]*(\\d+)/);

            if (viewMatch) result.views = parseInt(viewMatch[1]);
            if (likeMatch) result.likes = parseInt(likeMatch[1]);
            if (commentMatch) result.comments = parseInt(commentMatch[1]);
            if (shareMatch) result.shares = parseInt(shareMatch[1]);

            return JSON.stringify(result);
        })()
        """)
