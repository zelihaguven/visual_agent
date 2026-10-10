"""PDF sayfasını görsele çevir ve kaynak kutularını vurgula."""
from pathlib import Path
from typing import Any

import pypdfium2 as pdfium
from PIL import Image, ImageDraw

DPI = 110
HIGHLIGHT = (255, 214, 0)


def page_image(pdf_path: Path, page: int, boxes: list[dict[str, Any]]) -> Image.Image:
    """page: 1 tabanlı PDF sayfası. boxes: bu sayfaya ait {'page','bbox_tl',...} kutuları (point)."""
    pdf = pdfium.PdfDocument(str(pdf_path))
    try:
        scale = DPI / 72
        img = pdf[page - 1].render(scale=scale).to_pil().convert("RGBA")
    finally:
        pdf.close()
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for b in boxes:
        if b["page"] != page:
            continue
        l, t, r, bt = (v * scale for v in b["bbox_tl"])
        draw.rectangle([l, t, r, bt], fill=HIGHLIGHT + (70,), outline=HIGHLIGHT + (255,), width=3)
    return Image.alpha_composite(img, overlay).convert("RGB")
