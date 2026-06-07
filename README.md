# 🎬 Douyin Chrome Automation

通过 AppleScript + JavaScript 控制已登录的 Chrome 浏览器，自动化操作抖音创作者平台。**无需 Selenium、Playwright 或 Remote Debugging Port。**

[English](#english) | 中文

## ✨ 特性

- ✅ **零依赖** — 只需 macOS + Python3 + Chrome，不需要 pip install 任何包
- ✅ **复用登录态** — 直接控制你已登录的 Chrome，无需处理 Cookie/验证码
- ✅ **视频上传** — Base64 编码注入 `input[type=file]`，绕过浏览器安全限制
- ✅ **内容发布** — 自动填写标题、话题标签、点击发布
- ✅ **评论管理** — 读取评论、自动回复
- ✅ **数据监控** — 抓取播放量、点赞、粉丝数等数据
- ✅ **私信回复** — 自动读取和回复私信

## 🚀 快速开始

### 环境要求

- macOS（已在 macOS 26.4.1 + M4 上测试）
- Python 3.10+
- Google Chrome（已登录抖音）
- Chrome 启用 AppleScript：`Chrome → View → Developer → Allow JavaScript from Apple Events`

### 安装

```bash
git clone https://github.com/YOUR_USERNAME/douyin-chrome-automation.git
cd douyin-chrome-automation
# 无需安装依赖，零依赖项目
```

### 使用

```python
from douyin import DouyinAutomation

# 初始化（自动连接已打开的 Chrome）
dy = DouyinAutomation()

# 1. 上传视频
dy.upload_video("/path/to/video.mp4", title="AI自动化演示", topics=["AI", "自动化"])

# 2. 发布（填写完信息后点击发布）
dy.publish()

# 3. 获取账号数据
stats = dy.get_stats()
print(stats)  # {'followers': 93, 'likes': 143, 'views': 51, ...}

# 4. 读取最新评论
comments = dy.get_comments(limit=10)

# 5. 回复评论
dy.reply_comment(comment_id="xxx", text="感谢支持！")

# 6. 获取私信列表
messages = dy.get_messages()
```

### 命令行使用

```bash
# 上传视频
python3 -m douyin upload /path/to/video.mp4 --title "AI自动化" --topics "AI,效率"

# 查看数据
python3 -m douyin stats

# 读取评论
python3 -m douyin comments --limit 10

# 回复评论
python3 -m douyin reply --comment-id xxx --text "感谢支持"
```

## 🔧 技术原理

### 为什么不用 Selenium/Playwright？

| 方案 | 需要重启Chrome | 需要调试端口 | 需要装包 | 保持登录态 |
|------|:-:|:-:|:-:|:-:|
| Selenium | ❌ | ✅ | ✅ | ⚠️ 不稳定 |
| Playwright | ❌ | ✅ | ✅ | ⚠️ 不稳定 |
| Remote Debugging | ✅ 必须关闭重开 | ✅ | ❌ | ❌ Cookie丢失 |
| **本项目** | **❌** | **❌** | **❌** | **✅** |

### 核心方案：AppleScript → Chrome JS → DOM 操作

```
Python → osascript → Google Chrome → execute javascript → DOM
```

### 视频上传原理

浏览器安全限制：`input[type=file]` 不能通过 JS 直接赋值本地路径。

解决方案：
1. Python 读取视频文件 → Base64 编码
2. AppleScript 执行 Chrome JS
3. JS 中 `atob()` 解码 → `Uint8Array` → `File` 对象
4. `DataTransfer` 注入到 `input.files`
5. 触发 `change` 事件，抖音框架感知到文件变化

```javascript
// 核心注入代码
var bin = atob(base64Data);
var arr = new Uint8Array(bin.length);
for (var i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
var file = new File([arr], "video.mp4", {type: "video/mp4"});
var dt = new DataTransfer();
dt.items.add(file);
input.files = dt.files;
input.dispatchEvent(new Event('change', {bubbles: true}));
```

### 文件大小限制

| 文件大小 | 方式 | 说明 |
|---------|------|------|
| < 5MB | JS 直接注入 | Base64 通过 `chrome_as.py eval` 注入 |
| 5MB - 50MB | AppleScript 注入 | Base64 通过 `osascript` 直接执行 |
| > 50MB | 分块注入 | 将文件分块 base64 编码后拼接注入 |

## 📁 项目结构

```
douyin-chrome-automation/
├── README.md
├── LICENSE
├── douyin/
│   ├── __init__.py
│   ├── core.py          # 核心自动化类
│   ├── chrome.py        # Chrome AppleScript 控制器
│   ├── upload.py        # 视频上传模块
│   ├── publish.py       # 发布模块（标题/话题/封面）
│   ├── comments.py      # 评论管理模块
│   ├── messages.py      # 私信模块
│   ├── analytics.py     # 数据监控模块
│   └── cli.py           # 命令行入口
├── examples/
│   ├── upload_and_publish.py
│   ├── auto_reply.py
│   └── daily_stats.py
└── tests/
    └── test_chrome.py
```

## ⚠️ 注意事项

1. **请合理使用** — 频繁操作可能触发抖音风控，建议每次操作间隔 30 秒以上
2. **仅供学习** — 请遵守抖音平台规则，不要用于恶意刷量等行为
3. **Cookie 有效期** — Chrome 中的抖音登录态可能过期，需要重新登录
4. **Chrome 前台** — AppleScript 控制 Chrome 时，Chrome 需要在前台运行

## 🤝 Contributing

欢迎 PR！请确保：
- 代码有中文注释
- 新功能附带使用示例
- 不引入外部依赖（保持零依赖特性）

## 📄 License

MIT License

---

## English

Automate Douyin (TikTok China) Creator Platform via AppleScript + Chrome JavaScript injection. Zero dependencies, zero Selenium, zero Playwright. Just macOS + Python3 + Chrome.

### Key Features

- Upload videos via Base64 → DataTransfer injection
- Auto-fill titles, hashtags, and publish
- Read and reply to comments
- Monitor analytics (views, likes, followers)
- Send/receive DMs

### Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/douyin-chrome-automation.git
cd douyin-chrome-automation
python3 -m douyin upload video.mp4 --title "My Video" --topics "AI,automation"
```

See [中文文档](#-快速开始) for full documentation.
