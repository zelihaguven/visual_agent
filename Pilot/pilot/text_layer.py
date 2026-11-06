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


# --- Anlamsız dizi skoru (OCR sonrası süzgeç ve eski/yeni katman seçimi; karar 2026-11-06, docs/PLAN-OCR.md §9) -----
# quality()'den daha sıkı: OCR'ın çizim, levha ve ters dönmüş sayfada ürettiği dizileri de yakalar ("NNN", "RWQQN",
# "ııuııuıı", "AWK}", "oy}"). Sayfa sınıflandırmasında kullanılmaz: dijital sayfadaki harf listeleri (JUKI s.31 "B C D
# F G") onu düşürür; yalnız aynı sayfanın iki OCR katmanını karşılaştırmak ve OCR metnini kabul etmek için.
# Eşik bütün belgeler için tek (OCR_MIN_SCORE); belgeye ya da sayfaya özel eşik yok.
OCR_MIN_SCORE = 0.85
_VOWELS_WIDE = _VOWELS | set("àâäéèêëîïôûùáíóúñÀÂÉÈÊÎÔÛÁÍÓÚ")
_ROMAN = re.compile(r"^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$")
_JUNK_CHARS = set("|«»~\\{}®$¢£¥§¶^`")


def _junk_word(word: str) -> bool:
    core = word.strip(".,;:()[]\"'!?")
    if not core:
        return False
    if set(core) & _JUNK_CHARS and not any(ch.isdigit() for ch in core):
        return True                                             # "|", "AWK}", "«": OCR'ın çizgi ve gölge okuması
    if not core.isalpha():
        return False                                            # sayı, kod, kesir, birimli değer: değerlendirilmez
    if len(core) == 1:
        return core not in "aAIoOeEyY"
    if _ROMAN.match(core):
        return False                                            # "III" (Type III) gerçek
    if re.search(r"(.)\1\1", core.casefold()):
        return True                                             # aynı harf üç kez: "NNN", "ııı"
    if not set(core) & _VOWELS_WIDE and len(core) >= 4:
        return True                                             # sesli harfsiz uzun dizi: "RWQQN" ("lbs", "mm", "NSN" değil)
    if len(core) >= 8 and core.isupper():
        vr = sum(c in _VOWELS_WIDE for c in core) / len(core)
        if vr < 0.25 or vr > 0.6:
            return True                                         # uzun büyük harf dizisi, sesli oranı dil dışı
    inner = core[1:]
    return any(c.islower() for c in inner) and any(c.isupper() for c in inner)   # "aN", "JopurpAo": iç harf karışık


def junk_score(text: str) -> float:
    """1 − anlamsız dizi oranı (boşlukla ayrılmış dizilerde). Metin yoksa 0."""
    words = text.split()
    if not words:
        return 0.0
    return round(1.0 - sum(map(_junk_word, words)) / len(words), 3)


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
