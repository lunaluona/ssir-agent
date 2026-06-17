#!/usr/bin/env python3
"""
Render cover.html to PNG using Playwright headless Chromium.
Usage: python3 scripts/render_cover.py <cover.html path> <output.png path>
"""
import sys, os

def render(html_path: str, out_path: str) -> None:
    from playwright.sync_api import sync_playwright

    html_abs = os.path.abspath(html_path)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 650, "height": 900})
        page.goto(f"file://{html_abs}")
        # wait for fonts + Tailwind CDN (or timeout after 6s)
        try:
            page.wait_for_load_state("networkidle", timeout=6000)
        except Exception:
            pass
        page.wait_for_timeout(400)  # extra settle for font render

        card = page.locator("#card")
        card.screenshot(path=out_path)
        browser.close()

    print(f"✅ 封面已保存：{out_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 render_cover.py <cover.html> <output.png>")
        sys.exit(1)
    render(sys.argv[1], sys.argv[2])
