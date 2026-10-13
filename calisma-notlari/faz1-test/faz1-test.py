"""


Adımlar:
  1. PDF'in ilgili sayfalarını Docling ile parse et -> öğeler + sayfa + bbox
  2. Anahtar kelimelere göre hedef öğeyi (dikiş paragrafı vb.) seç
  3a. streamlit-pdf-viewer ile PDF'i aç, bbox'ı annotation olarak ver (viewer modu)
  3b. Sayfayı 150 DPI'da PNG'ye çevir, bbox'ı ölçekleyip sarı kutu çiz
  4. Aynısını taranmış pantolon şartnamesinde (OCR) ve Brother kılavuzunda tekrarla
  5. Başarı ölçütü: Kutu doğru paragrafın üstüne düşüyor mu? -> PNG'ler gözle kontrol edilir,
     ayrıca otomatik kontroller (bbox sayfa içinde mi, metin anahtar kelimeyi içeriyor mu)
  6. Sayfa geçişi: Sayfa sonunda başlayıp sonraki sayfada biten paragrafları bul, birleştir,
     araya üst/alt bilgi girmiş mi kontrol et, iki sayfada da vurgula

Kullanım:
  python faz1-test.py                      # tüm dokümanlar
  python faz1-test.py --doc gl-pd-14-04a   # tek doküman
  python faz1-test.py --doc gl-pd-07-14a --pages 8 9 10   # sayfaları elle ver (1 tabanlı)
  python faz1-test.py --report-only        # mevcut sonuçlardan birleşik raporu yeniden üret
  streamlit run faz1-test.py -- --viewer   # 3a: tarayıcıda PDF.js ile vurgu

Çıktılar: faz1_output/<doc_id>/ altında elements.json, selected.json, highlight_pXX.png,
transitions.json, transition_pXX.png ve faz1_output/report.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANUALS = ROOT.parent.parent / "test-dokumanlari"
OUTPUT = ROOT / "faz1_output"
DPI = 150

SENTENCE_END = (".", ":", ";", "!", "?")


@dataclass
class DocConfig:
    doc_id: str
    file: str
    question: str  # Denemenin canlandırdığı kullanıcı sorusu (raporda gösterilir)
    keywords: list[str]
    force_ocr: bool = False
    pages: list[int] | None = None  # 1 tabanlı. None ise metin katmanından otomatik bulunur


DOCS = {
    "gl-pd-14-04a": DocConfig(
        "gl-pd-14-04a",
        "GL-PD-14-04A_ACU-Coat.pdf",
        "Ceketin dış görünür dikişlerinde SPI kaç olmalı?",
        [r"stitches per inch", r"outside visible stitching", r"\bSPI\b"],
    ),
    "gl-pd-07-14a": DocConfig(
        "gl-pd-07-14a",
        "GL-PD-07-14A_Combat-Trousers.pdf",
        "Pantolonun dış görünür dikişlerinde SPI kaç olmalı?",
        [r"stitches per inch", r"outside visible stitching", r"\bSPI\b"],
        force_ocr=True,
    ),
    "brother-s7300a": DocConfig(
        "brother-s7300a",
        "Brother_S-7300A_Instruction.pdf",
        "S-7300A'da üst iplik gergin değil (upper thread is not tight), ne yapmalıyım?",
        [r"upper thread is not tight", r"upper thread tension"],
    ),
}

# Deneme sırasında yaşanan problemler ve çözümleri. Rapora olduğu gibi yazılır.
# durum: "çözüldü" | "açık"
FINDINGS = [
    {"baslik": "Test dosyası modülü yükleyemedi",
     "ne_oldu": "faz1-test.py adında '-' olduğu için testler dosyayı yoldan yüklüyor. dataclass'lar modülün "
                "sys.modules'ta kayıtlı olmasını beklediği için yükleme AttributeError verdi.",
     "cozum": "Test dosyasında modül çalıştırılmadan önce sys.modules'a kaydedildi.", "durum": "çözüldü"},
    {"baslik": "Brother denemesi hiç tamamlanmadı",
     "ne_oldu": "Arka planda başlatılan çalıştırma, oturum kapanınca yarıda kaldı. Brother'a ait hiçbir çıktı oluşmadı.",
     "cozum": "Yeniden çalıştırıldı. Uzun işlerin oturum açıkken bitirilmesi gerekiyor.", "durum": "çözüldü"},
    {"baslik": "Gereksiz yere 26 sayfa parse ediliyordu",
     "ne_oldu": "Brother'da aday sayfalar birbirinden uzaktı (77-79 ve 100-102). Docling'e tek aralık (77-102) "
                "verildiği için 6 yerine 26 sayfa parse ediliyordu (CPU'da 20+ dakika).",
     "cozum": "Sayfalar ardışık gruplara bölünüp her grup ayrı parse ediliyor (contiguous_groups). Süre 2-3 dakikaya indi.",
     "durum": "çözüldü"},
    {"baslik": "Rapor sadece son çalıştırılan dokümanı gösteriyordu / eski çıktılar kalıyordu",
     "ne_oldu": "Her çalıştırma report.md'nin üzerine sadece kendi sonucunu yazıyordu. Eski PNG/JSON dosyaları da "
                "klasörde kalıp raporu yanıltabiliyordu.",
     "cozum": "Her doküman sonucu result.json olarak saklanıyor, rapor hepsinden birleştiriliyor. "
              "Her çalıştırmada dokümanın eski çıktıları önce siliniyor.", "durum": "çözüldü"},
    {"baslik": "Tablonun tamamı vurgulanıyordu",
     "ne_oldu": "Docling tabloyu tek öğe olarak veriyor. Brother arıza tablosunda soru tek bir satırla (Upper thread "
                "is not tight) ilgiliyken 4 satırlık tablonun tamamı vurgulandı.",
     "cozum": "Tablo hücrelerinden satır öğeleri (table_row) üretiliyor. Seçim satır seviyesinde yapılıyor: ilgili "
              "satır sarı, tablonun geri kalanı bağlam için açık mavi çerçeveyle gösteriliyor.", "durum": "çözüldü"},
    {"baslik": "Fiziksel ve basılı sayfa numarası farklı",
     "ne_oldu": "Brother'da seçilen sayfa PDF'in 101. sayfası, ama sayfanın altında basılı numara 90. Kullanıcı basılı "
                "kılavuzda 90'a bakar, 's.101' görürse kafası karışır.",
     "cozum": "Basılı numara sayfanın alt/üst bilgisinden okunuyor ve 's.90 (PDF s.101)' şeklinde gösteriliyor.",
     "durum": "çözüldü"},
    {"baslik": "OCR bir satırı kaybetti (sessiz hata)",
     "ne_oldu": "Taranmış pantolon şartnamesinde 'and conform to the ASTM D 6193 seam and stitch types listed in "
                "Table V. The backside of seams' satırı 'ans     a    s  s       ams' olarak okundu. Otomatik kontroller "
                "bunu yakalamadı, sadece görsele bakınca fark edildi. 'ASTM D6193' ile yapılan bir arama bu paragrafı bulamaz.",
     "cozum": "Bozuk OCR şüphesi için otomatik uyarı eklendi. PDF'in kendi OCR katmanındaki metin de rapora "
              "karşılaştırma için yazılıyor. Karşılaştırmada PDF'in kendi OCR katmanının kayıp satırı doğru okuduğu, "
              "ama kendi küçük hatalarının olduğu görüldü ('confOlm', 'protmding'). İki OCR farklı yerlerde hata yapıyor. "
              "Kalıcı çözüm açık: iki OCR'ı karşılaştırıp bozuk bölümde diğerini kullanmak, farklı OCR motoru denemek, "
              "kullanıcıya her zaman orijinal sayfa görüntüsünü göstermek.", "durum": "açık"},
    {"baslik": "Tablo satırı metninde başlık tekrarı",
     "ne_oldu": "Brother tablosunda 'Problem' başlığı iki sütunu (sıra no + açıklama) kapsıyor. Satır metni "
                "'Problem: 1 | Problem: Upper thread is not tight. 0573M' şeklinde çıktı. Vurgu doğru, ama metin chunk "
                "olarak kullanılırsa gereksiz tekrar ve çizim kodu (0573M) aramayı kirletebilir.",
     "cozum": "Birleşik başlıklarda tekrarı kaldırmak, çizim kodlarını ayrı alana almak. Chunking adımında ele alınacak.",
     "durum": "açık"},
    {"baslik": "Kılavuz içi sayfa atıfları basılı numarayla",
     "ne_oldu": "Brother arıza tablosundaki 'Page' sütunu (67, 65, 16...) basılı numaraları gösteriyor. Sistem bu "
                "atıfları takip etmek isterse basılı numarayı PDF sayfasına çevirmesi gerekir (67 → PDF s.78).",
     "cozum": "Ingestion'da tüm sayfalar için basılı → fiziksel numara eşleme tablosu çıkarılmalı.", "durum": "açık"},
    {"baslik": "Tarayıcıdaki vurgu (3a) gözle doğrulanmadı",
     "ne_oldu": "streamlit-pdf-viewer görüntüleyicisinin hatasız açıldığı otomatik testle doğrulandı, ama vurgunun "
                "tarayıcıda doğru yere düştüğü henüz gözle kontrol edilmedi.",
     "cozum": "`streamlit run faz1-test.py -- --viewer` ile açılıp üç dokümanda kontrol edilmeli.", "durum": "açık"},
]




def bottomleft_to_topleft(bbox: list[float], page_height: float) -> list[float]:
    """PDF koordinatı (orijin sol-alt) -> resim koordinatı (orijin sol-üst). [l, t, r, b]."""
    l, t, r, b = bbox
    return [l, page_height - t, r, page_height - b]


def pt_to_px(bbox_tl: list[float], dpi: int = DPI) -> list[int]:
    """Point (1/72 inç) -> piksel. bbox sol-üst orijinli olmalı."""
    s = dpi / 72.0
    return [round(v * s) for v in bbox_tl]


def bbox_inside_page(bbox_tl: list[float], page_w: float, page_h: float, tol: float = 1.0) -> bool:
    l, t, r, b = bbox_tl
    return -tol <= l < r <= page_w + tol and -tol <= t < b <= page_h + tol


def keyword_score(text: str, keywords: list[str]) -> int:
    return sum(len(re.findall(k, text, flags=re.IGNORECASE)) for k in keywords)


def select_best_element(elements: list[dict], keywords: list[str]) -> dict | None:
    """En çok anahtar kelime eşleşmesi olan öğe. Eşitlikte daha kısa metin (daha kesin vurgu).
    Satırlarına ayrılmış tablolar bütün olarak aday olmaz, satırları aday olur."""
    candidates = [e for e in elements if not (e.get("label") == "table" and e.get("has_rows"))]
    scored = [(keyword_score(e["text"], keywords), -len(e["text"]), e) for e in candidates if e["text"]]
    scored = [s for s in scored if s[0] > 0]
    if not scored:
        return None
    return max(scored, key=lambda s: (s[0], s[1]))[2]


def _normalize_repeating(text: str) -> str:
    return re.sub(r"\d+", "#", text.strip().lower())


def find_repeating_furniture(elements: list[dict], min_ratio: float = 0.5, edge: float = 0.12) -> set[str]:
    """Birden çok sayfada, sayfanın üst/alt kenarında tekrar eden metinler (üst/alt bilgi)."""
    pages = {e["page"] for e in elements}
    if len(pages) < 2:
        return set()
    seen: dict[str, set[int]] = {}
    for e in elements:
        _, t, _, b = e["bbox_tl"]
        h = e["page_h"]
        if t <= h * edge or b >= h * (1 - edge):
            seen.setdefault(_normalize_repeating(e["text"]), set()).add(e["page"])
    need = max(2, int(len(pages) * min_ratio))
    return {k for k, v in seen.items() if len(v) >= need and k}


def remove_furniture(elements: list[dict]) -> tuple[list[dict], list[dict]]:
    """Üst/alt bilgileri ayıkla. (kalanlar, atılanlar)"""
    furn = find_repeating_furniture(elements)
    kept, dropped = [], []
    for e in elements:
        is_furn = e.get("label") in ("page_header", "page_footer") or _normalize_repeating(e["text"]) in furn
        (dropped if is_furn else kept).append(e)
    return kept, dropped


def union_bbox(boxes: list[list[float]]) -> list[float]:
    return [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]


def group_table_rows(cells: list[dict]) -> list[dict]:
    """Tablo hücrelerini mantıksal satırlara grupla.

    cells: {r0, r1, c0, c1, text, bbox_tl (veya None), header (bool)}. r1/c1 hariç (exclusive).
    Birden çok ızgara satırına yayılan hücreler (ör. arıza tablosunda "Problem" hücresi, yanında
    birkaç "Possible cause" satırı) aynı mantıksal satırda toplanır: Her ızgara satırının "çapası",
    o satırı kapsayan en soldaki hücredir. Çapası aynı olan ardışık satırlar tek satırdır.
    Dönüş: [{text, bbox_tl, cells}], metin "Başlık: değer | Başlık: değer" biçiminde.
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
        parts = []
        for c in row_cells:
            h = headers.get(c["c0"])
            parts.append(f"{h}: {c['text'].strip()}" if h and h != c["text"].strip() else c["text"].strip())
        boxes = [c["bbox_tl"] for c in row_cells if c.get("bbox_tl")]
        rows.append({"text": " | ".join(parts), "bbox_tl": union_bbox(boxes) if boxes else None,
                     "cells": row_cells})
    return rows


