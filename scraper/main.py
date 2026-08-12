#!/usr/bin/env python3
"""
AutoDrive 智驾资讯 · 每日自动抓取管线

用法:
  python scraper/main.py                        # 抓取昨天资讯
  python scraper/main.py --date 20260811        # 抓取指定日期
  python scraper/main.py --no-ai                # 仅抓取，跳过 AI 处理（用于测试）
  python scraper/main.py --weekly-only          # 仅生成周精选和洞察

环境变量:
  ANTHROPIC_API_KEY   Claude API 密钥（AI 处理必需）
"""

import argparse
import os
import sys
from datetime import datetime, timezone, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from fetcher import fetch_all
from processor import process_articles, generate_insight
from generator import (
    generate_feed,
    generate_weekly,
    generate_insight as write_insight,
    update_index,
    get_week_str,
)

TZ_BEIJING = timezone(timedelta(hours=8))


def main():
    parser = argparse.ArgumentParser(description="AutoDrive 智驾资讯抓取管线")
    parser.add_argument("--date", type=str, default=None, help="目标日期 YYYYMMDD（默认昨天）")
    parser.add_argument("--no-ai", action="store_true", help="跳过 AI 处理")
    parser.add_argument("--weekly-only", action="store_true", help="仅生成周精选")
    args = parser.parse_args()

    # 确定目标日期
    if args.date:
        date_str = args.date
    else:
        yesterday = datetime.now(TZ_BEIJING) - timedelta(days=1)
        date_str = yesterday.strftime("%Y%m%d")

    week_str = get_week_str(date_str)

    if args.weekly_only:
        print("📋 仅生成周精选模式")
        # 读取当日 feed 中的精选文章
        import json
        feed_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "news", f"feed_{date_str}.json"
        )
        if os.path.exists(feed_path):
            with open(feed_path, "r") as f:
                feed = json.load(f)
            featured = [it for it in feed["items"] if it.get("is_featured")]
            generate_weekly(featured, week_str)
            topics = generate_insight(featured)
            if topics:
                write_insight(topics, week_str)
            update_index(date_str, week_str)
        else:
            print(f"❌ Feed 文件不存在: {feed_path}")
        return

    # === 第一步：抓取 ===
    print("\n" + "=" * 60)
    print("📡 第一步：多源抓取")
    print("=" * 60)
    raw_articles = fetch_all(date_str)

    if not raw_articles:
        print("\n⚠ 未抓取到任何文章，生成空 feed")
        generate_feed([], date_str)
        update_index(date_str, week_str)
        return

    # === 第二步：AI 处理 ===
    if args.no_ai:
        print("\n⏩ 跳过 AI 处理（--no-ai），使用规则分类")
        for a in raw_articles:
            a["category"] = "技术"
            a["importance"] = 60
            a["summary"] = a.get("summary_raw", "")
            a["is_featured"] = False
            a["companies"] = []
            a["takeaway"] = ""
            a["has_time"] = True
        processed = raw_articles
    else:
        print("\n" + "=" * 60)
        print("🤖 第二步：AI 分类 & 打分")
        print("=" * 60)
        processed = process_articles(raw_articles)

    # 按重要性排序
    processed.sort(key=lambda x: x.get("importance", 0), reverse=True)

    # === 第三步：生成数据文件 ===
    print("\n" + "=" * 60)
    print("📁 第三步：生成数据文件")
    print("=" * 60)
    generate_feed(processed, date_str)

    # 提取精选文章
    featured = [it for it in processed if it.get("is_featured")]

    # 周精选 & 洞察
    print(f"\n📊 精选文章: {len(featured)} 篇")
    if featured:
        generate_weekly(featured, week_str)

        # 生成洞察（如果有多篇精选）
        if len(featured) >= 3 and not args.no_ai:
            print("\n💡 生成洞察分析...")
            topics = generate_insight(featured)
            if topics:
                write_insight(topics, week_str)

    # 更新索引
    update_index(date_str, week_str)

    # === 统计报告 ===
    print("\n" + "=" * 60)
    print("📊 执行报告")
    print("=" * 60)
    cats = {}
    for a in processed:
        cats[a["category"]] = cats.get(a["category"], 0) + 1
    print(f"  抓取总数: {len(raw_articles)}")
    print(f"  AI 处理: {len(processed)}")
    print(f"  精选: {len(featured)}")
    print(f"  分类分布: {cats}")
    print(f"  日期: {date_str}")
    print(f"  周: {week_str}")
    print("=" * 60)
    print("🎉 完成！")


if __name__ == "__main__":
    main()
