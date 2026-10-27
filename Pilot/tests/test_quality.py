"""Aşama 2.5 veri kalitesi: genel kurallar (dokümana özgü değil). PDF ve model gerektirmez.

- Paragraf içi numaralı başlık yeni bölüm başlatır; adım listesi ve ölçüler başlık sayılmaz
- Harf aralıklı başlık bölüm adı olmaz
- İçindekiler, dizin, ön sayfa işaretlenir (nav) ve aramada dışarıda kalır
- OCR farklı yazımlı üst bilgi ayıklanır
- Sorudaki kaynak ifadesi aramadan çıkar
- RRF eşitlikleri belirli bir sırayla bozulur (gömülü ve sunucu modu aynı sırayı verir)
"""
import random
from types import SimpleNamespace

import pytest
from qdrant_client import QdrantClient, models

from pilot import retrieve
from pilot.chunk import RUN_IN_HEADING, build_chunks, nav_kind
from pilot.index import collection_schema
from pilot.parse import remove_furniture
from pilot.query import strip_source_phrases
from pilot.registry import BY_ID

META = BY_ID["gl-pd-14-04a"]
W, H = 612.0, 792.0


def el(text, page=1, label="text", top=300.0):
    box = {"page": page, "bbox_tl": [50.0, top, 560.0, top + 20], "page_w": W, "page_h": H}
    return {"id": f"e{page}_{top}", "label": label, "text": text, "page": page, "bbox_tl": box["bbox_tl"],
            "page_w": W, "page_h": H, "pages": [page], "boxes": [box]}


@pytest.fixture(autouse=True)
def no_pdf(monkeypatch):
    """build_chunks basılı sayfa numarası için PDF'i açar; testte PDF yok."""
    from pilot import chunk
    monkeypatch.setattr(chunk, "printed_page_labels", lambda path, pages: {p: None for p in pages})


# ---------- bölüm başlığı ----------

@pytest.mark.parametrize("text,heading", [
    ("3.7.1 Fastener tape (hook and loop). All widths of hook and loop tape shall be sewn", "3.7.1 Fastener tape (hook and loop)"),
    ("3.6 Design. The coat design for Style A-Unisex", "3.6 Design"),
    ("3.7.4.3 Eyelets. The sewn-in eyelets", "3.7.4.3 Eyelets"),
])
def test_run_in_numbered_heading(text, heading):
    m = RUN_IN_HEADING.match(text)
    assert m and f"{m.group(1)} {m.group(2)}" == heading


@pytest.mark.parametrize("text", [
    "1. Turn off the power switch. Then remove the needle.",      # adım listesi: tek düzeyli numara
    "3.5 mm thread is used for the hem.",                         # ölçü: küçük harfle devam
    "2.5 Adjust the tension until the stitch is balanced and the thread lies flat on both sides of the fabric "
    "without puckering or looping anywhere along the seam line.",  # başlık için fazla uzun cümle
    "12 Thread tension spring",                                   # noktasız, tek sayı
])
def test_not_run_in_heading(text):
    assert not RUN_IN_HEADING.match(text)


def test_run_in_heading_starts_new_section_and_chunk():
    els = [el("3.5.1 Slide fasteners", label="section_header", top=100),
           el("The slide fastener shall be size 5.", top=150),
           el("3.7.1 Fastener tape (hook and loop). Sewn 1/8-inch from edge.", top=200)]
    chunks = build_chunks(META, els)
    assert [c.section for c in chunks] == ["3.5.1 Slide fasteners", "3.7.1 Fastener tape (hook and loop)"]
    assert "Sewn 1/8-inch" in chunks[1].text and "Sewn" not in chunks[0].text


def test_letter_spaced_heading_is_not_a_section():
    els = [el("Real heading", label="section_header", top=100),
           el("R e p a i r a n d A d j u s t m e n t", label="section_header", top=150),
           el("Body text after the running title.", top=200)]
    chunks = build_chunks(META, els)
    assert chunks[0].section == "Real heading"
    assert "R e p a i r" not in chunks[0].embed_text


# ---------- gezinme parçaları ----------

