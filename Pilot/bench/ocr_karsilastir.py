"""Yerel OCR karşılaştırması, CPU (docs/PLAN-OCR.md §8; karar 2026-11-06): OCRmyPDF ve Docling + Tesseract.
Model ve bulut yok. Tesseract kullanıcı klasöründe (tur + eng); OCRmyPDF Ghostscript'siz çalıştırılır
(--rasterizer pypdfium, --output-type pdf).

Testler:
  i   bilinen OCR hataları: pantolon şartnamesinin (taranmış, OCR katmanlı) hatalı sayfaları, yeniden OCR
      ("112 inch" = 1/2, "114 inch" = 1/4, "7-114" = 7-1/4, "3116" = 3/16, "IS min" = 15 min)
  ii  metin katmanı silinmiş sentetik sayfalar: dijital sayfalar 300 dpi görüntü + bozulma (eğiklik, bulanıklık, JPEG,
      gri ton); doğru cevap orijinal metin katmanı (Docling, OCR kapalı). Sayısal değer duyarlılığı/kesinliği, metin
      benzerliği, tablo hücresi, kutu örtüşmesi (IoU, sayfa vurgusu)
  iii Türkçe karakterli sentetik sayfa (ç ğ ı ö ş ü İ)
  iv  sayfa başına süre
  ek  Strickland'ın metin katmanı olmayan sayfaları; Granovsky'nin bozuk (harf aralıklı) katmanı (kalite skoru önce/sonra)
Her iki aday için yapı Docling'den okunur: OCRmyPDF çıktısı Docling (OCR kapalı) ile, Docling + Tesseract kendi içinde.

Kullanım (Pilot klasöründe):  $env:PILOT_ANSWER_MODE = "bugun"; python -m bench.ocr_karsilastir
Çıktı: eval/bench/ocr/ocr_karsilastirma_<tarih>.md, ham/ocr_karsilastirma.json; ara PDF'ler data/ocr_test/ (git dışı)
"""
from __future__ import annotations

import difflib
import io
import json
import os
import re
import subprocess
import time
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from bench.common import PILOT_DIR

TESS_DIR = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Tesseract-OCR"
OCRMYPDF = Path(os.sys.executable).parent / "ocrmypdf.exe"
WORK = PILOT_DIR / "data" / "ocr_test"
OUT = PILOT_DIR / "eval" / "bench" / "ocr"
KNOWN = {   # bilinen hata → doğru yazım (pantolon şartnamesi OCR katmanı)
    "112 inch": (r"\b112\s*inch", r"\b1/2\s*inch"),
    "114 inch": (r"\b114\s*inch", r"\b1/4\s*inch"),
    "7-114": (r"\b7-114\b", r"\b7-1/4\b"),
    "3116": (r"\b3116\b", r"\b3/16\b"),
    "IS min": (r"\bIS min", r"\b15 min"),
}
KNOWN_PAGES = [10, 11, 18, 19, 20, 22, 25, 37, 38]          # chunks.jsonl'de bu hataların geçtiği sayfalar
SYNTH = {"gl-pd-14-04a": [21, 22, 23, 24, 25], "brother-s7300a": [12, 13], "juki-mo6800s": [3]}
TR_TEXT = ("İğne ipliği gerginliği: Dikiş başında ipliğin çözülmesini önlemek için üst ipliği şöyle ayarlayın. "
           "Çağanoz ucu, iğne mili 1,8 mm yükseldiğinde iğnenin ortasına gelmelidir. Ölçü tablosu: kol boyu 61 cm, "
           "göğüs çevresi 104 cm (± 2), dikiş sıklığı inç başına 11 (± 1). Şerit, düğme ve fermuar dikişleri "
           "özel ayarlıdır; ığ, üğ, öş, çş harfleri doğru okunmalı. Işık şiddeti, iş güvenliği, ölçüm gözlüğü.")


def _env() -> dict:
    env = dict(os.environ)
    env["PATH"] = str(TESS_DIR) + os.pathsep + env.get("PATH", "")
    return env


def subset(src: Path, pages: list[int], dst: Path) -> Path:
    import pymupdf
    out = pymupdf.open()
    with pymupdf.open(str(src)) as d:
        for p in pages:
            out.insert_pdf(d, from_page=p - 1, to_page=p - 1)
    out.save(str(dst))
    return dst


