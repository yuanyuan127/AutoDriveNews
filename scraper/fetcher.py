"""
文章抓取模块 — 从 RSS / 网页获取自动驾驶相关文章
"""

import hashlib
import re
import sys
import time
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

import feedparser
import requests
from bs4 import BeautifulSoup

from sources import SOURCES, SEARCH_KEYWORDS

# 使用常见的浏览器 UA，避免被反爬
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# 北京时间
TZ_BEIJING = timezone(timedelta(hours=8))


def is_relevant(text: str) -> bool:
    """判断文章是否与自动驾驶相关"""
    if not text:
        return False
    text_lower = text.lower()
    for kw in SEARCH_KEYWORDS:
        if kw.lower() in text_lower:
            return True
    return False


def clean_html(html_text: str) -> str:
    """去除 HTML 标签"""
    return re.sub(r"<[^>]+>", "", html_text or "").strip()


def http_get(url: str, timeout: int = 20) -> requests.Response:
    """带重试的 HTTP GET 请求"""
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.exceptions.Timeout:
            if attempt < 2:
                time.sleep(2)
                continue
            raise
        except requests.exceptions.ConnectionError:
            if attempt < 2:
                time.sleep(3)
                continue
            raise
    raise Exception(f"无法访问 {url}")


def fetch_rss(source: dict, seen_urls: set) -> list:
    """从 RSS 抓取文章"""
    articles = []
    rss_url = source.get("rss", "")
    if not rss_url:
        return articles

    try:
        # 先尝试直接请求 RSS 内容
        resp = requests.get(rss_url, headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            print(f"  ⚠ HTTP {resp.status_code}", end="")
            return articles

        feed = feedparser.parse(resp.content)
        if not feed.entries:
            if feed.bozo:
                print(f"  ⚠ 解析异常: {str(feed.bozo_exception)[:60]}", end="")
            else:
                print(f"  ⚠ 无条目", end="")
            return articles

        count = 0
        for entry in feed.entries:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            summary = clean_html(entry.get("summary", "") or entry.get("description", ""))

            if not title or not link:
                continue
            if link in seen_urls:
                continue
            if not is_relevant(f"{title} {summary}"):
                continue

            # 解析发布时间
            published = entry.get("published_parsed") or entry.get("updated_parsed")
            if published:
                pub_dt = datetime(*published[:6], tzinfo=timezone.utc)
            else:
                pub_dt = datetime.now(timezone.utc)

            articles.append({
                "title": title[:200],
                "url": link,
                "source_name": source["name"],
                "source_key": source["key"],
                "summary_raw": summary[:500] if summary else "",
                "publish_ts": int(pub_dt.timestamp()),
                "publish_date": pub_dt.astimezone(TZ_BEIJING).strftime("%Y-%m-%d"),
                "fetched_from": "rss",
            })
            seen_urls.add(link)
            count += 1

        return articles

    except requests.exceptions.Timeout:
        print(f"  ⚠ 超时", end="")
    except requests.exceptions.ConnectionError:
        print(f"  ⚠ 连接失败(可能被墙)", end="")
    except Exception as e:
        print(f"  ✗ {str(e)[:50]}", end="")

    return articles


def fetch_all(target_date: str = None) -> list:
    """
    从所有来源抓取文章
    target_date: YYYYMMDD 格式，默认抓取昨天
    """
    if target_date is None:
        yesterday = datetime.now(TZ_BEIJING) - timedelta(days=1)
        target_date = yesterday.strftime("%Y%m%d")

    print(f"\n{'='*60}")
    print(f"🚗 AutoDrive 资讯抓取 · 目标日期: {target_date}")
    print(f"{'='*60}\n")

    all_articles = []
    seen_urls = set()
    success_count = 0

    for source in SOURCES:
        print(f"📡 {source['name']:6s} ", end="")
        articles = fetch_rss(source, seen_urls)
        print(f"→ {len(articles)} 篇")
        all_articles.extend(articles)
        if articles:
            success_count += 1

    # 只保留目标日期的文章
    date_articles = [a for a in all_articles if a["publish_date"] == target_date]

    # 如果严格按日期筛选结果太少，放宽到最近 2 天
    if len(date_articles) < 5:
        yesterday = datetime.now(TZ_BEIJING) - timedelta(days=1)
        yday_str = yesterday.strftime("%Y-%m-%d")
        day_before = (yesterday - timedelta(days=1)).strftime("%Y-%m-%d")
        date_articles = [a for a in all_articles
                         if a["publish_date"] in (yday_str, day_before)]

    print(f"\n📊 总计: {len(all_articles)} 篇 | {success_count}/{len(SOURCES)} 源成功 | "
          f"最终 {len(date_articles)} 篇")
    return date_articles


if __name__ == "__main__":
    articles = fetch_all()
    for a in articles[:10]:
        print(f"  [{a['source_name']}] {a['title'][:80]}")
