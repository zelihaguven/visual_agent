"""Öğeler -> arama parçaları (chunk). Başlık sınırını aşmaz, sayfa ve bbox listesini korur.

Parça türleri:
  text       ardışık paragraf/liste öğeleri, CHUNK_MAX_CHARS'a kadar
  table_row  tablonun mantıksal satırı ("Başlık: değer | ...")
  table      satırlarına ayrılamayan tablo (markdown)
"""
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .config import CHUNK_MAX_CHARS, CHUNKS_PATH
from .parse import merge_cross_page, printed_page_labels, remove_furniture
from .registry import DocMeta

HEADING_LABELS = ("section_header", "title")
SKIP_LABELS = ("picture", "figure", "page_header", "page_footer")
MIN_CHARS = 3
MAX_SECTION_CHARS = 80


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


def build_chunks(meta: DocMeta, elements: list[dict[str, Any]]) -> list[Chunk]:
    """Bir dokümanın parse edilmiş öğelerinden parçalar üret."""
    elements = merge_cross_page(remove_furniture(elements))
    pages = sorted({p for e in elements for p in e["pages"]})
    labels = printed_page_labels(meta.path, pages)

    chunks: list[Chunk] = []
    section = ""
    buf: list[dict[str, Any]] = []

    def make(chunk_type: str, text: str, els: list[dict[str, Any]]) -> None:
        text = text.strip()
        if len(text) < MIN_CHARS:
            return
        boxes = [b for e in els for b in e["boxes"]]
        pgs = sorted({b["page"] for b in boxes})
        chunks.append(Chunk(
            chunk_id=f"{meta.doc_id}-{len(chunks):05d}", doc_id=meta.doc_id, brand=meta.brand,
            product=meta.product, doc_type=meta.doc_type, lang=meta.lang_of(pgs[0]),
            chunk_type=chunk_type, section=section, page=pgs[0], pages=pgs,
            page_labels={str(p): labels.get(p) for p in pgs}, boxes=boxes, text=text,
            embed_text=_embed_text(meta, section, text)))

    def flush() -> None:
        nonlocal buf
        if buf:
            make("text", " ".join(e["text"].strip() for e in buf), buf)
            buf = []

    for e in elements:
        label = e["label"]
        if label in SKIP_LABELS:
            continue
        if label in HEADING_LABELS:
            flush()
            section = e["text"].strip()[:MAX_SECTION_CHARS]
            continue
        if label == "table":
            flush()
            if not e.get("has_rows"):
                make("table", e["text"], [e])
            continue
        if label == "table_row":
            flush()
            make("table_row", e["text"], [e])
            continue
        # metin/liste/dipnot/başlık dışı her şey paragraf gibi biriktirilir
        if not e["text"].strip():
            continue
        for piece in _split_long(e):
            size = sum(len(x["text"]) for x in buf) + len(piece["text"])
            lang_changes = bool(buf) and meta.lang_of(piece["page"]) != meta.lang_of(buf[0]["page"])
            if buf and (size > CHUNK_MAX_CHARS or lang_changes):
                flush()
            buf.append(piece)
    flush()
    return chunks


def write_chunks(chunks: list[Chunk], path: Path = CHUNKS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")


def read_chunks(path: Path = CHUNKS_PATH) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
