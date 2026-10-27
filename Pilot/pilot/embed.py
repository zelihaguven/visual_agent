"""bge-m3 (dense + sparse) ve reranker sarmalayıcıları. Tembel yüklenir, CPU'da çalışır.

Reranker sağlayıcısı config'den (PILOT_RERANK_*); varsayılan bge-reranker-v2-m3, torch backend, max_length 512.
Sağlayıcılar: rerankers.py."""
import warnings
from functools import lru_cache
from typing import Any

from .config import (DENSE_MODE, DENSE_SHORT_DIM, EMBED_BATCH, EMBED_CLOUD_MODEL, EMBED_DEVICE, EMBED_DOC_PREFIX,
                     EMBED_MAX_LENGTH, EMBED_MODEL, EMBED_PROVIDER, EMBED_QUERY_PREFIX, RERANK_BACKEND, RERANK_BATCH,
                     RERANK_MAX_LENGTH, RERANK_MODEL, RERANK_PROVIDER, SPARSE_KIND, INDEX_SPARSE)

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


def short_vector(v: list[float], dim: int) -> list[float]:
    """MRL: vektörün ilk dim bileşeni, yeniden normalize (MRL eğitimli modellerde; bge-m3 MRL değildir)."""
    import math
    head = v[:dim]
    n = math.sqrt(sum(x * x for x in head)) or 1.0
    return [x / n for x in head]


@lru_cache(maxsize=1)
def _cloud():
    from .cloud import CloudEmbedder, EmbedCache
    if not EMBED_CLOUD_MODEL:
        raise RuntimeError("PILOT_EMBED_PROVIDER=openrouter için PILOT_EMBED_MODEL gerekli")
    return CloudEmbedder(EMBED_CLOUD_MODEL, cache=EmbedCache())


def encode_query(text: str, sparse_text: str | None = None) -> dict[str, Any]:
    """Sorgu vektörleri: {'dense', 'sparse', 'short'?}. Sağlayıcı ve sparse türü config'den. sparse_text: sparse kol için
    ayrı metin (query_en). Bulut sorgu embedding'i önbelleğe alınmaz (süre ölçümü gerçek çağrıyla)."""
    if EMBED_PROVIDER == "local":
        vecs = embed([text] if not sparse_text else [text, sparse_text])
        dense, sparse = vecs[0]["dense"], vecs[-1]["sparse"]
    elif EMBED_PROVIDER == "openrouter":
        dense = _cloud().embed([EMBED_QUERY_PREFIX + text], use_cache=False)[0]
        sparse = None
    else:
        raise ValueError(f"bilinmeyen embedding sağlayıcısı: {EMBED_PROVIDER}")
    if SPARSE_KIND == "bm25" or sparse is None:
        from .sparse import bm25_query
        sparse = bm25_query(sparse_text or text)
    out = {"dense": dense, "sparse": sparse}
    if DENSE_MODE != "full":
        out["short"] = short_vector(dense, DENSE_SHORT_DIM)
    return out


def encode_docs(texts: list[str]) -> list[dict[str, Any]]:
    """İndeksleme vektörleri: {'dense', 'sparses': {tür: vektör}}. İndekslenen sparse türleri INDEX_SPARSE (local:
    bge-m3 ve bm25 ikisi birden, sorgu anında PILOT_SPARSE ile seçilir). Bulut embedding önbelleğe alınır."""
    sparses: dict[str, list[Any]] = {}
    if EMBED_PROVIDER == "local":
        vecs = embed(texts)
        dense = [v["dense"] for v in vecs]
        sparses["bge-m3"] = [v["sparse"] for v in vecs]
    else:
        dense = _cloud().embed([EMBED_DOC_PREFIX + t for t in texts])
    if "bm25" in INDEX_SPARSE:
        from .sparse import bm25_docs
        sparses["bm25"] = bm25_docs(texts)
    return [{"dense": d, "sparses": {k: v[i] for k, v in sparses.items() if k in INDEX_SPARSE}}
            for i, d in enumerate(dense)]


def rerank_enabled() -> bool:
    return RERANK_PROVIDER != "none"


def rerank(query: str, passages: list[str]) -> list[float]:
    if not passages:
        return []
    return _reranker()(query, passages)
