"""Şekil anlama: aday seçimi, başlık bulma, açıklama temizliği, şekil parçası, doğrulama. VLM ve PDF taklit edilir."""
import json

import pytest

from pilot import chunk as chunk_mod
from pilot import figures
from pilot.chunk import build_chunks
from pilot.figures import AUTO_PREFIX, DECORATIVE, clean_description, figure_text, find_caption, is_candidate
from pilot.pipeline import format_sources
from pilot.registry import BY_ID
from pilot.retrieve import Hit
from pilot.verify import verify

W, H = 612.0, 792.0


def el(text="", page=1, label="picture", box=(100.0, 200.0, 400.0, 450.0), eid=None):
    b = {"page": page, "bbox_tl": list(box), "page_w": W, "page_h": H}
    return {"id": eid or f"e{page}_{box[1]}", "label": label, "text": text, "page": page,
            "bbox_tl": list(box), "page_w": W, "page_h": H, "pages": [page], "boxes": [b]}


# --- aday seçimi ----------------------------------------------------------------------

def test_large_picture_is_candidate():
    assert is_candidate(el())


@pytest.mark.parametrize("box", [(60, 200, 85, 224),       # uyarı ikonu
                                 (50, 400, 560, 430)])     # ince şerit
def test_icons_and_strips_are_not_candidates(box):
    assert not is_candidate(el(box=box))


def test_non_picture_is_not_candidate():
    assert not is_candidate(el("Body", label="text"))


# --- başlık ---------------------------------------------------------------------------

def test_caption_just_below_is_found():
    fig = el()
    cap = el("Figure 3. Pocket placement", label="caption", box=(110, 460, 380, 475))
    assert find_caption(fig, [fig, cap]) == "Figure 3. Pocket placement"


def test_caption_above_is_found_and_nearest_wins():
    fig = el()
    near = el("Figure 1. Near", label="caption", box=(110, 180, 380, 195))
    far = el("Figure 9. Far", label="caption", box=(110, 470, 380, 485))
    assert find_caption(fig, [fig, far, near]) == "Figure 1. Near"


@pytest.mark.parametrize("cap", [el("Figure 2. Other page", label="caption", page=2, box=(110, 460, 380, 475)),
                                 el("Figure 2. Too far", label="caption", box=(110, 520, 380, 535)),
                                 el("Figure 2. Side column", label="caption", box=(420, 460, 560, 475))])
def test_unrelated_captions_are_ignored(cap):
    fig = el()
    assert find_caption(fig, [fig, cap]) == ""


# --- açıklama temizliği ---------------------------------------------------------------

def test_decorative_answer_is_recognized():
    assert clean_description("DECORATIVE.") == DECORATIVE
    assert clean_description("  decorative ") == DECORATIVE


def test_logo_description_counts_as_decorative():
    assert clean_description("The figure shows a logo for \"Team Soldier Certified Gear\".") == DECORATIVE
    keep = "The figure shows a jacket front with the position of the logo patch."
    assert clean_description(keep) == keep


def test_foreign_script_sentences_are_dropped_and_spaces_collapsed():
    raw = "The bobbin case is\n inserted into the hook.  它被插入。 The latch faces up."
    assert clean_description(raw) == "The bobbin case is inserted into the hook. The latch faces up."
    assert clean_description("Turn the dial 1.5 turns.") == "Turn the dial 1.5 turns."


# --- şekil parçası --------------------------------------------------------------------

FIG = {"page": 1, "hash": "h", "caption": "Figure 3. Pocket placement", "labels": "Pocket flap",
       "desc": "A jacket front with the pocket flap aligned to the seam."}


@pytest.fixture
def no_pdf(monkeypatch):
    monkeypatch.setattr(chunk_mod, "printed_page_labels", lambda path, pages: {p: str(p) for p in pages})


def test_described_picture_becomes_figure_chunk_at_the_end(no_pdf):
    meta = BY_ID["gl-pd-14-04a"]
    els = [el("3.5 Pockets", label="section_header", box=(50, 100, 560, 120)),
           el("Pocket text before.", label="text", box=(50, 130, 560, 150)),
           el(eid="pic1"),
           el("Pocket text after.", label="text", box=(50, 500, 560, 520))]
    plain = build_chunks(meta, els)
    chunks = build_chunks(meta, els, {"pic1": FIG})
    assert [c.chunk_type for c in chunks] == ["text", "figure"]
    # metin akışı şekille bölünmez, metin parçalarının kimlikleri değişmez
    assert [(c.chunk_id, c.text) for c in chunks[:1]] == [(c.chunk_id, c.text) for c in plain]
    fig = chunks[1]
    assert fig.section == "3.5 Pockets"
    assert fig.boxes[0]["bbox_tl"] == [100.0, 200.0, 400.0, 450.0]
    assert fig.text.startswith("Şekil başlığı: Figure 3. Pocket placement\nŞekildeki yazılar: Pocket flap\n")
    assert AUTO_PREFIX in fig.text and fig.generated == FIG["desc"]
    assert "pocket flap aligned" in fig.embed_text


