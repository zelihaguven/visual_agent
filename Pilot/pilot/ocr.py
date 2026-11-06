"""Yüklemede yerel OCR (karar 2026-11-06; docs/PLAN-OCR.md §9). Ağ ve model yok: OCRmyPDF + Tesseract, Ghostscript'siz.

Akış (belge başına, yüklemede bir kez):
1. Metin katmanı kontrolü (text_layer.check_pdf, özgün dosyada): sayfa sınıfı
     metin → OCR yok | yok → --skip-text | taranmis → --redo-ocr | zayif → --force-ocr
2. Dil sayfa başına, kayıttaki dil aralığından (DocMeta.lang_of → Tesseract dil verisi); her sayfaya tek dil. Aynı
   (bayrak, dil) sayfaları tek OCRmyPDF çağrısında (--pages). --rotate-pages: ters ya da yan dönmüş taranmış sayfa
   (Granovsky s.147–191) okunmadan önce döndürülür.
3. Sayfa sayfa seçim (karar 2026-11-06, ek 1): eski ve yeni katmanın anlamsız dizi skoru (text_layer.junk_score)
   karşılaştırılır; yeni katman daha kötüyse (skor farkı > SCORE_TOL) eski katman kalır. Tarayıcı yazılımının iyi
   OCR'ı (ör. FineReader) böylece kaybolmaz.
4. OCR sonrası kalite süzgeci (ek 1c): metni olmayan sayfanın yeni OCR metni skoru text_layer.OCR_MIN_SCORE'un
   altındaysa (çizim, levha: anlamsız dizi) alınmaz; sayfa görüntü sayfası kalır. Eşik bütün belgeler için tek.
5. Sonuç PDF config.OCR_DIR/<doc_id>.pdf (sayfa sayısı ve sırası özgünle aynı; içindekiler korunur) ve sayfa başına
   karar kaydı <doc_id>.json (kapsam raporu ve parçaların `ocr` işareti için).
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from . import config
from .registry import DocMeta
from .text_layer import OCR_MIN_SCORE, check_pdf, junk_score

log = logging.getLogger(__name__)

FLAGS = {"yok": "--skip-text", "taranmis": "--redo-ocr", "zayif": "--force-ocr"}
SCORE_TOL = 0.02          # yeni katman eskiden bu kadar düşükse bile "daha kötü" sayılmaz (skor gürültüsü)


@dataclass
class PageDecision:
    page: int
    kind: str                 # metin | yok | taranmis | zayif (text_layer)
    lang: str                 # Tesseract dil verisi ("" = OCR yok)
    old_score: float
    new_score: float | None
    chosen: str               # ozgun | yeni | eski (OCR'lı sayfa, eski katman kaldı) | goruntu (OCR metni süzgeçten geçmedi)
    reason: str = ""


def ocrmypdf_exe() -> str:
    exe = Path(sys.executable).parent / ("ocrmypdf.exe" if os.name == "nt" else "ocrmypdf")
    return str(exe) if exe.exists() else (shutil.which("ocrmypdf") or "ocrmypdf")


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env["PATH"] = str(config.TESSERACT_DIR) + os.pathsep + env.get("PATH", "")
    return env


def tesseract_langs() -> set[str]:
    """Kurulu Tesseract dil verileri (eksik dil yüklemede açık hata verir; kurulum listesi §8)."""
    exe = shutil.which("tesseract", path=_env()["PATH"]) or "tesseract"
    r = subprocess.run([exe, "--list-langs"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return {x.strip() for x in r.stdout.splitlines()[1:] if x.strip()}


def page_ranges(pages: list[int]) -> str:
    """[1, 2, 3, 7, 9, 10] → '1-3,7,9-10' (OCRmyPDF --pages)."""
    out, ps = [], sorted(set(pages))
    i = 0
    while i < len(ps):
        j = i
        while j + 1 < len(ps) and ps[j + 1] == ps[j] + 1:
            j += 1
        out.append(str(ps[i]) if i == j else f"{ps[i]}-{ps[j]}")
        i = j + 1
    return ",".join(out)


def plan_groups(meta: DocMeta, kinds: dict[int, str]) -> dict[tuple[str, str], list[int]]:
    """(bayrak, dil) → sayfalar. Dil sayfa başına kayıttaki dil aralığından."""
    groups: dict[tuple[str, str], list[int]] = {}
    for page, kind in sorted(kinds.items()):
        if kind not in FLAGS:
            continue
        lang = config.TESSERACT_LANGS.get(meta.lang_of(page), "eng")
        groups.setdefault((FLAGS[kind], lang), []).append(page)
    return groups


def choose(kind: str, old_score: float, new_score: float) -> tuple[str, str]:
    """Sayfa sayfa seçim (saf fonksiyon; testli). Dönüş: (seçim, neden)."""
    if kind == "yok":
        if new_score >= OCR_MIN_SCORE:
            return "yeni", ""
        return "goruntu", f"OCR metni anlamsız dizi (skor {new_score:.2f} < {OCR_MIN_SCORE})"
    if new_score < old_score - SCORE_TOL:
        return "eski", f"yeni katman daha kötü (skor {new_score:.2f} < eski {old_score:.2f})"
    return "yeni", ""


def run_ocrmypdf(src: Path, dst: Path, flag: str, lang: str, pages: list[int]) -> float:
    t = time.perf_counter()
    cmd = [ocrmypdf_exe(), "-l", lang, flag, "--pages", page_ranges(pages), "--rotate-pages",
           "--rasterizer", "pypdfium", "--output-type", "pdf", "--pdfa-backend", "internal", "-q",
           "-j", str(config.OCR_JOBS), str(src), str(dst)]
    r = subprocess.run(cmd, env=_env(), capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"OCRmyPDF {r.returncode} ({flag} {lang}): {r.stderr[-500:]}")
    return time.perf_counter() - t


def ocr_document(meta: DocMeta, force: bool = False) -> dict[str, Any]:
    """Belgeyi gerekiyorsa OCR'la. Dönüş: karar kaydı (kayıt dosyasına da yazılır). OCR gerekmiyorsa OCR'lı PDF
    üretilmez (DocMeta.path özgün dosyayı gösterir)."""
    import pymupdf

    src, out_pdf = meta.source_path, meta.ocr_path
    out_json = out_pdf.with_suffix(".json")
    if out_json.exists() and not force:
        return json.loads(out_json.read_text(encoding="utf-8"))
    checks = check_pdf(src)
    kinds = {c.page: c.kind for c in checks}
    groups = plan_groups(meta, kinds)
    record: dict[str, Any] = {"doc_id": meta.doc_id, "kaynak": meta.file, "tarih": time.strftime("%Y-%m-%d %H:%M"),
                              "sure_sn": 0.0, "sayfalar": []}
    if not groups:
        for p in (out_pdf, out_json):
            p.unlink(missing_ok=True)
        record["sayfalar"] = [asdict(PageDecision(c.page, c.kind, "", junk_score(""), None, "ozgun")) for c in checks]
        return record
    missing = {lang for _, lang in groups} - tesseract_langs()
    if missing:
        raise RuntimeError(f"{meta.doc_id}: Tesseract dil verisi kurulu değil: {sorted(missing)} "
                           "(docs/KURULUM-KENDI-BELGELER.md §8)")
    decisions: dict[int, PageDecision] = {}
    with tempfile.TemporaryDirectory(prefix="pilot_ocr_") as tmp, pymupdf.open(str(src)) as orig:
        outputs: dict[int, Any] = {}
        opened: list[Any] = []
        for i, ((flag, lang), pages) in enumerate(groups.items()):
            dst = Path(tmp) / f"g{i}.pdf"
            secs = run_ocrmypdf(src, dst, flag, lang, pages)
            record["sure_sn"] += secs
            log.info("%s: OCR %s %s, %d sayfa, %.0f sn", meta.doc_id, flag, lang, len(pages), secs)
            doc = pymupdf.open(str(dst))
            opened.append(doc)
            for p in pages:
                old = orig[p - 1].get_text()
                new = doc[p - 1].get_text()
                o, n = junk_score(old), junk_score(new)
                chosen, why = choose(kinds[p], o, n)
                decisions[p] = PageDecision(p, kinds[p], lang, o, n, chosen, why)
                if chosen == "yeni":
                    outputs[p] = doc
        final = pymupdf.open()
        for c in checks:
            p = c.page
            if p in outputs:
                final.insert_pdf(outputs[p], from_page=p - 1, to_page=p - 1)
            else:
                final.insert_pdf(orig, from_page=p - 1, to_page=p - 1)
                decisions.setdefault(p, PageDecision(p, c.kind, "", junk_score(orig[p - 1].get_text()), None, "ozgun"))
        try:
            final.set_toc(orig.get_toc())
        except Exception:  # noqa: BLE001 - bozuk içindekiler OCR'ı düşürmesin
            log.warning("%s: içindekiler kopyalanamadı", meta.doc_id)
        out_pdf.parent.mkdir(parents=True, exist_ok=True)
        final.save(str(out_pdf), garbage=3, deflate=True)
        final.close()
        for doc in opened:
            doc.close()                      # Windows: açık dosya geçici klasörün silinmesini engeller
    record["sure_sn"] = round(record["sure_sn"], 1)
    record["sayfalar"] = [asdict(decisions[p]) for p in sorted(decisions)]
    out_json.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    return record


def load_record(meta: DocMeta) -> dict[str, Any] | None:
    p = meta.ocr_path.with_suffix(".json")
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def ocr_pages(meta: DocMeta) -> set[int]:
    """Metni yeni OCR'dan gelen sayfalar (parçaların `ocr` işareti)."""
    rec = load_record(meta) if config.OCR_ENABLED else None
    return {d["page"] for d in (rec or {}).get("sayfalar", []) if d["chosen"] == "yeni"}


def summary(record: dict[str, Any]) -> dict[str, Any]:
    from collections import Counter
    c = Counter(d["chosen"] for d in record.get("sayfalar", []))
    return {"yeni_ocr": c["yeni"], "eski_katman_kaldi": c["eski"], "goruntu_kaldi": c["goruntu"], "ozgun": c["ozgun"],
            "eski_kaldi_sayfalar": [d["page"] for d in record["sayfalar"] if d["chosen"] == "eski"],
            "goruntu_sayfalar": [d["page"] for d in record["sayfalar"] if d["chosen"] == "goruntu"],
            "sure_sn": record.get("sure_sn")}
