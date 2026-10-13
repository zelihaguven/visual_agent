"""Kelime araması için metin işleme: belirteçleme (tokenization), kök bulma, BM25 seyrek vektörü.

- Kodlar ve sayılar olduğu gibi korunur: "S-7300A", "E-07", "10-14", "146391-001", "D6193".
- Kelimeler köklerine indirilir (Snowball). Doküman kendi diliyle, soru hem Türkçe hem İngilizce
  kökleriyle temsil edilir (Türkçe soru + İngilizce manuel için ucuz bir köprü; kod ve terimler
  zaten ortak). Asıl diller arası eşleşmeyi anlamsal arama (bge-m3) sağlar.
- BM25: doküman tarafında terim frekansı doygunluğu + uzunluk normalizasyonu hesaplanır,
  IDF'i Qdrant sorgu anında uygular (sparse vector modifier=IDF). Böylece filtreler aynı yerde.
"""

from __future__ import annotations

import re
import zlib
from collections import Counter
from functools import lru_cache

CODE = re.compile(r"[A-Za-zÇĞİÖŞÜçğıöşü]*\d[\w]*(?:[-./]\w+)*|[A-Za-z]+-\d[\w-]*")
WORD = re.compile(r"[A-Za-zÇĞİÖŞÜçğıöşü]+")

STOP_EN = set("""a an the and or of to in on for with by at from as is are be been was were this that these
those it its shall should will may can not no all any each per into than then there their which who what when
where how if but such other""".split())
STOP_TR = set("""ve veya ile bir bu şu o da de mi mı mu mü ne nasıl nedir ne kadar için gibi olarak olan olmalı
olmalıdır kaç hangi neden niçin ya ise ki çok daha en her ama fakat yani bunu şunu onu ben sen biz siz""".split())

TR_LOWER = str.maketrans({"I": "ı", "İ": "i"})


def tr_lower(s: str) -> str:
    return s.translate(TR_LOWER).lower()


@lru_cache(maxsize=4)
def _stemmer(lang: str):
    import snowballstemmer
    return snowballstemmer.stemmer({"tr": "turkish", "en": "english"}[lang])


def _codes(text: str) -> list[str]:
    out = []
    for m in CODE.finditer(text):
        tok = m.group(0).strip(".-/").lower()
        if tok and not tok.isalpha():
            out.append(tok)
            compact = re.sub(r"[-./]", "", tok)          # "S-7300A" ve "S7300A" aynı eşleşsin
            if compact != tok:
                out.append(compact)
    return out


def tokenize(text: str, lang: str) -> list[str]:
    """Doküman metni için belirteçler (tek dil)."""
    low = tr_lower(text) if lang == "tr" else text.lower()
    stop = STOP_TR if lang == "tr" else STOP_EN
    words = [w for w in WORD.findall(low) if len(w) > 1 and w not in stop]
    stems = _stemmer(lang).stemWords(words)
    return stems + _codes(text)


def tokenize_query(text: str) -> list[str]:
    """Soru için belirteçler: Türkçe ve İngilizce köklerin birleşimi + kodlar."""
    toks = set(tokenize(text, "tr")) | set(tokenize(text, "en"))
    return sorted(toks)


def token_id(tok: str) -> int:
    return zlib.crc32(tok.encode("utf-8")) & 0x7FFFFFFF


def bm25_doc_vector(tokens: list[str], avgdl: float, k1: float = 1.2, b: float = 0.75) -> tuple[list[int], list[float]]:
    tf = Counter(tokens)
    dl = len(tokens) or 1
    norm = k1 * (1 - b + b * dl / max(avgdl, 1.0))
    idx: dict[int, float] = {}
    for tok, f in tf.items():
        i = token_id(tok)
        idx[i] = idx.get(i, 0.0) + f * (k1 + 1) / (f + norm)
    return list(idx.keys()), list(idx.values())


def query_vector(tokens: list[str]) -> tuple[list[int], list[float]]:
    ids = sorted({token_id(t) for t in tokens})
    return ids, [1.0] * len(ids)