def image_only(src: Path, pages: list[int], dst: Path, degrade: bool = True) -> Path:
    """Sayfaları 300 dpi görüntüye çevirip metin katmanı olmayan PDF yapar (sentetik tarama)."""
    import pymupdf
    from PIL import Image, ImageFilter
    out = pymupdf.open()
    with pymupdf.open(str(src)) as d:
        for p in pages:
            page = d[p - 1]
            pix = page.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("L")
            if degrade:
                img = img.rotate(1.2, expand=False, fillcolor=255).filter(ImageFilter.GaussianBlur(0.7))
                buf = io.BytesIO()
                img.save(buf, "JPEG", quality=70)
                img = Image.open(io.BytesIO(buf.getvalue()))
            buf = io.BytesIO()
            img.save(buf, "PNG")
            np = out.new_page(width=page.rect.width, height=page.rect.height)
            np.insert_image(np.rect, stream=buf.getvalue())
    out.save(str(dst))
    return dst


def turkish_pdfs() -> tuple[Path, Path]:
    import pymupdf
    font = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "arial.ttf"
    d = pymupdf.open()
    page = d.new_page()
    page.insert_textbox(pymupdf.Rect(60, 60, 540, 780), TR_TEXT, fontsize=12, fontfile=str(font), fontname="arial")
    digital = WORK / "turkce_dijital.pdf"
    d.save(str(digital))
    return digital, image_only(digital, [1], WORK / "turkce_goruntu.pdf")


def run_ocrmypdf(inp: Path, out: Path, mode: str) -> float:
    """mode: skip (metin katmanı olan sayfayı atla) | redo (eski OCR katmanını yeniden yap) | force."""
    flag = {"skip": "--skip-text", "redo": "--redo-ocr", "force": "--force-ocr"}[mode]
    t = time.perf_counter()
    r = subprocess.run([str(OCRMYPDF), "-l", "tur+eng", flag, "--rasterizer", "pypdfium", "--output-type", "pdf",
                        "--pdfa-backend", "internal", "-q", str(inp), str(out)], env=_env(), capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"ocrmypdf {r.returncode}: {r.stderr[-400:]}")
    return time.perf_counter() - t


_CONV: dict[str, Any] = {}


def docling_doc(path: Path, ocr: bool):
    """Docling belgesi: OCR kapalı (bugünkü ayrıştırma) ya da Tesseract tam sayfa OCR (tur + eng)."""
    key = "ocr" if ocr else "plain"
    if key not in _CONV:
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import OcrMode, PdfPipelineOptions, TesseractCliOcrOptions
        from docling.document_converter import DocumentConverter, PdfFormatOption
        opts = PdfPipelineOptions()
        opts.do_table_structure = True
        opts.do_ocr = ocr
        if ocr:
            opts.ocr_options = TesseractCliOcrOptions(lang=["tur", "eng"], mode=OcrMode.FULL_PAGE,
                                                      tesseract_cmd=str(TESS_DIR / "tesseract.exe"))
        _CONV[key] = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)})
    os.environ["PATH"] = str(TESS_DIR) + os.pathsep + os.environ.get("PATH", "")
    t = time.perf_counter()
    doc = _CONV[key].convert(str(path)).document
    return doc, time.perf_counter() - t


def pages_of(doc) -> dict[int, dict[str, Any]]:
    """Sayfa başına metin, tablo hücreleri ve metin öğesi kutuları."""
    from docling_core.types.doc import TableItem
    out: dict[int, dict[str, Any]] = {}
    for item, _lvl in doc.iterate_items():
        if not getattr(item, "prov", None):
            continue
        pg = item.prov[0].page_no
        d = out.setdefault(pg, {"text": [], "cells": 0, "boxes": []})
        if isinstance(item, TableItem):
            cells = [c.text for c in item.data.table_cells if c.text.strip()]
            d["cells"] += len(cells)
            d["text"] += cells
        elif getattr(item, "text", ""):
            d["text"].append(item.text)
            b = item.prov[0].bbox.to_top_left_origin(doc.pages[pg].size.height)
            d["boxes"].append((item.text, (b.l, b.t, b.r, b.b)))
    for d in out.values():
        d["text"] = " ".join(d["text"])
    return out


def _nums(text: str) -> Counter:
    from pilot.verify import numbers_in
    return Counter(re.findall(r"\d+(?:[.,/]\d+)*", text)) if text else Counter()


def _iou(a, b) -> float:
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


