"""Parçaları Qdrant'a dense + sparse vektörle yaz. Gömülü (lokal) mod varsayılan; PILOT_QDRANT_URL ile sunucu modu.

Sunucu modunda koleksiyon ayarları config'den gelir (HNSW, quantization, on_disk) ve brand/doc_id/access alanlarına
payload indeksi kurulur; filtreli aramanın hızı büyük koleksiyonda buna bağlı. Gömülü mod kaba kuvvetle arar.
"""
import logging
import shutil
from typing import Any

from qdrant_client import QdrantClient, models

from .config import (COLLECTION, HNSW_EF_CONSTRUCT, HNSW_FULL_SCAN_THRESHOLD, HNSW_M, INDEX_SPARSE, PAYLOAD_ON_DISK,
                     QDRANT_API_KEY, QDRANT_DIR, QDRANT_GRPC, QDRANT_REUSE, QDRANT_URL, QUANT_ALWAYS_RAM,
                     QUANTIZATION, VECTORS_ON_DISK)
from .embed import encode_docs, short_vector
from .registry import BY_ID

log = logging.getLogger(__name__)
DENSE_DIM = 1024
BATCH = 64
SPARSE_NAMES = {"bge-m3": "sparse", "bm25": "bm25"}    # sparse vektörün koleksiyondaki adı


def short_name(dim: int) -> str:
    return f"dense_s{dim}"
PAYLOAD_INDEXES = ("brand", "doc_id", "access")     # keyword; access bir liste (departman/yetki grupları)


def client() -> QdrantClient:
    if QDRANT_URL:
        return QdrantClient(url=QDRANT_URL, prefer_grpc=QDRANT_GRPC, api_key=QDRANT_API_KEY, timeout=120)
    QDRANT_DIR.mkdir(parents=True, exist_ok=True)
    return QdrantClient(path=str(QDRANT_DIR))


# Arama istemcisi: REUSE ise (varsayılan) süreç boyunca tek örnek (gömülü modda her açılış koleksiyonu diskten yükler,
# ~2 sn). Kapalıysa her aramada açılıp kapanır; gömülü klasör aramalar arasında başka sürece açık kalır.
REUSE = QDRANT_REUSE
_shared: QdrantClient | None = None


def search_client() -> QdrantClient:
    global _shared
    if not REUSE:
        return client()
    if _shared is None:
        _shared = client()
    return _shared


def release(qc: QdrantClient) -> None:
    """search_client() ile alınan istemciyi bırakır: paylaşılan örnek açık kalır, diğerleri kapanır."""
    if qc is not _shared:
        qc.close()


def close_shared() -> None:
    global _shared
    if _shared is not None:
        _shared.close()
        _shared = None


def quantization_config(kind: str, always_ram: bool) -> models.QuantizationConfig | None:
    if kind == "none":
        return None
    if kind == "int8":
        return models.ScalarQuantization(scalar=models.ScalarQuantizationConfig(
            type=models.ScalarType.INT8, quantile=0.99, always_ram=always_ram))
    if kind == "binary":
        return models.BinaryQuantization(binary=models.BinaryQuantizationConfig(always_ram=always_ram))
    raise ValueError(f"bilinmeyen quantization: {kind} (none | int8 | binary)")


def collection_schema(dense_dim: int = DENSE_DIM, *, m: int | None = HNSW_M, ef_construct: int | None = HNSW_EF_CONSTRUCT,
                      full_scan_threshold: int | None = HNSW_FULL_SCAN_THRESHOLD, quantization: str = QUANTIZATION,
                      always_ram: bool = QUANT_ALWAYS_RAM, vectors_on_disk: bool = VECTORS_ON_DISK,
                      payload_on_disk: bool = PAYLOAD_ON_DISK, sparse: str | tuple[str, ...] = INDEX_SPARSE,
                      short_dims: tuple[int, ...] = ()) -> dict[str, Any]:
    """create_collection argümanları. sparse: tür ya da türler ('bge-m3' → 'sparse', 'bm25' → 'bm25'; bm25'te IDF'i
    Qdrant uygular). short_dims: MRL kısa vektörleri (dense_s256 ...), kısa vektörle aday çekmek için."""
    kinds = (sparse,) if isinstance(sparse, str) else tuple(sparse)
    hnsw = None
    if any(x is not None for x in (m, ef_construct, full_scan_threshold)):
        hnsw = models.HnswConfigDiff(m=m, ef_construct=ef_construct, full_scan_threshold=full_scan_threshold)
    vectors = {"dense": models.VectorParams(size=dense_dim, distance=models.Distance.COSINE, hnsw_config=hnsw,
                                            on_disk=vectors_on_disk or None)}
    for d in short_dims:
        vectors[short_name(d)] = models.VectorParams(size=d, distance=models.Distance.COSINE, hnsw_config=hnsw,
                                                     on_disk=vectors_on_disk or None)
    sparse_cfg = {SPARSE_NAMES[k]: (models.SparseVectorParams(modifier=models.Modifier.IDF) if k == "bm25"
                                    else models.SparseVectorParams()) for k in kinds}
    return {"vectors_config": vectors,
            "sparse_vectors_config": sparse_cfg,
            "quantization_config": quantization_config(quantization, always_ram),
            "on_disk_payload": payload_on_disk or None}


def create_collection(qc: QdrantClient, name: str = COLLECTION, payload_indexes: bool | None = None,
                      **schema: Any) -> None:
    """payload_indexes None: sunucu modunda kurulur (gömülü modda etkisi yok)."""
    qc.create_collection(name, **(schema or collection_schema()))
    if payload_indexes if payload_indexes is not None else bool(QDRANT_URL):
        for field in PAYLOAD_INDEXES:
            qc.create_payload_index(name, field, field_schema=models.PayloadSchemaType.KEYWORD)


