"""
数据源配置 — 每个来源的 RSS 地址 / 抓取策略
字段说明：
  name: 显示名称
  rss: RSS 订阅地址（优先使用）
  list_url: 文章列表页（RSS 不可用时的降级方案）
  type: rss | html
  encoding: 网页编码（默认 utf-8）
"""

SOURCES = [
    {
        "name": "36氪",
        "key": "36kr",
        "rss": "https://36kr.com/feed",
        "list_url": "https://36kr.com/search/articles/%E8%87%AA%E5%8A%A8%E9%A9%BE%E9%A9%B6",
        "type": "rss",
    },
    {
        "name": "澎湃新闻",
        "key": "thepaper",
        "rss": "https://www.thepaper.cn/rss_www.xml",
        "list_url": "https://www.thepaper.cn/search?q=自动驾驶",
        "type": "rss",
    },
    {
        "name": "机器之心",
        "key": "jiqizhixin",
        "rss": "https://www.jiqizhixin.com/rss",
        "list_url": "https://www.jiqizhixin.com/search?q=自动驾驶",
        "type": "rss",
    },
    {
        "name": "钛媒体",
        "key": "tmtpost",
        "rss": "https://www.tmtpost.com/rss.xml",
        "list_url": "https://www.tmtpost.com/search?q=自动驾驶",
        "type": "rss",
    },
    {
        "name": "亿欧",
        "key": "iyiou",
        "rss": "https://www.iyiou.com/rss",
        "list_url": "https://www.iyiou.com/search?keyword=自动驾驶",
        "type": "rss",
    },
    {
        "name": "雷科技",
        "key": "leikeji",
        "rss": "",
        "list_url": "https://www.leikeji.com/search?q=自动驾驶",
        "type": "html",
    },
    {
        "name": "新浪",
        "key": "sina",
        "rss": "https://tech.sina.com.cn/rss/auto.xml",
        "list_url": "https://search.sina.com.cn/?q=自动驾驶",
        "type": "rss",
    },
    {
        "name": "搜狐汽车",
        "key": "sohu_auto",
        "rss": "https://auto.sohu.com/rss",
        "list_url": "https://auto.sohu.com/search?keyword=自动驾驶",
        "type": "rss",
    },
    {
        "name": "今日头条",
        "key": "toutiao",
        "rss": "",
        "list_url": "https://so.toutiao.com/search?keyword=自动驾驶",
        "type": "html",
    },
]

# 搜索关键词（用于过滤和搜索）
SEARCH_KEYWORDS = [
    "自动驾驶", "无人驾驶", "智能驾驶", "智驾",
    "Robotaxi", "Robovan",
    "VLA", "VLM", "端到端", "世界模型", "大模型",
    "激光雷达", "毫米波雷达", "域控制器", "智驾芯片",
    "英伟达", "NVIDIA", "高通", "Mobileye", "地平线",
    "FSD", "NOA", "NOP", "NGP", "ADS",
    "特斯拉", "华为智驾", "小鹏智驾", "蔚来智驾",
    "百度Apollo", "Waymo", "Cruise",
]
