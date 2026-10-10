"""Cevap sonrası otomatik doğrulama (kod tarafı, LLM değil).

Kontroller: kaynak numaraları geçerli mi, alıntı kaynakta birebir geçiyor mu, [n] atıfları,
cevap/sesli metindeki sayılar alıntılarda var mı, kaynaktaki 'N (± t)' toleransı cevapta tam mı.
"""
import re
from dataclasses import dataclass, field

NUM = r"\d+(?:[.,]\d+)?"
NUM_RE = re.compile(NUM)
TOL_RE = re.compile(rf"({NUM})\s*\(\s*±\s*({NUM})\s*\)")
CITE_RE = re.compile(r"\[(\d+)\]")
# Harf önekli kodlar (S-7300A, E-07, D6193): içindeki rakamlar bir "değer" değildir.
CODE_RE = re.compile(r"\b[A-Za-z]{1,5}-?\d+[A-Za-z]*\b")


def normalize(text: str) -> str:
    """Boşluk, tırnak ve tire farklarını yok say (karşılaştırma için)."""
    t = text.casefold().replace(" ", " ")
    t = t.replace("’", "'").replace("“", '"').replace("”", '"').replace("–", "-").replace("—", "-")
    t = re.sub(r"\s*-\s*", "-", t)
    return re.sub(r"\s+", " ", t).strip()


def _canon_num(s: str) -> str:
    return s.replace(",", ".")


def numbers_in(text: str) -> set[str]:
    cleaned = CODE_RE.sub(" ", CITE_RE.sub("", text))
    return {_canon_num(m.group(0)) for m in NUM_RE.finditer(cleaned)}


@dataclass
class Verification:
    status: str                       # "verified" | "partial" | "not_found" | "failed"
    problems: list[str] = field(default_factory=list)
    checks: dict[str, bool] = field(default_factory=dict)

    @property
    def badge(self) -> str:
        return {"verified": "✔ Doğrulandı", "partial": "⚠ Kısmen doğrulandı",
                "not_found": "✖ Kaynaklarda bulunamadı", "failed": "✖ Doğrulanamadı"}[self.status]


def verify(answer: dict, sources: dict[int, str]) -> Verification:
    """answer: LLM'in JSON çıktısı. sources: {kaynak_no: chunk metni}."""
    if answer.get("bulunamadi"):
        ok = not answer.get("cevap", "").strip()
        return Verification("not_found" if ok else "failed",
                            [] if ok else ["bulunamadi=true ama cevap dolu"], {"bos_cevap": ok})
    problems: list[str] = []
    checks: dict[str, bool] = {}

    quotes = answer.get("alintilar") or []
    checks["alinti_var"] = bool(quotes)
    if not quotes:
        problems.append("Cevap var ama alıntı yok")

    norm_sources = {no: normalize(t) for no, t in sources.items()}
    exact = True
    for q in quotes:
        no, text = q.get("kaynak_no"), q.get("metin", "")
        if no not in norm_sources:
            problems.append(f"Geçersiz kaynak numarası: {no}")
            exact = False
        elif normalize(text) not in norm_sources[no]:
            problems.append(f"Alıntı kaynakta birebir bulunamadı: {text[:70]!r}")
            exact = False
    checks["alinti_birebir"] = exact

    cites = {int(c) for c in CITE_RE.findall(answer.get("cevap", ""))}
    cites_ok = bool(cites) and cites <= set(sources)
    checks["atif_gecerli"] = cites_ok
    if not cites_ok:
        problems.append("Cevapta geçerli [n] atfı yok" if not cites else f"Geçersiz atıf: {sorted(cites - set(sources))}")

    quote_text = " ".join(q.get("metin", "") for q in quotes)
    quote_nums = numbers_in(quote_text)
    text_ans = answer.get("cevap", "")
    text_voice = answer.get("sesli_metin", "")
    stray = sorted((numbers_in(text_ans) | numbers_in(text_voice)) - quote_nums)
    checks["sayilar_alintida"] = not stray
    if stray:
        problems.append(f"Alıntıda olmayan sayı(lar): {stray}")

    tol_ok = True
    ans_norm = re.sub(r"\s+", "", text_ans + " " + text_voice).replace(",", ".")
    for m in TOL_RE.finditer(quote_text):
        n, t = _canon_num(m.group(1)), _canon_num(m.group(2))
        if n in numbers_in(text_ans) and f"±{t}" not in ans_norm and f"artıeksi{t}" not in ans_norm:
            tol_ok = False
            problems.append(f"Tolerans düşmüş: kaynak '{m.group(0)}', cevapta ± {t} yok")
    checks["tolerans_tam"] = tol_ok

    hard = not (checks["alinti_var"] and checks["alinti_birebir"] and checks["sayilar_alintida"]
                and checks["tolerans_tam"])
    if hard:
        return Verification("failed", problems, checks)
    return Verification("verified" if cites_ok else "partial", problems, checks)
