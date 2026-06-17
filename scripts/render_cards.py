#!/usr/bin/env python3
"""
Generate and render XHS content cards from xhs.json using Playwright.
Usage: python3 scripts/render_cards.py <slug>

Outputs:
  data/output/{week}/{slug}/images/02_card.png
  data/output/{week}/{slug}/images/03_card.png  ...
  data/output/{week}/{slug}/images/XX_cta.png
"""
import json, re, os, sys, tempfile
import html as html_lib
from playwright.sync_api import sync_playwright


# ── JSON loader (handles literal newlines in string values) ─────────────────

def load_json_robust(path):
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Fix literal control chars inside JSON strings via state machine
        out, in_str, escaped = [], False, False
        for ch in raw:
            if escaped:
                out.append(ch); escaped = False
            elif ch == "\\" and in_str:
                out.append(ch); escaped = True
            elif ch == '"':
                in_str = not in_str; out.append(ch)
            elif in_str and ch == "\n":
                out.append("\\n")
            elif in_str and ch == "\r":
                out.append("\\r")
            else:
                out.append(ch)
        return json.loads("".join(out))


# ── Helpers ──────────────────────────────────────────────────────────────────

def find_xhs_json(slug):
    for root, _, files in os.walk("data/output"):
        if "xhs.json" in files and slug in root:
            return os.path.join(root, "xhs.json")
    return None


def extract_hashtags(body, n=3):
    tags = re.findall(r"#\S+", body)
    return " ".join(tags[:n]) if tags else "#社会创新 #SSIR"


def extract_cta_question(body):
    """Pick the most suitable interactive question from body text."""
    lines = [l.strip() for l in body.split("\n")]
    candidates = []
    for line in lines:
        # Strip leading emoji/symbols
        clean = re.sub(r"^[\U00010000-\U0010ffff☀-⟿ἰ0-ᾟF💬👇🏻✨🌱📌]+\s*", "", line).strip()
        if ("？" in clean or "?" in clean) and 8 < len(clean) < 55:
            candidates.append(clean)
    return candidates[-1] if candidates else "你对这个话题有什么想法？"


def parse_point(text):
    """Returns (emoji, label, body) tuple from a supporting_point string."""
    # Extract leading emoji cluster
    emoji_re = re.compile(
        r"^([\U00010000-\U0010ffff☀-⟿ἰ0-ᾟFᾠ0-ᾩF"
        r"↔-↙✂-➰⭐⭕]+)\s*"
    )
    m = emoji_re.match(text)
    emoji, rest = ("", text) if not m else (m.group(1), text[m.end():])

    # Extract bold label: text before first ：or : (max 20 chars)
    lm = re.match(r"^([^：:\n]{1,24}[：:])\s*", rest)
    label, body = ("", rest) if not lm else (lm.group(1), rest[lm.end():])

    return emoji, label, body


def make_points_html(points):
    parts = []
    for i, pt in enumerate(points):
        if i:
            parts.append('<div class="point-sep"></div>')
        emoji, label, body = parse_point(pt)
        emoji_html = f'<span class="point-emoji">{html_lib.escape(emoji)}</span>' if emoji else ""
        label_html = f'<span class="point-label">{html_lib.escape(label)}</span>' if label else ""
        parts.append(
            f'<div class="point">{emoji_html}'
            f'<div class="point-body">{label_html}{html_lib.escape(body)}</div></div>'
        )
    return "\n".join(parts)


# ── Renderer ─────────────────────────────────────────────────────────────────

def render_html_to_png(html_content, out_path):
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html_content)
        tmp = f.name
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 650, "height": 850})
            page.goto(f"file://{os.path.abspath(tmp)}")
            try:
                page.wait_for_load_state("networkidle", timeout=4000)
            except Exception:
                pass
            page.wait_for_timeout(300)
            page.locator("#card").screenshot(path=out_path)
            browser.close()
    finally:
        os.unlink(tmp)
    print(f"  ✓ {out_path}")


def fill_template(template_path, replacements):
    with open(template_path, encoding="utf-8") as f:
        html = f.read()
    for k, v in replacements.items():
        html = html.replace(k, v)
    return html


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 render_cards.py <slug>")
        sys.exit(1)

    slug = sys.argv[1]
    xhs_path = find_xhs_json(slug)
    if not xhs_path:
        print(f"Error: xhs.json not found for '{slug}'"); sys.exit(1)

    xhs = load_json_robust(xhs_path)
    out_dir = os.path.dirname(xhs_path)
    images_dir = os.path.join(out_dir, "images")

    hashtags = extract_hashtags(xhs.get("body", ""))
    # CTA fallback: extract from body if no explicit cta_card entry
    cta_q_fallback = extract_cta_question(xhs.get("body", ""))

    content_tpl = "templates/xhs_card_content.html"
    cta_tpl     = "templates/xhs_card_cta.html"

    idx = 2  # 01 is cover
    generated = []
    cta_rendered = False

    for suggestion in xhs.get("image_suggestions", []):
        # ── Resolve type: new flat format first, fallback to prompt_for_designer ──
        stype = suggestion.get("type") or suggestion.get("prompt_for_designer", {}).get("type", "")
        pd    = suggestion.get("prompt_for_designer", {})  # old format fallback

        if stype == "infographic_card":
            # New format: fields at suggestion level; old format: inside prompt_for_designer
            title    = suggestion.get("card_title")    or pd.get("main_text", "")
            subtitle = suggestion.get("card_subtitle") or pd.get("card_subtitle", "")
            points   = suggestion.get("supporting_points") or pd.get("supporting_points", [])

            html = fill_template(content_tpl, {
                "PLACEHOLDER_NUMBER":      f"{idx:02d}.",
                "PLACEHOLDER_TITLE":       html_lib.escape(title),
                "PLACEHOLDER_SUBTITLE":    html_lib.escape(subtitle),
                "PLACEHOLDER_POINTS_HTML": make_points_html(points),
                "PLACEHOLDER_HASHTAGS":    html_lib.escape(hashtags),
            })
            out = os.path.join(images_dir, f"{idx:02d}_card.png")
            render_html_to_png(html, out)
            generated.append(out)
            idx += 1

        elif stype == "cta_card":
            question = suggestion.get("question") or pd.get("question", cta_q_fallback)
            cta_html = fill_template(cta_tpl, {
                "PLACEHOLDER_QUESTION": html_lib.escape(question),
                "PLACEHOLDER_HASHTAGS": html_lib.escape(hashtags),
            })
            cta_out = os.path.join(images_dir, f"{idx:02d}_cta.png")
            render_html_to_png(cta_html, cta_out)
            generated.append(cta_out)
            idx += 1
            cta_rendered = True

    # If no explicit cta_card in image_suggestions, auto-generate from body
    if not cta_rendered:
        cta_html = fill_template(cta_tpl, {
            "PLACEHOLDER_QUESTION": html_lib.escape(cta_q_fallback),
            "PLACEHOLDER_HASHTAGS": html_lib.escape(hashtags),
        })
        cta_out = os.path.join(images_dir, f"{idx:02d}_cta.png")
        render_html_to_png(cta_html, cta_out)
        generated.append(cta_out)

    print(f"\n✅ 图卡生成完成：{images_dir}/")
    print(f"   内容卡 × {idx - 2}，互动卡 × 1，共 {len(generated)} 张")


if __name__ == "__main__":
    main()
