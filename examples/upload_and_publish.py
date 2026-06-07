"""
示例：上传视频并发布
"""

from douyin import DouyinAutomation

# 初始化
dy = DouyinAutomation()

# 上传视频
result = dy.upload_video(
    video_path="/Users/sy/Videos/my_video.mp4",
    title="0代码用AI自动化，10分钟搭一个24小时数字员工 #AI自动化 #效率提升",
    topics=["AI自动化", "效率提升", "AI工具"]
)
print(f"上传结果: {result}")

# 发布
if result.get("success"):
    publish_result = dy.publish()
    print(f"发布结果: {publish_result}")