GARBLED = re.compile(r"(?:\b\w{1,3}\s{2,}){3,}")


def find_garbled_spans(text: str) -> list[str]:
    """OCR bozukluğu şüphesi: kısa harf parçaları + çok boşluk ('ans     a    s  s       ams')."""
    return [m.group(0).strip() for m in GARBLED.finditer(text)]


def fmt_page(page: int, label: str | None) -> str:
    """Kullanıcıya gösterilecek sayfa: basılı numara farklıysa 's.90 (PDF s.101)'."""
    if label and label != str(page):
        return f"s.{label} (PDF s.{page})"
    return f"s.{page}"


def join_texts(a: str, b: str) -> str:
    """Satır sonu tirelemesini de birleştirerek iki metni birleştir."""
    a = a.rstrip()
    if a.endswith("-") and b[:1].islower():
        return a[:-1] + b.lstrip()
    return a + " " + b.lstrip()


def is_continuation(prev: dict, nxt: dict) -> bool:
    """prev sayfanın son paragrafı, nxt sonraki sayfanın ilk paragrafı: aynı paragraf mı?"""
    if nxt["page"] != prev["page"] + 1:
        return False
    if prev.get("label") not in ("text", "list_item", "paragraph"):
        return False
    if nxt.get("label") not in ("text", "list_item", "paragraph"):
        return False
    p, n = prev["text"].rstrip(), nxt["text"].lstrip()
    if not p or not n:
        return False
    return (not p.endswith(SENTENCE_END)) and (n[0].islower() or p.endswith("-") or p.endswith(","))


