"""bge-m3 (dense + sparse) ve reranker sarmalayıcıları. Tembel yüklenir, CPU'da çalışır.

Reranker sağlayıcısı config'den (PILOT_RERANK_*); varsayılan bge-reranker-v2-m3, FlagEmbedding, max_length 512.
Sağlayıcılar: rerankers.py."""
import warnings
from functools import lru_cache
from typing import Any

from .config import (EMBED_BATCH, EMBED_DEVICE, EMBED_MAX_LENGTH, EMBED_MODEL, RERANK_BACKEND, RERANK_BATCH,
                     RERANK_MAX_LENGTH, RERANK_MODEL, RERANK_PROVIDER)

warnings.filterwarnings("ignore")


@lru_cache(maxsize=1)
def _embedder():
    from FlagEmbedding import BGEM3FlagModel
    return BGEM3FlagModel(EMBED_MODEL, use_fp16=False, devices=[EMBED_DEVICE])


@lru_cache(maxsize=1)
def _reranker():
    from .rerankers import make_reranker
    return make_reranker(RERANK_PROVIDER, RERANK_MODEL, RERANK_BACKEND, RERANK_MAX_LENGTH, RERANK_BATCH)


def embed(texts: list[str]) -> list[dict[str, Any]]:
    """Her metin için {'dense': list[float], 'sparse': {token_id: weight}}."""
    out = _embedder().encode(texts, batch_size=EMBED_BATCH, max_length=EMBED_MAX_LENGTH,
                             return_dense=True, return_sparse=True)
    return [{"dense": d.tolist(),
             "sparse": {int(k): float(v) for k, v in w.items()}}
            for d, w in zip(out["dense_vecs"], out["lexical_weights"])]


def rerank(query: str, passages: list[str]) -> list[float]:
    if not passages:
        return []
    return _reranker()(query, passages)