@pytest.mark.parametrize("text,page,kind", [
    ("1. Longevity and Reliability of Machines 9 2. Wear of Machine Parts and Improvement of Their Resistance 11 "
     "3. Main Factors Influencing the Wear 13 4. Lubrication 17", 5, "toc"),
    ("Fabrics of Wool or Worsted 3 Materials Used in the Making of Suit or Coat 4 Shrinking 5 Laboratory Equipment "
     "and Tools 6 Directions for Cutting 9 Pressing 12", 9, "toc"),                                  # numarasız
    ("5-5-1. Needle up/down ........ 32 5-5-2. Thread trimming lock ........ 32", 10, "toc"),       # noktalı
    ("card, 252 comb, 255 fitting, 251 healds and reed, 261 fluted rollers, 256 loom units, 260 roller covering, 257 "
     "slay and shuttle, 261", 270, "index"),
    ("© Gertrude Strickland 1956 Published simultaneously in Canada. All rights reserved. No part of this book may "
     "be reproduced.", 6, "front_matter"),
])
def test_navigation_pages_detected(text, page, kind):
    assert nav_kind(text, page) == kind


@pytest.mark.parametrize("text,page", [
    ("3.7.1 Fastener tape (hook and loop). All widths of hook and loop tape shall be sewn 1/8-inch to 3/16-inch "
     "from bound selvage.", 10),
    ("Type I - 50/50 Nylon/Cotton Ripstop Type II - 65/25/10 Rayon/Para-Aramid/Nylon Ripstop Flame Resistant", 1),
    ("Size: X-Short | 30: 24-7/8 | 33: 25-3/8 | 36: 25-7/8 | 39: 26-3/8", 49),
    ("The process of part wear in time is irregular (Fig. 2). During the initial period I of machine operation, "
     "when new parts are run-in, there is a stronger wear; further, comes the period II.", 12),
    ("This edition of the manual covers models 6804 and 6814. Copyright notices are on the last page.", 40),   # geç sayfa
    ("1. Name the different kinds of machining carried out in repair of parts. 2. What is the meaning of transfer "
     "of part sizes into repair sizes?", 44),
])
def test_content_not_flagged_as_navigation(text, page):
    assert nav_kind(text, page) == ""


def test_only_text_chunks_get_nav():
    els = [el("1. Wear 9 2. Lubrication 11 3. Repair 13 4. Assembly 17 5. Testing 21", top=100),
           el("Seam | SPI 9 | 11 | 13 | 17", label="table_row", top=200)]
    chunks = build_chunks(META, els)
    assert [(c.chunk_type, c.nav) for c in chunks] == [("text", "toc"), ("table_row", "")]


# ---------- üst bilgi ----------

def test_running_header_with_ocr_variants_is_removed():
    variants = ["GLlPD 07-14A", "GLIPD 07-14A", "GLlPD 07-l4A", "GL/PD 07-14A"]
    els = [el(variants[p % 4], page=p, top=20.0) for p in range(1, 9)]
    els += [el(f"Body text {p}", page=p, top=300.0) for p in range(1, 9)]
    kept = remove_furniture(els)
    assert [e["text"] for e in kept] == [f"Body text {p}" for p in range(1, 9)]


# ---------- kaynak ifadesi ----------

@pytest.mark.parametrize("q,aliases,expected", [
    ("Granovsky kitabına göre makine parçalarının aşınması hangi aşamalardan geçer?", ["Granovsky"],
     "makine parçalarının aşınması hangi aşamalardan geçer?"),
    ("Granovsky'ye göre iğne şeridi nasıl değiştirilir?", ["Granovsky"], "iğne şeridi nasıl değiştirilir?"),
    ("S-7300A kılavuzunda iplik gerginliği nasıl ayarlanır?", ["S-7300A"], "iplik gerginliği nasıl ayarlanır?"),
    ("Kılavuza göre iğne nasıl değiştirilir?", [], "iğne nasıl değiştirilir?"),
    ("According to the Granovsky book, how are flats repaired?", ["Granovsky"], "how are flats repaired?"),
])
def test_source_phrase_removed(q, aliases, expected):
    assert strip_source_phrases(q, aliases) == expected