def merge_cross_page(elements: list[dict]) -> tuple[list[dict], list[dict]]:
    """Sayfa sınırında bölünmüş paragrafları birleştir. elements okuma sırasında ve
    üst/alt bilgilerden temizlenmiş olmalı. (birleşmiş liste, birleştirme kayıtları)"""
    out: list[dict] = []
    merges: list[dict] = []
    for e in elements:
        if out and is_continuation(out[-1], e):
            prev = out[-1]
            merged = dict(prev)
            merged["text"] = join_texts(prev["text"], e["text"])
            merged["boxes"] = prev["boxes"] + e["boxes"]
            merged["pages"] = sorted(set(prev["pages"]) | set(e["pages"]))
            out[-1] = merged
            merges.append({"from_page": prev["page"], "to_page": e["page"],
                           "end_of_prev": prev["text"][-80:], "start_of_next": e["text"][:80],
                           "merged_text": merged["text"]})
        else:
            out.append(e)
    return out, merges



# PDF  (pypdfium2 + Pillow + Docling)


def page_texts(pdf_path: Path) -> list[str]:
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(str(pdf_path))
    try:
        return [pdf[i].get_textpage().get_text_range() for i in range(len(pdf))]
    finally:
        pdf.close()


def find_candidate_pages(pdf_path: Path, keywords: list[str], top: int = 2) -> list[int]:
    """Metin katmanında anahtar kelimeleri en çok içeren sayfalar (1 tabanlı).
    Taranmış PDF'te metin katmanı yoksa boş liste döner."""
    texts = page_texts(pdf_path)
    scored = sorted(((keyword_score(t, keywords), i + 1) for i, t in enumerate(texts)), reverse=True)
    return sorted(p for s, p in scored[:top] if s > 0)


