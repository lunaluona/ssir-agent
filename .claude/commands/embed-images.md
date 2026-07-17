---
description: 从 PDF 提取插图并嵌入到 wechat.md 对应位置。用法：/embed-images {slug}
---

# /embed-images 图片嵌入

## 输入解析

从参数中确定 slug（如 `what-are-schools-for-now`）。

## 执行流程

### Step 1：定位文件

- PDF：`data/articles/{slug}/source.pdf`
- 已有 wechat.md：在 `data/output/` 下找到对应的文件（可能有多个周次，取最新的）
- 图片输出目录：与 wechat.md 同级的 `figures/` 子目录

如果 PDF 不存在，告知用户把 PDF 放到 `data/articles/{slug}/source.pdf` 后重试。

### Step 2：提取图片

运行以下命令：

```bash
python3 /Users/luonacai/Projects/ssir-agent/scripts/extract_pdf_images.py \
  data/articles/{slug}/source.pdf \
  data/output/{week}/{slug}/figures/
```

读取生成的 `figures/manifest.json`，查看每张图片的：
- `file`：文件名（如 `figure-01.png`）
- `caption`：从 PDF 提取的图注原文（英文）
- `page`：所在 PDF 页码

### Step 3：语义匹配

读取 wechat.md 全文。对每张图片，依据以下策略确定插入位置：

1. **图注匹配**：将英文图注关键词与 wechat.md 各段落比对，找到语义最近的段落
2. **页码参考**：PDF 页码对应文章进度，可估算对应 wechat.md 的大致章节位置（靠前的页面对应前面的章节）
3. **章节边界**：优先插在 `▍` 章节标题之后，或相关段落之后，不要插在段落中间

### Step 4：插入 Markdown

在匹配段落之后（或章节标题之后）插入：

```markdown
![{图注中文译文}](figures/{filename})
```

图注中文译文规则：
- 如果原图注是一句完整描述，翻译成中文（≤40字）
- 如果原图注只有"Figure 1"之类，改为"图{N}"
- 如果无图注，写"图{N}"

### Step 5：输出报告

```
✅ 图片嵌入完成：{wechat.md 路径}

共处理 {N} 张图片：
- figure-01.png → 插入位置：▍{章节名} 之后（匹配依据：{关键词}）
- figure-02.png → 插入位置：第 {段落首句} 之后
...

如有匹配把握不足的图片，会在此列出，供人工核查。
```

## 注意事项

- 同一位置不插入超过 1 张图（防止堆叠）
- 微信公众号编辑器支持标准 Markdown 图片语法，路径用相对路径
- 装饰图、广告、封面等已由提取脚本过滤（< 120×80px 的图片不提取）
- 如果某张图实在找不到匹配段落，在文末列出，标注"待人工定位"
