"""Sesli okunacak metni hazırla: sayı, tolerans, aralık, kesir -> Türkçe kelimeler (kural tablosu)."""
import re

_NUM = r"\d+(?:[.,]\d+)?"


_ONES = ("sıfır", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz")
_TENS = ("", "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan")


def _int_words(n: int) -> str:
    """0-999999 arası tam sayı -> ayrı yazılmış Türkçe kelimeler ('on bir', 'yüz yirmi')."""
    if n < 10:
        return _ONES[n]
    if n < 100:
        return " ".join(w for w in (_TENS[n // 10], _ONES[n % 10] if n % 10 else "") if w)
    if n < 1000:
        head = "yüz" if n // 100 == 1 else f"{_ONES[n // 100]} yüz"
        return f"{head} {_int_words(n % 100)}" if n % 100 else head
    if n < 1_000_000:
        head = "bin" if n // 1000 == 1 else f"{_int_words(n // 1000)} bin"
        return f"{head} {_int_words(n % 1000)}" if n % 1000 else head
    return " ".join(_ONES[int(d)] for d in str(n))  # çok büyük sayı: rakam rakam


def _say(n: str) -> str:
    n = n.replace(",", ".")
    if "." in n:
        whole, frac = n.split(".", 1)
        return f"{_int_words(int(whole))} virgül " + " ".join(_ONES[int(d)] for d in frac)
    return _int_words(int(n))


def _tolerance(m: re.Match[str]) -> str:
    return f"{_say(m.group(1))}, artı eksi {_say(m.group(2))}"


def _range(m: re.Match[str]) -> str:
    return f"{_say(m.group(1))} ile {_say(m.group(2))} arası"


def _fraction(m: re.Match[str]) -> str:
    """5/8 -> 'sekizde beş' (payda yer-bulunma eki: -de/-da; ünlü uyumu için son ünlüye bakılır)."""
    denom = _say(m.group(2))
    last_vowel = next((c for c in reversed(denom) if c in "aeıioöuü"), "e")
    suffix = "da" if last_vowel in "aıou" else "de"
    return f"{denom}{suffix} {_say(m.group(1))}"


def normalize_for_speech(text: str) -> str:
    t = re.sub(r"\[\d+\]", "", text)                                              # atıf numaraları okunmaz
    t = re.sub(rf"({_NUM})\s*\(\s*±\s*({_NUM})\s*\)", _tolerance, t)             # 11 (± 1)
    t = re.sub(rf"({_NUM})\s*±\s*({_NUM})", lambda m: f"{_say(m.group(1))} artı eksi {_say(m.group(2))}", t)
    t = re.sub(r"(?<![\w/])(\d+)\s*/\s*(\d+)(?![\w/])", _fraction, t)             # 5/8
    t = re.sub(rf"(?<![\w.,-])({_NUM})\s*[-–]\s*({_NUM})(?![\w-])", _range, t)    # 10-14
    t = re.sub(rf"(?<![\w-])({_NUM})(?![\w-])", lambda m: _say(m.group(1)), t)    # kalan sayılar
    t = re.sub(r"\s+([.,;:!?])", r"\1", t)
    return re.sub(r"\s+", " ", t).strip()
