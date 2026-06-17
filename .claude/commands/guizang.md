# /guizang

使用 `guizang-social-card-skill` 生成小红书图文卡片组或微信公众号封面对。

**调用方式**：`/guizang [需求描述或 slug]`

---

调用此命令时，通过 Skill 工具执行 `guizang-social-card-skill`，将用户提供的所有参数和上下文完整传递给该 skill。

skill 会处理：
- 小红书 3:4 图文卡片组（封面 + 正文图卡）
- 微信公众号封面对（21:9 + 1:1）
- Editorial Magazine × E-ink 或 Swiss International 两种风格
- HTML + Playwright 渲染为 PNG，输出到 `output/` 目录
