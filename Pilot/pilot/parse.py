"""PDF -> öğe listesi (Docling, OCR kapalı: PDF'in kendi metin katmanı kullanılır).

Her öğe: id, label, text, page, bbox_tl [l,t,r,b] (sol-üst orijin, point), page_w, page_h, pages, boxes.
Faz 1 denemesindeki (calisma-notlari/faz1-test/faz1-test.py) üst/alt bilgi ayıklama, tablo satırı ve
sayfa geçişi birleştirme mantığının pilot sürümü.
"""
import json
import logging
import re
import time
from pathlib import Path
from typing import Any

import pymupdf
import pypdfium2 as pdfium

from .config import DOCLING_DEVICE, EDGE_BAND, FURNITURE_MIN_RATIO, PAGES_PER_BATCH, PARSED_DIR, SENTENCE_END
from .registry import DocMeta
from .tables import SPAN_SEP

log = logging.getLogger(__name__)

TEXT_LABELS = ("text", "list_item", "paragraph")


# --- Docling ---------------------------------------------------------------------------

def _converter():
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    from docling.datamodel.accelerator_options import AcceleratorOptions

    opts = PdfPipelineOptions()
    opts.accelerator_options = AcceleratorOptions(device=DOCLING_DEVICE)
    opts.do_ocr = False
    opts.do_table_structure = True
    return DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)})


def _union_bbox(boxes: list[list[float]]) -> list[float]:
    return [min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes)]