def has_text_layer(pdf_path: Path, min_chars: int = 50) -> bool:
    return any(len(t.strip()) >= min_chars for t in page_texts(pdf_path))


def expand_pages(pages: list[int], n_pages: int) -> list[int]:
    """Sayfa geçişi kontrolü için her sayfanın bir öncesi ve sonrasını da al."""
    out = set()
    for p in pages:
        out.update(x for x in (p - 1, p, p + 1) if 1 <= x <= n_pages)
    return sorted(out)


def page_count(pdf_path: Path) -> int:
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(str(pdf_path))
    try:
        return len(pdf)
    finally:
        pdf.close()


def render_page(pdf_path: Path, page_no: int, dpi: int = DPI):
    """page_no 1 tabanlı. PIL.Image döner."""
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(str(pdf_path))
    try:
        return pdf[page_no - 1].render(scale=dpi / 72.0).to_pil().convert("RGB")
    finally:
        pdf.close()


def draw_boxes(img, boxes_tl_pt: list[list[float]], dpi: int = DPI, color=(255, 230, 0),
               fill_alpha: int = 90, outline=(230, 120, 0), width: int = 3):
    """Yarı saydam kutular + kenar çizgisi. Varsayılan: sarı vurgu."""
    from PIL import Image, ImageDraw
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for box in boxes_tl_pt:
        px = pt_to_px(box, dpi)
        d.rectangle(px, fill=color + (fill_alpha,), outline=outline + (255,), width=width)
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def draw_context_and_highlight(img, context_boxes, highlight_boxes, dpi: int = DPI):
    """İki katmanlı vurgu: bağlam (ör. tablonun tamamı) açık mavi çerçeve, asıl cevap sarı."""
    if context_boxes:
        img = draw_boxes(img, context_boxes, dpi, color=(120, 170, 255), fill_alpha=20,
                         outline=(90, 140, 230), width=2)
    return draw_boxes(img, highlight_boxes, dpi)