def test_decorative_and_undescribed_pictures_are_skipped(no_pdf):
    meta = BY_ID["gl-pd-14-04a"]
    els = [el(eid="logo"), el(eid="new", box=(100, 500, 400, 700))]
    assert build_chunks(meta, els, {"logo": {**FIG, "desc": DECORATIVE}}) == []


def test_figure_text_without_caption_or_labels_is_only_description():
    assert figure_text({**FIG, "caption": "", "labels": ""}) == f"{AUTO_PREFIX} {FIG['desc']}"


def test_figure_source_is_marked_for_the_model():
    chunk = {"doc_id": "gl-pd-14-04a", "brand": "US Army (GL-PD)", "product": "Ceket", "lang": "en",
             "doc_type": "product_standard", "section": "3.5 Pockets", "chunk_type": "figure", "text": figure_text(FIG)}
    out = format_sources([Hit(chunk, 0, 1.0)])
    assert 'parça="şekil"' in out and AUTO_PREFIX in out


# --- doğrulama ------------------------------------------------------------------------

def answer(quote):
    return {"bulunamadi": False, "alintilar": [{"kaynak_no": 1, "metin": quote}],
            "cevap": "Şekle göre cep kapağı dikişe hizalanır [1].", "sesli_metin": "Cep kapağı dikişe hizalanır.",
            "netlestirme_sorusu": None, "celiski_var": False}


def test_quote_from_generated_description_is_only_partial():
    v = verify(answer("pocket flap aligned to the seam"), {1: figure_text(FIG)}, {1: FIG["desc"]})
    assert v.status == "partial"
    assert v.checks["alinti_kaynak_metni"] is False
    assert any("otomatik açıklamasından" in p for p in v.problems)


def test_quote_from_caption_of_figure_is_verified():
    v = verify(answer("Pocket placement"), {1: figure_text(FIG)}, {1: FIG["desc"]})
    assert v.status == "verified" and v.checks["alinti_kaynak_metni"] is True


def test_text_sources_without_generated_part_are_unchanged():
    v = verify(answer("pocket flap aligned to the seam"), {1: "The pocket flap aligned to the seam."})
    assert v.status == "verified"


# --- doküman: önbellek ve yeniden kullanım --------------------------------------------

class _Closable:
    def close(self):
        pass

    def __getitem__(self, i):
        return None


def test_same_image_is_described_once_and_rerun_reuses_results(monkeypatch, tmp_path):
    monkeypatch.setattr(figures, "FIGURES_DIR", tmp_path)
    monkeypatch.setattr(figures.pdfium, "PdfDocument", lambda path: _Closable())
    monkeypatch.setattr(figures.pymupdf, "open", lambda path: _Closable())
    monkeypatch.setattr(figures, "crop_png", lambda pdf, e: b"same-image" if e["page"] < 3 else b"other")
    monkeypatch.setattr(figures, "figure_labels", lambda page, box: "")
    seen = []

    def fake_describe(png, **ctx):
        seen.append(ctx["section"])
        return f"desc of {png.decode()}"

    monkeypatch.setattr(figures, "describe", fake_describe)
    meta = BY_ID["brother-s7300a"]
    els = [el("Bobbin", label="section_header", box=(50, 50, 560, 70)),
           el(eid="a", page=1), el(eid="b", page=2), el(eid="c", page=3), el(eid="icon", page=3, box=(60, 60, 85, 85))]
    res = figures.describe_document(meta, els)
    assert seen == ["Bobbin", "Bobbin"]                        # a ve b aynı görsel: tek çağrı
    assert set(res["figures"]) == {"a", "b", "c"}               # ikon aday değil
    assert res["figures"]["b"]["desc"] == "desc of same-image"
    saved = json.loads((tmp_path / "brother-s7300a.json").read_text(encoding="utf-8"))
    assert saved["figures"] == res["figures"]

    seen.clear()
    figures.describe_document(meta, els)
    assert seen == []                                          # ikinci çalıştırma: VLM çağrılmaz
    figures.describe_document(BY_ID["brother-s7300b"], els[:2])
    assert seen == []                                          # başka doküman, aynı görsel: yeniden kullanılır


def test_limit_stops_new_calls(monkeypatch, tmp_path):
    monkeypatch.setattr(figures, "FIGURES_DIR", tmp_path)
    monkeypatch.setattr(figures.pdfium, "PdfDocument", lambda path: _Closable())
    monkeypatch.setattr(figures.pymupdf, "open", lambda path: _Closable())
    monkeypatch.setattr(figures, "crop_png", lambda pdf, e: e["id"].encode())
    monkeypatch.setattr(figures, "figure_labels", lambda page, box: "")
    monkeypatch.setattr(figures, "describe", lambda png, **ctx: "x")
    res = figures.describe_document(BY_ID["brother-s7300a"], [el(eid=f"f{i}", page=i + 1) for i in range(4)], limit=2)
    assert len(res["figures"]) == 2
