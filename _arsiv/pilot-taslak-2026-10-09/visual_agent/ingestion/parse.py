"""Docling ile ayrıştırma. Parti parti çalışır ve her partiyi diske yazar (yarıda kalırsa devam eder).

OCR stratejisi (R7, Faz 1'de OCR'ın bir satırı sessizce kaybetmesi):
- Metin katmanı olan sayfalar (dijital PDF'ler ve önceden OCR katmanı eklenmiş taranmış PDF'ler)
  metin katmanından okunur (do_ocr=False). Faz 1'de PDF'in kendi OCR katmanının, Docling OCR'ının
  kaybettiği satırı doğru okuduğu görülmüştü.
- Metin katmanı olmayan sayfalar ayrıca tam sayfa OCR ile ayrıştırılır.
- Bozuk OCR şüphesi (kısa harf parçaları + çok boşluk) chunk'a uyarı olarak eklenir.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from ..config import PARSED_DIR, DocMeta
from .pdf_utils import page_count, pages_without_text

BATCH = 12  # Docling'e tek seferde verilen sayfa sayısı


def _converter(ocr: bool):
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    opts = PdfPipelineOptions()
    opts.do_table_structure = True
    opts.do_ocr = ocr
    if ocr:
        opts.ocr_options.force_full_page_ocr = True
    return DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)})


def _groups(pages: list[int], size: int) -> list[list[int]]:
    """Ardışık sayfaları en fazla `size` uzunluğunda gruplara böler."""
    out: list[list[int]] = []
    for p in sorted(set(pages)):
        if out and p == out[-1][-1] + 1 and len(out[-1]) < size:
            out[-1].append(p)
        else:
            out.append([p])
    return out


def _table_cells(item, page_h: float) -> list[dict]:
    data = getattr(item, "data", None)
    if data is None or not getattr(data, "table_cells", None):
        return []
    cells = []
    for c in data.table_cells:
        bbox = None
        if c.bbox is not None:
            bb = c.bbox.to_top_left_origin(page_height=page_h)
            bbox = [bb.l, bb.t, bb.r, bb.b]
        cells.append({"r0": c.start_row_offset_idx, "r1": c.end_row_offset_idx,
                      "c0": c.start_col_offset_idx, "c1": c.end_col_offset_idx,
                      "text": c.text or "", "bbox_tl": bbox, "header": bool(c.column_header)})
    return cells


def _doc_to_elements(doc, pages: list[int], prefix: str) -> list[dict]:
    """Docling dokümanından okuma sırasında öğeler: label, text, kutular (sol-üst orijin, point)."""
    elements = []
    for idx, (item, level) in enumerate(doc.iterate_items()):
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
            if p.page_no not in pages:
                continue
            size = doc.pages[p.page_no].size
            bb = p.bbox.to_top_left_origin(page_height=size.height)
            boxes.append({"page": p.page_no, "bbox_tl": [bb.l, bb.t, bb.r, bb.b],
                          "page_w": size.width, "page_h": size.height})
        if not boxes:
            continue
        el = {"id": f"{prefix}e{idx}", "label": label, "level": level, "text": text,
              "page": boxes[0]["page"], "page_w": boxes[0]["page_w"], "page_h": boxes[0]["page_h"],
              "pages": sorted({b["page"] for b in boxes}), "boxes": boxes}
        if label == "table":
            el["cells"] = _table_cells(item, boxes[0]["page_h"])
        elements.append(el)
    return elements


def parse_document(meta: DocMeta, log=print) -> list[dict]:
    """Dokümanın tüm sayfalarını ayrıştırır. Daha önce ayrıştırılan partiler diskten okunur."""
    out_dir = PARSED_DIR / meta.doc_id
    out_dir.mkdir(parents=True, exist_ok=True)
    n = page_count(meta.path)
    no_text = set(pages_without_text(meta.path))
    text_pages = [p for p in range(1, n + 1) if p not in no_text]

    plan = [(g, False) for g in _groups(text_pages, BATCH)] + [(g, True) for g in _groups(sorted(no_text), BATCH)]
    plan.sort(key=lambda x: x[0][0])
    converters: dict[bool, object] = {}
    elements: list[dict] = []
    for group, ocr in plan:
        part = out_dir / f"p{group[0]:04d}-{group[-1]:04d}{'-ocr' if ocr else ''}.json"
        if part.exists():
            elements += json.loads(part.read_text("utf-8"))
            continue
        t0 = time.time()
        if ocr not in converters:
            converters[ocr] = _converter(ocr)
        result = converters[ocr].convert(str(meta.path), page_range=(group[0], group[-1]))
        els = _doc_to_elements(result.document, group, prefix=f"p{group[0]}{'o' if ocr else ''}_")
        part.write_text(json.dumps(els, ensure_ascii=False), "utf-8")
        elements += els
        log(f"[{meta.doc_id}] sayfa {group[0]}-{group[-1]}{' (OCR)' if ocr else ''}: "
            f"{len(els)} öğe, {time.time() - t0:.0f} sn")
    elements.sort(key=lambda e: (e["page"], _order_key(e)))
    return elements


def _order_key(e: dict) -> int:
    """Aynı sayfa içinde Docling okuma sırasını koru (id'deki eN indeksi)."""
    try:
        return int(e["id"].rsplit("e", 1)[1])
    except (IndexError, ValueError):
        return 0
