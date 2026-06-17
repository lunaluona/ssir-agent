# Skill: /xhs-images-maker

## 用途
从 `xhs.json` 的 `image_suggestions` 读取内容，生成小红书正文图卡（内容卡 + 互动卡），用 Playwright 直接渲染为 PNG 存入 `images/`。**无需 baoyu skills，无需手动操作。**

**调用方式**：`/xhs-images-maker {slug}`

---

## 执行步骤

### 1. 一行调用

```bash
python3 scripts/render_cards.py {slug}
```

脚本自动完成以下所有工作：
- 找到 `data/output/{week}/{slug}/xhs.json`
- 解析 `image_suggestions` 里所有 `type: infographic_card` 条目
- 从 `body` 字段提取 hashtags 和互动问句
- 对每张内容卡：填充 `templates/xhs_card_content.html` → Playwright 渲染 → 保存 PNG
- 生成最后一张互动卡：填充 `templates/xhs_card_cta.html` → 渲染 → 保存 PNG

### 2. 输出位置

```
data/output/{week}/{slug}/images/
  01_cover.png     ← xhs-cover-maker 产出（封面）
  02_card.png      ← 第1张内容卡
  03_card.png      ← 第2张内容卡（如有）
  ...
  XX_cta.png       ← 互动卡（最后一张）
```

### 3. 报告

```
✅ 图卡生成完成：data/output/{week}/{slug}/images/
   内容卡 × N，互动卡 × 1，共 N+1 张
下一步：人工预览 → 确认文案 → 与封面一起上传小红书
```

---

## 图卡设计规范（模板）

**内容卡** `templates/xhs_card_content.html`：
- 背景：#EDECF0（浅灰）+ 白色装饰球（左下/右上角）
- 角标：黑底 `#1A1A1A` + 黄字 `#FFE566`，序号 02. 03. …
- 标题：46px 900 weight，来自 `main_text`
- 副标题：13.5px 灰色，来自 `content` 摘要
- 要点列表：正文，虚线分隔
- 底栏：`#FFE566` 黄色，左侧 hashtags，右侧「斯坦福社会创新评论中文版」

**互动卡** `templates/xhs_card_cta.html`：
- 相同背景 + 更大装饰球（更简洁）
- 居中：黑色「今日互动」标签 + 黄色圆角问题气泡
- 底栏同上

---

## 错误处理

| 问题 | 处理 |
|---|---|
| `xhs.json 不存在` | 提示先运行 `@xhs-writer {slug}` |
| `image_suggestions 为空` | 提示 xhs-writer 未产出图卡 prompts，手动检查 xhs.json |
| `playwright not found` | `pip3 install playwright && playwright install chromium` |
| PNG 空白/乱码 | 检查模板路径 `templates/xhs_card_*.html` 是否存在 |
