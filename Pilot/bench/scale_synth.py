"""Aşama 3a: sentetik vektörle ölçeklenme (süre, ANN recall, RAM/disk). Embed maliyeti yok.

Kullanım (Pilot klasöründe):
    python -m bench.scale_synth export                  # yerelde: gömülü indeksten gerçek bge-m3 + BM25 vektörleri
    python -m bench.scale_synth build --n 1000000 --collection synth_1m [--noise 0.015 --drop 0.3]   # VM
    python -m bench.scale_index copy --source synth_1m --target synth_100k --max-kademe 100000         # küçük kademe

- Görev dosyasındaki gibi: gerçek parçanın dense vektörü + küçük Gauss gürültüsü, yeniden normalize (σ=0,015/boyut:
  kaynağa kosinüs ~0,9); BM25 ağırlıkları rastgele ölçeklenir (0,5–1,5) ve her token %30 olasılıkla düşer (en az bir
  token kalır). Payload kaynak parçanın brand/doc_id/nav/metin dağılımını taşır (payload boyutu da gerçekçi); yetki
  yapay (bench.server.synthetic_access).
- İlk noktalar gerçek parçaların kendisidir (kimlik 0..R-1); sentetikler ardından. kademe alanı iç içe kademeler
  (10k/100k/1M) için; copy alt komutuyla küçük koleksiyonlar yeniden üretmeden çıkarılır.
- Yükleme gRPC ile (PILOT_QDRANT_GRPC=1 önerilir), HNSW kurulumu yükleme bitince açılır. Kaldığı yerden devam:
  mevcut nokta sayısı kadar atlanır (üretim tohumlu ve sıralı olduğu için aynı noktalar üretilir).
"""
import argparse
import json
import logging
import time
from pathlib import Path
from typing import Any

import numpy as np

from bench.scale_corpus import SCALE_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("scale_synth")
logging.getLogger("httpx").setLevel(logging.WARNING)

EXPORT = SCALE_DIR / "real_bge_m3.npz"
TIERS = (10_000, 100_000, 1_000_000)
BATCH = 1000
KEEP = ("chunk_id", "doc_id", "brand", "nav", "pages", "access", "text")    # text: arama içindekiler satırını eler


def export(collection: str = "manuals") -> Path:
    """Gömülü (ya da PILOT_QDRANT_URL ile sunucu) indeksteki gerçek parçaların dense + BM25 vektörleri ve payload'ı."""
    from pilot.index import client
    qc = client()
    ids, dense, sparse, payloads, offset = [], [], [], [], None
    while True:
        pts, offset = qc.scroll(collection, limit=500, offset=offset, with_payload=True, with_vectors=["dense", "bm25"])
        for p in pts:
            ids.append(int(p.id))
            dense.append(p.vector["dense"])
            sv = p.vector["bm25"]
            sparse.append({int(i): float(v) for i, v in zip(sv.indices, sv.values)})
            payloads.append({k: p.payload.get(k) for k in KEEP})
        if offset is None:
            break
    qc.close()
    EXPORT.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(EXPORT, ids=np.asarray(ids), dense=np.asarray(dense, dtype=np.float32),
                        sparse=np.asarray([json.dumps(s) for s in sparse]),
                        payload=np.asarray([json.dumps(p, ensure_ascii=False) for p in payloads]))
    log.info("%d gerçek parça → %s (%.1f MB)", len(ids), EXPORT, EXPORT.stat().st_size / 2**20)
    return EXPORT


def load_real() -> tuple[np.ndarray, list[dict[int, float]], list[dict[str, Any]]]:
    z = np.load(EXPORT)
    sparse = [{int(k): v for k, v in json.loads(s).items()} for s in z["sparse"]]
    return z["dense"], sparse, [json.loads(p) for p in z["payload"]]


def tier(pos: int) -> int:
    return next(t for t in TIERS if pos < t) if pos < TIERS[-1] else TIERS[-1]


