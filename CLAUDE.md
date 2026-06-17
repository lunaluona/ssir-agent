# SSIR 中文版编辑部

> Claude Code 项目持久上下文。每次启动自动加载。

## 项目目标

每周从 [Stanford Social Innovation Review](https://ssir.org/) 编辑出版本土化中文内容：
- 公众号长文：专业 + 深度
- 小红书笔记：轻量 + 场景化
- 配图：与小红书内容一致

## 编辑部成员（Sub-Agents）

定义在 `.claude/agents/`，按调用顺序：

| Agent | 职责 | 触发 |
|---|---|---|
| `@ssir-scraper` | 抓 RSS 拿候选 | 周一启动 |
| `@article-curator` | 整理人工提供的全文 | 粘贴正文后 |
| `@wechat-editor` | 编译公众号长文 | 主对话指派 |
| `@xhs-writer` | 改写小红书笔记 + 图像 prompt | 主对话指派 |
| `@xhs-image-designer` | 调 baoyu skills 生成图片 | xhs-writer 完成后 |

主对话（你 + Claude Code 主会话）是 orchestrator——通过 `/weekly` 命令一键拉起，或单独 `@xxx` 调度。

## 账号画像

### 公众号
- **定位**：社会创新前沿知识 → 目标更加本土化
- **读者**：关注公共价值的 changemaker、社会创新学习者、NGO 从业人员
- **风格**：专业、深度、保留学术严谨性，用中文读者习惯的表达

### 小红书
- **定位**：轻量拆解社会创新知识，交流共创新知
- **读者**：一二线城市女性为主，关注社会议题和"新消费"
- **风格**：场景化痛点开场、emoji 分点、互动性强

## 术语表

详见 `glossary.json`。核心约定：

| 英文 | 中文 | 备注 |
|---|---|---|
| venture philanthropy | 公益创投 | |
| system change | 系统性变化 | |
| change | 转型 | 避免"变革" |
| theory of change | 变革理论 | ⚠️ 例外：固定译法 |
| social change | 社会正向变化 | |

## 关键文件

```
ssir-agent/
├── CLAUDE.md                  # 本文件
├── glossary.json              # 术语
├── .claude/
│   ├── agents/                # 5 个 sub-agent
│   └── commands/weekly.md     # 一键启动 /weekly
├── prompts/
│   ├── select.md              # 选题评分 rubric
│   ├── wechat.md              # 公众号 SOP（@wechat-editor 必读）
│   └── xhs.md                 # 小红书 SOP（@xhs-writer 必读）
├── examples/
│   ├── wechat/                # 公众号风格示例（few-shot）
│   └── xhs/                   # 小红书风格示例（few-shot）
└── data/
    ├── seen.json              # 去重表
    ├── articles/              # 整理后的源文件
    │   ├── _index_2026-W21.json
    │   └── {slug}/source.md
    └── output/                # 周输出
        └── 2026-W21/
            ├── summary.md
            └── {slug}/
                ├── wechat.md
                ├── xhs.json
                └── images/
```

## 主对话（orchestrator）的行为指引

当用户用 `/weekly` 时，按 `.claude/commands/weekly.md` 执行。

当用户单独说"做 XX 文章的小红书版"时：
1. 找到对应 slug 的 source.md（如果没有就先调 article-curator）
2. 调用 `@xhs-writer {slug}`
3. xhs-writer 完成后，主动询问"要现在生成配图吗？"
4. 若是，调用 `@xhs-image-designer {slug}`

每个 sub-agent 完成后会返回结构化报告，把关键信息（路径、风险点、待人审项）传递给用户。

## 通用红线

1. **不编造**：原文没有的数据、观点、案例一字不加
2. **不删关键事实**：作者论证链必须保留
3. **政治/宗教/民族敏感** → 直接 skip
4. **涉中负面表述** → 加译者注客观平衡，不直接删
5. **版权**：标注 SSIR 来源 + 原文链接 + 原标题；小红书定位为"编译/读后感"而非全文翻译
