# /guizang

使用项目内置的 guizang-social-card-skill 生成小红书图文卡片组或微信公众号封面对。

**调用方式**：`/guizang [需求描述或 slug]`

---

## 启动序列

执行此命令时，按以下顺序读取本地 skill 文件，然后按 SKILL.md 的 Workflow 执行：

1. `skills/guizang-social-card-skill/SKILL.md` — 完整工作指南（必读）
2. 按需读取 `skills/guizang-social-card-skill/references/` 下的专项参考文件
3. HTML 种子模板在 `skills/guizang-social-card-skill/assets/` 下

所有 references 路径均已迁移至项目内，不依赖全局安装的 skill。

## 前置要求（协作者）

渲染需要 Python + Playwright：

```bash
pip install playwright
playwright install chromium
```

Node.js 验证脚本（`validate-social-deck.mjs`）为可选项，跳过不影响核心渲染。
