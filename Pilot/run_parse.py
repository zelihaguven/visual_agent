"""Tüm pilot dokümanlarını parse eder (Docling, sonuç data/parsed/ altında önbelleklenir)."""
import logging
import sys
import warnings

from pilot.parse import load_or_parse
from pilot.registry import DOCS
from pilot.text_layer import check_pdf, summary

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("parse")

if __name__ == "__main__":
    wanted = set(sys.argv[1:])
    for meta in DOCS:
        if wanted and meta.doc_id not in wanted:
            continue
        res = load_or_parse(meta)
        log.info("== %s: %d öğe, %.0f sn, başarısız sayfa: %s", meta.doc_id, res["n_elements"],
                 res["seconds"], res["failed_pages"] or "yok")
        # Kapsam raporu: sayfa başına metin katmanı (docs/PLAN-OCR.md §2). OCR bugün yapılmıyor: "yok" sayfalar aranamaz.
        tl = summary(check_pdf(meta.source_path))
        log.info("   metin katmanı: %d dijital, %d taranmış+OCR katmanı, %d zayıf, %d yok", tl["metin"], tl["taranmis"],
                 tl["zayif"], tl["yok"])
        if tl["yok"]:
            log.warning("   UYARI: %d sayfada metin katmanı yok, aranamaz (OCR gerekli): %s", tl["yok"], tl["ocr_gerekli"][:20])
        if tl["zayif"]:
            log.warning("   UYARI: %d sayfada metin katmanı bozuk (yeniden OCR): %s", tl["zayif"], tl["yeniden_ocr_adayi"][:20])
        from pilot import config
        from pilot.ocr import load_record
        from pilot.ocr import summary as ocr_summary
        rec = load_record(meta) if config.OCR_ENABLED else None
        if rec:
            o = ocr_summary(rec)
            log.info("   OCR: %d sayfa yeni OCR, %d eski katman kaldı, %d görüntü kaldı (süzgeç), %d belirsiz sayı dizisi, %.0f sn",
                     o["yeni_ocr"], o["eski_katman_kaldi"], o["goruntu_kaldi"], o["belirsiz_dizi"], o["sure_sn"] or 0)
        if tl["taranmis"]:
            log.info("   bilgi: %d taranmış sayfanın OCR katmanı kullanılıyor; sayısal hatalar metinden anlaşılmaz", tl["taranmis"])
