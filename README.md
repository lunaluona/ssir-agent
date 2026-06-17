# SSIR 中文内容 Agent

每周从 [SSIR](https://ssir.org/) 抓取文章 → 筛选 → 编译为公众号长文 + 改写为小红书笔记。

## 目录结构

```
ssir-agent/
├── CLAUDE.md                   # 项目持久上下文（Claude Code 自动加载）
├── glossary.json               # 术语表
├── prompts/
│   ├── select.md               # ① 筛选 prompt
│   ├── wechat.md               # ② 公众号编译 prompt
│   └── xhs.md                  # ③ 小红书改写 prompt
├── examples/
│   ├── wechat/
│   │   ├── sample_01_teacher_training.md
│   │   └── sample_02_foundation_spending.md
│   └── xhs/
│       ├── sample_01_sustainable_products.md
│       └── sample_02_rest_recovery.md
└── data/
    ├── seen.json               # 去重表（待你创建：{"seen": []})
    └── output/                 # 周输出目录
```

## 如何使用

### 1. 把这个目录变成 Claude Code 项目

```bash
cd ssir-agent
claude  # 启动 Claude Code，它会自动读取 CLAUDE.md
```

### 2. 典型一周流程

```
你（在 Claude Code 里）：
"读 SSIR RSS（https://ssir.org/site/rss）拿到本周新文章，
 按 prompts/select.md 评分筛选，输出 JSON 到 data/output/2026-W21/selection.json"

Claude Code 执行：
- fetch RSS
- 跟 data/seen.json 去重
- 用 prompts/select.md + CLAUDE.md 评分
- 输出 selection.json

你：
"对 selection.json 里 selected=true 的文章，
 - channel 包含 wechat 的，用 prompts/wechat.md 编译，存 wechat.md
 - channel 包含 xhs 的，用 prompts/xhs.md 改写，存 xhs.json"

Claude Code 执行：
- 按 channel 分发
- 每篇生成对应文件
- 更新 data/seen.json
- 输出 summary.md 列出所有产出
```

### 3. 人审 → 发布

`data/output/2026-W21/` 下会有：
- `selection.json` — 本周筛选结果与理由
- `<article_slug>/wechat.md` — 公众号成稿
- `<article_slug>/xhs.json` — 小红书成稿
- `summary.md` — 本周输出汇总

你过一遍 → 改 → 上传到对应平台。

## 自动化（可选）

GitHub Actions + Claude API 定时跑：

```yaml
# .github/workflows/weekly.yml
on:
  schedule:
    - cron: '0 1 * * 1'  # 每周一早上 9 点（UTC+8）
jobs:
  weekly:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run agent
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          npm install -g @anthropic-ai/claude-code
          claude -p "执行本周 SSIR pipeline" --output-format=json > weekly.log
      - name: Commit output
        run: |
          git config user.name "ssir-agent"
          git add data/
          git commit -m "weekly: $(date +%Y-W%V)"
          git push
```

然后你每周打开 GitHub 看 `data/output/` 新增内容，过审后发布。

## 迭代建议

每发完一篇，把"实际发布版"和"agent 产出版"做 diff，分析：
- 哪些地方你改了 → 看是不是要更新 prompt
- 哪些术语 / 表达你换了 → 进 `glossary.json`
- 选题如果发出去效果差 → 反思筛选 rubric 的权重

每月做一次 prompt 迭代会很有效果。
