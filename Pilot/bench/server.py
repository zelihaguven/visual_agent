"""Qdrant sunucu modu yardımcıları: gömülü indeksi yeniden embed etmeden sunucuya kopyala, sunucu bellek/disk bilgisi.

Kullanım (Pilot klasöründe; sunucu açık: qdrant/start_windows.ps1):
    python -m bench.server copy                                   # data/qdrant -> sunucu, koleksiyon "manuals"
    python -m bench.server copy --name manuals_q8 --quantization int8 --m 32 --ef-construct 200
    python -m bench.server copy --name manuals_access --synthetic-access   # yarısı "all", yarısı g1..g4
    python -m bench.server info --name manuals
Sunucu adresi: PILOT_QDRANT_URL (yoksa http://127.0.0.1:6333). Gömülü klasör kopyalama sırasında başka süreçte açık
olmamalı (arayüz kapalı).
"""
import argparse
import logging
import random
import time
from typing import Any

from qdrant_client import QdrantClient, models

from bench.common import PILOT_DIR, dir_size

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("server")
SERVER_DATA = PILOT_DIR / "data" / "qdrant_server"
GROUPS = ("g1", "g2", "g3", "g4")
EMBEDDED_COLLECTION = "manuals"         # gömülü indeksin koleksiyonu (run_index.py)


def synthetic_access(point_id: int, seed: int = 0) -> list[str]:
    """Yapay yetki dağılımı (ölçüm için): parçaların yarısı herkese açık, yarısı dört gruptan birine özel."""
    r = random.Random(f"{seed}:{point_id}")
    return ["all"] if r.random() < 0.5 else [r.choice(GROUPS)]


def server_client(url: str | None = None) -> QdrantClient:
    import os
    return QdrantClient(url=url or os.environ.get("PILOT_QDRANT_URL") or "http://127.0.0.1:6333",
                        api_key=os.environ.get("PILOT_QDRANT_API_KEY") or None, timeout=300)


def read_embedded(batch: int = 500) -> list[models.Record]:
    from pilot.config import QDRANT_DIR
    src = QdrantClient(path=str(QDRANT_DIR))
    try:
        out, offset = [], None
        while True:
            pts, offset = src.scroll(EMBEDDED_COLLECTION, limit=batch, offset=offset, with_payload=True,
                                     with_vectors=True)
            out += pts
            if offset is None:
                return out
    finally:
        src.close()


def wait_indexed(qc: QdrantClient, name: str, timeout: float = 1800) -> dict[str, Any]:
    t = time.time()
    while True:
        info = qc.get_collection(name)
        if info.status == models.CollectionStatus.GREEN and info.optimizer_status == models.OptimizersStatusOneOf.OK:
            return {"status": str(info.status), "points": info.points_count,
                    "indexed_vectors": info.indexed_vectors_count, "segments": info.segments_count,
                    "seconds": round(time.time() - t, 1)}
        if time.time() - t > timeout:
            raise TimeoutError(f"{name} indekslenmedi: {info.status}")
        time.sleep(1)


def copy(name: str, schema_args: dict[str, Any], synthetic: bool, batch: int = 256) -> dict[str, Any]:
    from pilot.index import PAYLOAD_INDEXES, collection_schema, with_access
    pts = read_embedded()
    log.info("gömülü indeks: %d parça okundu", len(pts))
    qc = server_client()
    if qc.collection_exists(name):
        qc.delete_collection(name)
    schema = collection_schema(**schema_args)
    t = time.time()
    qc.create_collection(name, **schema)
    for field in PAYLOAD_INDEXES:
        qc.create_payload_index(name, field, field_schema=models.PayloadSchemaType.KEYWORD)
    for i in range(0, len(pts), batch):
        qc.upsert(name, points=[models.PointStruct(
            id=p.id, vector=p.vector,
            payload={**with_access(p.payload), **({"access": synthetic_access(int(p.id))} if synthetic else {})})
            for p in pts[i:i + batch]])
    upload_s = time.time() - t
    idx = wait_indexed(qc, name)
    qc.close()
    res = {"name": name, "points": len(pts), "upload_s": round(upload_s, 1), "index": idx,
           "schema_args": schema_args, "synthetic_access": synthetic}
    log.info("kopyalandı: %s", res)
    return res


def server_memory(name: str | None = None) -> dict[str, Any]:
    """Sunucu sürecinin RAM'i (qdrant süreci) ve depo diski. Bütün koleksiyonlar için ortak."""
    import psutil
    procs = [p for p in psutil.process_iter(["name", "memory_info"]) if (p.info["name"] or "").lower().startswith("qdrant")]
    rss = sum(p.info["memory_info"].rss for p in procs) if procs else None
    out = {"mode": "server", "rss_mb": round(rss / 2**20, 1) if rss else None,
           "storage_mb": round(dir_size(SERVER_DATA / "storage") / 2**20, 1)}
    if name:
        qc = server_client()
        info = qc.get_collection(name)
        out.update(points=info.points_count, indexed_vectors=info.indexed_vectors_count, segments=info.segments_count,
                   collection_disk_mb=round(dir_size(SERVER_DATA / "storage" / "collections" / name) / 2**20, 1))
        qc.close()
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("copy")
    c.add_argument("--name", default="manuals")
    c.add_argument("--m", type=int)
    c.add_argument("--ef-construct", type=int)
    c.add_argument("--full-scan-threshold", type=int)
    c.add_argument("--quantization", default="none", choices=["none", "int8", "binary"])
    c.add_argument("--synthetic-access", action="store_true")
    i = sub.add_parser("info")
    i.add_argument("--name", default="manuals")
    a = ap.parse_args()
    if a.cmd == "copy":
        copy(a.name, {"m": a.m, "ef_construct": a.ef_construct, "full_scan_threshold": a.full_scan_threshold,
                      "quantization": a.quantization}, a.synthetic_access)
        print(server_memory(a.name))
    else:
        print(server_memory(a.name))


if __name__ == "__main__":
    main()
