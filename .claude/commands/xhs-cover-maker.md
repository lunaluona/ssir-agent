# Skill: /xhs-cover-maker

## 用途
从 `xhs.json` 读取封面文案，生成 `cover.html`，用 Playwright 直接渲染为 PNG 存入 `images/01_cover.png`。**无需手动开浏览器。**

**调用方式**：`/xhs-cover-maker {slug} [图片绝对路径]`

---

## 封面视觉规范

所有封面统一遵循以下结构（固定模板，不得自行改动布局）：

```
┌─────────────────────────────┐
│                             │  ← 背景：全出血主题图/插画
│  ┌───────────────────────┐  │
│  │  标题第一行            │  │  ← 白色圆角矩形标题框
│  │  标题第二行（高亮词）  │  │    字号 52-64px，黑体 Bold
│  └───────────────────────┘  │    关键词：红橙色 #E8453C
│                             │
│  #话题标签                  │  ← 标题框下方约 20px，中灰 #666
│                             │
│                             │
├─────────────────────────────┤
│ 来源：英文标题 / SSIR 年份  │  ← 底部来源条，半透明黑底
│ 作者：中文名（英文原名）    │    rgba(0,0,0,0.55)，斜体 18px
└─────────────────────────────┘
```

**标题框**：白底 `#FFFFFF`，圆角 12-16px，内边距上下 24px / 左右 32px，左右外边距 40px  
**关键词高亮**：1-2 个核心词（情绪动词或核心名词），颜色 `#E8453C`，其余深藏青 `#1A2B4A`  
**尺寸**：1080 × 1440px

---

## 执行步骤

### 1. 定位 xhs.json
```bash
find data/output -name "xhs.json" -path "*/{slug}/*"
# → data/output/{week}/{slug}/xhs.json
```

### 2. 提取字段

| xhs.json 字段 | 用途 |
|---|---|
| `cover.title` 或 `cover_text` | 封面大标题（ZH_TITLE） |
| `cover.hashtag` 或 `cover_subtext` | 话题标签，格式 `#XX`（HASHTAG） |
| `cover.highlight_words` | 需高亮的词列表，如 `["耗尽", "偷走"]` |

**EN_TITLE**：读 `data/articles/{slug}/source.md` 第一行 H1，去掉 `# `；若无则留 `""`

**AUTHOR**：从 `source.md` 提取作者字段，格式 `中文译名（英文原名）`

**IMAGE_PATH**：
- 优先用用户传入的绝对路径
- 否则取 `data/output/{week}/{slug}/images/` 里第一个图片文件
- **必须转为 base64 data URL 内嵌**（避免 file:// 跨域）：
  ```python
  import base64, mimetypes
  mime = mimetypes.guess_type(img_path)[0] or "image/jpeg"
  with open(img_path, "rb") as f:
      data_url = f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"
  ```
- 无图片则用纯色渐变占位背景

**DATE**：今天 `YYYYMMDD`

**HIGHLIGHTED_TITLE_HTML**：将 `zh_title` 中属于 `highlight_words` 的词用 `<span style="color:#E8453C">词</span>` 包裹，其余文字保持 `#1A2B4A`。`highlight_words` 为空时，取标题中第一个情绪动词或核心名词自动高亮。

### 3. 生成 cover.html

读 `templates/xhs_cover_template.html`，替换以下占位符：
```
PLACEHOLDER_EN_TITLE        → en_title（JS 转义）
PLACEHOLDER_ZH_TITLE        → zh_title 纯文本（JS 转义）
PLACEHOLDER_HIGHLIGHTED_HTML→ highlighted_title_html（含 <span> 标签）
PLACEHOLDER_HASHTAG         → hashtag（如 #心理健康）
PLACEHOLDER_AUTHOR          → author
PLACEHOLDER_IMAGE_PATH      → data_url
PLACEHOLDER_DATE            → date
```
写入 `data/output/{week}/{slug}/cover.html`

### 4. Playwright 渲染 → PNG

```bash
python3 scripts/render_cover.py \
  data/output/{week}/{slug}/cover.html \
  data/output/{week}/{slug}/images/01_cover.png
```

### 5. 报告

```
✅ 封面生成完成
  PNG: data/output/{week}/{slug}/images/01_cover.png
  HTML: data/output/{week}/{slug}/cover.html（如需微调可手动开浏览器重下载）
  高亮词：{highlight_words}
下一步：人工预览 → 确认文案 → 上传小红书
```

---

## 错误处理

| 问题 | 处理 |
|---|---|
| `xhs.json 不存在` | 提示先运行 `@xhs-writer {slug}` |
| `playwright not found` | `pip3 install playwright && playwright install chromium` |
| `cover_text / cover.title 均为空` | 用 `title` 字段兜底，警告文案可能偏长 |
| `highlight_words 为空` | 自动选标题中第一个情绪动词或核心名词高亮 |
| PNG 为空白 | 增加 `page.wait_for_timeout` 或检查 CDN 连通性 |

## 红线
- 标题框必须是白底圆角矩形，不得改为透明/彩色底
- 高亮色只用 `#E8453C`，不用其他颜色
- 底部来源条必须显示，不得省略
