# Step-by-Step 配置指南（Cursor IDE + Claude Code）

## 0. 前置准备

- ✅ Cursor IDE 已安装
- ✅ Node.js 18+（baoyu skills 需要）
- ✅ Claude Pro / Max / Team 订阅或 Console API 账号
- ✅ （可选）Claude in Chrome 浏览器扩展（用于抓 SSIR 订阅内容）

---

## Step 1：安装 Claude Code

在 Cursor 里 **`View > Terminal`**（或 `` Ctrl+` ``）打开集成终端，运行：

```bash
# 推荐：原生安装包，零依赖
curl -fsSL https://claude.ai/install.sh | bash

# 或者用 npm
npm install -g @anthropic-ai/claude-code
```

验证：
```bash
claude --version
```

---

## Step 2：把项目放到工作目录并打开

```bash
# 把我生成的 ssir-agent 文件夹放到你想要的位置
cd ~/Projects/ssir-agent  # 改成你的实际路径

# 在 Cursor 里打开这个文件夹
cursor .
```

打开后，在 Cursor 的集成终端里运行：

```bash
claude
```

首次运行会提示登录：
```
/login
```

按提示在浏览器里完成认证。Claude Code 会自动读取项目根的 `CLAUDE.md`，你应该会在欢迎屏里看到项目上下文已加载。

---

## Step 3：安装 baoyu skills（图像生成用）

baoyu skills 有两种安装方式，推荐用 **playbooks CLI** 一键装：

```bash
# 装 playbooks
npm install -g playbooks

# 装你需要的 skills
npx playbooks add skill jimliu/baoyu-skills --skill baoyu-cover-image
npx playbooks add skill jimliu/baoyu-skills --skill baoyu-image-cards
# 注：baoyu-xhs-images 已弃用，用 baoyu-image-cards 代替
```

或者手动 curl 安装到项目级 `.claude/skills/`：

```bash
mkdir -p .claude/skills/baoyu-cover-image
# 具体 URL 见 https://github.com/JimLiu/baoyu-skills
```

baoyu 默认走 Gemini API（通过 `baoyu-danger-gemini-web`），需要配置 Gemini 凭证。按 [baoyu-skills 仓库 README](https://github.com/JimLiu/baoyu-skills) 的说明做。

验证：在 Claude Code 会话里输入 `/` 看是否出现 `/baoyu-cover-image` 和 `/baoyu-image-cards`。

---

## Step 4：注册 sub-agents

`.claude/agents/` 下的 5 个 markdown 文件就是 sub-agent 定义，Claude Code 启动时自动发现。

验证：在会话里输入：

```
/agents
```

应该列出：
- ssir-scraper
- article-curator
- wechat-editor
- xhs-writer
- xhs-image-designer

加上 3 个内置的（explore / plan / general-purpose）。

如果没看到，确认：
1. 文件在 `.claude/agents/`（点号开头的隐藏文件夹）
2. YAML frontmatter 格式正确（`---` 包裹）
3. `name` 和 `description` 字段都填了

---

## Step 5：第一次试跑

### 方式 A：完整流程

```
/weekly
```

会按 `.claude/commands/weekly.md` 走 6 个阶段。

### 方式 B：单步测试（推荐第一次用）

测试 scraper：
```
@ssir-scraper 抓本周 SSIR
```

测试 curator（先准备一段你订阅看到的 SSIR 全文）：
```
我把这篇文章的全文准备好了：

URL: https://ssir.org/articles/entry/xxx
标题: Some Article Title

[粘贴完整正文，含作者简介、脚注]

请 @article-curator 整理
```

测试 wechat-editor：
```
@wechat-editor 编译刚才那篇的公众号版
```

测试 xhs-writer：
```
@xhs-writer 把刚才那篇做成小红书
```

测试 image-designer：
```
@xhs-image-designer 给刚才那篇生成配图
```

---

## Step 6：迭代 prompt

每跑完一篇：

1. 打开 `data/output/{week}/{slug}/wechat.md`，跟你想发的版本对比
2. 把差异告诉主对话：
   ```
   这次产出的导读太短了，标题候选都偏陈述句缺乏钩子。
   请帮我改 prompts/wechat.md 让导读 200-250 字，
   并要求标题候选中至少 2 个是问句式。改完用 git diff 给我看。
   ```
3. Claude Code 会直接改 `prompts/wechat.md`，下次再跑就生效

`prompts/*.md` 是你"喂养"agent 的核心，每周迭代 1-2 次会快速提升质量。

---

## 常见问题

**Q: 在 Cursor 里 Claude Code 和 Cursor 自己的 AI 会冲突吗？**
A: 不会。它们是两个独立工具——Cursor 的 AI 编辑代码用 Cmd+K / Cmd+L，Claude Code 是终端里的 agent。你也可以同时用：Cursor AI 改代码细节，Claude Code 跑 agent 流水线。

**Q: 为什么 @ssir-scraper 用 Haiku 而 @wechat-editor 不指定 model？**
A: Haiku 又快又便宜，scraper 只是解析 RSS 不需要"思考"。编译翻译这种需要语感的工作不指定 model，就会用主对话的 model（默认 Sonnet 或 Opus），质量更高。

**Q: sub-agent 之间能直接通信吗？**
A: 不能。<sub-agents 是相互隔离的，结果只通过主对话流转。所以"xhs-writer 完成后调 image-designer"是主对话决定的，不是 xhs-writer 自己调用 image-designer。

**Q: SSIR 全文必须人工粘贴吗？没有自动化方法？**
A: 严格来说有：用 Claude in Chrome 扩展登录你的 SSIR 订阅账号，让它打开文章、提取文本，然后你把结果粘到 Claude Code。但这一步无法跳过人工——SSIR 的反爬虫 + 订阅墙让纯自动化 fetch 不可行（也违反 ToS）。

**Q: 想要每周一早上自动跑怎么办？**
A: 全自动化需要规避"人工粘贴全文"这步——可行方案是：你周日晚上用 30 分钟把本周要做的 3 篇全文准备好放到 `data/articles/{slug}/source.md`，然后 GitHub Actions 周一早上自动跑 `claude -p "对 data/articles/ 下所有还没处理的文章，跑 wechat + xhs pipeline"`，产出存到 git 仓库，给你发邮件。
