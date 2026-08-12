"""
文章抓取模块 — 从 RSS / 网页获取自动驾驶相关文章
"""

import hashlib
import re
import sys
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

import feedparser
import requests
from bs4 import BeautifulSoup

from sources import SOURCES, SEARCH_KEYWORDS

HEADERS = {
    "User-Agent": "AutoDrive/1.0 (News Aggregator; +https://github.com/william-1225/autodrive)"
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


def extract_domain(url: str) -> str:
    """提取域名"""
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""


def fetch_rss(source: dict, seen_urls: set) -> list:
    """从 RSS 抓取文章"""
    articles = []
    rss_url = source.get("rss", "")
    if not rss_url:
        return articles

    try:
        feed = feedparser.parse(rss_url)
        if feed.bozo and not feed.entries:
            print(f"  ⚠ {source['name']} RSS 解析失败: {feed.bozo_exception}")
            return articles

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            summary = clean_html(entry.get("summary", "") or entry.get("description", ""))
            published = entry.get("published_parsed") or entry.get("updated_parsed")

            if not title or not link:
                continue
            if link in seen_urls:
                continue
            if not is_relevant(f"{title} {summary}"):
                continue

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

    except Exception as e:
        print(f"  ✗ {source['name']} RSS 抓取异常: {e}")

    return articles


def fetch_html(source: dict, seen_urls: set) -> list:
    """从网页列表抓取文章（RSS 不可用时的降级方案）"""
    articles = []
    list_url = source.get("list_url", "")
    if not list_url:
        return articles

    try:
        resp = requests.get(list_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "html.parser")

        # 通用链接提取策略
        for a_tag in soup.find_all("a", href=True):
            title = a_tag.get_text(strip=True)
            link = a_tag["href"]
            if not title or not link:
                continue
            if len(title) < 10 or len(title) > 200:
                continue
            if link in seen_urls:
                continue
            if not is_relevant(title):
                continue

            # 补全相对 URL
            if link.startswith("//"):
                link = "https:" + link
            elif link.startswith("/"):
                domain = urlparse(list_url).netloc
                link = f"https://{domain}{link}"

            articles.append({
                "title": title[:200],
                "url": link,
                "source_name": source["name"],
                "source_key": source["key"],
                "summary_raw": "",
                "publish_ts": int(datetime.now(timezone.utc).timestamp()),
                "publish_date": datetime.now(TZ_BEIJING).strftime("%Y-%m-%d"),
                "fetched_from": "html",
            })
            seen_urls.add(link)

    except Exception as e:
        print(f"  ✗ {source['name']} 网页抓取异常: {e}")

    return articles


def fetch_all(target_date: str = None) -> list:
    """
    从所有来源抓取文章
    target_date: YYYYMMDD 格式，默认抓取昨天
    返回文章列表
    """
    if target_date is None:
        yesterday = datetime.now(TZ_BEIJING) - timedelta(days=1)
        target_date = yesterday.strftime("%Y%m%d")

    print(f"\n{'='*60}")
    print(f"🚗 AutoDrive 资讯抓取 · 目标日期: {target_date}")
    print(f"{'='*60}\n")

    all_articles = []
    seen_urls = set()

    for source in SOURCES:
        print(f"📡 {source['name']} ({source['type']}) ", end="")
        if source["type"] == "rss" and source.get("rss"):
            articles = fetch_rss(source, seen_urls)
        else:
            articles = fetch_html(source, seen_urls)

        print(f"→ {len(articles)} 篇相关")
        all_articles.extend(articles)

    # 只保留目标日期的文章
    date_articles = [a for a in all_articles if a["publish_date"] == target_date]

    # 去重（按 URL）
    print(f"\n📊 总计: 抓取 {len(all_articles)} 篇 → 目标日期 {target_date} 共 {len(date_articles)} 篇")

    return date_articles


if __name__ == "__main__":
    articles = fetch_all()
    for a in articles[:10]:
        print(f"  [{a['source_name']}] {a['title'][:80]}")