def with_access(chunk: dict[str, Any]) -> dict[str, Any]:
    """Parça payload'ı + dokümanın yetki grupları (registry). chunks.jsonl değişmez; access indekslemede eklenir."""
    meta = BY_ID.get(chunk["doc_id"])
    return {**chunk, "access": list(meta.access) if meta else ["all"]}


def sync_access(qc: QdrantClient, name: str = COLLECTION) -> None:
    """Vektörlere dokunmadan payload'daki access alanını registry'ye göre günceller (yeniden embed gerekmez)."""
    for doc_id, meta in BY_ID.items():
        qc.set_payload(name, payload={"access": list(meta.access)}, points=models.Filter(must=[
            models.FieldCondition(key="doc_id", match=models.MatchValue(value=doc_id))]))


def _sv(sp: dict[int, float]) -> models.SparseVector:
    return models.SparseVector(indices=list(sp.keys()), values=list(sp.values()))


def point_vectors(v: dict[str, Any], sparse: str = "bm25", short_dims: tuple[int, ...] = ()) -> dict[str, Any]:
    """v: {'dense', 'sparses': {tür: vektör}} ya da tek sparse için {'dense', 'sparse'} (sparse türü)."""
    sparses = v.get("sparses") or {sparse: v["sparse"]}
    out = {"dense": v["dense"], **{SPARSE_NAMES[k]: _sv(sp) for k, sp in sparses.items()}}
    for d in short_dims:
        out[short_name(d)] = short_vector(v["dense"], d)
    return out


def _upsert(qc: QdrantClient, chunks: list[dict[str, Any]], first_id: int, collection: str = COLLECTION,
            short_dims: tuple[int, ...] = ()) -> None:
    for start in range(0, len(chunks), BATCH):
        batch = chunks[start:start + BATCH]
        vecs = encode_docs([c["embed_text"] for c in batch])
        points = [models.PointStruct(id=first_id + start + i, vector=point_vectors(v, short_dims=short_dims),
                                     payload=with_access(c))
                  for i, (c, v) in enumerate(zip(batch, vecs))]
        qc.upsert(collection, points=points)
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


def add_bm25(collection: str = COLLECTION) -> int:
    """Mevcut koleksiyona BM25 sparse vektörü ekler: vektörler ve payload kopyalanır, BM25 payload'daki embed_text'ten
    hesaplanır (yeniden embed yok). Qdrant var olan koleksiyona yeni sparse vektör adı eklemediği için koleksiyon aynı
    adla yeniden kurulur. Döner: nokta sayısı (zaten varsa 0). Gömülü ve sunucu modunda çalışır (PILOT_QDRANT_URL)."""
    from .sparse import bm25_docs
    qc = client()
    try:
        info = qc.get_collection(collection)
        if "bm25" in (info.config.params.sparse_vectors or {}):
            log.info("%s zaten bm25 taşıyor", collection)
            return 0
        pts, offset = [], None
        while True:
            batch, offset = qc.scroll(collection, limit=500, offset=offset, with_payload=True, with_vectors=True)
            pts += batch
            if offset is None:
                break
        dense_dim = info.config.params.vectors["dense"].size
        bm25 = bm25_docs([p.payload["embed_text"] for p in pts])
        qc.delete_collection(collection)
        create_collection(qc, collection, **collection_schema(dense_dim, sparse=("bge-m3", "bm25")))
        for i in range(0, len(pts), 256):
            qc.upsert(collection, points=[models.PointStruct(id=p.id, vector={**p.vector, "bm25": _sv(b)},
                                                             payload=p.payload)
                                          for p, b in zip(pts[i:i + 256], bm25[i:i + 256])])
        return len(pts)
    finally:
        qc.close()


def refresh_payloads(chunks: list[dict[str, Any]], doc_ids: list[str]) -> int:
    """Metni ve embed_text'i değişmemiş dokümanlarda yalnız payload'ı (ör. nav, access) yeniler; vektörlere dokunmaz.
    Parçalar chunk_id ile eşlenir. Döner: güncellenen nokta sayısı."""
    by_id = {c["chunk_id"]: c for c in chunks if c["doc_id"] in doc_ids}
    qc = client()
    n = 0
    try:
        offset = None
        while True:
            pts, offset = qc.scroll(COLLECTION, limit=500, offset=offset, with_payload=["chunk_id", "embed_text"],
                                    scroll_filter=models.Filter(must=[models.FieldCondition(
                                        key="doc_id", match=models.MatchAny(any=doc_ids))]))
            for p in pts:
                new = by_id.get(p.payload.get("chunk_id"))
                if new is None or new["embed_text"] != p.payload.get("embed_text"):
                    raise ValueError(f"{p.payload.get('chunk_id')}: embed_text değişmiş, yeniden embed gerekir")
                qc.overwrite_payload(COLLECTION, payload=with_access(new), points=[p.id])
                n += 1
            if offset is None:
                return n
    finally:
        qc.close()


def build_index(chunks: list[dict[str, Any]], rebuild: bool = True) -> int:
    if rebuild and not QDRANT_URL and QDRANT_DIR.exists():
        shutil.rmtree(QDRANT_DIR)
    qc = client()
    if rebuild and QDRANT_URL and qc.collection_exists(COLLECTION):
        qc.delete_collection(COLLECTION)
    create_collection(qc)
    _upsert(qc, chunks, 0)
    qc.close()
    return len(chunks)
