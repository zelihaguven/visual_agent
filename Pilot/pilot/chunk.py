"""Öğeler -> arama parçaları (chunk). Başlık sınırını aşmaz, sayfa ve bbox listesini korur.

Parça türleri:
  text       ardışık paragraf/liste öğeleri, CHUNK_MAX_CHARS'a kadar
  table_row  tablonun mantıksal satırı ("Başlık: değer | ...")
  table      satırlarına ayrılamayan tablo (markdown)
  figure     VLM ile açıklanmış şekil (figures.py): başlık + şekildeki yazılar + otomatik açıklama
"""
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from difflib import SequenceMatcher

from .config import CHUNK_MAX_CHARS, CHUNKS_PATH
from .figures import figure_text, is_described
from .parse import (_norm_repeating, furniture_keys, in_edge_band, is_letter_spaced, merge_cross_page,
                    printed_page_labels, remove_furniture)
from .registry import DocMeta

HEADING_LABELS = ("section_header", "title")
SKIP_LABELS = ("picture", "figure", "page_header", "page_footer")
MIN_CHARS = 3
MAX_SECTION_CHARS = 80
MAX_TABLE_SECTION_CHARS = 160

# --- Bölüm adı kuralları (yalnız section ve embed_text'i değiştirir; parça sınırları aynı) ---------------------------
# Kural 1: başlık etiketli öğe şu durumlarda bölüm adı olmaz, önceki bölüm sürer: OCR çöpü ("c: o o", Granovsky'de
# 273 parçanın bölümüydü), uyarı etiketi ("NOTE:", "CAUTION" — onlarca sayfaya taşınıyordu), sayfa üst bilgisinin
# ayıklamadan kaçan OCR varyantı ("OLlPD 07-14A"; sayfa kenarında ve bir üst bilgiye çok benzer).
ADMONITION = re.compile(
    r"^(notes?|caution|warning|danger|important|attention|notice|remarque|avertissement|pr[ée]caution|mise en garde|"
    r"nota|advertencia|precauci[óo]n|peligro|aviso|hinweis|achtung|warnung|vorsicht|gefahr|"
    r"not|uyar[ıi]|dikkat|tehlike|[öo]nemli)\s*[:!.]*$", re.I)
HEADER_SIMILARITY = 0.8


def is_ocr_junk(text: str) -> bool:
    """Baştaki numara atılınca 3+ harfli kelime yoksa ya da kelimeler metnin %40'ından azını tutuyorsa."""
    body = re.sub(r"^[\d.\s]+", "", text.strip())
    words = re.findall(r"[^\W\d_]{3,}", body)
    return bool(text.strip()) and (not words or sum(map(len, words)) / max(len(body), 1) < 0.4)


def heading_rejected(e: dict[str, Any], furniture: set[str]) -> str:
    """Kural 1: '' (bölüm adı olabilir) | 'ocr' | 'uyari' | 'ust_bilgi'."""
    t = e["text"].strip()
    if is_ocr_junk(t):
        return "ocr"
    if ADMONITION.match(t):
        return "uyari"
    if in_edge_band(e) and any(SequenceMatcher(None, _norm_repeating(t), k).ratio() >= HEADER_SIMILARITY
                               for k in furniture):
        return "ust_bilgi"
    return ""


# Kural 2: tablo satırları tablonun adını taşır ("TABLE V. Seam and stitch types"). Ad tablonun hemen üstünde ya da
# altında olabilir (GL-PD şartnamelerinde çoğunlukla altta); iki tablonun arasındaki ad, dokümanda tek anlamlı
# konumların çoğunluğuna göre bağlanır. "- Continued" ekleri atılır.
TABLE_CAPTION = re.compile(r"^\s*(TABLE|Table|TABLO|Tablo|TABLEAU|Tableau|TABLA|Tabla)\s+[IVXLC0-9]+[A-Za-z]?\b")
TABLE_LABELS = ("table", "table_row")


def _caption_text(t: str) -> str:
    first = t.strip().split("\n")[0]
    first = re.sub(r"\s*[-–]\s*Contin\w*.*$", "", first, flags=re.I)
    return first.strip()[:MAX_SECTION_CHARS]


