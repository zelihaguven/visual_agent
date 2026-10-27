"""BM25 sparse kol (bulut dense ile hibrit arama): fastembed Qdrant/bm25 + Qdrant'ın IDF modifier'ı.

Bulut embedding API'leri bge-m3'ün sparse ağırlıklarını vermez; bulut dense modellerde sparse kol BM25'tir. Koleksiyonda
'bm25' adlı, modifier=IDF sparse vektör: doküman tarafı terim sıklığı, IDF'i Qdrant uygular.

fastembed tokenizer'ı harf/rakam dışı her karakterde böler, küçük harfe çevirir, İngilizce kök alır. İki sorun genel
normalleştirmeyle giderilir (doküman ve sorgu aynı):
- "İ".lower() birleşik nokta üretir ve kelime bölünür ("İğne" → "ğne"). İ/ı → i.
- Tireli kodlar bölünür ("E-050" → e, 050; "E050" → e050): harf-tire-rakam birleştirilir.
"""
import re
from functools import lru_cache
from typing import Any

BM25_MODEL = "Qdrant/bm25"
_TR_FOLD = str.maketrans({"İ": "i", "ı": "i", "I": "i"})
_CODE_HYPHEN = re.compile(r"\b([A-Za-z]{1,4})[-‐–](\d)")


def normalize(text: str) -> str:
    return _CODE_HYPHEN.sub(r"\1\2", text).translate(_TR_FOLD)


@lru_cache(maxsize=1)
def _model():
    from fastembed.sparse.bm25 import Bm25
    return Bm25(BM25_MODEL)


def _to_dict(e: Any) -> dict[int, float]:
    return {int(i): float(v) for i, v in zip(e.indices, e.values)}


def bm25_docs(texts: list[str]) -> list[dict[int, float]]:
    return [_to_dict(e) for e in _model().embed([normalize(t) for t in texts])]


def bm25_query(text: str) -> dict[int, float]:
    return _to_dict(next(iter(_model().query_embed([normalize(text)]))))