def compare(gt: dict, got: dict) -> dict[str, float]:
    """Sayısal değer duyarlılık/kesinlik (sayı dizileri, kesir dahil), metin benzerliği, tablo hücresi, kutu IoU."""
    tp = fn = fp = 0
    sims, ious, cells_gt, cells_got = [], [], 0, 0
    for pg, g in gt.items():
        o = got.get(pg, {"text": "", "cells": 0, "boxes": []})
        a, b = _nums(g["text"]), _nums(o["text"])
        tp += sum((a & b).values())
        fn += sum((a - b).values())
        fp += sum((b - a).values())
        norm = lambda s: re.sub(r"\s+", " ", s).strip().lower()
        sims.append(difflib.SequenceMatcher(None, norm(g["text"]), norm(o["text"])).ratio())
        cells_gt += g["cells"]
        cells_got += o["cells"]
        for text, box in g["boxes"]:
            best = max(((difflib.SequenceMatcher(None, text, t2).ratio(), b2) for t2, b2 in o["boxes"]),
                       default=(0, None), key=lambda x: x[0])
            if best[0] >= 0.8:
                ious.append(_iou(box, best[1]))
    return {"sayi_duyarlilik": tp / max(tp + fn, 1), "sayi_kesinlik": tp / max(tp + fp, 1),
            "metin_benzerlik": sum(sims) / max(len(sims), 1), "tablo_hucre": f"{cells_got}/{cells_gt}",
            "kutu_iou": sum(ious) / max(len(ious), 1), "kutu_eslesen": len(ious)}


def known_errors(text: str) -> dict[str, tuple[int, int]]:
    return {k: (len(re.findall(bad, text)), len(re.findall(good, text))) for k, (bad, good) in KNOWN.items()}