def table_captions(elements: list[dict[str, Any]]) -> dict[int, str]:
    """Tablo öğesinin dizini → tablo adı."""
    is_cap = [e["label"] not in TABLE_LABELS and bool(TABLE_CAPTION.match(e["text"])) for e in elements]
    runs, i = [], 0
    while i < len(elements):
        if elements[i]["label"] in TABLE_LABELS:
            j = i
            while j + 1 < len(elements) and elements[j + 1]["label"] in TABLE_LABELS:
                j += 1
            runs.append((i, j))
            i = j + 1
        else:
            i += 1
    is_table = lambda k: 0 <= k < len(elements) and elements[k]["label"] in TABLE_LABELS
    below = {(i, j): j + 1 for i, j in runs if j + 1 < len(elements) and is_cap[j + 1]}
    above = {(i, j): i - 1 for i, j in runs if i - 1 >= 0 and is_cap[i - 1]}
    shared = lambda k: is_table(k - 1) and is_table(k + 1)          # iki tablonun arasındaki ad
    prefer_below = sum(not shared(k) for k in below.values()) >= sum(not shared(k) for k in above.values())
    out = {}
    for run in runs:
        first, second = (below, above) if prefer_below else (above, below)
        k = first.get(run)
        if k is None and run in second and not shared(second[run]):   # paylaşılan ad tercih edilen tabloya aittir
            k = second[run]
        if k is not None:
            for x in range(run[0], run[1] + 1):
                out[x] = _caption_text(elements[k]["text"])
    return out


# Kural 3: adı bilinen tabloda, en az üç düzeyli numaralı alt başlığın (3.11.1.1) kapsamı biter; satırlar o başlığın
# en yakın üst maddesine bağlanır ("3.11.1 Seams and stitching > TABLE V. ..."). Adı bilinmeyen tabloda bölüm aynı.
NUMBERED = re.compile(r"^(\d{1,2}(?:\.\d{1,2})+)\.?\s")


def parent_section(section: str, numbered: dict[str, str]) -> str:
    m = NUMBERED.match(section)
    if not m or m.group(1).count(".") < 2:
        return section
    parts = m.group(1).split(".")
    for n in range(len(parts) - 1, 0, -1):
        key = ".".join(parts[:n])
        if key in numbered:
            return numbered[key]
    return section


# Kural 4: bölüm adı boş kalan parça, PDF yer imlerinden (outline) sayfasına düşen son başlığı alır. Yer imleri
# OCR'dan üretilmişse (Granovsky: "ag xi", "(4).") kullanılmaz: başlıkların en az %80'i Kural 1'den geçmeli.
OUTLINE_MIN_VALID = 0.8


def pdf_outline(path: Path) -> list[tuple[int, str]]:
    """(sayfa, başlık) listesi, sayfaya göre sıralı; yer imi yoksa ya da güvenilmezse boş."""
    try:
        import pymupdf
        return clean_outline(pymupdf.open(path).get_toc())
    except Exception:
        return []


def clean_outline(toc: list[list[Any]]) -> list[tuple[int, str]]:
    entries = [(p, " ".join(t.split())[:MAX_SECTION_CHARS]) for _, t, p in toc if p >= 1]
    valid = [(p, t) for p, t in entries if t and not is_ocr_junk(t) and not ADMONITION.match(t)]
    if len(entries) < 3 or len(valid) < OUTLINE_MIN_VALID * len(entries):
        return []
    return sorted(valid, key=lambda x: x[0])


def outline_section(outline: list[tuple[int, str]], page: int) -> str:
    sec = ""
    for p, t in outline:
        if p > page:
            break
        sec = t
    return sec

# Paragraf içi numaralı başlık ("3.7.1 Fastener tape (hook and loop). All widths ..."): Docling bunları başlık değil
# metin olarak etiketliyor; önceki başlık sonraki bölümlerin parçalarına taşınıyordu (ceket şartnamesi s.9-11,
# "3.5.1 Slide fasteners"). En az iki düzeyli numara: "1. Gücü kapatın" gibi adım listeleri başlık sayılmaz. Başlık
# büyük harfle başlar ve kısa bir cümleyle noktada biter ("3.5 mm thread" başlık değil).
RUN_IN_HEADING = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){1,4})\.?\s+([A-Z][^.\n]{1,70}?)\.(?:\s|$)")

