#!/usr/bin/env python3
"""
Extract content figures and captions from an SSIR article PDF.

Usage:
    python3 scripts/extract_pdf_images.py <pdf_path> <output_dir>

Output:
    <output_dir>/figure-01.png, figure-02.png, ...
    <output_dir>/manifest.json
"""

import sys
import json
import re
from pathlib import Path

import fitz  # PyMuPDF


MIN_WIDTH = 120   # pixels — filter out tiny icons / decorative elements
MIN_HEIGHT = 80


def get_caption_near_image(page, img_bbox, page_height):
    """Return the text block most likely to be a caption for this image."""
    x0, y0, x1, y1 = img_bbox
    img_bottom = y1
    img_top = y0

    candidates = []
    blocks = page.get_text("blocks")
    for block in blocks:
        bx0, by0, bx1, by1, text, *_ = block
        text = text.strip()
        if not text:
            continue
        # Caption is typically just below the image (within 80pts) or just above
        below_gap = by0 - img_bottom
        above_gap = img_top - by1
        if 0 <= below_gap <= 80:
            candidates.append((below_gap, text))
        elif 0 <= above_gap <= 40:
            candidates.append((above_gap + 100, text))  # prefer below

    if not candidates:
        return ""
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def extract_images(pdf_path: str, output_dir: str) -> list[dict]:
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    figures = []
    fig_index = 0
    seen_xrefs = set()

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_height = page.rect.height
        image_list = page.get_images(full=True)

        for img_info in image_list:
            xref = img_info[0]
            if xref in seen_xrefs:
                continue
            seen_xrefs.add(xref)

            # Get image bounding box on page
            img_rects = page.get_image_rects(xref)
            if not img_rects:
                continue
            img_rect = img_rects[0]

            # Extract the raw image
            try:
                base_image = doc.extract_image(xref)
            except Exception:
                continue

            width = base_image.get("width", 0)
            height = base_image.get("height", 0)

            # Filter small / decorative images
            if width < MIN_WIDTH or height < MIN_HEIGHT:
                continue

            # Convert to PNG (handle CMYK)
            pix = fitz.Pixmap(doc, xref)
            if pix.colorspace and pix.colorspace.n > 3:
                pix = fitz.Pixmap(fitz.csRGB, pix)

            fig_index += 1
            filename = f"figure-{fig_index:02d}.png"
            out_path = output_dir / filename
            pix.save(str(out_path))

            caption = get_caption_near_image(page, img_rect, page_height)
            # Clean up caption: collapse whitespace, drop very long blocks (body text)
            caption = re.sub(r"\s+", " ", caption).strip()
            if len(caption) > 300:
                caption = caption[:300].rsplit(" ", 1)[0] + "…"

            figures.append({
                "index": fig_index,
                "file": filename,
                "page": page_num + 1,
                "width": width,
                "height": height,
                "caption": caption,
            })

    doc.close()

    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(figures, f, ensure_ascii=False, indent=2)

    return figures


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 extract_pdf_images.py <pdf_path> <output_dir>")
        sys.exit(1)

    pdf_path, output_dir = sys.argv[1], sys.argv[2]
    figures = extract_images(pdf_path, output_dir)

    print(f"提取完成：{len(figures)} 张图片")
    for fig in figures:
        print(f"  [{fig['index']:02d}] {fig['file']}  ({fig['width']}×{fig['height']})  第{fig['page']}页")
        if fig["caption"]:
            print(f"       图注：{fig['caption'][:80]}{'…' if len(fig['caption']) > 80 else ''}")
