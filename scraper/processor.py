"""
AI 处理模块 — 用 DeepSeek API 对文章进行分类、打分、摘要、提取洞察
需要环境变量: DEEPSEEK_API_KEY
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta

try:
    from openai import OpenAI
except ImportError:
    print("请先安装 openai SDK: pip install openai")
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
4. is_featured: 是否值得选入"每日精选"（当日最重要的 8-12 条，精选率控制在 30% 以内）
5. companies: 文章中涉及的公司/机构名称列表
6. takeaway: 仅对 is_featured=true 的文章，写一句 30-60 字的行业洞察/投资启示；非精选文章留空字符串

请严格按 JSON 数组格式返回，不要包含其他文字：
[{"title":"...","category":"技术","importance":92,"summary":"...","is_featured":true,"companies":["特斯拉"],"takeaway":"..."}]"""


def get_client():
    """获取 DeepSeek API 客户端"""
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        print("❌ 未设置 DEEPSEEK_API_KEY 环境变量")
        print("   在 DeepSeek 平台获取: https://platform.deepseek.com/api_keys")
        print("   export DEEPSEEK_API_KEY=sk-...")
        sys.exit(1)
    return OpenAI(api_key=api_key, base_url="https://api.deepseek.com")


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


def parse_json_response(text: str) -> list:
    """从 AI 返回的文本中解析 JSON 数组"""
    text = text.strip()
    # 去除 markdown 代码块标记
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:]) if len(lines) > 1 else text
        if text.endswith("```"):
            text = text[:-3]
    # 提取 JSON 数组
    if "[" in text and "]" in text:
        text = text[text.find("[") : text.rfind("]") + 1]
    return json.loads(text)


def process_articles(articles: list) -> list:
    """
    用 DeepSeek API 处理文章：分类、打分、摘要
    返回增强后的文章列表
    """
    if not articles:
        print("⚠ 没有文章需要处理")
        return []

    client = get_client()
    batches = list(chunk_articles(articles))
    processed = []

    print(f"\n🤖 开始 AI 处理 (DeepSeek): {len(articles)} 篇文章, 分 {len(batches)} 批")
    print(f"{'='*60}")

    for idx, batch in enumerate(batches):
        print(f"\n📝 批次 {idx + 1}/{len(batches)}: {len(batch)} 篇")
        user_input = build_batch_input(batch, idx, len(batches))

        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_input},
                ],
                max_tokens=4096,
                temperature=0.3,
            )

            result_text = response.choices[0].message.content
            ai_results = parse_json_response(result_text)

            # 合并回原始数据
            for i, result in enumerate(ai_results):
                if i < len(batch):
                    merged = {**batch[i]}
                    merged["category"] = result.get("category", "技术")
                    if merged["category"] not in CATEGORIES:
                        merged["category"] = "技术"
                    merged["importance"] = int(result.get("importance", 70))
                    merged["summary"] = result.get("summary", merged.get("summary_raw", ""))
                    merged["is_featured"] = bool(result.get("is_featured", False))
                    merged["companies"] = result.get("companies", [])
                    merged["takeaway"] = result.get("takeaway", "")
                    merged["has_time"] = True
                    processed.append(merged)
                    star = "⭐" if merged["is_featured"] else "  "
                    print(f"  {star} [{merged['category']}] 重要性:{merged['importance']} | {merged['title'][:50]}")

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

    try:
        client = get_client()
    except SystemExit:
        return []

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
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "user", "content": prompt},
            ],
            max_tokens=3000,
            temperature=0.5,
        )

        result_text = response.choices[0].message.content
        topics = parse_json_response(result_text)
        print(f"\n📊 生成了 {len(topics)} 个洞察专题")
        return topics

    except Exception as e:
        print(f"⚠ 洞察生成失败: {e}")
        return []
