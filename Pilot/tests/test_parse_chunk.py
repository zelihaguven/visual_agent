"""Parse sonrası temizlik ve parçalama: PDF/model gerektirmez."""
import pytest

from pilot import chunk as chunk_mod
from pilot import parse
from pilot.chunk import _split_long, build_chunks
from pilot.config import CHUNK_MAX_CHARS
from pilot.parse import group_table_rows, merge_cross_page, remove_furniture, _clean_block_text
from pilot.registry import BY_ID

W, H = 612.0, 792.0


def el(text, page=1, label="text", top=300.0, eid=None, **extra):
    box = {"page": page, "bbox_tl": [50.0, top, 560.0, top + 20], "page_w": W, "page_h": H}
    return {"id": eid or f"e{page}_{top}", "label": label, "text": text, "page": page,
            "bbox_tl": box["bbox_tl"], "page_w": W, "page_h": H, "pages": [page], "boxes": [box], **extra}


# --- remove_furniture ---------------------------------------------------------------

def test_repeating_header_with_changing_page_number_is_removed():
    els = [el(f"GL/PD 14-04A page {p}", page=p, top=20.0) for p in (1, 2, 3, 4)]
    els += [el(f"Body text {p}", page=p, top=300.0) for p in (1, 2, 3, 4)]
    kept = remove_furniture(els)
    assert all(e["text"].startswith("Body") for e in kept)
    assert len(kept) == 4


def test_labeled_page_header_is_removed_even_on_single_page():
    els = [el("Running header", label="page_header", top=10.0), el("Body")]
    assert [e["text"] for e in remove_furniture(els)] == ["Body"]


def test_body_text_repeating_in_the_middle_is_kept():
    els = [el("WARNING: unplug first", page=p, top=400.0) for p in (1, 2, 3)]
    assert len(remove_furniture(els)) == 3


# --- merge_cross_page ---------------------------------------------------------------

def test_paragraph_split_across_pages_is_merged_with_both_boxes():
    a = el("The eyelet stitching shall have at least", page=22, top=700.0)
    b = el("four overlapping stitches.", page=23, top=60.0)
    out = merge_cross_page([a, b])
    assert len(out) == 1
    assert out[0]["text"] == "The eyelet stitching shall have at least four overlapping stitches."
    assert out[0]["pages"] == [22, 23]
    assert [bx["page"] for bx in out[0]["boxes"]] == [22, 23]


def test_complete_sentence_is_not_merged_with_next_page():
    out = merge_cross_page([el("Done.", page=1), el("Next section starts here", page=2)])
    assert len(out) == 2


def test_hyphenated_word_is_joined_without_hyphen():
    out = merge_cross_page([el("The protru-", page=1), el("ding seam allowance.", page=2)])
    assert out[0]["text"].startswith("The protruding seam")


def test_non_adjacent_pages_are_never_merged():
    out = merge_cross_page([el("and then", page=1), el("continues here", page=3)])
    assert len(out) == 2


# --- group_table_rows ---------------------------------------------------------------

def cell(r, c, text, header=False, r1=None, c1=None):
    return {"r0": r, "r1": r1 or r + 1, "c0": c, "c1": c1 or c + 1, "text": text,
            "bbox_tl": [10.0 * c, 10.0 * r, 10.0 * c + 9, 10.0 * r + 9], "header": header}


def test_table_rows_get_header_prefixed_text():
    cells = [cell(0, 0, "Problem", header=True), cell(0, 1, "Cause", header=True),
             cell(1, 0, "Skipped stitches"), cell(1, 1, "Needle bent"),
             cell(2, 0, "Thread breaks"), cell(2, 1, "Tension too high")]
    rows = group_table_rows(cells)
    assert [r["text"] for r in rows] == ["Problem: Skipped stitches | Cause: Needle bent",
                                         "Problem: Thread breaks | Cause: Tension too high"]


def test_merged_cell_spanning_rows_groups_rows_together():
    cells = [cell(0, 0, "Problem", header=True), cell(0, 1, "Cause", header=True),
             cell(1, 0, "Upper thread loose", r1=3), cell(1, 1, "Tension weak"), cell(2, 1, "Wrong threading")]
    rows = group_table_rows(cells)
    assert len(rows) == 1
    assert "Tension weak" in rows[0]["text"] and "Wrong threading" in rows[0]["text"]


SHIFTED = [  # S-7300A s.98, Docling çıktısı: kod bir sonraki satırın "Remedy" hücresinde
    "Code: E050 Machine head is detected as being tilted back start sewing. | Cause: when ・Turn off the power | Remedy: return the machine",
    "Code: Machine head is detected as being tilted back during sewing. | Cause: Turn off the power and check P2. | Remedy: E051",
    "Code: Machine head is detected as being tilted back when power was turned on. | Cause: Turn off the power. | Remedy: E055",
    "Code: Touch key was being pressed when power was turned on. | Cause: Turn the power off and then back on again. | Remedy: E064",
]
CLEAN = [
    "Code: E050 | Cause: Machine head is detected as being tilted back when start sewing. | Remedy: Turn off the power.",
    "Code: E051 | Cause: Machine head is detected as being tilted back during sewing. | Remedy: Check connector P2.",
]
SIZES = [  # ceket beden tablosu: anahtar sütunu kod değil, kayma sayılmamalı
    "Size: Medium | XX- Short: 27 | X- Short: 28 | Short: 29 | Regular: 30-1/2 | Tol.: + 1/2",
    "Size: Large | XX- Short: 20-1/8 | X- Short: 21-1/8 | Short: 22-1/8 | Tol.: + 1/2",
]


