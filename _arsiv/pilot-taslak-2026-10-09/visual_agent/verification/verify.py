"""Cevabın otomatik doğrulanması (S11 Katman 5). Cevap kullanıcıya gitmeden önce çalışır.

Kontroller:
  a) Kaynak numaraları geçerli mi, en az bir atıf var mı?
  b) Her alıntı, belirtilen kaynak parçasında (normalize edilmiş) birebir geçiyor mu?
  c) İLERİ yön: Cevaptaki (ve sesli metindeki) her sayısal ifade alıntılarda ya da atıf yapılan
     parçalarda var mı?  -> uydurma / değişmiş değer
  d) GERİ yön: Alıntılardaki her tolerans ve aralık ifadesi cevapta TAM haliyle var mı?
     -> düşen tolerans ("11 (± 1)" -> "11")
  e) "Bulunamadı" tutarlılığı.

Durum: ok | warn (gösterilir, ⚠ rozet) | fail (cevap gösterilmez, sadece kaynak).
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field

from .numbers import canon_set, components, extract

FAIL, WARN, OK = "fail", "warn", "ok"


@dataclass
class Issue:
    level: str
    code: str
    message: str


@dataclass
class Verification:
    status: str = OK
    issues: list[Issue] = field(default_factory=list)
    quote_matches: list[dict] = field(default_factory=list)   # {kaynak_no, metin, exact, ratio}

    def add(self, level: str, code: str, message: str) -> None:
        self.issues.append(Issue(level, code, message))
        if level == FAIL or (level == WARN and self.status == OK):
            self.status = level

    @property
    def badge(self) -> str:
        return {OK: "✔ Kaynakla doğrulandı", WARN: "⚠ Kısmen doğrulandı, kaynağı kontrol edin",
                FAIL: "✖ Doğrulanamadı"}[self.status]


def _norm(s: str) -> str:
    s = s.replace("­", "")
    s = re.sub(r"-\s*\n\s*", "", s)                 # satır sonu tirelemesi
    s = s.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
    s = s.replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", s).strip().lower()


def quote_in_text(quote: str, text: str) -> tuple[bool, float]:
    """(birebir mi, benzerlik oranı). Birebir değilse en iyi pencere ile difflib oranı."""
    q, t = _norm(quote), _norm(text)
    if not q:
        return False, 0.0
    if q in t:
        return True, 1.0
    n = len(q)
    best = 0.0
    step = max(1, n // 8)
    for i in range(0, max(1, len(t) - n + 1), step):
        r = difflib.SequenceMatcher(None, q, t[i:i + n]).ratio()
        if r > best:
            best = r
    return False, best


CIT = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")


def cited_numbers(text: str) -> set[int]:
    out: set[int] = set()
    for m in CIT.finditer(text):
        out |= {int(x) for x in re.split(r"\s*,\s*", m.group(1))}
    return out


def verify(answer: dict, sources: list[dict], fuzzy_ok: float = 0.92) -> Verification:
    """answer: LLM çıktısı (prompt-taslak şeması). sources: LLM'e verilen parçalar, 1'den numaralı."""
    v = Verification()
    n = len(sources)
    not_found = bool(answer.get("bulunamadi"))
    cevap = answer.get("cevap") or ""
    sesli = answer.get("sesli_metin") or ""
    quotes = answer.get("alintilar") or []

    # e) bulunamadı tutarlılığı
    if not_found:
        if cevap.strip():
            v.add(WARN, "bulunamadi_tutarsiz", "Model 'bulunamadı' dedi ama cevap da yazdı; cevap gösterilmeyecek.")
        return v
    if not cevap.strip():
        v.add(FAIL, "bos_cevap", "Cevap boş.")
        return v

    # a) atıflar
    cits = cited_numbers(cevap)
    if not cits:
        v.add(FAIL, "atif_yok", "Cevapta kaynak numarası yok.")
    bad = sorted(c for c in cits if not 1 <= c <= n)
    if bad:
        v.add(FAIL, "gecersiz_atif", f"Geçersiz kaynak numarası: {bad} (verilen kaynak sayısı {n}).")

    # b) alıntılar
    if not quotes:
        v.add(FAIL, "alinti_yok", "Cevabın dayandığı alıntı yok.")
    for q in quotes:
        k = q.get("kaynak_no")
        text = q.get("metin") or ""
        if not isinstance(k, int) or not 1 <= k <= n:
            v.add(FAIL, "alinti_kaynak_gecersiz", f"Alıntının kaynak numarası geçersiz: {k}")
            continue
        exact, ratio = quote_in_text(text, sources[k - 1]["text"])
        v.quote_matches.append({"kaynak_no": k, "metin": text, "exact": exact, "ratio": round(ratio, 3)})
        if exact:
            continue
        # Sayılar alıntıda birebir olmalı (bulanık eşleşme sayı farkını gizlememeli)
        num_ok = canon_set(extract(text)) <= canon_set(extract(sources[k - 1]["text"]))
        if ratio >= fuzzy_ok and num_ok:
            v.add(WARN, "alinti_yaklasik", f"Alıntı kaynakla tam aynı değil (benzerlik {ratio:.2f}). "
                                           f"OCR farkı olabilir.")
        else:
            v.add(FAIL, "alinti_kaynakta_yok", f"Alıntı [{k}] numaralı kaynakta bulunamadı (benzerlik {ratio:.2f}).")

    # c) ileri yön: cevap ve sesli metindeki sayılar kaynakta var mı?
    quote_exprs = [e for q in quotes for e in extract(q.get("metin") or "")]
    cited_src = [sources[c - 1]["text"] for c in cits if 1 <= c <= n] or [s["text"] for s in sources]
    src_exprs = quote_exprs + [e for t in cited_src for e in extract(t)]
    src_canon = canon_set(src_exprs)
    src_parts = set().union(*(components(e) for e in src_exprs)) if src_exprs else set()
    for label, text in (("cevap", cevap), ("sesli metin", sesli)):
        for e in extract(text):
            supported = e.canon in src_canon or (e.kind == "number" and e.canon in src_parts)
            if not supported:
                v.add(FAIL, "kaynakta_olmayan_deger",
                      f"{label}: '{e.raw}' kaynaklarda yok (uydurulmuş veya değişmiş değer olabilir).")

    # d) geri yön: alıntıdaki tolerans/aralık ifadeleri cevapta tam haliyle var mı?
    ans_canon = canon_set(extract(cevap))
    for e in quote_exprs:
        if e.kind in ("tolerance", "range") and e.canon not in ans_canon:
            # Değerin bir parçası cevapta geçiyorsa tolerans/aralık düşmüş demektir
            parts = components(e)
            ans_parts = {x.canon for x in extract(cevap)}
            if parts & ans_parts:
                v.add(WARN, "tolerans_dustu",
                      f"Kaynaktaki '{e.raw}' cevapta tam haliyle yok (tolerans/aralık eksik olabilir).")
    return v
