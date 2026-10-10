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


def build_index(chunks: list[dict[str, Any]], rebuild: bool = True) -> int:
    if rebuild and QDRANT_DIR.exists():
        shutil.rmtree(QDRANT_DIR)
    qc = client()
    qc.create_collection(
        COLLECTION,
        vectors_config={"dense": models.VectorParams(size=DENSE_DIM, distance=models.Distance.COSINE)},
        sparse_vectors_config={"sparse": models.SparseVectorParams()})
    for start in range(0, len(chunks), BATCH):
        batch = chunks[start:start + BATCH]
        vecs = embed([c["embed_text"] for c in batch])
        points = []
        for i, (c, v) in enumerate(zip(batch, vecs)):
            sp = v["sparse"]
            points.append(models.PointStruct(
                id=start + i,
                vector={"dense": v["dense"],
                        "sparse": models.SparseVector(indices=list(sp.keys()), values=list(sp.values()))},
                payload=c))
        qc.upsert(COLLECTION, points=points)
        log.info("indekslendi: %d/%d", min(start + BATCH, len(chunks)), len(chunks))
    qc.close()
    return len(chunks)