def test_shifted_code_table_is_detected():
    assert parse._is_misaligned(SHIFTED)
    assert parse.misaligned_rows(SHIFTED) == 3


@pytest.mark.parametrize("rows", [CLEAN, SIZES])
def test_aligned_tables_are_not_flagged(rows):
    assert not parse._is_misaligned(rows)


def test_table_without_body_gives_no_rows():
    assert group_table_rows([cell(0, 0, "Only header", header=True)]) == []


# --- PyMuPDF yedeği metin temizliği ---------------------------------------------------

def test_clean_block_joins_hyphenated_line_breaks():
    assert _clean_block_text("de¬\nsign lines\nare shown") == "design lines are shown"
    assert _clean_block_text("con-\nstruction") == "construction"


# --- _split_long / build_chunks -----------------------------------------------------

def test_short_paragraph_is_not_split():
    e = el("Short.")
    assert _split_long(e) == [e]


def test_long_paragraph_splits_on_sentence_boundaries_and_keeps_boxes():
    sentence = "The seams shall be sewn with 11 (± 1) stitches per inch. "
    e = el(sentence * 40)
    parts = _split_long(e)
    assert len(parts) > 1
    assert all(len(p["text"]) <= CHUNK_MAX_CHARS for p in parts)
    assert all(p["boxes"] == e["boxes"] for p in parts)
    assert all(p["text"].endswith("inch.") for p in parts)


@pytest.fixture
def no_pdf(monkeypatch):
    monkeypatch.setattr(chunk_mod, "printed_page_labels", lambda path, pages: {p: str(p) for p in pages})


def test_build_chunks_sets_section_type_and_metadata(no_pdf):
    meta = BY_ID["gl-pd-14-04a"]
    els = [el("3.11 Configuration", label="section_header", top=100.0),
           el("Seams shall be sewn with 11 (± 1) stitches per inch.", top=130.0),
           el("Back", label="table_row", top=400.0, eid="t0_r0"),
           el("", label="picture", top=500.0)]
    chunks = build_chunks(meta, els)
    assert [c.chunk_type for c in chunks] == ["text", "table_row"]
    text = chunks[0]
    assert text.section == "3.11 Configuration"
    assert text.doc_id == "gl-pd-14-04a" and text.brand == "US Army (GL-PD)" and text.lang == "en"
    assert text.page == 1 and text.page_labels == {"1": "1"}
    assert text.embed_text.startswith("US Army (GL-PD) Ceket | 3.11 Configuration")


def test_pictures_and_empty_text_are_skipped(no_pdf):
    chunks = build_chunks(BY_ID["gl-pd-14-04a"], [el("", label="picture"), el("   ", label="text", top=200.0)])
    assert chunks == []


def test_chunk_never_crosses_a_heading(no_pdf):
    els = [el("Para A before.", top=100.0), el("Heading", label="section_header", top=150.0),
           el("Para B after.", top=200.0)]
    chunks = build_chunks(BY_ID["gl-pd-14-04a"], els)
    assert [c.text for c in chunks] == ["Para A before.", "Para B after."]
    assert chunks[1].section == "Heading"


def test_lang_follows_page_ranges_for_trilingual_manual(no_pdf):
    meta = BY_ID["bosch-ra1171"]
    chunks = build_chunks(meta, [el("English text", page=10), el("Texte français", page=40, top=301.0),
                                 el("Texto español", page=70, top=302.0)])
    assert [c.lang for c in chunks] == ["en", "fr", "es"]


def test_text_chunks_respect_max_length(no_pdf):
    els = [el("Sentence number %d is here. " % i * 3, top=100.0 + i) for i in range(40)]
    chunks = build_chunks(BY_ID["gl-pd-14-04a"], els)
    assert all(len(c.text) <= CHUNK_MAX_CHARS * 1.3 for c in chunks)
    assert len(chunks) > 1


# --- harf aralıklı OCR katmanı (Granovsky 1986) --------------------------------------

def _chars(words, letter_gap, word_gap, size=10.0, width=5.0):
    """Kelimeleri harf konumlarına çevir: (harf, x0, x1, punto)."""
    out, x = [], 0.0
    for wi, w in enumerate(words):
        if wi:
            x += word_gap - letter_gap
        for c in w:
            out.append((c, x, x + width, size))
            x += width + letter_gap
    return out


def test_letter_spaced_text_is_detected():
    assert parse.is_letter_spaced("C a r d f l a t is f i t t e d o n t h e f i n g e r")
    assert not parse.is_letter_spaced("The card flat is fitted on the finger for attenuating the impacts " * 2)
    assert not parse.is_letter_spaced("a b c")                       # çok kısa: karar verilmez


@pytest.mark.parametrize("letter_gap, word_gap", [(1.0, 4.0), (2.5, 6.0), (0.0, 3.0)])
def test_words_are_rebuilt_from_letter_positions(letter_gap, word_gap):
    words = ["Card", "flat", "is", "fitted", "on", "the", "finger."]
    assert parse._line_from_chars(_chars(words, letter_gap, word_gap)) == " ".join(words)


def test_single_word_line_is_not_split():
    assert parse._line_from_chars(_chars(["disassembly"], 1.0, 1.0)) == "disassembly"


def test_tracked_heading_becomes_one_word():
    assert parse._line_from_chars(_chars(["CONTENTS"], 4.0, 4.0)) == "CONTENTS"


def test_soft_hyphen_line_break_is_joined():
    assert _clean_block_text("have to over\xad\ncome the inertia") == "have to overcome the inertia"
