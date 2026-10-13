"""Parçaları Qdrant'a (gömülü/lokal mod) dense + sparse vektörle yaz."""
import logging
import shutil
from typing import Any

from qdrant_client import QdrantClient, models

from .config import COLLECTION, QDRANT_DIR
from .embed import embed

log = logging.getLogger(__name__)
DENSE_DIM = 1024
BATCH = 64


def client() -> QdrantClient:
    QDRANT_DIR.mkdir(parents=True, exist_ok=True)
    return QdrantClient(path=str(QDRANT_DIR))


def _upsert(qc: QdrantClient, chunks: list[dict[str, Any]], first_id: int) -> None:
    for start in range(0, len(chunks), BATCH):
        batch = chunks[start:start + BATCH]
        vecs = embed([c["embed_text"] for c in batch])
        points = []
        for i, (c, v) in enumerate(zip(batch, vecs)):
            sp = v["sparse"]
            points.append(models.PointStruct(
                id=first_id + start + i,
                vector={"dense": v["dense"],
                        "sparse": models.SparseVector(indices=list(sp.keys()), values=list(sp.values()))},
                payload=c))
        qc.upsert(COLLECTION, points=points)
        log.info("indekslendi: %d/%d", min(start + BATCH, len(chunks)), len(chunks))


def replace_docs(chunks: list[dict[str, Any]], doc_ids: list[str]) -> int:
    """Yalnız verilen dokümanların parçalarını yeniden indeksler (eskiler silinir). Tam indeks CPU'da ~1 saat,
    tek doküman ~10 dk. Diğer dokümanların vektörlerine dokunulmaz."""
    qc = client()
    try:
        qc.delete(COLLECTION, points_selector=models.FilterSelector(filter=models.Filter(must=[
            models.FieldCondition(key="doc_id", match=models.MatchAny(any=doc_ids))])))
        ids, offset = [], None
        while True:
            pts, offset = qc.scroll(COLLECTION, limit=1000, offset=offset, with_payload=False)
            ids += [int(p.id) for p in pts]
            if offset is None:
                break
        new = [c for c in chunks if c["doc_id"] in doc_ids]
        _upsert(qc, new, max(ids, default=-1) + 1)
        return len(new)
    finally:
        qc.close()


def build_index(chunks: list[dict[str, Any]], rebuild: bool = True) -> int:
    if rebuild and QDRANT_DIR.exists():
        shutil.rmtree(QDRANT_DIR)
    qc = client()
    qc.create_collection(
        COLLECTION,
        vectors_config={"dense": models.VectorParams(size=DENSE_DIM, distance=models.Distance.COSINE)},
        sparse_vectors_config={"sparse": models.SparseVectorParams()})
    _upsert(qc, chunks, 0)
    qc.close()
    return len(chunks)
