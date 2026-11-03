"""Metinden sayısal ifadeleri BÜTÜN olarak çıkarma ve normalize etme.

Neden bütün ifade? "11 (± 1)" içindeki "1" de kaynakta geçer. Rakam rakam karşılaştırma,
toleransın düşmesini veya değerin değişmesini yakalayamaz. İfadeler türleriyle çıkarılır:

    tolerance  11 (± 1)        -> 11±1
    range      10-14, 10 to 14 -> 10-14
    fraction   3/16, ½         -> 3/16, 1/2
    code       S-7300A, E-07, LSc-2, D 6193, 146391-001
    number     12, 1.5, 1,5    -> 12, 1.5
"""

from __future__ import annotations

import re
from dataclasses import dataclass

UNICODE_FRACTIONS = {"½": "1/2", "¼": "1/4", "¾": "3/4", "⅛": "1/8", "⅜": "3/8", "⅝": "5/8", "⅞": "7/8",
                     "⅓": "1/3", "⅔": "2/3", "⅙": "1/6", "⅚": "5/6", "⅕": "1/5"}
NUM = r"\d+(?:[.,]\d+)?"

PATTERNS: list[tuple[str, re.Pattern]] = [
    # Parça numarası: 146391-001
    ("code", re.compile(r"(?<![\w-])\d{4,}-\d{2,}(?![\w-])")),
    # Harfli kodlar: S-7300A, E-07, LSc-2, D6193 (büyük harfle başlar, boşluk içermez)
    ("code", re.compile(r"(?<![\w-])[A-Z][A-Za-z]{0,3}-?\d+[A-Za-z]{0,3}(?:-\d+)?(?![\w-])")),
    # Tolerans: 11 (± 1), 11 ± 1, 11 (+/- 1), 11 (+/-1)
    ("tolerance", re.compile(rf"({NUM})\s*\(?\s*(?:±|\+/-|\+-)\s*({NUM})\s*\)?")),
    # Aralık: 10-14, 10 – 14, 10 to 14, 10 ile 14, 10 ila 14 (kesir aralığı: 3/16 to 1/4)
    ("range", re.compile(rf"((?:\d+\s*/\s*\d+)|{NUM})\s*(?:-|–|—|\bto\b|\bile\b|\bila\b)\s*((?:\d+\s*/\s*\d+)|{NUM})(?![\w/])")),
    # Kesir: 3/16
    ("fraction", re.compile(r"(?<![\w/])\d+\s*/\s*\d+(?![\w/])")),
    # Düz sayı
    ("number", re.compile(rf"(?<![\w.,/-]){NUM}(?![\w/])")),
]

CITATION = re.compile(r"\[\d+(?:\s*,\s*\d+)*\]")
ENUMERATION = re.compile(r"(?m)^\s*\d{1,2}[.)]\s+")
SECTION_NO = re.compile(r"(?<![\w.])\d+(?:\.\d+){2,}(?![\w])")   # 3.11.1 gibi madde numaraları


@dataclass(frozen=True)
class Expr:
    kind: str
    canon: str
    raw: str


def _num(s: str) -> str:
    s = s.strip().replace(" ", "")
    if re.fullmatch(r"\d+,\d+", s):
        s = s.replace(",", ".")
    if re.fullmatch(r"\d+\.\d+", s):
        s = s.rstrip("0").rstrip(".") if "." in s else s
    return s


def _canon(kind: str, m: re.Match) -> str:
    raw = m.group(0)
    if kind == "tolerance":
        return f"{_num(m.group(1))}±{_num(m.group(2))}"
    if kind == "range":
        a, b = m.group(1), m.group(2)
        a = re.sub(r"\s", "", a) if "/" in a else _num(a)
        b = re.sub(r"\s", "", b) if "/" in b else _num(b)
        return f"{a}-{b}"
    if kind == "fraction":
        return re.sub(r"\s", "", raw)
    if kind == "code":
        return re.sub(r"[\s-]", "", raw).upper()
    return _num(raw)


def prepare(text: str) -> str:
    """Atıfları, madde numaralarını ve unicode kesirleri temizler."""
    text = CITATION.sub(" ", text)
    text = ENUMERATION.sub(" ", text)
    text = SECTION_NO.sub(" ", text)
    for k, v in UNICODE_FRACTIONS.items():
        text = re.sub(rf"(\d)\s*{k}", rf"\1 {v}", text)   # 1½ -> 1 1/2
        text = text.replace(k, v)
    return text


def extract(text: str) -> list[Expr]:
    """Örtüşmeyen ifadeler; önce daha özel kalıplar (kod, tolerans, aralık) eşleşir."""
    text = prepare(text)
    taken = [False] * len(text)
    out: list[tuple[int, Expr]] = []
    for kind, pat in PATTERNS:
        for m in pat.finditer(text):
            s, e = m.span()
            if any(taken[s:e]):
                continue
            raw = m.group(0).strip()
            if kind == "code" and not re.search(r"\d", raw):
                continue
            for i in range(s, e):
                taken[i] = True
            out.append((s, Expr(kind, _canon(kind, m), raw)))
    return [x for _, x in sorted(out, key=lambda t: t[0])]


def components(e: Expr) -> set[str]:
    """Bileşik bir ifadenin parçaları (ileri yön kontrolünde düz sayılar için)."""
    if e.kind == "tolerance":
        return set(e.canon.split("±"))
    if e.kind == "range":
        return set(e.canon.split("-"))
    return {e.canon}


def canon_set(exprs: list[Expr]) -> set[str]:
    return {e.canon for e in exprs}