def group_table_rows(cells: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Tablo hücrelerini mantıksal satırlara grupla; metin 'Başlık: değer | Başlık: değer'."""
    headers: dict[int, str] = {}
    for c in cells:
        if c["header"] and c["text"].strip():
            for col in range(c["c0"], c["c1"]):
                headers.setdefault(col, c["text"].strip())
    body = [c for c in cells if not c["header"] and c["text"].strip()]
    if not body:
        return []
    grid_rows = sorted({r for c in body for r in range(c["r0"], c["r1"])})
    groups: list[tuple[int, list[int]]] = []
    for r in grid_rows:
        covering = [i for i, c in enumerate(body) if c["r0"] <= r < c["r1"]]
        anchor = min(covering, key=lambda i: (body[i]["c0"], body[i]["r0"]))
        if groups and groups[-1][0] == anchor:
            groups[-1][1].append(r)
        else:
            groups.append((anchor, [r]))
    rows = []
    for _anchor, rs in groups:
        idx = sorted({i for i, c in enumerate(body) if any(c["r0"] <= r < c["r1"] for r in rs)},
                     key=lambda i: (body[i]["c0"], body[i]["r0"]))
        row_cells = [body[i] for i in idx]
        parts = []
        for c in row_cells:
            # Birleşik hücre kapladığı bütün sütunların ortak değeridir (JUKI s.3: hız üç modelin sütununu kaplıyor,
            # yalnız ilk sütunun başlığı yazılınca "MO-6804: 7,000" oluyordu). İlk sütundan başlayan geniş hücre
            # ara başlıktır, başlık almaz.
            heads = list(dict.fromkeys(headers[col] for col in range(c["c0"], c["c1"]) if col in headers))
            h = SPAN_SEP.join(heads) if c["c0"] > 0 or c["c1"] - c["c0"] == 1 else ""
            txt = c["text"].strip()
            parts.append(f"{h}: {txt}" if h and h != txt else txt)
        boxes = [c["bbox_tl"] for c in row_cells if c.get("bbox_tl")]
        rows.append({"text": " | ".join(parts), "bbox_tl": _union_bbox(boxes) if boxes else None})
    return rows


def _table_row_elements(item: Any, table_el: dict[str, Any]) -> list[dict[str, Any]]:
    data = getattr(item, "data", None)
    if data is None or not getattr(data, "table_cells", None):
        return []
    page_h = table_el["page_h"]
    cells = []
    for c in data.table_cells:
        bbox = None
        if c.bbox is not None:
            bb = c.bbox.to_top_left_origin(page_height=page_h)
            bbox = [bb.l, bb.t, bb.r, bb.b]
        cells.append({"r0": c.start_row_offset_idx, "r1": c.end_row_offset_idx,
                      "c0": c.start_col_offset_idx, "c1": c.end_col_offset_idx,
                      "text": c.text or "", "bbox_tl": bbox, "header": bool(c.column_header)})
    out = []
    for i, row in enumerate(group_table_rows(cells)):
        if not row["bbox_tl"]:
            continue
        box = {"page": table_el["page"], "bbox_tl": row["bbox_tl"],
               "page_w": table_el["page_w"], "page_h": page_h}
        out.append({"id": f"{table_el['id']}_r{i}", "label": "table_row", "text": row["text"],
                    "page": table_el["page"], "bbox_tl": row["bbox_tl"],
                    "page_w": table_el["page_w"], "page_h": page_h,
                    "pages": [table_el["page"]], "boxes": [box], "parent_id": table_el["id"]})
    return out


def _doc_to_elements(doc: Any, prefix: str) -> list[dict[str, Any]]:
    elements: list[dict[str, Any]] = []
    for idx, (item, _level) in enumerate(doc.iterate_items()):
        prov = getattr(item, "prov", None) or []
        if not prov:
            continue
        label = str(getattr(item, "label", "")).split(".")[-1].lower()
        if label == "table" and hasattr(item, "export_to_markdown"):
            text = item.export_to_markdown(doc=doc)
        else:
            text = getattr(item, "text", "") or ""
        boxes = []
        for p in prov:
            size = doc.pages[p.page_no].size
            bb = p.bbox.to_top_left_origin(page_height=size.height)
            boxes.append({"page": p.page_no, "bbox_tl": [bb.l, bb.t, bb.r, bb.b],
                          "page_w": size.width, "page_h": size.height})
        first = boxes[0]
        el = {"id": f"{prefix}e{idx}", "label": label, "text": text,
              "page": first["page"], "bbox_tl": first["bbox_tl"],
              "page_w": first["page_w"], "page_h": first["page_h"],
              "pages": sorted({b["page"] for b in boxes}), "boxes": boxes}
        elements.append(el)
        if label == "table":
            rows = _table_row_elements(item, el)
            el["has_rows"] = bool(rows)
            elements += rows
    return elements


def parse_pdf(meta: DocMeta) -> tuple[list[dict[str, Any]], list[int]]:
    """Dokümanı PAGES_PER_BATCH'lik aralıklarla parse et. (öğeler, başarısız sayfalar)."""
    n_pages = len(pymupdf.open(meta.path))
    conv = _converter()
    elements: list[dict[str, Any]] = []
    failed: list[int] = []
    for first in range(1, n_pages + 1, PAGES_PER_BATCH):
        last = min(first + PAGES_PER_BATCH - 1, n_pages)
        try:
            res = conv.convert(str(meta.path), page_range=(first, last))
            elements += _doc_to_elements(res.document, f"p{first}_")
        except Exception:  # noqa: BLE001 - tek bir kötü sayfa tüm dokümanı düşürmesin
            log.exception("%s s.%d-%d toplu parse başarısız, sayfa sayfa denenecek", meta.doc_id, first, last)
            for page in range(first, last + 1):
                try:
                    res = conv.convert(str(meta.path), page_range=(page, page))
                    elements += _doc_to_elements(res.document, f"p{page}_")
                except Exception:  # noqa: BLE001
                    log.exception("%s s.%d parse edilemedi", meta.doc_id, page)
                    failed.append(page)
        log.info("%s: s.%d-%d tamam (%d öğe)", meta.doc_id, first, last, len(elements))
    return elements, failed


# --- Temizlik --------------------------------------------------------------------------

def _norm_repeating(text: str) -> str:
    return re.sub(r"\d+", "#", text.strip().lower())


def remove_furniture(elements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Üst/alt bilgileri (sayfa kenarında, sayfaların çoğunda tekrar eden metin) ayıkla."""
    pages = {e["page"] for e in elements}
    seen: dict[str, set[int]] = {}
    for e in elements:
        _, t, _, b = e["bbox_tl"]
        h = e["page_h"]
        if t <= h * EDGE_BAND or b >= h * (1 - EDGE_BAND):
            seen.setdefault(_norm_repeating(e["text"]), set()).add(e["page"])
    need = max(2, int(len(pages) * FURNITURE_MIN_RATIO))
    furn = {k for k, v in seen.items() if len(v) >= need and k} if len(pages) >= 2 else set()
    return [e for e in elements
            if e["label"] not in ("page_header", "page_footer") and _norm_repeating(e["text"]) not in furn]


def _join(a: str, b: str) -> str:
    a = a.rstrip()
    if a.endswith("-") and b[:1].islower():
        return a[:-1] + b.lstrip()
    return a + " " + b.lstrip()


def _is_continuation(prev: dict[str, Any], nxt: dict[str, Any]) -> bool:
    if nxt["page"] != prev["page"] + 1:
        return False
    if prev["label"] not in TEXT_LABELS or nxt["label"] not in TEXT_LABELS:
        return False
    p, n = prev["text"].rstrip(), nxt["text"].lstrip()
    if not p or not n:
        return False
    return (not p.endswith(SENTENCE_END)) and (n[0].islower() or p.endswith("-") or p.endswith(","))


def merge_cross_page(elements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sayfa sınırında bölünmüş paragrafları birleştir (kutular iki sayfada da korunur)."""
    out: list[dict[str, Any]] = []
    for e in elements:
        if out and _is_continuation(out[-1], e):
            prev = out[-1]
            out[-1] = {**prev, "text": _join(prev["text"], e["text"]),
                       "boxes": prev["boxes"] + e["boxes"],
                       "pages": sorted(set(prev["pages"]) | set(e["pages"]))}
        else:
            out.append(e)
    return out


def printed_page_labels(pdf_path: Path, pages: list[int], bands=(0.06, 0.09, 0.12)) -> dict[int, str | None]:
    """Sayfa altındaki (yoksa üstündeki) basılı sayfa numarası. Bulunamazsa None."""
    pdf = pdfium.PdfDocument(str(pdf_path))
    labels: dict[int, str | None] = {}
    try:
        for page_no in pages:
            page = pdf[page_no - 1]
            w, h = page.get_size()
            tp = page.get_textpage()
            found = None
            for edge in ("bottom", "top"):
                for band in bands:
                    bottom, top = (0, h * band) if edge == "bottom" else (h * (1 - band), h)
                    text = tp.get_text_bounded(left=0, bottom=bottom, right=w, top=top) or ""
                    if is_letter_spaced(text, min_tokens=3):    # harf aralıklı OCR: "1 0 1" → "101"
                        text = re.sub(r"\b\d(?: \d\b)+", lambda m: m.group().replace(" ", ""), text)
                    nums = re.findall(r"(?<![\w/.-])(\d{1,4})(?![\w/.:-])", text)
                    if nums:
                        found = nums[0]
                        break
                if found:
                    break
            labels[page_no] = found
    finally:
        pdf.close()
    return labels


# --- Metin katmanı yedeği ----------------------------------------------------------------

FALLBACK_MIN_PDF_CHARS = 200     # PDF metin katmanında en az bu kadar karakter olan sayfa değerlendirilir
FALLBACK_MIN_COVERAGE = 0.5      # Docling bu orandan azını yakalamışsa sayfa PyMuPDF bloklarıyla değişir
FALLBACK_KEEP_PICTURE_MAX = 0.6  # değişen sayfada bundan küçük şekiller korunur (büyükler tam sayfa tarama görseli)


def _clean_block_text(raw: str) -> str:
    """Satır sonu tirelemesini ('de¬\nsign', 'con-\nstruction', yumuşak tire 'over\xad\ncome') birleştir,
    satır sonlarını boşluk yap."""
    text = re.sub(r"[¬\-\xad]\s*\n\s*(?=[a-z])", "", raw)
    return re.sub(r"\s*\n\s*", " ", text).strip()


# Harf aralıklı OCR katmanı: FineReader çıktısında (Granovsky 1986) her harf ayrı kelime ("C a r d f l a t").
# Kelime araması ve alıntı doğrulaması bu metinle çalışmaz. Kelimeler harflerin konumundan yeniden kurulur.

def is_letter_spaced(text: str, min_tokens: int = 20) -> bool:
    """Metnin çoğu tek harflik parçalardan oluşuyor mu?"""
    tokens = text.split()
    return len(tokens) >= min_tokens and sum(len(t) == 1 for t in tokens) > 0.5 * len(tokens)


def _line_from_chars(chars: list[tuple[str, float, float, float]]) -> str:
    """chars: (harf, x0, x1, punto). Satırdaki harf boşlukları iki kümeye ayrılır (harf içi / kelime arası); eşik
    satır satır bulunur, çünkü iki yana yaslı satırlarda harf aralığı satırdan satıra değişiyor."""
    if len(chars) < 2:
        return "".join(c[0] for c in chars)
    gaps = [chars[i + 1][1] - chars[i][2] for i in range(len(chars) - 1)]
    size = max(c[3] for c in chars)
    ordered = sorted(gaps)
    if ordered[-1] - ordered[0] < 0.12 * size:          # tek küme: tek kelime (aralıklı başlık "C O N T E N T S" da)
        threshold = float("inf")
    else:
        best = None
        for i in range(1, len(ordered)):
            a, b = ordered[:i], ordered[i:]
            ma, mb = sum(a) / len(a), sum(b) / len(b)
            spread = sum((x - ma) ** 2 for x in a) + sum((x - mb) ** 2 for x in b)
            if best is None or spread < best:
                best, threshold = spread, (ordered[i - 1] + ordered[i]) / 2
    threshold = max(threshold, 0.08 * size)
    out = chars[0][0]
    for gap, c in zip(gaps, chars[1:]):
        out += (" " if gap > threshold else "") + c[0]
    return out


def _respaced_blocks(page: pymupdf.Page) -> list[tuple[float, float, float, float, str, int, int]]:
    """page.get_text('blocks') biçiminde, kelimeleri harf konumlarından yeniden kurulmuş bloklar."""
    blocks = []
    for no, b in enumerate(page.get_text("rawdict")["blocks"]):
        if b["type"] != 0:
            continue
        lines = [_line_from_chars([(c["c"], c["bbox"][0], c["bbox"][2], s["size"])
                                   for s in line["spans"] for c in s["chars"] if c["c"].strip()])
                 for line in b["lines"]]
        blocks.append((*b["bbox"], "\n".join(t for t in lines if t), no, 0))
    return blocks


def _pymupdf_page_elements(page: pymupdf.Page, page_no: int) -> list[dict[str, Any]]:
    w, h = page.rect.width, page.rect.height
    out = []
    blocks = _respaced_blocks(page) if is_letter_spaced(page.get_text()) else page.get_text("blocks")
    for i, (x0, y0, x1, y1, raw, _no, kind) in enumerate(blocks):
        text = _clean_block_text(raw)
        if kind != 0 or len(text) < 2:
            continue
        box = {"page": page_no, "bbox_tl": [x0, y0, x1, y1], "page_w": w, "page_h": h}
        out.append({"id": f"fb{page_no}_{i}", "label": "text", "text": text, "page": page_no,
                    "bbox_tl": [x0, y0, x1, y1], "page_w": w, "page_h": h,
                    "pages": [page_no], "boxes": [box], "source": "pdf_text_layer"})
    return out


def apply_text_fallback(meta: DocMeta, elements: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[int]]:
    """Docling'in metin katmanını büyük oranda kaçırdığı sayfaları (tam sayfa tarama görseli
    'picture' sayılınca olur) ya da metni harf aralıklı olan sayfaları PyMuPDF blokları ile değiştir.
    Değişen sayfada Docling'in bulduğu şekiller (tam sayfa tarama görseli değilse) korunur: şekil anlama kullanır.
    (yeni öğeler, değişen sayfalar)"""
    doc = pymupdf.open(meta.path)
    got: dict[int, int] = {}
    for e in elements:
        if e["label"] not in ("picture", "table_row"):
            got[e["page"]] = got.get(e["page"], 0) + len(e["text"].replace(" ", ""))
    swapped: list[int] = []
    for page_no in range(1, len(doc) + 1):
        raw = doc[page_no - 1].get_text()
        pdf_chars = len(raw.replace(" ", "").replace("\n", ""))
        if pdf_chars >= FALLBACK_MIN_PDF_CHARS and (got.get(page_no, 0) < FALLBACK_MIN_COVERAGE * pdf_chars
                                                    or is_letter_spaced(raw)):
            swapped.append(page_no)
    if not swapped:
        return elements, []

    def figure_on_scan(e: dict[str, Any]) -> bool:
        l, t, r, b = e["bbox_tl"]
        return e["label"] == "picture" and (r - l) * (b - t) < FALLBACK_KEEP_PICTURE_MAX * e["page_w"] * e["page_h"]

    keep = [e for e in elements if e["page"] not in set(swapped) or figure_on_scan(e)]
    for page_no in swapped:
        keep += _pymupdf_page_elements(doc[page_no - 1], page_no)
    moved = set(swapped)
    keep.sort(key=lambda e: (e["page"], e["bbox_tl"][1], e["bbox_tl"][0]) if e["page"] in moved else (e["page"], -1, 0))
    return keep, swapped


# --- Tablo yedeği ------------------------------------------------------------------------
# Docling bazı tablolarda hücreleri kaydırıyor: S-7300A arıza tablosunda (s.98) kod çoğu satırda bir sonraki satırın
# "Remedy" hücresine düşmüş, kelimeler komşu hücrelere dağılmış ("Code: Machine head is detected as being tilted back
# during sewing. | ... | Remedy: E051"). Model bir açıklamayı yanlış koda bağlayabilir (R4, PILOT-RAPORU C2).
# Kayma tespit edilirse o sayfanın tablosu PyMuPDF'in tablo bulucusundan yeniden okunur (bu tabloda temiz).

KEY_RE = re.compile(r"[A-Za-z]{1,3}-?\d{2,4}[A-Za-z]?")       # satır anahtarı biçimi: E051, S-7300A (harf + rakam)


def _cells(row_text: str) -> list[str]:
    """'Code: E050 ... | Cause: ... | Remedy: ...' → hücre değerleri."""
    return [part.split(": ", 1)[-1].strip() for part in row_text.split(" | ")]


def misaligned_rows(rows: list[str]) -> int:
    """İlk hücresi anahtarla başlamayan ama başka bir hücresinde tek başına anahtar duran satır sayısı."""
    bad = 0
    for text in rows:
        cells = _cells(text)
        first = cells[0].split()[:1]
        if first and KEY_RE.fullmatch(first[0]):
            continue
        if any(KEY_RE.fullmatch(w) for c in cells[1:] for w in c.split()[-1:] + c.split()[:1]):
            bad += 1
    return bad


def _is_misaligned(rows: list[str]) -> bool:
    bad = misaligned_rows(rows)
    return bad >= 2 and bad >= 0.15 * len(rows)


def _overlap(a: list[float], b: list[float]) -> float:
    w = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    h = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    area = (b[2] - b[0]) * (b[3] - b[1])
    return w * h / area if area else 0.0


def _pymupdf_table_rows(page: pymupdf.Page, table_el: dict[str, Any]) -> list[dict[str, Any]]:
    """Docling tablosunun alanıyla örtüşen PyMuPDF tablolarının satırları (Docling satırlarıyla aynı biçimde)."""
    out = []
    tables = [t for t in page.find_tables().tables if _overlap(table_el["bbox_tl"], list(t.bbox)) > 0.5]
    for t in sorted(tables, key=lambda t: t.bbox[1]):
        data = t.extract()
        if len(data) < 2:
            continue
        keep = [j for j in range(len(data[0])) if any((r[j] or "").strip() for r in data)]   # boş sütunlar atılır
        header = [(data[0][j] or "").replace("\n", " ").strip() for j in keep]
        for i, (row, rect) in enumerate(zip(data[1:], t.rows[1:])):
            vals = [(row[j] or "").replace("\n", " ").strip() for j in keep]
            if not any(vals):
                continue
            text = " | ".join(f"{h}: {v}" if h and h != v else v for h, v in zip(header, vals) if v)
            bbox = list(rect.bbox)
            box = {"page": table_el["page"], "bbox_tl": bbox, "page_w": table_el["page_w"], "page_h": table_el["page_h"]}
            out.append({"id": f"{table_el['id']}_m{len(out)}", "label": "table_row", "text": text,
                        "page": table_el["page"], "bbox_tl": bbox, "page_w": table_el["page_w"],
                        "page_h": table_el["page_h"], "pages": [table_el["page"]], "boxes": [box],
                        "parent_id": table_el["id"], "source": "pymupdf_table"})
    return out


def apply_table_fallback(meta: DocMeta, elements: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[int]]:
    """Satırları kaymış Docling tablolarını PyMuPDF tablolarıyla değiştir. (yeni öğeler, değişen sayfalar)"""
    by_parent: dict[str, list[dict[str, Any]]] = {}
    for e in elements:
        if e["label"] == "table_row" and e.get("parent_id"):
            by_parent.setdefault(e["parent_id"], []).append(e)
    doc = pymupdf.open(meta.path)
    replace: dict[str, list[dict[str, Any]]] = {}
    for e in elements:
        rows = by_parent.get(e["id"])
        if e["label"] != "table" or not rows or not _is_misaligned([r["text"] for r in rows]):
            continue
        new = _pymupdf_table_rows(doc[e["page"] - 1], e)
        if new and not _is_misaligned([r["text"] for r in new]):
            replace[e["id"]] = new
        else:
            log.warning("%s s.%d: tablo kaymış ama PyMuPDF yedeği de temiz değil, Docling satırları kaldı",
                        meta.doc_id, e["page"])
    if not replace:
        return elements, []
    out: list[dict[str, Any]] = []
    for e in elements:
        if e["label"] == "table_row" and e.get("parent_id") in replace:
            continue
        out.append(e)
        if e["id"] in replace:
            out += replace[e["id"]]
    return out, sorted({e["page"] for e in elements if e["id"] in replace})


# --- Önbellek --------------------------------------------------------------------------

def parsed_path(meta: DocMeta) -> Path:
    return PARSED_DIR / f"{meta.doc_id}.json"


def load_or_parse(meta: DocMeta, force: bool = False) -> dict[str, Any]:
    """Parse sonucunu diskten oku, yoksa üret ve yaz."""
    path = parsed_path(meta)
    if path.exists() and not force:
        result = json.loads(path.read_text(encoding="utf-8"))   # Windows varsayılanı cp1254: açık UTF-8
    else:
        started = time.time()
        elements, failed = parse_pdf(meta)
        result = {"doc_id": meta.doc_id, "n_elements": len(elements), "failed_pages": failed,
                  "seconds": round(time.time() - started, 1), "elements": elements}
    changed = False
    if "fallback_pages" not in result:
        result["elements"], result["fallback_pages"] = apply_text_fallback(meta, result["elements"])
        changed = True
    if "table_fallback_pages" not in result:
        result["elements"], result["table_fallback_pages"] = apply_table_fallback(meta, result["elements"])
        changed = True
    if changed:
        result["n_elements"] = len(result["elements"])
        PARSED_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    return result
