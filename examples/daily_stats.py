"""
示例：每日数据监控
"""

import json
from datetime import datetime
from douyin import DouyinAutomation

dy = DouyinAutomation()

# 获取账号数据
stats = dy.get_stats()
print(f"账号数据: {json.dumps(stats, ensure_ascii=False, indent=2)}")

# 获取详细分析
analytics = dy.get_analytics()
print(f"数据总览: {json.dumps(analytics, ensure_ascii=False, indent=2)}")

# 保存到文件
today = datetime.now().strftime("%Y-%m-%d")
log_entry = {
    "date": today,
    "stats": stats,
    "analytics": analytics
}

with open(f"stats_{today}.json", "w") as f:
    json.dump(log_entry, f, ensure_ascii=False, indent=2)

print(f"数据已保存到 stats_{today}.json")
