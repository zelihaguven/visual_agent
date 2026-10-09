"""
faz1-test.py için testler.

  pytest test_faz1.py -v                 # birim test
  pytest test_faz1.py -v -m "not slow"   # sadece hızlı testler (Docling/OCR yok)

docling kullanıldı  
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
# Dosya adında "-" olduğu için normal import çalışmaz, yoldan yüklenir.
# dataclass'lar modülün sys.modules'ta kayıtlı olmasını beklediği için önce kaydedilir.
_spec = importlib.util.spec_from_file_location("faz1", ROOT / "faz1-test.py")
faz1 = importlib.util.module_from_spec(_spec)
sys.modules["faz1"] = faz1
_spec.loader.exec_module(faz1)


def el(text, page, label="text", top=300, h=842.0, w=595.0):
    box = [72.0, float(top), 523.0, float(top) + 20]
    return {"id": f"x{page}{top}", "label": label, "text": text, "page": page, "bbox_tl": box,
            "page_w": w, "page_h": h, "pages": [page],
            "boxes": [{"page": page, "bbox_tl": box, "page_w": w, "page_h": h}]}


# ---------------------------------------------------------------- koordinat dönüşümü (K2)

def test_bottomleft_to_topleft_flips_vertical_axis():
    # A4 yüksekliği 842 pt. Alttan 700-760 arası bir kutu, üstten 82-142 arasıdır.
    assert faz1.bottomleft_to_topleft([72, 760, 523, 700], 842) == [72, 82, 523, 142]


def test_pt_to_px_scales_by_dpi():
    # 150 DPI'da ölçek 150/72 ≈ 2.083
    assert faz1.pt_to_px([72, 72, 144, 144], dpi=150) == [150, 150, 300, 300]
    assert faz1.pt_to_px([72, 72, 144, 144], dpi=72) == [72, 72, 144, 144]


def test_bbox_inside_page():
    assert faz1.bbox_inside_page([72, 82, 523, 142], 595, 842)
    assert not faz1.bbox_inside_page([72, 82, 700, 142], 595, 842)   # sağdan taşıyor
    assert not faz1.bbox_inside_page([72, 142, 523, 82], 595, 842)   # ters (t > b)


# ---------------------------------------------------------------- hedef öğe seçimi (adım 2)

def test_select_best_element_prefers_more_keyword_hits():
    kws = [r"stitches per inch", r"\bSPI\b"]
    elements = [el("General requirements for the coat.", 1),
                el("Overedge shall be 10 (± 2) stitches per inch.", 1, top=400),
                el("All outside visible stitching shall be 11 (± 1) stitches per inch (SPI).", 1, top=500)]
    assert "11 (± 1)" in faz1.select_best_element(elements, kws)["text"]


def test_select_best_element_none_when_no_match():
    assert faz1.select_best_element([el("Nothing relevant here.", 1)], [r"thread tension"]) is None


# ---------------------------------------------------------------- tablo satırı seviyesinde vurgu

def cell(r0, r1, c0, text, top=None, header=False):
    bbox = None if top is None else [72.0 + c0 * 100, float(top), 172.0 + c0 * 100, float(top) + 20 * (r1 - r0)]
    return {"r0": r0, "r1": r1, "c0": c0, "c1": c0 + 1, "text": text, "bbox_tl": bbox, "header": header}


def brother_like_cells():
    # Brother arıza tablosuna benzer: "Problem" hücresi birden çok "Possible cause" satırına yayılıyor
    return [cell(0, 1, 0, "Problem", 100, header=True), cell(0, 1, 1, "Possible cause", 100, header=True),
            cell(1, 3, 0, "Upper thread is not tight.", 120),
            cell(1, 2, 1, "Is the upper thread tension too weak?", 120),
            cell(2, 3, 1, "Adjust the lower thread tension or upper thread tension.", 140),
            cell(3, 4, 0, "Lower thread is not tight.", 160),
            cell(3, 4, 1, "Is the upper thread tension too strong?", 160)]


def test_group_table_rows_merges_row_spanning_cells():
    rows = faz1.group_table_rows(brother_like_cells())
    assert len(rows) == 2
    assert rows[0]["text"].startswith("Problem: Upper thread is not tight.")
    assert "Possible cause: Is the upper thread tension too weak?" in rows[0]["text"]
    assert "Lower thread" not in rows[0]["text"]
    assert rows[0]["bbox_tl"] == [72.0, 120.0, 272.0, 160.0]   # iki satırın birleşimi


def test_selection_prefers_table_row_over_whole_table():
    table = el("whole table text upper thread is not tight upper thread tension upper thread tension", 101,
               label="table")
    table["has_rows"] = True
    rows = faz1.group_table_rows(brother_like_cells())
    row_els = [dict(el(r["text"], 101, label="table_row"), bbox_tl=r["bbox_tl"]) for r in rows]
    sel = faz1.select_best_element([table] + row_els, faz1.DOCS["brother-s7300a"].keywords)
    assert sel["label"] == "table_row"
    assert "Upper thread is not tight" in sel["text"]


# ---------------------------------------------------------------- sayfa numarası ve OCR uyarısı

def test_fmt_page_shows_printed_and_pdf_page():
    assert faz1.fmt_page(101, "90") == "s.90 (PDF s.101)"
    assert faz1.fmt_page(22, "22") == "s.22"
    assert faz1.fmt_page(5, None) == "s.5"


def test_find_garbled_spans_detects_lost_ocr_line():
    bad = "uniform appearance ans     a    s  s       ams (inside garment) shall be flat"
    assert faz1.find_garbled_spans(bad)
    assert faz1.find_garbled_spans("All seams shall be 10-14 stitches per inch.") == []


# ---------------------------------------------------------------- üst/alt bilgi temizliği (adım 6)

def test_repeating_header_footer_removed():
    elements = []
    for p in (11, 12, 13):
        elements += [el(f"GL-PD-14-04A", p, top=20),                 # üst bilgi
                     el(f"Body text on page {p}.", p, top=300),
                     el(f"{p}", p, top=800)]                        # sayfa no (alt bilgi)
    kept, dropped = faz1.remove_furniture(elements)
    assert all("Body text" in e["text"] for e in kept)
    assert len(dropped) == 6


def test_docling_furniture_labels_removed():
    kept, dropped = faz1.remove_furniture([el("Header", 1, label="page_header"), el("Body.", 1)])
    assert [e["text"] for e in kept] == ["Body."]


# ---------------------------------------------------------------- sayfa geçişi birleştirme (adım 6)

def test_cross_page_paragraph_merged_with_both_pages_and_boxes():
    elements = [el("All outside visible stitching shall be", 12, top=780),
                el("sewn with 11 (± 1) stitches per inch.", 13, top=60)]
    merged, merges = faz1.merge_cross_page(elements)
    assert len(merged) == 1 and len(merges) == 1
    assert merged[0]["text"] == "All outside visible stitching shall be sewn with 11 (± 1) stitches per inch."
    assert merged[0]["pages"] == [12, 13]
    assert [b["page"] for b in merged[0]["boxes"]] == [12, 13]


def test_hyphenated_word_joined_across_pages():
    merged, _ = faz1.merge_cross_page([el("The stitch-", 12, top=780), el("ing shall be even.", 13, top=60)])
    assert merged[0]["text"] == "The stitching shall be even."


def test_not_merged_when_sentence_ends():
    merged, merges = faz1.merge_cross_page([el("Sentence ends here.", 12, top=780),
                                            el("New paragraph starts.", 13, top=60)])
    assert len(merged) == 2 and merges == []


def test_not_merged_when_next_is_heading_or_table():
    merged, _ = faz1.merge_cross_page([el("Text without period", 12, top=780),
                                       el("3.6 buttonholes", 13, top=60, label="section_header")])
    assert len(merged) == 2


def test_not_merged_when_pages_not_consecutive():
    merged, _ = faz1.merge_cross_page([el("Text without period", 12), el("continues here.", 14)])
    assert len(merged) == 2


def test_header_between_pages_does_not_block_merge_after_cleanup():
    elements = []
    for p in (11, 12, 13):
        elements.append(el("GL-PD-14-04A", p, top=20))
    elements.insert(2, el("All outside visible stitching shall be", 12, top=780))
    elements.append(el("sewn with 11 (± 1) stitches per inch.", 13, top=60))
    elements.sort(key=lambda e: (e["page"], e["bbox_tl"][1]))
    kept, _ = faz1.remove_furniture(elements)
    merged, merges = faz1.merge_cross_page(kept)
    assert len(merges) == 1
    assert "GL-PD-14-04A" not in merges[0]["merged_text"]


def test_expand_pages():
    assert faz1.expand_pages([1, 12], 13) == [1, 2, 11, 12, 13]


def test_contiguous_groups_splits_distant_pages():
    # Brother'da 77-79 ve 100-102: tek aralık (77-102) 26 sayfa parse ederdi
    assert faz1.contiguous_groups([77, 78, 79, 100, 101, 102]) == [[77, 78, 79], [100, 101, 102]]
    assert faz1.contiguous_groups([12]) == [[12]]


# ---------------------------------------------------------------- vurgu çizimi (adım 3b)

def test_draw_boxes_colors_only_inside_box():
    Image = pytest.importorskip("PIL.Image")
    img = Image.new("RGB", (1240, 1754), "white")           # A4 boyutu, baska boyutta manual gelirse değişmeli 
    out = faz1.draw_boxes(img, [[72, 82, 523, 142]], dpi=150)
    inside = out.getpixel((600, 230))                        
    outside = out.getpixel((600, 1000))
    assert inside != (255, 255, 255)
    assert outside == (255, 255, 255)


# ---------------------------------------------------------------- PDF metin katmanı (pypdfium2)

def _need_pdf(name):
    pytest.importorskip("pypdfium2")
    p = faz1.MANUALS / name
    if not p.exists():
        pytest.skip(f"{name} yok")
    return p


def test_coat_has_text_layer_and_candidate_pages():
    p = _need_pdf("GL-PD-14-04A_ACU-Coat.pdf")
    assert faz1.has_text_layer(p)
    assert faz1.find_candidate_pages(p, faz1.DOCS["gl-pd-14-04a"].keywords)


def test_printed_page_label_differs_from_pdf_page():
    p = _need_pdf("Brother_S-7300A_Instruction.pdf")
    assert faz1.printed_page_label(p, 101) == "90"    # PDF s.101, sayfanın altında "90"
    assert faz1.printed_page_label(p, 77) == "66"     # alt bantta gövde metni de var ("1: Reverse OFF")
    c = _need_pdf("GL-PD-14-04A_ACU-Coat.pdf")
    assert faz1.printed_page_label(c, 22) == "22"


def test_render_page_size_matches_dpi():
    p = _need_pdf("GL-PD-14-04A_ACU-Coat.pdf")
    img = faz1.render_page(p, 1, dpi=150)
    # US Letter 612x792 pt veya A4 595x842 pt -> 150 DPI'da ~1275x1650 veya ~1240x1754 px
    assert 1200 <= img.width <= 1300 and 1600 <= img.height <= 1800


# ---------------------------------------------------------------- 3a: streamlit-pdf-viewer

def test_viewer_app_runs_without_error():
    """Görüntüleyici hatasız açılıyor mu? (Vurgunun tarayıcıda doğru göründüğü ayrıca gözle kontrol edilir.)"""
    pytest.importorskip("streamlit_pdf_viewer")
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(ROOT / "faz1-test.py"), default_timeout=60).run()
    assert not at.exception, at.exception
    assert at.title and "Faz 1" in at.title[0].value
    ann = faz1.OUTPUT / "gl-pd-14-04a" / "annotations.json"
    if ann.exists():  # deneme çalıştırıldıysa seçilen metin ekranda olmalı, uyarı olmamalı
        assert not at.warning


# ---------------------------------------------------------------- docling 

def _need_docling():
    pytest.importorskip("docling")
    pytest.importorskip("pypdfium2")
    pytest.importorskip("PIL")


def _assert_doc_result(res, must_contain):
    assert res.error is None, res.error
    sel = res.selected
    assert sel is not None
    assert must_contain.lower() in sel["text"].lower()
    assert all(res.checks.values()), res.checks
    for img in res.images:
        assert (faz1.ROOT / img).exists()
    out = faz1.OUTPUT / res.doc_id
    for f in ("elements.json", "selected.json", "transitions.json", "annotations.json"):
        assert (out / f).exists()
    ann = json.loads((out / "annotations.json").read_text("utf-8"))
    assert ann and all(a["width"] > 0 and a["height"] > 0 for a in ann)


@pytest.mark.slow
def test_e2e_coat_digital():
    _need_docling()
    _need_pdf("GL-PD-14-04A_ACU-Coat.pdf")
    _assert_doc_result(faz1.run_doc(faz1.DOCS["gl-pd-14-04a"]), "stitch")


@pytest.mark.slow
def test_e2e_trousers_scanned_ocr():
    _need_docling()
    p = _need_pdf("GL-PD-07-14A_Combat-Trousers.pdf")
    cfg = faz1.DOCS["gl-pd-07-14a"]
    pages = faz1.find_candidate_pages(p, cfg.keywords) or None
    _assert_doc_result(faz1.run_doc(cfg, pages), "stitch")


@pytest.mark.slow
def test_e2e_brother_manual():
    _need_docling()
    _need_pdf("Brother_S-7300A_Instruction.pdf")
    res = faz1.run_doc(faz1.DOCS["brother-s7300a"])
    _assert_doc_result(res, "upper thread is not tight")
    assert res.selected["label"] == "table_row"            # tablonun tamamı değil, ilgili satır
    assert "lower thread is not tight" not in res.selected["text"].lower()
    assert res.page_labels[str(res.selected["page"])] == "90"