# Gezinme sayfaları: içindekiler, dizin, ön sayfa (künye, telif). Hiçbir soruya cevap değiller ama sorunun terimlerini
# içerdikleri için aday listesinde yer kaplıyorlar (BENCHMARK-RAPORU Aşama 2.5). Parça 'nav' alanıyla işaretlenir,
# arama onları Qdrant filtresinde dışarıda tutar. Biçim kuralları; dokümana özgü değil.
_TOC_ENTRY = re.compile(r"(?:^|\s)(?:Chapter\s+)?\d{1,2}(?:[.\-]\d{1,2})*\.?\s+[A-Z][^.\n]{3,90}?\s\.*\s*\d{1,3}(?=\s|$)")
_TITLE_PAGE = re.compile(r"([A-Z][A-Za-z ,'&\-()]{2,80}?)\s(\d{1,3})(?=\s|$)")
_INDEX_ENTRY = re.compile(r"[A-Za-z][A-Za-z\-' ]{1,40},\s*\d{1,3}(?:\s*[-–]\s*\d{1,3})?(?:,\s*\d{1,3})*(?=\s|$|[;.])")
_FRONT = re.compile(r"©|\b(?:first published|copyright|isbn|translated from|printed in|all rights reserved|"
                    r"registered trademark|edition)\b", re.I)
FRONT_MATTER_PAGES = 6


def _dot_leader_toc(text: str) -> bool:
    from .retrieve import is_toc
    return is_toc(text)


def nav_kind(text: str, page: int) -> str:
    """'toc' | 'index' | 'front_matter' | '' (içerik)."""
    t = " ".join(text.split())
    if _dot_leader_toc(t):
        return "toc"
    toc = _TOC_ENTRY.findall(t)
    if len(toc) >= 3 and sum(map(len, toc)) >= 0.6 * len(t):
        return "toc"
    entries = _TITLE_PAGE.findall(t)
    nums = [int(n) for _, n in entries]
    rising = sum(b >= a for a, b in zip(nums, nums[1:]))
    covered = sum(len(a) + len(n) + 1 for a, n in entries)
    if len(entries) >= 5 and rising >= 0.8 * (len(nums) - 1) and covered >= 0.7 * len(t):
        return "toc"            # numarasız içindekiler: başlık + artan sayfa numarası
    idx = _INDEX_ENTRY.findall(t)
    if len(idx) >= 6 and sum(map(len, idx)) >= 0.5 * len(t):
        return "index"
    if page <= FRONT_MATTER_PAGES and len({m.lower() for m in _FRONT.findall(t)}) >= 2:
        return "front_matter"
    return ""


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    brand: str
    product: str
    doc_type: str
    lang: str
    chunk_type: str
    section: str
    page: int
    pages: list[int]
    page_labels: dict[str, str | None]
    boxes: list[dict[str, Any]]
    text: str
    embed_text: str = field(default="")
    generated: str = field(default="")   # metnin model üretimi kısmı (şekil açıklaması): doğrulamada kaynak sayılmaz
    nav: str = field(default="")         # gezinme parçası: toc | index | front_matter (aramada dışarıda tutulur)


def _embed_text(meta: DocMeta, section: str, text: str) -> str:
    head = f"{meta.brand} {meta.product}"
    return f"{head} | {section}\n{text}" if section else f"{head}\n{text}"


def _split_long(el: dict[str, Any]) -> list[dict[str, Any]]:
    """CHUNK_MAX_CHARS'tan uzun tek paragrafı cümle sınırından böl. Kutular aynı kalır."""
    text = el["text"].strip()
    if len(text) <= CHUNK_MAX_CHARS:
        return [el]
    sentences = re.split(r"(?<=[.!?;])\s+(?=[A-Z0-9(])", text)
    parts: list[str] = []
    cur = ""
    for s in sentences:
        if cur and len(cur) + len(s) + 1 > CHUNK_MAX_CHARS:
            parts.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        parts.append(cur)
    return [{**el, "text": part} for part in parts]


