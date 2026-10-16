"""Şekil anlama: parse edilmiş 'picture' öğelerine VLM ile metin açıklaması (doküman işleme sırasında bir kez).

Sonuç data/figures/<doc_id>.json'a yazılır; chunk.py bunları 'figure' parçası yapar, böylece çizimler aranabilir.
Parça metni üç kısımdan oluşur:
  - şekil başlığı (caption) ve şeklin içindeki yazılar: PDF'ten birebir, kaynak metnidir
  - otomatik açıklama: VLM üretimi, kaynak metni DEĞİL. Doğrulama (verify.py) bu kısımdan yapılan alıntıyı
    "doğrulandı" saymaz; kullanıcı şekli sayfada kendisi kontrol eder.

Aynı görsel (ör. S-7300A ve S-7300B kılavuzlarındaki ortak çizimler) içerik özetiyle tanınır, bir kez açıklanır.
"""
import hashlib
import io
import json
import logging
import re
import time
from pathlib import Path
from typing import Any

import ollama
import pymupdf
import pypdfium2 as pdfium

from .config import FIGURE_DPI, FIGURE_MAX_PX, FIGURE_MIN_AREA, FIGURE_MIN_SIDE, FIGURES_DIR, VLM_MODEL
from .registry import DocMeta
from .verify import FOREIGN_SCRIPT_RE

log = logging.getLogger(__name__)

PROMPT_VERSION = 2            # talimat değişirse artırılır: eski açıklamalar yeniden üretilir
# 2: Bağlamda Türkçe ürün adı ("Kahve makinesi") verilince model onu etikette yazıyormuş gibi aktardı
#    ("The label on the machine reads 'Mr. Coffee Kahve makinesi'"). Bağlamda yalnız marka ve İngilizce tür var,
#    basılı olmayan yazıyı aktarmak yasak.
DECORATIVE = "DECORATIVE"     # logo, ikon, süs: parça üretilmez
AUTO_PREFIX = "Otomatik şekil açıklaması (model üretimi, kaynak metni değil):"
CAPTION_MAX_GAP = 40          # point: şekil kutusuyla başlık arasındaki en büyük dikey boşluk
LABELS_MAX_CHARS = 300
PAD = 6                       # point: kırpmada kutunun çevresine eklenen pay
# 3B model logoyu çoğu zaman 'DECORATIVE' demeden tarif ediyor ("The figure shows a logo for Team Soldier ...", ceket
# s.18). Yalnız açıklama doğrudan logo diye başlıyorsa süs sayılır ("logonun ceketteki yeri" gibi tarifler kalır).
LOGO_RE = re.compile(r"^the (?:figure|image|picture) (?:shows|is|depicts|displays) (?:a|an|the) (?:\w+ ){0,2}logo\b", re.I)

DOC_TYPE_EN = {"product_standard": "garment product specification", "machine_manual": "machine instruction manual",
               "tailoring_guide": "tailoring book", "repair_guide": "textile machine repair book"}

PROMPT = """You are describing a figure from a technical document ({doc}) so that it can be found by text search.
Section: {section}
Caption: {caption}
Text printed in the figure: {labels}

Describe in 2-4 plain English sentences what the figure shows: the machine part, garment area or object, \
what is being done (for example the direction of an arrow, a part being turned, inserted or adjusted), \
and which labelled parts appear.
Rules:
- Only describe what is visible. Do not guess model names, measurements or values that are not printed in the figure.
- Quote text only if it is printed in the figure. The document name above is context, not text in the figure.
- Do not repeat the caption word for word.
- If the figure is only a logo, a decorative picture, a warning symbol or an icon without technical content, \
answer exactly: DECORATIVE"""


# --- Seçim ve bağlam -------------------------------------------------------------------

