# 智驾资讯 AutoDrive 🚗

自动聚合自动驾驶行业最新资讯的网站，每日自动更新。

**覆盖范围**：VLA/端到端模型、Robotaxi/Robovan、智驾芯片、激光雷达、政策法规等。

**数据来源**：36氪、澎湃新闻、机器之心、钛媒体、亿欧、雷科技、新浪、搜狐汽车、今日头条。

## 快速部署到 GitHub Pages

### 1. 创建 GitHub 仓库

```bash
cd autodrive
git init
git add -A
git commit -m "🚀 智驾资讯 AutoDrive 初始版本"
gh repo create autodrive --public --source=. --push
```

### 2. 设置 GitHub Pages

- 进入仓库 → Settings → Pages
- Source: `Deploy from a branch`
- Branch: `main` / `/(root)`
- 保存后等待 1-2 分钟，访问 `https://你的用户名.github.io/autodrive/`

### 3. 配置自动抓取（核心步骤）

#### 3.1 添加 DeepSeek API Key

进入仓库 → Settings → Secrets and variables → Actions → New repository secret：
- **Name**: `DEEPSEEK_API_KEY`
- **Value**: 你的 DeepSeek API Key（格式 `sk-...`）

> 去 [platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys) 创建。
> DeepSeek 性价比极高，每天处理几十篇文章仅需几分钱。

#### 3.2 启用 GitHub Actions

进入仓库 → Actions → 启用 Workflows → 找到 "每日智驾资讯抓取" → 启用。

之后每天北京时间 8:00 自动运行，也可以手动触发。

## 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 设置 API Key
export DEEPSEEK_API_KEY=sk-...

# 运行抓取（默认抓昨天）
python scraper/main.py

# 仅抓取不调 AI（测试用）
python scraper/main.py --no-ai

# 预览网站
python3 -m http.server 3000
# → 打开 http://localhost:3000
```

## 项目结构

```
├── index.html                    # 网站主页面
├── data/news/                    # 资讯数据（自动更新）
│   ├── index.json                # 索引
│   ├── feed_YYYYMMDD.json        # 每日 feed
│   ├── weekly_YYYYWNN.json       # 每周精选
│   └── insight_YYYYWNN.json      # 每周洞察
├── scraper/                      # 抓取管线
│   ├── main.py                   # 入口
│   ├── fetcher.py                # RSS/网页抓取
│   ├── processor.py              # AI 分类 & 打分
│   ├── generator.py              # JSON 生成
│   └── sources.py                # 数据源配置
├── .github/workflows/
│   └── daily-fetch.yml           # GitHub Actions 定时任务
└── requirements.txt
```

## 五维分类

| 分类 | 涵盖内容 |
|------|---------|
| 政策 | 法规标准、准入管理、数据合规 |
| 市场 | 融资财报、市占率、合作、人事 |
| RoboX | Robotaxi、Robovan、无人配送运营 |
| 技术 | VLA/VLM、端到端、感知、仿真 |
| 硬件 | 芯片、激光雷达、域控、传感器 |
