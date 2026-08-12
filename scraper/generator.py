"""
数据生成模块 — 将处理后的文章写入 JSON 文件
"""

import json
import os
from collections import Counter
from datetime import datetime, timezone, timedelta

TZ_BEIJING = timezone(timedelta(hours=8))

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "news")


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def build_source_counts(articles: list) -> dict:
    """统计每个来源的文章数"""
    counter = Counter(a["source_name"] for a in articles)
    return dict(counter.most_common())


def generate_feed(articles: list, date_str: str):
    """生成每日 feed JSON"""
    ensure_data_dir()

    feed = {
        "source_counts": build_source_counts(articles),
        "brand_counts": {},
        "items": articles,
    }

    filepath = os.path.join(DATA_DIR, f"feed_{date_str}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(feed, f, ensure_ascii=False, indent=2)

    print(f"✅ 已生成: {filepath} ({len(articles)} 条)")
    return filepath


def generate_weekly(featured_articles: list, week_str: str):
    """生成每周精选 JSON"""
    ensure_data_dir()

    data = {
        "selected_count": len(featured_articles),
        "items": featured_articles,
    }

    filepath = os.path.join(DATA_DIR, f"weekly_{week_str}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ 已生成: {filepath}")
    return filepath


def generate_insight(topics: list, week_str: str):
    """生成每周洞察 JSON"""
    ensure_data_dir()

    data = {"topics": topics}

    filepath = os.path.join(DATA_DIR, f"insight_{week_str}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ 已生成: {filepath}")
    return filepath


def update_index(date_str: str, week_str: str):
    """更新 index.json — 添加新日期、更新 latest"""
    ensure_data_dir()

    index_path = os.path.join(DATA_DIR, "index.json")

    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
    else:
        index = {"latest": date_str, "latest_week": week_str, "dates": []}

    # 更新最新日期
    index["latest"] = date_str
    index["latest_week"] = week_str

    # 添加新日期到列表（去重排序）
    dates_set = set(index.get("dates", []))
    dates_set.add(date_str)
    index["dates"] = sorted(dates_set, reverse=True)

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"✅ 已更新索引: {index_path} (latest={date_str}, {len(index['dates'])} 个日期)")
    return index_path


def get_week_str(date_str: str) -> str:
    """根据日期 YYYYMMDD 计算 ISO 周 (如 2026W33)"""
    year = int(date_str[:4])
    month = int(date_str[4:6])
    day = int(date_str[6:8])
    dt = datetime(year, month, day)
    iso = dt.isocalendar()
    return f"{iso[0]}W{iso[1]:02d}"
