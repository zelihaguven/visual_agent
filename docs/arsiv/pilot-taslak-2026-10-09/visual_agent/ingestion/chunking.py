"""Öğelerden chunk üretimi: temizlik, sayfa geçişi birleştirme, başlık bazlı bölümleme, tablo satırları.

Faz 1'den devralınan ve burada çözülen açık maddeler:
- Tablo satırında başlık tekrarı ("Problem: 1 | Problem: Upper thread...") → aynı başlıklı
  ardışık hücreler tek değerde birleştirilir.
- Çizim kodları ("0573M") arama metnini kirletmesin → ayrı alana alınır.
- Bozuk OCR şüphesi chunk'a uyarı olarak eklenir (R7).
"""

from __future__ import annotations

import re

from ..config import SETTINGS, DocMeta

SENTENCE_END = (".", ":", ";", "!", "?")
TEXT_LABELS = {"text", "paragraph", "list_item", "caption", "footnote", "formula", "code", "checkbox_selected",
               "checkbox_unselected", "reference"}
HEADER_LABELS = {"section_header", "title"}
SKIP_LABELS = {"page_header", "page_footer"}
GARBLED = re.compile(r"(?:\b\w{1,3}\s{2,}){3,}")
DRAWING_CODE = re.compile(r"\s*\b\d{4}[A-Z]{1,2}\b\s*$")


# ----------------------------------------------------------------------------- temizlik

def _norm_repeat(text: str) -> str:
    return re.sub(r"\d+", "#", text.strip().lower())


def remove_furniture(elements: list[dict], min_ratio: float = 0.3, edge: float = 0.1) -> tuple[list[dict], set[str]]:
    """Birçok sayfada, sayfanın üst/alt kenarında tekrar eden metinleri (üst/alt bilgi) atar."""
    pages = {e["page"] for e in elements}
    seen: dict[str, set[int]] = {}
    for e in elements:
        b = e["boxes"][0]
        _, t, _, bot = b["bbox_tl"]
        h = b["page_h"]
        if t <= h * edge or bot >= h * (1 - edge):
            seen.setdefault(_norm_repeat(e["text"]), set()).add(e["page"])
    need = max(3, int(len(pages) * min_ratio))
    furniture = {k for k, v in seen.items() if k and len(v) >= need}
    kept = [e for e in elements if e["label"] not in SKIP_LABELS and _norm_repeat(e["text"]) not in furniture]
    return kept, furniture


def _join(a: str, b: str) -> str:
    a = a.rstrip()
    if a.endswith("-") and b[:1].islower():
        return a[:-1] + b.lstrip()
    return a + " " + b.lstrip()


def _is_continuation(prev: dict, nxt: dict) -> bool:
    if nxt["page"] != prev["pages"][-1] + 1:
        return False
    if prev["label"] not in TEXT_LABELS or nxt["label"] not in TEXT_LABELS:
        return False
    p, n = prev["text"].rstrip(), nxt["text"].lstrip()
    if not p or not n:
        return False
    return (not p.endswith(SENTENCE_END)) and (n[0].islower() or p.endswith(("-", ",")))


def merge_cross_page(elements: list[dict]) -> tuple[list[dict], int]:
    out: list[dict] = []
    merges = 0
    for e in elements:
        if out and _is_continuation(out[-1], e):
            prev = dict(out[-1])
            prev["text"] = _join(prev["text"], e["text"])
            prev["boxes"] = prev["boxes"] + e["boxes"]
            prev["pages"] = sorted(set(prev["pages"]) | set(e["pages"]))
            out[-1] = prev
            merges += 1
        else:
            out.append(e)
    return out, merges


# ----------------------------------------------------------------------------- tablolar

def _union(boxes: list[list[float]]) -> list[float]:
    return [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]


def group_table_rows(cells: list[dict]) -> list[dict]:
    """Tablo hücrelerini mantıksal satırlara gruplar (birden çok ızgara satırına yayılan hücreler dahil).

    Dönüş: [{text, bbox_tl, drawing_codes}], metin 'Başlık: değer | Başlık: değer'.
    Aynı başlığı paylaşan ardışık hücreler tek değerde birleştirilir.
    """
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
        parts: list[tuple[str | None, str]] = []
        codes: list[str] = []
        for c in row_cells:
            val = c["text"].strip()
            m = DRAWING_CODE.search(val)
            if m and len(val) > len(m.group(0)):
                codes.append(m.group(0).strip())
                val = val[: m.start()].rstrip()
            h = headers.get(c["c0"])
            if parts and parts[-1][0] == h and h is not None:
                parts[-1] = (h, parts[-1][1] + " " + val)
            else:
                parts.append((h, val))
        text = " | ".join(f"{h}: {v}" if h and h != v else v for h, v in parts)
        boxes = [c["bbox_tl"] for c in row_cells if c.get("bbox_tl")]
        rows.append({"text": text, "bbox_tl": _union(boxes) if boxes else None, "drawing_codes": codes})
    return rows