def printed_page_label(pdf_path: Path, page_no: int, bands=(0.06, 0.09, 0.12)) -> str | None:
    """Sayfanın alt (yoksa üst) bilgisindeki basılı sayfa numarası. Metin katmanı yoksa None.
    Örn. Brother S-7300A'nın 101. PDF sayfasının altında '90' yazar.
    Bant kenardan içeri doğru kademeli genişletilir: Geniş bant gövde metnindeki sayıları
    (ör. '1: Reverse OFF') da yakalayabildiği için kenara en yakın bantta bulunan numara seçilir."""
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(str(pdf_path))
    try:
        page = pdf[page_no - 1]
        w, h = page.get_size()
        tp = page.get_textpage()
        for edge in ("bottom", "top"):
            for band in bands:
                bottom, top = (0, h * band) if edge == "bottom" else (h * (1 - band), h)
                text = tp.get_text_bounded(left=0, bottom=bottom, right=w, top=top) or ""
                nums = re.findall(r"(?<![\w/.-])(\d{1,4})(?![\w/.:-])", text)
                if nums:
                    return nums[0]
        return None
    finally:
        pdf.close()


def text_in_bbox(pdf_path: Path, page_no: int, bbox_tl: list[float]) -> str:
    """PDF'in kendi metin katmanında (taranmışsa mevcut OCR katmanı) bir kutunun içindeki metin."""
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(str(pdf_path))
    try:
        page = pdf[page_no - 1]
        _, h = page.get_size()
        l, t, r, b = bbox_tl
        return page.get_textpage().get_text_bounded(left=l, bottom=h - b, right=r, top=h - t) or ""
    finally:
        pdf.close()


def docling_parse(pdf_path: Path, pages: list[int], force_ocr: bool) -> list[dict]:
    """Docling ile verilen sayfaları parse et. Öğeleri okuma sırasında döndürür."""
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    opts = PdfPipelineOptions()
    opts.do_table_structure = True
    opts.do_ocr = True
    if force_ocr:
        opts.ocr_options.force_full_page_ocr = True
    conv = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)})

    # Birbirinden uzak sayfa grupları (ör. 77-79 ve 100-102) ayrı ayrı parse edilir.
    # Tek aralık verilirse aradaki tüm sayfalar da gereksiz yere parse edilir.
    elements = []
    for group in contiguous_groups(pages):
        result = conv.convert(str(pdf_path), page_range=(group[0], group[-1]))
        elements += _doc_to_elements(result.document, pages, id_prefix=f"p{group[0]}_")
    return elements


def contiguous_groups(pages: list[int]) -> list[list[int]]:
    """[11, 12, 13, 18, 19] -> [[11, 12, 13], [18, 19]]"""
    groups: list[list[int]] = []
    for p in sorted(set(pages)):
        if groups and p == groups[-1][-1] + 1:
            groups[-1].append(p)
        else:
            groups.append([p])
    return groups


def _doc_to_elements(doc, pages: list[int], id_prefix: str = "") -> list[dict]:
    elements = []
    for idx, (item, _level) in enumerate(doc.iterate_items()):
        prov = getattr(item, "prov", None) or []
        if not prov:
            continue
        label = str(getattr(item, "label", "")).split(".")[-1].lower()
        if hasattr(item, "export_to_markdown") and label == "table":
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
        first = boxes[0]
        el = {
            "id": f"{id_prefix}e{idx}", "label": label, "text": text,
            "page": first["page"], "bbox_tl": first["bbox_tl"],
            "page_w": first["page_w"], "page_h": first["page_h"],
            "pages": sorted({b["page"] for b in boxes}), "boxes": boxes,
        }
        elements.append(el)
        if label == "table":
            rows = _table_row_elements(item, el)
            el["has_rows"] = bool(rows)
            elements += rows
    return elements


def _table_row_elements(item, table_el: dict) -> list[dict]:
    """Docling tablosundan satır öğeleri. Tablo tek sayfada varsayılır (ilk prov sayfası)."""
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
        out.append({
            "id": f"{table_el['id']}_r{i}", "label": "table_row", "text": row["text"],
            "page": table_el["page"], "bbox_tl": row["bbox_tl"],
            "page_w": table_el["page_w"], "page_h": page_h,
            "pages": [table_el["page"]], "boxes": [box],
            "parent_id": table_el["id"], "context_boxes": table_el["boxes"],
        })
    return out


# --------------------------------------------------------------------------------------
# Deneme akışı
# --------------------------------------------------------------------------------------

@dataclass
class DocResult:
    doc_id: str
    pages: list[int] = field(default_factory=list)
    n_elements: int = 0
    selected: dict | None = None
    checks: dict = field(default_factory=dict)
    merges: list[dict] = field(default_factory=list)
    dropped_furniture: list[str] = field(default_factory=list)
    images: list[str] = field(default_factory=list)
    page_labels: dict = field(default_factory=dict)   # {"101": "90"} PDF sayfası -> basılı numara
    warnings: list[str] = field(default_factory=list)
    text_layer_compare: str | None = None             # OCR'lı dokümanda PDF'in kendi metin katmanı
    seconds: float = 0.0
    error: str | None = None


