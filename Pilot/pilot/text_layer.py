"""Yüklemede sayfa başına metin katmanı kontrolü (karar 2026-11-06; docs/PLAN-OCR.md §2). Model ve ağ yok.

Her sayfa için: metin katmanı var mı, ne kadar, kalitesi ne. Sınıflar:
  metin     dijital metin katmanı: bugünkü ayrıştırma
  taranmis  sayfayı görüntü kaplıyor ve üstünde (OCR) metin katmanı var: bugün aranabilir, ama katmandaki sayısal
            hatalar ("112" = ½, "IS" = 15) metne bakarak anlaşılamaz → yeniden OCR adayı (karşılaştırmalı)
  zayif     katman bozuk (harf aralıklı, sesli harfsiz diziler, tanınmayan karakter): yeniden OCR gerekli
  yok       metin yok ya da çok az, sayfayı görüntü kaplıyor: aranamaz → OCR'a gönder
Kapsam raporunda sayfa listesiyle uyarı olarak gösterilir.

Kalite skoru (0–1) genel sinyallerden; belgeye özel kural yok:
  - harf aralıklı tek harf oranı ("C a r d f l a t")
  - sesli harf içermeyen 4+ harfli küçük harfli kelimeler ("wrnkl") ve tanınmayan karakterler (�)
  Harf/rakam karışıklığı kullanılmaz: teknik belgede olağan ("LSd-1", "3/16-inch", "230psi"; kalibrasyon 2026-11-06).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

MIN_CHARS = 50            # bundan az metinli sayfa "yok" (görüntü kaplıyorsa)
IMAGE_COVER = 0.5         # sayfanın bu oranından fazlasını görüntü kaplıyorsa taranmış sayfa sayılır
WEAK_SCORE = 0.85         # kalite skoru bunun altındaysa "zayif"

_WORD = re.compile(r"[^\s]+")
_CODE = re.compile(r"^[A-Z]{1,5}-?\d+[A-Z]{0,3}[)(.,:;]*$")          # E050, S-7300A, RA1171 gibi kodlar normal
_VOWELS = set("aeıioöuüAEIİOÖUÜ" "yY")


@dataclass
class PageCheck:
    page: int
    chars: int
    image_cover: float
    score: float
    kind: str               # metin | zayif | yok
    reasons: list[str]


def quality(text: str) -> tuple[float, list[str]]:
    """(skor, nedenler). Skor = 1 − bozuk kelime oranı (bozuk: harf aralıklı tek harf, karışık harf/rakam, sesli
    harfsiz uzun dizi, tanınmayan karakter)."""
    words = [w.strip(".,;:()[]\"'!?") for w in _WORD.findall(text)]
    words = [w for w in words if w]
    if not words:
        return 0.0, ["metin yok"]
    singles = sum(len(w) == 1 and w.isalpha() and w not in ("a", "A", "I", "o", "O", "e", "y") for w in words)
    novowel = sum(len(w) >= 4 and w.isalpha() and not (set(w) & _VOWELS) and not w.isupper() for w in words)
    bad_chars = text.count("�")
    n = len(words)
    reasons = []
    if singles / n > 0.15:
        reasons.append(f"harf aralıklı ({singles}/{n})")
    if novowel / n > 0.03:
        reasons.append(f"sesli harfsiz dizi ({novowel}/{n})")
    if bad_chars:
        reasons.append(f"tanınmayan karakter ({bad_chars})")
    score = max(0.0, 1.0 - (singles + novowel + bad_chars) / n)
    return round(score, 3), reasons


def check_pdf(path: Path | str) -> list[PageCheck]:
    """Belgenin her sayfası için metin katmanı kontrolü (PyMuPDF; bugünkü ayrıştırmanın kullandığı kütüphane)."""
    import pymupdf
    out = []
    with pymupdf.open(str(path)) as doc:
        for i, page in enumerate(doc, start=1):
            text = page.get_text()
            area = page.rect.width * page.rect.height or 1.0
            cover = 0.0
            for info in page.get_image_info():
                x0, y0, x1, y1 = info["bbox"]
                cover += max(0.0, (x1 - x0) * (y1 - y0)) / area
            cover = round(min(cover, 1.0), 3)
            chars = len(text.strip())
            score, reasons = quality(text)
            if chars < MIN_CHARS:
                kind = "yok" if cover >= IMAGE_COVER or chars == 0 else "metin"     # boş/şekil sayfası da olabilir
                if kind == "yok":
                    reasons = ["metin katmanı yok ya da çok az" + (", sayfayı görüntü kaplıyor" if cover >= IMAGE_COVER else "")]
            elif score < WEAK_SCORE:
                kind = "zayif"
            elif cover >= IMAGE_COVER:
                kind = "taranmis"
                reasons = reasons + ["taranmış sayfa, OCR metin katmanı (sayısal hatalar metinden anlaşılamaz)"]
            else:
                kind = "metin"
            out.append(PageCheck(i, chars, cover, score, kind, reasons))
    return out


def summary(checks: list[PageCheck]) -> dict:
    """Kapsam raporu için özet: sınıf sayıları ve uyarı sayfaları."""
    from collections import Counter
    c = Counter(p.kind for p in checks)
    return {"sayfa": len(checks), "metin": c["metin"], "taranmis": c["taranmis"], "zayif": c["zayif"], "yok": c["yok"],
            "yeniden_ocr_karsilastir": [p.page for p in checks if p.kind == "taranmis"],
            "ocr_gerekli": [p.page for p in checks if p.kind == "yok"],
            "yeniden_ocr_adayi": [p.page for p in checks if p.kind == "zayif"]}


if __name__ == "__main__":
    import json
    import sys
    for f in sys.argv[1:]:
        cs = check_pdf(f)
        print(Path(f).name, json.dumps(summary(cs), ensure_ascii=False))