# ----------------------------------------------------------------------------- chunking

def _words(text: str) -> int:
    return len(text.split())


def build_chunks(elements: list[dict], meta: DocMeta, page_labels: dict[int, str | None]) -> tuple[list[dict], dict]:
    """Okuma sırasındaki öğelerden chunk listesi + istatistik."""
    clean, furniture = remove_furniture(elements)
    merged, n_merges = merge_cross_page(clean)

    chunks: list[dict] = []
    stats = {"elements": len(elements), "furniture": len(furniture), "cross_page_merges": n_merges,
             "pictures": 0, "pictures_with_caption": 0, "tables": 0, "table_rows": 0, "garbled": 0}
    section = ""
    buf: list[dict] = []

    def base(label: str, text: str, boxes: list[dict], context_boxes=None, extra=None) -> dict:
        pages = sorted({b["page"] for b in boxes})
        warnings = []
        if GARBLED.search(text):
            warnings.append("ocr_bozuk_supheli")
            stats["garbled"] += 1
        ch = {
            "chunk_id": f"{meta.doc_id}:{len(chunks):05d}",
            "doc_id": meta.doc_id, "title": meta.title, "brand": meta.brand, "doc_type": meta.doc_type,
            "product": meta.product, "product_model": meta.product_model, "version": meta.version,
            "lang": meta.lang, "access": meta.access,
            "label": label, "section": section, "text": text.strip(),
            "pages": pages, "page_labels": {str(p): page_labels.get(p) for p in pages},
            "boxes": boxes, "context_boxes": context_boxes or [], "warnings": warnings,
        }
        if extra:
            ch.update(extra)
        prefix = " | ".join(x for x in (meta.title, meta.product_model or meta.product or "", section) if x)
        ch["embed_text"] = f"{prefix}\n{ch['text']}"
        return ch

    def flush():
        nonlocal buf
        if not buf:
            return
        text = ""
        for e in buf:
            text = _join(text, e["text"]) if text else e["text"]
        boxes = [b for e in buf for b in e["boxes"]]
        label = "list" if all(e["label"] == "list_item" for e in buf) else "text"
        chunks.append(base(label, text, boxes))
        buf = []

    for i, e in enumerate(merged):
        lab = e["label"]
        if lab in HEADER_LABELS:
            flush()
            section = e["text"].strip()[:160]
            continue
        if lab == "table":
            flush()
            stats["tables"] += 1
            rows = group_table_rows(e.get("cells") or [])
            page = e["boxes"][0]
            if rows:
                for r in rows:
                    if not r["bbox_tl"]:
                        continue
                    box = {"page": page["page"], "bbox_tl": r["bbox_tl"], "page_w": page["page_w"],
                           "page_h": page["page_h"]}
                    chunks.append(base("table_row", r["text"], [box], context_boxes=e["boxes"],
                                       extra={"drawing_codes": r["drawing_codes"]}))
                    stats["table_rows"] += 1
            elif e["text"].strip():
                chunks.append(base("table", e["text"], e["boxes"]))
            continue
        if lab == "picture":
            flush()
            stats["pictures"] += 1
            # Görsel anlama (VLM açıklaması) pilotta kurum içi model olmadığı için yok.
            # Sadece yakınındaki başlık/açıklama (caption) varsa aranabilir bir görsel chunk'ı üretilir.
            cap = next((x for x in merged[i + 1:i + 3] if x["label"] == "caption"), None)
            if cap:
                stats["pictures_with_caption"] += 1
                chunks.append(base("figure", f"[Şekil] {cap['text']}", e["boxes"] + cap["boxes"]))
            continue
        if lab in TEXT_LABELS:
            if not e["text"].strip():
                continue
            if buf and _words(" ".join(x["text"] for x in buf)) + _words(e["text"]) > SETTINGS.chunk_words:
                flush()
            buf.append(e)
            continue
    flush()
    # Çok kısa, tek başına anlamsız chunk'ları (ör. tek kelimelik etiketler) at
    chunks = [c for c in chunks if _words(c["text"]) >= 3 or c["label"] == "table_row"]
    for n, c in enumerate(chunks):
        c["chunk_id"] = f"{meta.doc_id}:{n:05d}"
    return chunks, stats