def run_doc(cfg: DocConfig, pages_override: list[int] | None = None) -> DocResult:
    res = DocResult(cfg.doc_id)
    t0 = time.time()
    out_dir = OUTPUT / cfg.doc_id
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in list(out_dir.glob("*.png")) + list(out_dir.glob("*.json")):  # eski çıktılar raporu yanıltmasın
        old.unlink()
    pdf_path = MANUALS / cfg.file
    try:
        n = page_count(pdf_path)
        base = pages_override or cfg.pages or find_candidate_pages(pdf_path, cfg.keywords)
        if not base:
            if has_text_layer(pdf_path):
                raise RuntimeError("Anahtar kelime hiçbir sayfada bulunamadı. --pages ile sayfa verin.")
            print(f"[{cfg.doc_id}] Metin katmanı yok (taranmış). Tüm sayfalar OCR'lanacak, uzun sürebilir.")
            base = list(range(1, n + 1))
        res.pages = expand_pages(base, n)
        print(f"[{cfg.doc_id}] Parse edilecek sayfalar: {res.pages}")

        # 1. Parse
        elements = docling_parse(pdf_path, res.pages, cfg.force_ocr)
        res.n_elements = len(elements)
        (out_dir / "elements.json").write_text(json.dumps(elements, ensure_ascii=False, indent=2), "utf-8")

        # 6 (hazırlık). Üst/alt bilgi temizliği + sayfa geçişi birleştirme
        clean, dropped = remove_furniture(elements)
        res.dropped_furniture = sorted({d["text"] for d in dropped})
        merged, res.merges = merge_cross_page(clean)

        # 2. Hedef öğeyi seç (birleşmiş liste üzerinden: paragraf iki sayfadaysa iki kutu gelir)
        sel = select_best_element(merged, cfg.keywords)
        res.selected = sel
        (out_dir / "selected.json").write_text(json.dumps(sel, ensure_ascii=False, indent=2), "utf-8")
        if sel is None:
            raise RuntimeError("Anahtar kelimeleri içeren öğe bulunamadı.")

        # 5. Otomatik kontroller
        res.checks = {
            "secilen_metin_anahtar_kelime_iceriyor": keyword_score(sel["text"], cfg.keywords) > 0,
            "tum_kutular_sayfa_icinde": all(bbox_inside_page(b["bbox_tl"], b["page_w"], b["page_h"])
                                           for b in sel["boxes"]),
            "secilen_metinde_ust_alt_bilgi_yok": not any(d.lower() in sel["text"].lower()
                                                         for d in res.dropped_furniture if len(d) > 5),
        }

        # Basılı sayfa numaraları (kullanıcıya "s.90 (PDF s.101)" gösterilir)
        for page in sorted(set(sel["pages"]) | set(res.pages)):
            res.page_labels[str(page)] = printed_page_label(pdf_path, page)

        # OCR kalite uyarısı (sessiz hata riskine karşı)
        garbled = find_garbled_spans(sel["text"])
        if garbled:
            res.warnings.append(f"Seçilen metinde bozuk OCR şüphesi: {garbled}")
        if cfg.force_ocr:
            res.text_layer_compare = " ".join(text_in_bbox(pdf_path, b["page"], b["bbox_tl"])
                                              for b in sel["boxes"]).strip()

        # 3b. Sayfayı PNG'ye çevir + kutu çiz (seçilen öğenin her sayfası).
        # Tablo satırıysa tablonun tamamı bağlam olarak açık mavi, satır sarı çizilir.
        for page in sel["pages"]:
            boxes = [b["bbox_tl"] for b in sel["boxes"] if b["page"] == page]
            ctx = [b["bbox_tl"] for b in sel.get("context_boxes", []) if b["page"] == page]
            img = draw_context_and_highlight(render_page(pdf_path, page), ctx, boxes)
            path = out_dir / f"highlight_p{page:02d}.png"
            img.save(path)
            res.images.append(str(path.relative_to(ROOT)))

        # 6. Sayfa geçişi birleşmelerini de görselleştir
        for m in res.merges:
            item = next(e for e in merged if m["merged_text"] == e["text"])
            for page in item["pages"]:
                boxes = [b["bbox_tl"] for b in item["boxes"] if b["page"] == page]
                path = out_dir / f"transition_p{page:02d}.png"
                draw_boxes(render_page(pdf_path, page), boxes, color=(0, 200, 255)).save(path)
                res.images.append(str(path.relative_to(ROOT)))
        (out_dir / "transitions.json").write_text(json.dumps(res.merges, ensure_ascii=False, indent=2), "utf-8")

        # 3a için: streamlit-pdf-viewer annotation formatı (sol-üst orijin, point)
        def _ann(b, color):
            return {"page": b["page"], "x": b["bbox_tl"][0], "y": b["bbox_tl"][1],
                    "width": b["bbox_tl"][2] - b["bbox_tl"][0], "height": b["bbox_tl"][3] - b["bbox_tl"][1],
                    "color": color}
        ann = [_ann(b, "orange") for b in sel["boxes"]] + [_ann(b, "lightblue") for b in sel.get("context_boxes", [])]
        (out_dir / "annotations.json").write_text(json.dumps(ann, indent=2), "utf-8")
    except Exception as exc:  # deneme raporunda hata da görünsün
        res.error = f"{type(exc).__name__}: {exc}"
    res.seconds = round(time.time() - t0, 1)
    (out_dir / "result.json").write_text(json.dumps(asdict(res), ensure_ascii=False, indent=2), "utf-8")
    return res


