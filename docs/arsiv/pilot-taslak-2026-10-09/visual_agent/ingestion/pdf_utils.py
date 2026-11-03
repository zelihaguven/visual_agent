"""PDF yardımcıları (pypdfium2): metin katmanı, basılı sayfa numarası, sayfa aralığı çıkarma.

Faz 1 denemesindeki (Pre/faz1-test/faz1-test.py) fonksiyonların pilot için düzenlenmiş hali.
"""

from __future__ import annotations

import re
from pathlib import Path


def page_texts(pdf_path: Path) -> list[str]:
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(str(pdf_path))
    try:
        return [pdf[i].get_textpage().get_text_range() for i in range(len(pdf))]
    finally:
        pdf.close()


def page_count(pdf_path: Path) -> int:
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(str(pdf_path))
    try:
        return len(pdf)
    finally:
        pdf.close()


def pages_without_text(pdf_path: Path, min_chars: int = 50) -> list[int]:
    """Metin katmanı olmayan (OCR gerektiren) sayfalar, 1 tabanlı."""
    return [i + 1 for i, t in enumerate(page_texts(pdf_path)) if len(t.strip()) < min_chars]


_NUM = re.compile(r"(?<![\w/.-])(\d{1,4})(?![\w/.:-])")


def printed_page_labels(pdf_path: Path, bands=(0.06, 0.09, 0.12)) -> dict[int, str | None]:
    """Her PDF sayfası için alt (yoksa üst) bilgideki basılı sayfa numarası.

    Bant kenardan içeri kademeli genişletilir; kenara en yakın bantta bulunan numara seçilir.
    Basılı numara yoksa None. Faz 1: Brother S-7300A'da PDF s.101 = basılı s.90.
    """
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(str(pdf_path))
    out: dict[int, str | None] = {}
    try:
        for i in range(len(pdf)):
            page = pdf[i]
            w, h = page.get_size()
            tp = page.get_textpage()
            label = None
            for edge in ("bottom", "top"):
                for band in bands:
                    bottom, top = (0, h * band) if edge == "bottom" else (h * (1 - band), h)
                    text = tp.get_text_bounded(left=0, bottom=bottom, right=w, top=top) or ""
                    nums = _NUM.findall(text)
                    if nums:
                        label = nums[0]
                        break
                if label:
                    break
            out[i + 1] = label
    finally:
        pdf.close()
    return _clean_labels(out)


def _clean_labels(labels: dict[int, str | None]) -> dict[int, str | None]:
    """Tutarsız etiketleri ele: Basılı numara PDF numarasıyla sabit farkla artmalı.

    En sık görülen fark (offset) bulunur; bu farka uymayan tekil etiketler (gövde metnindeki
    rastgele sayılar) atılır. Kitapçık düzenindeki dokümanlarda (ör. Mr. Coffee) tutarlı fark
    yoksa etiketler olduğu gibi bırakılmaz, hepsi None olur (yanlış numara göstermektense hiç).
    """
    diffs: dict[int, int] = {}
    for p, lab in labels.items():
        if lab and lab.isdigit():
            diffs[p - int(lab)] = diffs.get(p - int(lab), 0) + 1
    if not diffs:
        return {p: None for p in labels}
    offset, count = max(diffs.items(), key=lambda kv: kv[1])
    if count < max(3, len(labels) * 0.3):
        return {p: None for p in labels}
    return {p: (lab if lab and lab.isdigit() and p - int(lab) == offset else None) for p, lab in labels.items()}


def fmt_page(page: int, label: str | None) -> str:
    """Kullanıcıya gösterilecek sayfa: basılı numara farklıysa 's.90 (PDF s.101)'."""
    if label and label != str(page):
        return f"s.{label} (PDF s.{page})"
    return f"s.{page}"


def extract_pages(pdf_path: Path, pages: list[int], out_path: Path) -> Path:
    """Verilen sayfalardan (1 tabanlı) yeni bir PDF oluşturur.

    Kullanıcıya dokümanın tamamı yerine sadece izin verilen sayfa aralığı gönderilir
    (cevaplar.md: 'genel olarak maksimum bir sayfa önce ve sonrası görülecek').
    """
    import pypdfium2 as pdfium
    src = pdfium.PdfDocument(str(pdf_path))
    dst = pdfium.PdfDocument.new()
    try:
        dst.import_pages(src, [p - 1 for p in pages])
        out_path.parent.mkdir(parents=True, exist_ok=True)
        dst.save(str(out_path))
    finally:
        dst.close()
        src.close()
    return out_path


def render_page(pdf_path: Path, page_no: int, dpi: int = 110):
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(str(pdf_path))
    try:
        return pdf[page_no - 1].render(scale=dpi / 72.0).to_pil().convert("RGB")
    finally:
        pdf.close()
