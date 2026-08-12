"""
数据源配置 — 每个来源的 RSS 地址 / 抓取策略
"""

SOURCES = [
    {
        "name": "36氪",
        "key": "36kr",
        # 36kr 有公开 RSS
        "rss": "https://36kr.com/feed",
        "type": "rss",
    },
    {
        "name": "机器之心",
        "key": "jiqizhixin",
        "rss": "https://www.jiqizhixin.com/rss",
        "type": "rss",
    },
    {
        "name": "钛媒体",
        "key": "tmtpost",
        "rss": "https://www.tmtpost.com/rss.xml",
        "type": "rss",
    },
    {
        "name": "亿欧",
        "key": "iyiou",
        "rss": "https://www.iyiou.com/rss",
        "type": "rss",
    },
    {
        "name": "澎湃新闻",
        "key": "thepaper",
        "rss": "https://www.thepaper.cn/rss_www.xml",
        "type": "rss",
    },
    {
        "name": "新浪科技",
        "key": "sina",
        # 新浪科技 RSS
        "rss": "https://tech.sina.com.cn/rss/auto.xml",
        "type": "rss",
    },
    {
        "name": "搜狐汽车",
        "key": "sohu_auto",
        "rss": "https://auto.sohu.com/rss",
        "type": "rss",
    },
    {
        "name": "雷科技",
        "key": "leikeji",
        "rss": "",
        "type": "html",
    },
    {
        "name": "今日头条",
        "key": "toutiao",
        "rss": "",
        "type": "html",
    },
]

# 搜索关键词（用于过滤相关文章）
SEARCH_KEYWORDS = [
    "自动驾驶", "无人驾驶", "智能驾驶", "智驾",
    "Robotaxi", "Robovan",
    "VLA", "VLM", "端到端", "世界模型", "大模型",
    "激光雷达", "毫米波雷达", "域控制器", "智驾芯片",
    "英伟达", "NVIDIA", "高通", "Mobileye", "地平线",
    "FSD", "NOA", "NOP", "NGP", "ADS",
    "特斯拉", "华为智驾", "小鹏智驾", "蔚来智驾",
    "百度Apollo", "Waymo", "Cruise",
    "征程", "黑芝麻", "速腾聚创", "禾赛",
    "Orin", "Thor",
]
