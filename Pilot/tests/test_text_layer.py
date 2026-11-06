"""Yüklemede metin katmanı kontrolü (docs/PLAN-OCR.md §2): ağsız, sentetik PDF'lerle."""
import pymupdf

from pilot.text_layer import check_pdf, quality, summary


def _pdf(tmp_path, pages):
    doc = pymupdf.open()
    for kind in pages:
        page = doc.new_page()
        if kind in ("image", "scan"):
            pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 60, 80), False)
            pix.clear_with(200)
            page.insert_image(page.rect, pixmap=pix)
        if kind in ("text", "scan"):
            page.insert_text((72, 72), "The seams for all outside visible stitching shall be sewn with 11 (± 1) "
                                       "stitches per inch. Overedge stitching LSd-1, 3/16-inch, 230psi.", fontsize=8)
        if kind == "spaced":
            page.insert_text((72, 72), "C a r d f l a t s a r e w o r n a n d t h e w i r e i s b e n t", fontsize=8)
    p = tmp_path / "t.pdf"
    doc.save(str(p))
    return p


def test_classes_digital_scan_image_and_spaced(tmp_path):
    kinds = [c.kind for c in check_pdf(_pdf(tmp_path, ["text", "scan", "image", "spaced"]))]
    assert kinds == ["metin", "taranmis", "yok", "zayif"]


def test_technical_tokens_do_not_lower_quality():
    score, reasons = quality("LSd-1 SSa-2 3/16-inch 230psi 50Hz/60Hz PD1404A-BACK E050 S-7300A 11 (± 1)")
    assert score >= 0.95 and not reasons


def test_summary_lists_pages_for_coverage_report(tmp_path):
    s = summary(check_pdf(_pdf(tmp_path, ["text", "image", "spaced"])))
    assert s["ocr_gerekli"] == [2] and s["yeniden_ocr_adayi"] == [3] and s["metin"] == 1
