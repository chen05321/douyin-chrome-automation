#!/usr/bin/env python3
"""
抖音自动化 CLI 命令行工具

用法：
    python3 -m douyin upload /path/to/video.mp4 --title "标题" --topics "AI,自动化"
    python3 -m douyin stats
    python3 -m douyin comments --limit 10
    python3 -m douyin analytics
"""

import argparse
import json
import sys

from .core import DouyinAutomation


def cmd_upload(args):
    """上传视频"""
    dy = DouyinAutomation()
    topics = args.topics.split(",") if args.topics else None
    result = dy.upload_video(args.video, title=args.title or "", topics=topics)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_stats(args):
    """获取账号数据"""
    dy = DouyinAutomation()
    result = dy.get_stats()
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_comments(args):
    """获取评论"""
    dy = DouyinAutomation()
    result = dy.get_comments(limit=args.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_analytics(args):
    """获取数据分析"""
    dy = DouyinAutomation()
    result = dy.get_analytics()
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_publish(args):
    """点击发布"""
    dy = DouyinAutomation()
    result = dy.publish()
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="抖音创作者平台自动化工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python3 -m douyin upload video.mp4 --title "AI自动化演示" --topics "AI,效率"
  python3 -m douyin stats
  python3 -m douyin comments --limit 20
  python3 -m douyin analytics
  python3 -m douyin publish
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # upload
    p_upload = subparsers.add_parser("upload", help="上传视频")
    p_upload.add_argument("video", help="视频文件路径")
    p_upload.add_argument("--title", "-t", help="视频标题/描述")
    p_upload.add_argument("--topics", help="话题标签，逗号分隔")
    p_upload.set_defaults(func=cmd_upload)

    # stats
    p_stats = subparsers.add_parser("stats", help="获取账号数据")
    p_stats.set_defaults(func=cmd_stats)

    # comments
    p_comments = subparsers.add_parser("comments", help="获取评论")
    p_comments.add_argument("--limit", "-l", type=int, default=10, help="获取数量")
    p_comments.set_defaults(func=cmd_comments)

    # analytics
    p_analytics = subparsers.add_parser("analytics", help="获取数据分析")
    p_analytics.set_defaults(func=cmd_analytics)

    # publish
    p_publish = subparsers.add_parser("publish", help="点击发布")
    p_publish.set_defaults(func=cmd_publish)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