def load_results() -> list[DocResult]:
    """faz1_output altındaki tüm doküman sonuçları (rapor tüm dokümanları göstersin diye)."""
    out = []
    for doc_id in DOCS:
        p = OUTPUT / doc_id / "result.json"
        if p.exists():
            out.append(DocResult(**json.loads(p.read_text("utf-8"))))
    return out


ELEMENT_NAMES = {"text": "paragraf", "table_row": "tablo satırı", "table": "tablo", "list_item": "liste maddesi",
                 "section_header": "başlık", "picture": "görsel", "caption": "başlık/açıklama"}
CHECK_NAMES = {"secilen_metin_anahtar_kelime_iceriyor": "Seçilen metin soruyla ilgili anahtar kelimeleri içeriyor",
               "tum_kutular_sayfa_icinde": "Vurgu kutuları sayfanın içinde",
               "secilen_metinde_ust_alt_bilgi_yok": "Seçilen metne üst/alt bilgi karışmamış"}


def _pages_str(r: DocResult, pages: list[int]) -> str:
    return ", ".join(fmt_page(p, r.page_labels.get(str(p))) for p in pages)


def _md_text(text: str, limit: int = 600) -> str:
    """Rapor için tek satırlık alıntı (tablo satırlarındaki | işaretleri bozmasın)."""
    t = re.sub(r"\s+", " ", text).strip()
    return (t[:limit] + "…") if len(t) > limit else t


def write_report(results: list[DocResult]) -> Path:
    def status(r: DocResult) -> str:
        if r.error:
            return "❌ Hata"
        if not all(r.checks.values()):
            return "❌ Kontrol başarısız"
        return "⚠️ Uyarı var" if r.warnings else "✅ Başarılı"

    lines = [
        "# Faz 1 denemesi raporu", "",
        f"_Son güncelleme: {time.strftime('%Y-%m-%d %H:%M')}_", "",
        "**Amaç (Faz 1 kontrol noktası):** Bir manuelden ilgili parçayı sayfa no + bbox ile çıkarıp sayfayı vurgulu "
        "gösterebiliyor muyuz? Ayrıntılı plan: `Pre/notes/kaynak-gosterme.md`.", "",
        "**Başarı ölçütü:** Sarı kutu doğru paragrafın/satırın üstüne düşüyor mu? Otomatik kontrollere ek olarak "
        "aşağıdaki görseller **gözle** kontrol edilmeli.", "",
        "## Özet", "",
        "| Doküman | Soru | Sonuç | Bulunan kaynak | Süre |",
        "|---------|------|-------|----------------|------|",
    ]
    for r in results:
        cfg = DOCS.get(r.doc_id)
        src = "-"
        if r.selected:
            src = f"{ELEMENT_NAMES.get(r.selected['label'], r.selected['label'])}, {_pages_str(r, r.selected['pages'])}"
        lines.append(f"| `{r.doc_id}` | {cfg.question if cfg else ''} | {status(r)} | {src} | {r.seconds} sn |")
    lines.append("")

    for r in results:
        cfg = DOCS.get(r.doc_id)
        lines += [f"## {r.doc_id}", ""]
        if cfg:
            lines += [f"**Soru:** {cfg.question}  ", f"**Dosya:** `{cfg.file}`" + ("  (taranmış, OCR ile)" if cfg.force_ocr else ""), ""]
        if r.error:
            lines += [f"❌ **Hata:** {r.error}", ""]
        lines += [f"- Parse edilen sayfalar: {_pages_str(r, r.pages)}",
                  f"- Çıkarılan öğe sayısı: {r.n_elements}", f"- Süre: {r.seconds} sn"]
        if r.selected:
            sel = r.selected
            lines += [f"- **Seçilen öğe:** {ELEMENT_NAMES.get(sel['label'], sel['label'])}, "
                      f"**{_pages_str(r, sel['pages'])}**", "", f"> {_md_text(sel['text'])}", ""]
        for k, v in r.checks.items():
            lines.append(f"- {'✅' if v else '❌'} {CHECK_NAMES.get(k, k)}")
        for w in r.warnings:
            lines.append(f"- ⚠️ {w}")
        if r.text_layer_compare is not None:
            lines += ["", "**Karşılaştırma:** Aynı kutunun içinde PDF'in kendi (önceden eklenmiş) OCR katmanındaki metin:", "",
                      f"> {_md_text(r.text_layer_compare)}", ""]
        lines.append(f"- Atılan üst/alt bilgiler: {', '.join(f'`{d}`' for d in r.dropped_furniture[:5]) or 'yok'}")
        lines.append(f"- Sayfa geçişinde birleştirilen paragraf: {len(r.merges)}")
        for m in r.merges[:3]:
            lines.append(f"  - {_pages_str(r, [m['from_page']])} → {_pages_str(r, [m['to_page']])}: "
                         f"\"…{_md_text(m['end_of_prev'])[-50:]}\" + \"{_md_text(m['start_of_next'])[:50]}…\"")
        if r.images:
            lines += ["", "**Görseller** (sarı: bulunan kaynak, açık mavi: bağlam, örn. tablonun tamamı, "
                      "turkuaz: sayfa geçişi birleştirmesi):", ""]
            for img in r.images:
                rel = Path(img).relative_to("faz1_output").as_posix()
                lines += [f"![{Path(img).name}]({rel})", ""]
        lines.append("")

    lines += ["## Yaşanan problemler ve çözümler", "",
              "| # | Problem | Ne oldu? | Çözüm | Durum |", "|---|---------|----------|-------|-------|"]
    for i, f in enumerate(FINDINGS, 1):
        mark = "✅ Çözüldü" if f["durum"] == "çözüldü" else "🟡 Açık"
        lines.append(f"| {i} | {f['baslik']} | {f['ne_oldu']} | {f['cozum']} | {mark} |")
    lines.append("")

    path = OUTPUT / "report.md"
    path.write_text("\n".join(lines), "utf-8")
    return path


