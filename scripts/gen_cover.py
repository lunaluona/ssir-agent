#!/usr/bin/env python3
"""
Generate cover.html from template + xhs.json, then render to PNG via Playwright.
Usage: python3 scripts/gen_cover.py <slug> [image_path]
"""
import sys, os, json, re, base64, mimetypes
from datetime import date

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def find_week_dir(slug):
    output = os.path.join(PROJECT, "data", "output")
    for week in sorted(os.listdir(output), reverse=True):
        d = os.path.join(output, week, slug)
        if os.path.isdir(d):
            return week, d
    raise FileNotFoundError(f"No output dir found for slug: {slug}")

def to_data_url(img_path):
    mime = mimetypes.guess_type(img_path)[0] or "image/jpeg"
    with open(img_path, "rb") as f:
        return f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"

def build_highlighted_html(title, highlight_words):
    """Wrap highlight_words in <span class='hl'>; case-sensitive match."""
    result = title
    for word in highlight_words:
        result = result.replace(word, f'<span class="hl">{word}</span>')
    return result

def auto_highlight(title):
    """Fallback: highlight the longest 2-char+ noun/verb cluster after 第一个逗号 or last chunk."""
    # Split on Chinese punctuation and pick the most impactful segment
    parts = re.split(r'[，,、]', title)
    best = max(parts, key=lambda p: len(p)) if parts else title
    # Take last 3-4 chars of the longest part as the hook
    hook = best.strip()
    if len(hook) > 4:
        hook = hook[-4:]
    return title.replace(hook, f'<span class="hl">{hook}</span>', 1)

def get_author(source_md_path):
    if not os.path.exists(source_md_path):
        return ""
    with open(source_md_path, encoding="utf-8") as f:
        for line in f:
            m = re.search(r'\*\*作者\*\*[：:]\s*(.+)', line)
            if m:
                return m.group(1).strip()
    return ""

def main():
    slug = sys.argv[1] if len(sys.argv) > 1 else None
    if not slug:
        print("Usage: python3 gen_cover.py <slug> [image_path]")
        sys.exit(1)

    user_image = sys.argv[2] if len(sys.argv) > 2 else None

    week, out_dir = find_week_dir(slug)
    xhs_path = os.path.join(out_dir, "xhs.json")
    if not os.path.exists(xhs_path):
        print(f"❌ xhs.json not found: {xhs_path}")
        sys.exit(1)

    with open(xhs_path, encoding="utf-8") as f:
        raw = f.read()
    # xhs.json may contain literal newlines inside string values (invalid JSON)
    # Replace control chars inside strings before parsing
    import re as _re
    raw_fixed = _re.sub(r'(?<!\\)\n', '\\n', raw)
    try:
        xhs = json.loads(raw_fixed)
    except json.JSONDecodeError:
        # Fallback: extract only the fields we need via regex
        xhs = {}
        for key in ("cover_text", "cover_subtext", "title"):
            m = _re.search(rf'"{key}"\s*:\s*"([^"]*)"', raw)
            if m:
                xhs[key] = m.group(1)
        # hashtags array
        m = _re.search(r'"hashtags"\s*:\s*\[([^\]]+)\]', raw, _re.DOTALL)
        if m:
            xhs["hashtags"] = _re.findall(r'"([^"]+)"', m.group(1))

    source_md = os.path.join(PROJECT, "data", "articles", slug, "source.md")

    # --- Extract fields ---
    # Primary: look inside image_suggestions for the cover entry (new schema)
    cover_suggestion = {}
    for item in xhs.get("image_suggestions", []):
        if item.get("type") == "cover":
            cover_suggestion = item
            break

    attribution = cover_suggestion.get("attribution", {})
    zh_title        = xhs.get("cover_text", "")
    hashtag         = (xhs.get("hashtags", [""])[0] if xhs.get("hashtags") else
                       xhs.get("cover_subtext", ""))
    highlight_words = cover_suggestion.get("highlight_words", [])

    # attribution fields (new schema takes priority over source.md)
    en_title   = attribution.get("source_en", "")
    author_raw = attribution.get("author", "")
    pub_line   = attribution.get("publication", "")  # e.g. 《斯坦福社会创新评论》2024年

    # Fallback: parse from source.md if attribution empty
    if not en_title and os.path.exists(source_md):
        with open(source_md, encoding="utf-8") as f:
            first = f.readline().strip()
            en_title = first.lstrip("# ").strip()
    if not author_raw:
        author_raw = get_author(source_md)

    year = ""
    if pub_line:
        m = re.search(r'(\d{4})', pub_line)
        if m:
            year = m.group(1)
    if not year and os.path.exists(source_md):
        with open(source_md, encoding="utf-8") as f:
            for line in f:
                m = re.search(r'(\d{4})-\d{2}-\d{2}', line)
                if m:
                    year = m.group(1)
                    break

    # Build highlighted HTML
    if highlight_words:
        highlighted_html = build_highlighted_html(zh_title, highlight_words)
    else:
        highlighted_html = auto_highlight(zh_title)

    # Image
    img_data_url = ""
    if user_image and os.path.exists(user_image):
        img_data_url = to_data_url(user_image)
    else:
        # Search in common locations
        candidates = [
            os.path.join(out_dir, "guizang", "assets"),
            os.path.join(out_dir, "images"),
            os.path.join(out_dir),
        ]
        for d in candidates:
            if os.path.isdir(d):
                for f in os.listdir(d):
                    if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                        img_data_url = to_data_url(os.path.join(d, f))
                        print(f"  Using image: {os.path.join(d, f)}")
                        break
            if img_data_url:
                break

    today = date.today().strftime("%Y%m%d")

    # --- Read template and substitute ---
    tmpl_path = os.path.join(PROJECT, "templates", "xhs_cover_template.html")
    with open(tmpl_path, encoding="utf-8") as f:
        html = f.read()

    # Build publication line: use attribution field if present, else fallback
    publication = pub_line if pub_line else f"《斯坦福社会创新评论》{year}年"

    html = html.replace("PLACEHOLDER_HIGHLIGHTED_HTML", highlighted_html)
    html = html.replace("PLACEHOLDER_HASHTAG", hashtag)
    html = html.replace("PLACEHOLDER_EN_TITLE", en_title)
    html = html.replace("PLACEHOLDER_PUBLICATION", publication)
    html = html.replace("PLACEHOLDER_YEAR", year)
    html = html.replace("PLACEHOLDER_AUTHOR", author_raw)
    html = html.replace("PLACEHOLDER_IMAGE_PATH", img_data_url)
    html = html.replace("PLACEHOLDER_DATE", today)

    # Write cover.html
    cover_html_path = os.path.join(out_dir, "cover.html")
    with open(cover_html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  cover.html → {cover_html_path}")

    # Render PNG
    images_dir = os.path.join(out_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    out_png = os.path.join(images_dir, "01_cover.png")

    render_script = os.path.join(PROJECT, "scripts", "render_cover.py")
    import subprocess
    result = subprocess.run(
        ["python3", render_script, cover_html_path, out_png],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("❌ Render error:", result.stderr)
        sys.exit(1)
    print(result.stdout.strip())
    print(f"\n✅ 封面生成完成")
    print(f"   PNG : {out_png}")
    print(f"   HTML: {cover_html_path}")
    print(f"   高亮词: {highlight_words or '[自动]'}")

if __name__ == "__main__":
    main()
