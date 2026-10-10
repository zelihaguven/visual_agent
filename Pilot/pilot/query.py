"""Sorgu analizi: sorudaki model kodu / ürün adı / marka adından doküman filtresi (kural tabanlı)."""
import re
from dataclasses import dataclass

from .registry import BRAND_ALIASES, DOCS


def _squash(text: str) -> str:
    """Karşılaştırma için: küçük harf, '-', boşluk, '.' ve '_' atılmış."""
    return re.sub(r"[\s\-_.]+", "", text.casefold())


@dataclass(frozen=True)
class QueryContext:
    doc_ids: tuple[str, ...]      # boşsa filtre yok
    matched: tuple[str, ...]      # hangi ifadeler eşleşti (arayüzde gösterilir)


def analyze_query(question: str) -> QueryContext:
    q = _squash(question)
    doc_ids: list[str] = []
    matched: list[str] = []
    for doc in DOCS:
        for alias in doc.aliases:
            if _squash(alias) in q:
                doc_ids.append(doc.doc_id)
                matched.append(alias)
                break
    # model kodu belirtilmemiş marka adı (örn. "Brother"): modellerinin hepsi
    for brand, ids in BRAND_ALIASES.items():
        if brand in q and not any(i in doc_ids for i in ids):
            doc_ids += list(ids)
            matched.append(brand)
    # "s7300" (a/b belirtilmeden) iki modeli de kapsar
    if "s7300" in q and not any(d.startswith("brother-s7300") for d in doc_ids):
        doc_ids += ["brother-s7300a", "brother-s7300b"]
        matched.append("s7300")
    return QueryContext(tuple(dict.fromkeys(doc_ids)), tuple(matched))