def synth_batch(start: int, n: int, dense: np.ndarray, sparse: list[dict[int, float]], payloads: list[dict[str, Any]],
                noise: float, drop: float, seed: int) -> list[Any]:
    """[start, start+n) kimlikli noktalar. Kimlik R'den küçükse gerçek parça; değilse sentetik. Rastgelelik kimlikten
    türetilir: aynı kimlik her koşuda aynı nokta (kaldığı yerden devam ve kademe kopyası tutarlı)."""
    from qdrant_client import models

    from bench.server import synthetic_access
    R = len(dense)
    out = []
    for pid in range(start, start + n):
        if pid < R:
            v, sp, pl = dense[pid], sparse[pid], {**payloads[pid], "kind": "gercek"}
        else:
            g = np.random.default_rng([seed, pid])
            j = int(g.integers(R))
            v = dense[j] + g.normal(0, noise, dense.shape[1]).astype(np.float32)
            v = v / np.linalg.norm(v)
            keys = [k for k in sparse[j] if g.random() >= drop] or [next(iter(sparse[j]))]
            sp = {k: float(sparse[j][k] * g.uniform(0.5, 1.5)) for k in keys}
            pl = {**{k: payloads[j][k] for k in ("doc_id", "brand", "nav", "pages", "text")}, "chunk_id": f"syn-{pid:07d}",
                  "access": synthetic_access(pid), "kind": "sentetik", "source_id": j}
        out.append(models.PointStruct(
            id=pid, payload={**pl, "kademe": 0 if pid < R else tier(pid)},
            vector={"dense": np.asarray(v, dtype=np.float32).tolist(),
                    "bm25": models.SparseVector(indices=list(sp), values=list(sp.values()))}))
    return out


def build(n: int, collection: str, noise: float, drop: float, seed: int, workers: int) -> dict[str, Any]:
    from concurrent.futures import ThreadPoolExecutor

    from bench.scale_index import ensure_collection, finalize, paths
    from bench.server import server_client
    dense, sparse, payloads = load_real()
    meta = {"corpus": "sentetik", "embed": "bge-m3-local", "model": "BAAI/bge-m3", "dim": int(dense.shape[1]),
            "batch": BATCH, "short_dims": [], "full_on_disk": False, "full_hnsw": True, "n": n, "noise": noise,
            "drop": drop, "seed": seed, "real": len(dense)}
    qc = server_client()
    ensure_collection(qc, collection, meta)
    paths(collection)[1].write_text(json.dumps(meta, indent=1), encoding="utf-8")
    have = qc.count(collection).count
    start = (have // BATCH) * BATCH                    # yarım kalan toplu iş baştan (upsert aynı kimlikle)
    log.info("%s: %d nokta var, %d'den devam, hedef %d", collection, have, start, n)
    t0, done = time.time(), 0

    def work(s: int) -> int:
        pts = synth_batch(s, min(BATCH, n - s), dense, sparse, payloads, noise, drop, seed)
        qc.upsert(collection, points=pts, wait=True)
        return len(pts)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        for i, k in enumerate(ex.map(work, range(start, n, BATCH))):
            done += k
            if i % 50 == 0:
                rate = done / max(time.time() - t0, 1e-9)
                log.info("%d/%d · %.0f nokta/sn · kalan ~%.1f dk", start + done, n, rate, (n - start - done) / rate / 60)
    finalize(qc, collection)
    res = {"collection": collection, "points": qc.count(collection).count, "seconds": round(time.time() - t0, 1), **meta}
    paths(collection)[2].write_text(json.dumps(res, indent=1), encoding="utf-8")
    log.info("bitti: %s", res)
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export")
    e.add_argument("--collection", default="manuals")
    b = sub.add_parser("build")
    b.add_argument("--n", type=int, default=TIERS[-1])
    b.add_argument("--collection", default="synth_1m")
    b.add_argument("--noise", type=float, default=0.015)
    b.add_argument("--drop", type=float, default=0.3)
    b.add_argument("--seed", type=int, default=0)
    b.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    if a.cmd == "export":
        export(a.collection)
    else:
        build(a.n, a.collection, a.noise, a.drop, a.seed, a.workers)


if __name__ == "__main__":
    main()
