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


# Birimler: Türkçe ek gelebilir ("5 mm'dir" -> "beş milimetredir"). Kesme işareti atılır.
_UNITS = (
    (r"\bSPI\b", "inç başına dikiş"),
    (r"\bsti\s*/\s*min\b", "dikiş/dakika"),
    (r"\bmm\b", "milimetre"),
    (r"\bcm\b", "santimetre"),
)


# Binlik ayırıcı: İngilizce kaynakta "7,000 sti/min" (yedi bin) Türkçe ondalık gibi "yedi virgül sıfır sıfır sıfır"
# okunuyordu (2026-10-16, JUKI MO-6800S). Sıfırla başlamayan 1-3 haneli tam kısım + tam 3 haneli gruplar binliktir;
# "0,125" ve "3,8" ondalık kalır.
_THOUSANDS_RE = re.compile(r"(?<![\d.,])([1-9]\d{0,2})((?:[.,]\d{3})+)(?![.,]?\d)")
# Oran birimi: "7000 sti/min" -> "dakikada yedi bin dikiş". Sondaki ek ("dikiş/dakikadır") "dikiştir" olur.
_RATE_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:sti|stitches|dikiş)\s*/\s*(?:min|dakika)(\w*)")


def _rate(m: re.Match[str]) -> str:
    suffix = "tir" if re.fullmatch(r"[dt][ıiuü]r", m.group(2) or "") else ""
    return f"dakikada {m.group(1)} dikiş{suffix}"


def _units(t: str) -> str:
    for pat, word in _UNITS:
        t = re.sub(pat + r"(?:['’](\w+))?", lambda m: word + (m.group(1) or ""), t)
    return t


def normalize_for_speech_en(text: str) -> str:
    """İngilizce cevap için: atıflar atılır, tolerans okunur hale gelir. Sayıları TTS kendisi okur (İngilizce)."""
    t = re.sub(r"\[\d+\]", "", text)
    t = re.sub(rf"({_NUM})\s*\(\s*±\s*({_NUM})\s*\)", r"\1, plus or minus \2", t)
    t = re.sub(rf"({_NUM})\s*±\s*({_NUM})", r"\1 plus or minus \2", t)
    t = re.sub(r"\bSPI\b", "stitches per inch", t)
    t = re.sub(r"\s+([.,;:!?])", r"\1", t)
    return re.sub(r"\s+", " ", t).strip()


def normalize_for_speech(text: str) -> str:
    t = re.sub(r"\[\d+\]", "", text)                                              # atıf numaraları okunmaz
    t = _THOUSANDS_RE.sub(lambda m: m.group(1) + re.sub(r"[.,]", "", m.group(2)), t)   # 7,000 -> 7000
    t = _RATE_RE.sub(_rate, t)                                                    # 7000 sti/min
    t = _units(t)
    t = re.sub(rf"({_NUM})\s*\(\s*±\s*({_NUM})\s*\)", _tolerance, t)             # 11 (± 1)
    t = re.sub(rf"({_NUM})\s*±\s*({_NUM})", lambda m: f"{_say(m.group(1))} artı eksi {_say(m.group(2))}", t)
    t = re.sub(r"(?<![\w/])(\d+)\s*/\s*(\d+)(?![\w/])", _fraction, t)             # 5/8
    t = re.sub(rf"(?<![\w.,-])({_NUM})\s*[-–]\s*({_NUM})(?![\w-])", _range, t)    # 10-14
    t = re.sub(rf"(?<![\w-])({_NUM})(?![\w-])", lambda m: _say(m.group(1)), t)    # kalan sayılar
    t = re.sub(r"\s+([.,;:!?])", r"\1", t)
    return re.sub(r"\s+", " ", t).strip()
