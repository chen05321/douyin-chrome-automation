"""
示例：自动回复评论
"""

import time
from douyin import DouyinAutomation

dy = DouyinAutomation()

# 获取最新评论
comments = dy.get_comments(limit=20)
print(f"最新评论 ({len(comments)} 条):")
for i, c in enumerate(comments):
    print(f"  [{i}] {c[:100]}")

# 自动回复每一条评论
reply_text = "感谢支持！想要自动化配置图的可以私信我 😊"
for i in range(len(comments)):
    print(f"回复第 {i} 条评论...")
    dy.reply_comment(text=reply_text, comment_index=i)
    time.sleep(30)  # 间隔30秒，避免风控

print("回复完成！")
