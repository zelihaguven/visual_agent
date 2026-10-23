"""Hibrit arama (dense + sparse, RRF) + marka/doküman filtresi + reranker."""
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from qdrant_client import models

from .config import COLLECTION
from .embed import embed, rerank
from .index import client

PREFETCH_K = 30      # her kolun (dense, sparse) getirdiği aday sayısı
FUSED_K = 20         # RRF sonrası rerank'a giden aday sayısı

# İsteğe bağlı zamanlama kancası (bench/measure.py): aşama adı ve süresi (sn) ile çağrılır. None: ölçüm yok.
timing_hook: Callable[[str, float], None] | None = None


def _lap(stage: str, t: float) -> float:
    now = time.perf_counter()
    if timing_hook is not None:
        timing_hook(stage, now - t)
    return now

# İçindekiler satırı ("5-5-1. Needle up/down ........ 32"): Hiçbir soruya cevap değil ama terimleri içerdiği için
# üst sıralara çıkıyor (çağanoz sorusunda 1., "A makinesi ceket ölçüsü" cevabında alıntı olarak kullanıldı).
# Dar tutuldu: "TOTAL. ....... 1 | 00.00%" gibi gerçek tablo satırları elenmez.
_TOC = re.compile(r"\.{5,}\s*\d+")
_TOC_LINE = re.compile(r"\s*[\w\-. ()/]{3,80}?\s*\.{5,}\s*\d+\s*")


def is_toc(text: str) -> bool:
    return len(_TOC.findall(text)) >= 2 or bool(_TOC_LINE.fullmatch(text))


@dataclass(frozen=True)
class Hit:
    chunk: dict[str, Any]
    fused_rank: int
    rerank_score: float | None = None


def _filter(brands: list[str] | None, doc_ids: list[str] | None) -> models.Filter | None:
    must = []
    if brands:
        must.append(models.FieldCondition(key="brand", match=models.MatchAny(any=brands)))
    if doc_ids:
        must.append(models.FieldCondition(key="doc_id", match=models.MatchAny(any=doc_ids)))
    return models.Filter(must=must) if must else None


def search(query: str, *, brands: list[str] | None = None, doc_ids: list[str] | None = None,
           mode: str = "hybrid", top_k: int = 5, do_rerank: bool = True,
           query_en: str | None = None) -> list[Hit]:
    """mode: 'dense' | 'sparse' | 'hybrid'. query_en verilirse sparse kol ona göre çalışır
    (TR soru + EN doküman: kelime araması için çeviri)."""
    flt = _filter(brands, doc_ids)
    t = time.perf_counter()
    dense_vec = embed([query])[0]
    sparse_src = embed([query_en])[0]["sparse"] if query_en else dense_vec["sparse"]
    dense_q = dense_vec["dense"]
    sparse_q = models.SparseVector(indices=list(sparse_src.keys()), values=list(sparse_src.values()))

    t = _lap("embed", t)
    qc = client()
    t = _lap("qdrant_open", t)
    try:
        if mode == "dense":
            res = qc.query_points(COLLECTION, query=dense_q, using="dense", query_filter=flt,
                                  limit=FUSED_K, with_payload=True)
        elif mode == "sparse":
            res = qc.query_points(COLLECTION, query=sparse_q, using="sparse", query_filter=flt,
                                  limit=FUSED_K, with_payload=True)
        else:
            res = qc.query_points(
                COLLECTION,
                prefetch=[models.Prefetch(query=dense_q, using="dense", filter=flt, limit=PREFETCH_K),
                          models.Prefetch(query=sparse_q, using="sparse", filter=flt, limit=PREFETCH_K)],
                query=models.FusionQuery(fusion=models.Fusion.RRF),
                limit=FUSED_K, with_payload=True)
    finally:
        qc.close()
    t = _lap("qdrant", t)

    points = [p for p in res.points if not is_toc(p.payload["text"])]
    if not do_rerank or not points:
        return [Hit(p.payload, i) for i, p in enumerate(points[:top_k])]
    scores = rerank(query, [p.payload["text"] for p in points])
    _lap("rerank", t)
    order = sorted(range(len(points)), key=lambda i: scores[i], reverse=True)[:top_k]
    return [Hit(points[i].payload, i, scores[i]) for i in order]
