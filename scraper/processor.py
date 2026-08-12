"""
AI 处理模块 — 用 Claude API 对文章进行分类、打分、摘要、提取洞察
需要环境变量: ANTHROPIC_API_KEY
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta

try:
    from anthropic import Anthropic
except ImportError:
    print("请先安装 anthropic SDK: pip install anthropic")
    sys.exit(1)

TZ_BEIJING = timezone(timedelta(hours=8))

CATEGORIES = ["政策", "市场", "RoboX", "技术", "硬件"]

SYSTEM_PROMPT = """你是一个自动驾驶行业资讯分析专家。你的任务是对输入的新闻文章列表进行分析处理。

对每篇文章，请返回以下字段：
1. category: 五分类之一（政策/市场/RoboX/技术/硬件）
   - 政策：法规、标准、政府准入、数据合规
   - 市场：融资、财报、市场份额、商业合作、人事变动
   - RoboX：Robotaxi/Robovan/无人配送等自动驾驶商业运营
   - 技术：端到端模型、VLA/VLM、感知算法、规划控制、仿真、世界模型
   - 硬件：芯片（英伟达/高通/地平线等）、激光雷达、域控制器、传感器
2. importance: 重要性评分 1-100（综合考量：行业影响力、技术突破性、企业体量）
   - 90+: 行业里程碑事件
   - 80-89: 重大进展
   - 70-79: 值得关注
   - 60-69: 一般动态
   - <60: 边缘信息
3. summary: 50-150字中文摘要，提炼核心信息
4. is_featured: 是否值得选入"每日精选"（当日最重要的 8-12 条）
5. companies: 文章中涉及的公司/机构名称列表
6. takeaway: 仅对 is_featured=true 的文章，写一句 30-60 字的行业洞察/投资启示

请严格按 JSON 数组格式返回，示例：
[{"title":"...","category":"技术","importance":92,"summary":"...","is_featured":true,"companies":["特斯拉"],"takeaway":"..."}]
"""


def chunk_articles(articles: list, batch_size: int = 10) -> list:
    """将文章分批，每批最多 batch_size 篇"""
    for i in range(0, len(articles), batch_size):
        yield articles[i : i + batch_size]


def build_batch_input(articles: list, batch_idx: int, total_batches: int) -> str:
    """构建一批文章的输入文本"""
    lines = [f"批次 {batch_idx + 1}/{total_batches} — 请处理以下 {len(articles)} 篇文章：\n"]
    for i, a in enumerate(articles, 1):
        lines.append(f"#{i}")
        lines.append(f"标题: {a['title']}")
        lines.append(f"来源: {a['source_name']}")
        lines.append(f"原摘要: {a.get('summary_raw', '无')}")
        lines.append("")
    return "\n".join(lines)


def process_articles(articles: list) -> list:
    """
    用 Claude API 处理文章：分类、打分、摘要
    返回增强后的文章列表
    """
    if not articles:
        print("⚠ 没有文章需要处理")
        return []

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("❌ 未设置 ANTHROPIC_API_KEY 环境变量")
        print("   export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    client = Anthropic(api_key=api_key)
    batches = list(chunk_articles(articles))
    processed = []

    print(f"\n🤖 开始 AI 处理: {len(articles)} 篇文章, 分 {len(batches)} 批")
    print(f"{'='*60}")

    for idx, batch in enumerate(batches):
        print(f"\n📝 批次 {idx + 1}/{len(batches)}: {len(batch)} 篇")
        user_input = build_batch_input(batch, idx, len(batches))

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_input}],
                temperature=0.3,
            )

            # 解析 AI 返回的 JSON
            result_text = response.content[0].text
            # 尝试提取 JSON 块
            json_match = result_text.strip()
            if json_match.startswith("```"):
                json_match = json_match.split("\n", 1)[1].rsplit("\n```", 1)[0]
            if "[" in json_match and "]" in json_match:
                json_match = json_match[json_match.find("[") : json_match.rfind("]") + 1]

            ai_results = json.loads(json_match)

            # 合并回原始数据
            for i, result in enumerate(ai_results):
                if i < len(batch):
                    # 保留原始抓取字段
                    merged = {**batch[i]}
                    # 覆盖/添加 AI 分析字段
                    merged["category"] = result.get("category", "技术")
                    if merged["category"] not in CATEGORIES:
                        # 默认归为技术类
                        merged["category"] = "技术"
                    merged["importance"] = int(result.get("importance", 70))
                    merged["summary"] = result.get("summary", merged.get("summary_raw", ""))
                    merged["is_featured"] = bool(result.get("is_featured", False))
                    merged["companies"] = result.get("companies", [])
                    merged["takeaway"] = result.get("takeaway", "")
                    merged["has_time"] = True
                    processed.append(merged)
                    print(f"  ✅ [{merged['category']}] 重要性:{merged['importance']} | {merged['title'][:50]}")

        except json.JSONDecodeError as e:
            print(f"  ❌ JSON 解析失败: {e}")
            # 降级：使用规则分类
            for a in batch:
                a["category"] = "技术"
                a["importance"] = 60
                a["summary"] = a.get("summary_raw", "")
                a["is_featured"] = False
                a["companies"] = []
                a["takeaway"] = ""
                a["has_time"] = True
                processed.append(a)
            print(f"  ⚠ 批次 {idx+1} 降级为规则分类")

        except Exception as e:
            print(f"  ❌ API 调用失败: {e}")
            for a in batch:
                a["category"] = "技术"
                a["importance"] = 60
                a["summary"] = a.get("summary_raw", "")
                a["is_featured"] = False
                a["companies"] = []
                a["takeaway"] = ""
                a["has_time"] = True
                processed.append(a)

    return processed


def generate_insight(featured_articles: list) -> list:
    """
    基于精选文章生成每周洞察专题
    返回 topics 列表
    """
    if not featured_articles:
        return []

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return []

    client = Anthropic(api_key=api_key)

    articles_text = "\n\n".join(
        f"#{i} [{a['category']}] {a['title']}\n{a['summary']}\n公司: {', '.join(a.get('companies', []))}"
        for i, a in enumerate(featured_articles[:15], 1)
    )

    prompt = f"""基于本周自动驾驶行业精选文章，生成 2-4 个深度洞察专题。

以下是本周精选文章：
{articles_text}

请返回 JSON 数组格式：
[{{"title":"专题标题","summary":"200-400字专题分析，综合多篇文章信息","why_it_matters":"100-200字，说明为什么这个趋势重要"}}]

围绕以下方向组织专题：
- 技术范式转移（VLA/端到端/世界模型）
- 商业化进展（Robotaxi 规模化运营）
- 硬件军备竞赛（芯片/传感器）
- 政策与监管突破
- 市场格局变化"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )

        result_text = response.content[0].text
        if "```" in result_text:
            result_text = result_text.split("\n", 1)[1].rsplit("\n```", 1)[0]
        if "[" in result_text and "]" in result_text:
            result_text = result_text[result_text.find("[") : result_text.rfind("]") + 1]

        topics = json.loads(result_text)
        print(f"\n📊 生成了 {len(topics)} 个洞察专题")
        return topics

    except Exception as e:
        print(f"⚠ 洞察生成失败: {e}")
        return []