def build_chunks(meta: DocMeta, elements: list[dict[str, Any]],
                 figures: dict[str, dict[str, Any]] | None = None) -> list[Chunk]:
    """Bir dokümanın parse edilmiş öğelerinden parçalar üret. figures: figures.load_figures() çıktısı.
    Şekil parçaları sona eklenir: Metin akışını bölmezler, metin parçalarının kimlikleri değişmez."""
    furniture = furniture_keys(elements)
    elements = merge_cross_page(remove_furniture(elements))
    pages = sorted({p for e in elements for p in e["pages"]})
    labels = printed_page_labels(meta.path, pages)
    captions = table_captions(elements)
    outline = pdf_outline(meta.path)

    chunks: list[Chunk] = []
    section = ""
    numbered: dict[str, str] = {}          # görülen numaralı başlıklar: "3.11.1" → "3.11.1 Seams and stitching"
    buf: list[dict[str, Any]] = []
    figure_els: list[tuple[str, dict[str, Any]]] = []

    def set_section(s: str) -> None:
        nonlocal section
        section = s
        m = NUMBERED.match(s)
        if m:
            numbered[m.group(1)] = s

    def make(chunk_type: str, text: str, els: list[dict[str, Any]], sec: str | None = None,
             generated: str = "", caption: str = "") -> None:
        sec = section if sec is None else sec
        if caption and caption not in sec:
            sec = f"{parent_section(sec, numbered)} > {caption}"[:MAX_TABLE_SECTION_CHARS] if sec else caption
        text = text.strip()
        if len(text) < MIN_CHARS:
            return
        boxes = [b for e in els for b in e["boxes"]]
        pgs = sorted({b["page"] for b in boxes})
        if not sec and outline:
            sec = outline_section(outline, pgs[0])
        chunks.append(Chunk(
            chunk_id=f"{meta.doc_id}-{len(chunks):05d}", doc_id=meta.doc_id, brand=meta.brand,
            product=meta.product, doc_type=meta.doc_type, lang=meta.lang_of(pgs[0]),
            chunk_type=chunk_type, section=sec, page=pgs[0], pages=pgs,
            page_labels={str(p): labels.get(p) for p in pgs}, boxes=boxes, text=text,
            embed_text=_embed_text(meta, sec, text), generated=generated,
            nav=nav_kind(text, pgs[0]) if chunk_type == "text" else ""))

    def flush() -> None:
        nonlocal buf
        if buf:
            make("text", " ".join(e["text"].strip() for e in buf), buf)
            buf = []

    for idx, e in enumerate(elements):
        label = e["label"]
        if label == "picture" and is_described((figures or {}).get(e["id"])):
            figure_els.append((section, e))
            continue
        if label in SKIP_LABELS:
            continue
        if label in HEADING_LABELS:
            flush()
            # Harf aralıklı başlık ("R e p a i r a n d A d j u s t m e n t"): kelime sınırları kayıp, bölüm adı
            # olamaz. Granovsky'de kitap adı bütün kitabın bölüm adı olmuştu (685 parça). Önceki bölüm sürer.
            # Kural 1 (OCR çöpü, uyarı etiketi, üst bilgi) de aynı: parça yine burada kapanır, yalnız ad değişmez.
            if not is_letter_spaced(e["text"], min_tokens=4) and not heading_rejected(e, furniture):
                set_section(e["text"].strip()[:MAX_SECTION_CHARS])
            continue
        if label == "table":
            flush()
            if not e.get("has_rows"):
                make("table", e["text"], [e], caption=captions.get(idx, ""))
            continue
        if label == "table_row":
            flush()
            make("table_row", e["text"], [e], caption=captions.get(idx, ""))
            continue
        # metin/liste/dipnot/başlık dışı her şey paragraf gibi biriktirilir
        if not e["text"].strip():
            continue
        for piece in _split_long(e):
            run_in = RUN_IN_HEADING.match(piece["text"].strip())
            if run_in:
                flush()
                set_section(f"{run_in.group(1)} {run_in.group(2)}"[:MAX_SECTION_CHARS])
            size = sum(len(x["text"]) for x in buf) + len(piece["text"])
            lang_changes = bool(buf) and meta.lang_of(piece["page"]) != meta.lang_of(buf[0]["page"])
            if buf and (size > CHUNK_MAX_CHARS or lang_changes):
                flush()
            buf.append(piece)
    flush()
    for sec, e in figure_els:
        fig = figures[e["id"]]
        make("figure", figure_text(fig), [e], sec=sec, generated=fig["desc"])
    return chunks


def write_chunks(chunks: list[Chunk], path: Path = CHUNKS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")


def read_chunks(path: Path = CHUNKS_PATH) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
