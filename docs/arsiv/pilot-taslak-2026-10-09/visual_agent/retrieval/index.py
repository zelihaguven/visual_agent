"""Gömülü Qdrant indeksi: dense (bge-m3) + seyrek (BM25) vektör + metadata.

Gömülü mod (QdrantClient(path=...)) Docker gerektirmez. Üretimde aynı kod bir Qdrant sunucusuna
bağlanır (sadece istemci oluşturma değişir).
"""

from __future__ import annotations

import json
import uuid
from functools import lru_cache

from ..config import CHUNKS_DIR, QDRANT_DIR, SETTINGS
from . import models
from .text import bm25_doc_vector, tokenize

DENSE = "dense"
SPARSE = "bm25"
STATS_FILE = "corpus_stats.json"


@lru_cache(maxsize=1)
def client():
    from qdrant_client import QdrantClient
    QDRANT_DIR.mkdir(parents=True, exist_ok=True)
    return QdrantClient(path=str(QDRANT_DIR))


def ensure_collection(dim: int = 1024) -> None:
    from qdrant_client import models as qm
    c = client()
    if c.collection_exists(SETTINGS.collection):
        return
    c.create_collection(
        SETTINGS.collection,
        vectors_config={DENSE: qm.VectorParams(size=dim, distance=qm.Distance.COSINE)},
        sparse_vectors_config={SPARSE: qm.SparseVectorParams(modifier=qm.Modifier.IDF)},
    )


def _point_id(chunk_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))


def _avgdl(all_chunks: list[dict]) -> float:
    lens = [len(tokenize(c["embed_text"], c["lang"])) for c in all_chunks]
    return sum(lens) / max(len(lens), 1)


def index_chunks(chunks: list[dict], avgdl: float, log=print) -> None:
    from qdrant_client import models as qm
    ensure_collection()
    texts = [c["embed_text"] for c in chunks]
    log(f"  embedding: {len(texts)} parça (CPU, birkaç dakika sürebilir)")
    vecs = models.embed(texts, show_progress=True)
    points = []
    for c, v in zip(chunks, vecs):
        idx, val = bm25_doc_vector(tokenize(c["embed_text"], c["lang"]), avgdl)
        payload = {k: v2 for k, v2 in c.items() if k != "embed_text"}
        points.append(qm.PointStruct(id=_point_id(c["chunk_id"]),
                                     vector={DENSE: v, SPARSE: qm.SparseVector(indices=idx, values=val)},
                                     payload=payload))
    for i in range(0, len(points), 128):
        client().upsert(SETTINGS.collection, points=points[i:i + 128])


def delete_document(doc_id: str) -> int:
    """Bir dokümanın indeksteki tüm parçalarını siler. Silinen nokta sayısını döndürür."""
    from qdrant_client import models as qm
    c = client()
    if not c.collection_exists(SETTINGS.collection):
        return 0
    flt = qm.Filter(must=[qm.FieldCondition(key="doc_id", match=qm.MatchValue(value=doc_id))])
    n = c.count(SETTINGS.collection, count_filter=flt, exact=True).count
    c.delete(SETTINGS.collection, points_selector=qm.FilterSelector(filter=flt))
    return n


def load_all_chunks() -> list[dict]:
    out = []
    for p in sorted(CHUNKS_DIR.glob("*.jsonl")):
        out += [json.loads(line) for line in p.read_text("utf-8").splitlines() if line.strip()]
    return out


def save_stats(avgdl: float) -> None:
    (QDRANT_DIR / STATS_FILE).write_text(json.dumps({"avgdl": avgdl}), "utf-8")


def load_stats() -> dict:
    p = QDRANT_DIR / STATS_FILE
    return json.loads(p.read_text("utf-8")) if p.exists() else {"avgdl": 100.0}


def compute_avgdl(chunks: list[dict]) -> float:
    return _avgdl(chunks)