def is_candidate(el: dict[str, Any]) -> bool:
    """Açıklanmaya değer şekil: 'picture' ve ikon/şerit olmayacak kadar büyük."""
    if el["label"] != "picture":
        return False
    l, t, r, b = el["bbox_tl"]
    w, h = r - l, b - t
    return min(w, h) >= FIGURE_MIN_SIDE and w * h >= FIGURE_MIN_AREA * el["page_w"] * el["page_h"]


def find_caption(fig: dict[str, Any], elements: list[dict[str, Any]]) -> str:
    """Aynı sayfada, şeklin hemen altında ya da üstünde, yatayda örtüşen en yakın 'caption' öğesi."""
    l, t, r, b = fig["bbox_tl"]
    best, best_gap = "", CAPTION_MAX_GAP + 1
    for e in elements:
        if e["label"] != "caption" or e["page"] != fig["page"] or not e["text"].strip():
            continue
        cl, ct, cr, cb = e["bbox_tl"]
        if min(r, cr) <= max(l, cl):
            continue
        gap = ct - b if ct >= b else t - cb if cb <= t else 0.0
        if 0 <= gap < best_gap:
            best, best_gap = e["text"].strip(), gap
    return best


def figure_labels(page: pymupdf.Page, bbox_tl: list[float]) -> str:
    """Şeklin içindeki PDF metin katmanı kelimeleri (parça adları, ok yazıları). Tek karakterlik çağrı
    numaraları ("1", "2") atılır: arama için gürültü."""
    words = page.get_text("words", clip=pymupdf.Rect(*bbox_tl))
    words.sort(key=lambda w: (w[5], w[6], w[7]))          # blok, satır, kelime sırası
    kept = [w[4] for w in words if len(w[4]) >= 2 or w[4].isalpha()]
    return " ".join(kept)[:LABELS_MAX_CHARS].strip()


def crop_png(pdf: pdfium.PdfDocument, el: dict[str, Any]) -> bytes:
    """Şekil kutusunu FIGURE_DPI'da kırp, uzun kenarı FIGURE_MAX_PX'e küçült. PNG baytları."""
    page = pdf[el["page"] - 1]
    pw, ph = page.get_size()
    l, t, r, b = el["bbox_tl"]
    crop = (max(0.0, l - PAD), max(0.0, ph - b - PAD), max(0.0, pw - r - PAD), max(0.0, t - PAD))
    img = page.render(scale=FIGURE_DPI / 72, crop=crop).to_pil().convert("RGB")
    img.thumbnail((FIGURE_MAX_PX, FIGURE_MAX_PX))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# --- VLM -------------------------------------------------------------------------------

def clean_description(raw: str) -> str:
    """Boşlukları topla; 'DECORATIVE' cevabını tanı; başka alfabeye kayan cümleleri at (qwen Çinceye kayabiliyor)."""
    text = re.sub(r"\s+", " ", raw).strip()
    if DECORATIVE in text[:30].upper() or LOGO_RE.match(text):
        return DECORATIVE
    sentences = re.split(r"(?<=[.!?])\s+|(?<=[。！？])\s*", text)
    return " ".join(s for s in sentences if not FOREIGN_SCRIPT_RE.search(s)).strip()


def describe(png: bytes, *, doc: str, section: str, caption: str, labels: str) -> str:
    prompt = PROMPT.format(doc=doc, section=section or "-", caption=caption or "-", labels=labels or "-")
    resp = ollama.chat(model=VLM_MODEL, messages=[{"role": "user", "content": prompt, "images": [png]}],
                       options={"temperature": 0, "num_predict": 220, "num_ctx": 4096}, keep_alive="30m")
    return clean_description(resp["message"]["content"])


# --- Doküman ---------------------------------------------------------------------------

def figures_path(meta: DocMeta) -> Path:
    return FIGURES_DIR / f"{meta.doc_id}.json"


def load_figures(meta: DocMeta) -> dict[str, dict[str, Any]]:
    """{öğe id: {page, hash, caption, labels, desc}}. Açıklama üretilmemişse boş."""
    path = figures_path(meta)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))["figures"]