# --------------------------------------------------------------------------------------
# 3a: streamlit-pdf-viewer ile tarayıcıda gösterim
# --------------------------------------------------------------------------------------

def viewer_app():
    import streamlit as st
    from streamlit_pdf_viewer import pdf_viewer

    st.set_page_config(page_title="Faz 1: PDF vurgu", layout="wide")
    st.title("Faz 1: streamlit-pdf-viewer ile vurgu (3a)")
    doc_id = st.selectbox("Doküman", list(DOCS))
    ann_path = OUTPUT / doc_id / "annotations.json"
    if not ann_path.exists():
        st.warning(f"Önce `python faz1-test.py --doc {doc_id}` çalıştırın.")
        return
    annotations = json.loads(ann_path.read_text("utf-8"))
    sel = json.loads((OUTPUT / doc_id / "selected.json").read_text("utf-8"))
    left, right = st.columns([1, 2])
    with left:
        st.subheader("Seçilen öğe")
        res_path = OUTPUT / doc_id / "result.json"
        labels = json.loads(res_path.read_text("utf-8")).get("page_labels", {}) if res_path.exists() else {}
        st.caption("Kaynak: " + ", ".join(fmt_page(p, labels.get(str(p))) for p in sel["pages"]))
        st.write(sel["text"])
        st.json(annotations)
    with right:
        pdf_viewer(str(MANUALS / DOCS[doc_id].file), annotations=annotations,
                   scroll_to_annotation=1, render_text=True, height=900)


def _in_streamlit() -> bool:
    """`streamlit run` veya Streamlit test aracı (AppTest) altında mı çalışıyoruz?"""
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        return get_script_run_ctx() is not None
    except ImportError:
        return False


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--doc", choices=list(DOCS), help="Tek doküman çalıştır")
    ap.add_argument("--pages", type=int, nargs="+", help="Sayfaları elle ver (1 tabanlı)")
    ap.add_argument("--viewer", action="store_true", help="streamlit run ile 3a görüntüleyici")
    ap.add_argument("--report-only", action="store_true", help="Parse etmeden, mevcut sonuçlardan raporu yeniden üret")
    args = ap.parse_args(argv)

    if args.viewer:
        viewer_app()
        return 0

    if args.report_only:
        print(f"Rapor: {write_report(load_results()).relative_to(ROOT)}")
        return 0

    targets = [DOCS[args.doc]] if args.doc else list(DOCS.values())
    results = [run_doc(cfg, args.pages) for cfg in targets]
    report = write_report(load_results())
    for r in results:
        status = "HATA" if r.error else ("OK" if all(r.checks.values()) else "KONTROL ET")
        print(f"[{r.doc_id}] {status} ({r.seconds} sn) {r.error or ''}")
    print(f"Rapor: {report.relative_to(ROOT)}")
    return 1 if any(r.error for r in results) else 0


if __name__ == "__main__":
    if _in_streamlit():
        viewer_app()
    else:
        sys.exit(main())