def main() -> None:
    from bench import require_mode
    require_mode("bugun")
    from pilot.registry import BY_ID
    from pilot.text_layer import check_pdf, quality
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    res: dict[str, Any] = {"tarih": time.strftime("%Y-%m-%d %H:%M"), "tesseract": str(TESS_DIR)}
    log = lambda m: print(f"{time.strftime('%H:%M:%S')} {m}", flush=True)

    # (i) bilinen hatalar: pantolon
    src = subset(BY_ID["gl-pd-07-14a"].path, KNOWN_PAGES, WORK / "pantolon_hatali.pdf")
    base = " ".join(p.get_text() for p in __import__("pymupdf").open(str(src)))
    t_my = run_ocrmypdf(src, WORK / "pantolon_ocrmypdf.pdf", "redo")
    my = " ".join(p.get_text() for p in __import__("pymupdf").open(str(WORK / "pantolon_ocrmypdf.pdf")))
    dt_doc, t_dt = docling_doc(src, ocr=True)
    dt = " ".join(d["text"] for d in pages_of(dt_doc).values())
    res["i_bilinen_hatalar"] = {"sayfa": len(KNOWN_PAGES), "bugunku_katman": known_errors(base),
                                "ocrmypdf_redo": known_errors(my), "docling_tesseract": known_errors(dt),
                                "sure_sn_sayfa": {"ocrmypdf": t_my / len(KNOWN_PAGES), "docling_tesseract": t_dt / len(KNOWN_PAGES)}}
    log(f"(i) {res['i_bilinen_hatalar']}")

    # (ii) sentetik: metin katmanı silinmiş sayfalar
    rows = []
    for did, pgs in SYNTH.items():
        orig = subset(BY_ID[did].path, pgs, WORK / f"{did}_orijinal.pdf")
        img = image_only(BY_ID[did].path, pgs, WORK / f"{did}_goruntu.pdf")
        gt_doc, _ = docling_doc(orig, ocr=False)
        gt = pages_of(gt_doc)
        t1 = run_ocrmypdf(img, WORK / f"{did}_ocrmypdf.pdf", "skip")
        my_doc, t1b = docling_doc(WORK / f"{did}_ocrmypdf.pdf", ocr=False)
        dt_doc, t2 = docling_doc(img, ocr=True)
        rows.append({"belge": did, "sayfa": len(pgs),
                     "ocrmypdf": {**compare(gt, pages_of(my_doc)), "sn_sayfa": (t1 + t1b) / len(pgs), "sn_sayfa_yalniz_ocr": t1 / len(pgs)},
                     "docling_tesseract": {**compare(gt, pages_of(dt_doc)), "sn_sayfa": t2 / len(pgs)}})
        log(f"(ii) {did} {rows[-1]}")
    res["ii_sentetik"] = rows

    # (iii) Türkçe karakter
    dig, img = turkish_pdfs()
    t1 = run_ocrmypdf(img, WORK / "turkce_ocrmypdf.pdf", "skip")
    my_t = __import__("pymupdf").open(str(WORK / "turkce_ocrmypdf.pdf"))[0].get_text()
    dt_doc, t2 = docling_doc(img, ocr=True)
    dt_t = " ".join(d["text"] for d in pages_of(dt_doc).values())
    tr = "çğıöşüİÇĞÖŞÜ"
    def tr_score(t: str) -> dict:
        n = lambda s: re.sub(r"\s+", " ", s).strip()
        return {"benzerlik": round(difflib.SequenceMatcher(None, n(TR_TEXT), n(t)).ratio(), 3),
                "turkce_harf": f"{sum(min(TR_TEXT.count(c), t.count(c)) for c in tr)}/{sum(TR_TEXT.count(c) for c in tr)}",
                "sayilar": f"{sum((_nums(TR_TEXT) & _nums(t)).values())}/{sum(_nums(TR_TEXT).values())}"}
    res["iii_turkce"] = {"ocrmypdf": {**tr_score(my_t), "sn": t1}, "docling_tesseract": {**tr_score(dt_t), "sn": t2}}
    log(f"(iii) {res['iii_turkce']}")

    # ek: Strickland metinsiz sayfalar, Granovsky bozuk katman
    stk = [c.page for c in check_pdf(BY_ID["strickland-1956"].path) if c.kind == "yok"]
    sub = subset(BY_ID["strickland-1956"].path, stk, WORK / "strickland_metinsiz.pdf")
    t1 = run_ocrmypdf(sub, WORK / "strickland_ocrmypdf.pdf", "skip")
    my_pages = [p.get_text() for p in __import__("pymupdf").open(str(WORK / "strickland_ocrmypdf.pdf"))]
    dt_doc, t2 = docling_doc(sub, ocr=True)
    dt_pages = pages_of(dt_doc)
    res["strickland_metinsiz"] = {
        "sayfa": len(stk), "sayfalar": stk,
        "ocrmypdf": {"metinli_sayfa(>=50 krk)": sum(len(t.strip()) >= 50 for t in my_pages),
                     "toplam_krk": sum(len(t) for t in my_pages), "sn_sayfa": t1 / max(len(stk), 1),
                     "ornek": [t.strip()[:120] for t in my_pages if len(t.strip()) >= 50][:3]},
        "docling_tesseract": {"metinli_sayfa(>=50 krk)": sum(len(d["text"].strip()) >= 50 for d in dt_pages.values()),
                              "toplam_krk": sum(len(d["text"]) for d in dt_pages.values()), "sn_sayfa": t2 / max(len(stk), 1)}}
    log(f"strickland {res['strickland_metinsiz']}")
    gpages = [10, 30, 60, 120, 180, 240]
    sub = subset(BY_ID["granovsky-1986"].path, gpages, WORK / "granovsky_ornek.pdf")
    before = [quality(p.get_text())[0] for p in __import__("pymupdf").open(str(sub))]
    t1 = run_ocrmypdf(sub, WORK / "granovsky_ocrmypdf.pdf", "redo")
    after_my = [quality(p.get_text())[0] for p in __import__("pymupdf").open(str(WORK / "granovsky_ocrmypdf.pdf"))]
    t1f = run_ocrmypdf(sub, WORK / "granovsky_ocrmypdf_force.pdf", "force")
    after_myf = [quality(p.get_text())[0] for p in __import__("pymupdf").open(str(WORK / "granovsky_ocrmypdf_force.pdf"))]
    dt_doc, t2 = docling_doc(sub, ocr=True)
    after_dt = [quality(d["text"])[0] for d in pages_of(dt_doc).values()]
    res["granovsky_bozuk_katman"] = {"sayfalar": gpages, "kalite_once": before, "ocrmypdf_redo": after_my,
                                     "ocrmypdf_force": after_myf, "docling_tesseract": after_dt,
                                     "sn_sayfa": {"ocrmypdf_redo": t1 / len(gpages), "ocrmypdf_force": t1f / len(gpages),
                                                  "docling_tesseract": t2 / len(gpages)}}
    log(f"granovsky {res['granovsky_bozuk_katman']}")
    (OUT / "ham").mkdir(parents=True, exist_ok=True)
    (OUT / "ham" / "ocr_karsilastirma.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1)[:6000])


if __name__ == "__main__":
    main()