@pytest.mark.parametrize("q,aliases", [
    ("S-7300A'da E050 hatası ne demek?", ["S-7300A"]),            # varlık sorunun parçası
    ("Ceketin dış dikişlerinde SPI kaç olmalı?", ["ceket"]),
    ("Kılavuz pimi nasıl sökülür?", []),                           # 'kılavuz' parça adı, göre yok
])
def test_question_without_source_phrase_unchanged(q, aliases):
    assert strip_source_phrases(q, aliases) == q


# ---------- RRF: belirli sıra ----------

def P(pid, score):
    return SimpleNamespace(id=pid, score=score, payload={"text": str(pid)})


def test_rrf_scores_match_qdrant_formula_and_break_ties():
    dense = [P(1, 0.9), P(2, 0.8), P(3, 0.7)]
    sparse = [P(2, 5.0), P(1, 4.0), P(4, 3.0)]
    out = retrieve.rrf_fuse(dense, sparse, 10)
    # 1 ve 2 aynı füzyon skoru (1/2 + 1/3): dense skoru yüksek olan (1) önce
    assert [p.id for p, _ in out] == [1, 2, 3, 4]
    assert out[0][1] == pytest.approx(1 / 2 + 1 / 3) and out[1][1] == pytest.approx(1 / 3 + 1 / 2)
    # 3 (yalnız dense, 3. sıra) ve 4 (yalnız sparse, 3. sıra) eşit: dense kolda olan önce
    assert out[2][1] == out[3][1] == pytest.approx(1 / 4)


def test_rrf_equal_scores_fall_back_to_id():
    out = retrieve.rrf_fuse([], [P(9, 1.0), P(3, 1.0)], 10)
    assert [p.id for p, _ in out] == [9, 3]           # farklı sıra: 1/2 > 1/3
    out = retrieve.rrf_fuse([P(9, 0.5)], [P(3, 1.0)], 10)
    assert [p.id for p, _ in out] == [9, 3]           # aynı füzyon skoru, dense skoru olan önce


def test_order_independent_of_tie_order_inside_arms():
    """Gömülü ve sunucu modu eşit skorlu sonuçları farklı sırada döndürüyordu. canonical + rrf_fuse sonrası sıra yalnız
    skor değerlerine bağlı: kolların içindeki eşitler karıştırılsa da sonuç aynı."""
    rnd = random.Random(1)
    dense = [P(i, round(rnd.random(), 1)) for i in range(40)]           # çok eşitlik
    sparse = [P(i + 20, round(rnd.random() * 3, 0)) for i in range(40)]
    ref = None
    for _ in range(30):
        d, s = dense[:], sparse[:]
        rnd.shuffle(d)
        rnd.shuffle(s)
        out = [p.id for p, _ in retrieve.rrf_fuse(retrieve.canonical(d, 30), retrieve.canonical(s, 30), 20)]
        ref = ref or out
        assert out == ref


def test_search_excludes_navigation_chunks(monkeypatch):
    c = QdrantClient(":memory:")
    c.create_collection(retrieve.COLLECTION, **collection_schema(4))
    pts = []
    for i in range(30):
        nav = "toc" if i % 3 == 0 else ""
        pts.append(models.PointStruct(id=i, vector={"dense": [1.0, 0.1 * i, 0.0, 0.5],
                                                    "sparse": models.SparseVector(indices=[1], values=[1.0 + i])},
                                      payload={"doc_id": "d", "text": f"t{i}", "pages": [1], "nav": nav}))
    pts.append(models.PointStruct(id=99, vector={"dense": [1.0, 0.0, 0.0, 0.5]},       # eski indeks: nav alanı yok
                                  payload={"doc_id": "d", "text": "eski", "pages": [1]}))
    c.upsert(retrieve.COLLECTION, points=pts)
    monkeypatch.setattr(retrieve, "search_client", lambda: c)
    monkeypatch.setattr(retrieve, "release", lambda _: None)
    monkeypatch.setattr(retrieve, "encode_query",
                        lambda text, sparse_text=None: {"dense": [1.0, 0.0, 0.0, 0.5], "sparse": {1: 1.0}})
    hits = retrieve.search("q", top_k=40, do_rerank=False)
    ids = {int(h.chunk["text"][1:]) if h.chunk["text"] != "eski" else 99 for h in hits}
    assert ids and not any(i % 3 == 0 for i in ids if i != 99)
    assert 99 in ids
