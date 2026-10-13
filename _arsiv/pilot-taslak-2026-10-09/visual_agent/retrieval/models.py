"""Embedding ve reranker modelleri (kurum içi, CPU). Bir kez yüklenir."""

from __future__ import annotations

import threading
from functools import lru_cache

from ..config import SETTINGS

_lock = threading.Lock()


@lru_cache(maxsize=1)
def embedder():
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer(SETTINGS.embed_model, device="cpu")
    m.max_seq_length = SETTINGS.embed_max_len
    return m


@lru_cache(maxsize=1)
def reranker():
    from sentence_transformers import CrossEncoder
    return CrossEncoder(SETTINGS.rerank_model, device="cpu", max_length=SETTINGS.rerank_max_len)


def embed(texts: list[str], batch_size: int = 8, show_progress: bool = False) -> list[list[float]]:
    with _lock:
        vecs = embedder().encode(texts, batch_size=batch_size, normalize_embeddings=True,
                                 show_progress_bar=show_progress, convert_to_numpy=True)
    return vecs.tolist()


def rerank_scores(query: str, passages: list[str]) -> list[float]:
    """0-1 arası alaka skoru (bge-reranker çıktısı sigmoid ile)."""
    import math
    with _lock:
        raw = [float(x) for x in reranker().predict([(query, p) for p in passages], batch_size=8,
                                                     show_progress_bar=False)]
    # Kütüphane sürümüne göre çıktı ham logit ya da sigmoid uygulanmış olabilir.
    if any(x < 0 or x > 1 for x in raw):
        return [1 / (1 + math.exp(-x)) for x in raw]
    return raw