def _known_descriptions() -> dict[str, str]:
    """Daha önce (herhangi bir dokümanda) aynı model ve talimatla açıklanmış görseller: {özet: açıklama}."""
    known: dict[str, str] = {}
    for path in FIGURES_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("model") == VLM_MODEL and data.get("prompt_version") == PROMPT_VERSION:
            known.update({f["hash"]: f["desc"] for f in data["figures"].values() if f.get("desc")})
    return known


def describe_document(meta: DocMeta, elements: list[dict[str, Any]], *, force: bool = False,
                      limit: int | None = None) -> dict[str, Any]:
    """Dokümanın aday şekillerini açıkla, her şekilden sonra diske yaz (yarıda kalırsa kaldığı yerden sürer).
    limit: en fazla bu kadar yeni VLM çağrısı (deneme için)."""
    path = figures_path(meta)
    old: dict[str, Any] = {}
    if path.exists() and not force:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("model") == VLM_MODEL and data.get("prompt_version") == PROMPT_VERSION:
            old = data["figures"]
    known = {} if force else _known_descriptions()
    result = {"doc_id": meta.doc_id, "model": VLM_MODEL, "prompt_version": PROMPT_VERSION, "figures": {}}
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    def save() -> None:
        path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")

    doc_name = f"{meta.brand}, {DOC_TYPE_EN.get(meta.doc_type, 'technical document')}"
    section, calls = "", 0
    pdf, mu = pdfium.PdfDocument(str(meta.path)), pymupdf.open(meta.path)
    try:
        for el in elements:
            if el["label"] in ("section_header", "title"):
                section = el["text"].strip()[:80]
            if not is_candidate(el):
                continue
            png = crop_png(pdf, el)
            digest = hashlib.sha1(png).hexdigest()
            entry = {"page": el["page"], "hash": digest, "caption": find_caption(el, elements),
                     "labels": figure_labels(mu[el["page"] - 1], el["bbox_tl"]), "desc": "", "seconds": 0.0}
            prev = old.get(el["id"])
            if prev and prev["hash"] == digest and prev.get("desc"):
                entry["desc"], entry["seconds"] = clean_description(prev["desc"]), prev.get("seconds", 0.0)
            elif digest in known:
                entry["desc"] = known[digest]
            elif limit is not None and calls >= limit:
                continue
            else:
                t = time.time()
                try:
                    entry["desc"] = describe(png, doc=doc_name, section=section,
                                             caption=entry["caption"], labels=entry["labels"])
                except Exception:  # noqa: BLE001 - tek şekil tüm dokümanı düşürmesin; sonraki çalıştırmada denenir
                    log.exception("%s s.%d %s açıklanamadı", meta.doc_id, el["page"], el["id"])
                    continue
                entry["seconds"] = round(time.time() - t, 1)
                calls += 1
                known[digest] = entry["desc"]
                log.info("%s s.%d %s (%.0f sn): %s", meta.doc_id, el["page"], el["id"], entry["seconds"],
                         entry["desc"][:90])
            result["figures"][el["id"]] = entry
            save()
    finally:
        pdf.close()
        mu.close()
    save()
    return result


def figure_text(fig: dict[str, Any]) -> str:
    """Parça metni: başlık ve şekildeki yazılar (PDF'ten birebir), sonra otomatik açıklama (işaretli)."""
    parts = []
    if fig.get("caption"):
        parts.append(f"Şekil başlığı: {fig['caption']}")
    if fig.get("labels"):
        parts.append(f"Şekildeki yazılar: {fig['labels']}")
    parts.append(f"{AUTO_PREFIX} {fig['desc']}")
    return "\n".join(parts)


def is_described(fig: dict[str, Any] | None) -> bool:
    return bool(fig and fig.get("desc") and fig["desc"] != DECORATIVE)
