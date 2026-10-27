"""Aşama 3b: kalabalık korpusunu Qdrant sunucusuna indeksler. Paralel bulut embedding, kaldığı yerden devam.

Kullanım (Pilot klasöründe; PILOT_QDRANT_URL ile sunucu; bulut için OPENROUTER_API_KEY):
    python -m bench.scale_index index --corpus data/scale/corpus --collection scale_qwen3_8b --embed qwen3-8b \
        --workers 16 [--max-kademe 100000] [--yes]
    python -m bench.scale_index index ... --embed bge-m3-local --device cuda --workers 1   # local yol (GPU'lu VM)
    python -m bench.scale_index copy --source scale_qwen3_8b --target scale_qwen3_8b_100k --max-kademe 100000
    python -m bench.scale_index status --collection scale_qwen3_8b
    python -m bench.scale_index probe --collection scale_qwen3_8b --query "E050 hatası ne demek?"

- Koleksiyon (qwen3-8b): tam vektör "dense" (4096, diskte, HNSW'siz: yalnız yeniden skorlamada okunur), MRL kısa
  vektör "dense_s256" (RAM'de, HNSW), "bm25" (IDF'i Qdrant uygular). Arama: PILOT_DENSE_MODE=short_rescore.
  Kısa vektör tam vektörün başından türetilir (ek istek yok). Payload indeksleri: brand, doc_id, access, nav, kademe.
- Kaldığı yerden: nokta kimliği = korpustaki sıra; toplu iş (batch) Qdrant'a yazılınca data/scale/progress/
  <koleksiyon>.done dosyasına eklenir. Yeniden başlatınca bitmiş toplu işler atlanır. Ctrl+C güvenli: süren istekler
  biter, yazılmayan toplu iş sonra yeniden gönderilir (upsert aynı kimlikle; çift kayıt olmaz).
- Toplu yükleme sırasında HNSW kurulumu ertelenir (indexing_threshold=0); bütün toplu işler bitince açılır.
- Maliyet: koşmadan önce kalan token × ZDR fiyatı; 5 USD'yi aşarsa --yes gerekir. ZDR zorunlu (pilot/cloud.py).
"""
import argparse
import json
import logging
import signal
import threading
import time
from collections.abc import Iterator
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from pathlib import Path
from typing import Any

from bench.scale_corpus import SCALE_DIR, iter_corpus

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("scale_index")
logging.getLogger("httpx").setLevel(logging.WARNING)            # her Qdrant isteği satır yazmasın

PROGRESS_DIR = SCALE_DIR / "progress"
COST_LIMIT_USD = 5.0
BATCH_RETRIES = 3            # kalıcı görünen hatada (ör. 400, eksik vektör) toplu işin yeniden denenmesi
LOG_EVERY = 20               # toplu iş
INDEXING_THRESHOLD = 20_000  # Qdrant varsayılanı (KB); yükleme bitince geri açılır


def spec_for(key: str) -> dict[str, Any]:
    from bench.providers import specs
    return specs()[key]


def paths(collection: str) -> tuple[Path, Path, Path]:
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    return (PROGRESS_DIR / f"{collection}.done", PROGRESS_DIR / f"{collection}.meta.json",
            PROGRESS_DIR / f"{collection}.stats.json")


def batches(corpus: Path, size: int, max_kademe: int | None) -> Iterator[tuple[int, list[dict[str, Any]]]]:
    buf: list[dict[str, Any]] = []
    k = 0
    for r in iter_corpus(corpus, max_kademe):
        buf.append(r)
        if len(buf) == size:
            yield k, buf
            k, buf = k + 1, []
    if buf:
        yield k, buf


# ---------- embedding ----------

class Embedder:
    """İş parçacığı başına bir istemci (requests.Session paylaşılmaz). Toplam istatistik kilitle toplanır."""

    def __init__(self, spec: dict[str, Any], device: str) -> None:
        self.spec, self.device = spec, device
        self.local = threading.local()
        self.lock = threading.Lock()
        self.stats = {"requests": 0, "prompt_tokens": 0, "cost_usd": 0.0, "network_s": 0.0, "retries": 0,
                      "batch_retries": 0}
        self._st = None

    def _cloud(self):
        if not hasattr(self.local, "e"):
            from pilot.cloud import CloudEmbedder
            self.local.e = CloudEmbedder(self.spec["model"], batch=10 ** 6, cache=None)
        return self.local.e

    def _st_model(self):
        with self.lock:
            if self._st is None:
                from sentence_transformers import SentenceTransformer
                self._st = SentenceTransformer(self.spec["model"], device=self.device)
            return self._st

    def __call__(self, texts: list[str]) -> list[list[float]]:
        if self.spec["provider"] == "local":
            return self._st_model().encode(texts, batch_size=32, normalize_embeddings=True).tolist()
        e = self._cloud()
        before = dict(e.stats)
        vecs = e.embed(texts, use_cache=False)
        with self.lock:
            for k in ("requests", "prompt_tokens", "cost_usd", "network_s", "retries"):
                self.stats[k] += e.stats[k] - before[k]
        return vecs


# ---------- koleksiyon ----------

def schema(dim: int, short_dims: tuple[int, ...], full_on_disk: bool, full_hnsw: bool) -> dict[str, Any]:
    from qdrant_client import models

    from pilot.index import collection_schema
    s = collection_schema(dim, sparse="bm25", short_dims=short_dims, vectors_on_disk=False, quantization="none")
    if short_dims:
        # Tam vektör yalnız kısa vektörün adaylarını yeniden skorlar: graf gerekmez (1M × 4096'da saatler ve GB'lar)
        s["vectors_config"]["dense"] = models.VectorParams(
            size=dim, distance=models.Distance.COSINE, on_disk=full_on_disk or None,
            hnsw_config=None if full_hnsw else models.HnswConfigDiff(m=0))
    s["optimizers_config"] = models.OptimizersConfigDiff(indexing_threshold=0)
    return s


def ensure_collection(qc, name: str, meta: dict[str, Any]) -> None:
    from qdrant_client import models

    from pilot.index import PAYLOAD_INDEXES
    if qc.collection_exists(name):
        return
    qc.create_collection(name, **schema(meta["dim"], tuple(meta["short_dims"]), meta["full_on_disk"], meta["full_hnsw"]))
    for f in PAYLOAD_INDEXES + ("nav",):
        qc.create_payload_index(name, f, field_schema=models.PayloadSchemaType.KEYWORD)
    qc.create_payload_index(name, "kademe", field_schema=models.PayloadSchemaType.INTEGER)


def payload(r: dict[str, Any]) -> dict[str, Any]:
    from pilot.index import with_access
    p = with_access(r) if r["kind"] == "gercek" else {**r, "access": ["all"]}
    p.pop("boxes", None)                            # vurgulama kutuları ölçekte gereksiz yük
    return p


def finalize(qc, name: str) -> None:
    from qdrant_client import models
    qc.update_collection(name, optimizer_config=models.OptimizersConfigDiff(indexing_threshold=INDEXING_THRESHOLD))
    log.info("%s: HNSW kurulumu açıldı (indexing_threshold=%d); durum: python -m bench.scale_index status", name,
             INDEXING_THRESHOLD)


# ---------- indeksleme ----------

def estimate_usd(spec: dict[str, Any], corpus: Path, todo: set[int], size: int, max_kademe: int | None) -> tuple[float, int]:
    from bench.providers import doc_text, prices
    chars = sum(sum(len(doc_text(spec, r)) for r in b) for k, b in batches(corpus, size, max_kademe) if k in todo)
    tokens = int(chars / 3.0)
    price = prices().get(spec["model"], 0.0) if spec["provider"] == "openrouter" else 0.0
    return tokens * price, tokens


def index(corpus: Path, collection: str, key: str, workers: int, size: int, short_dims: tuple[int, ...],
          max_kademe: int | None, yes: bool, device: str, full_on_disk: bool, full_hnsw: bool,
          stop_after: int | None) -> dict[str, Any]:
    from qdrant_client import models

    from bench.providers import doc_text
    from bench.server import server_client
    from pilot.index import point_vectors
    from pilot.sparse import bm25_docs

    spec = spec_for(key)
    if spec["provider"] == "local":
        short_dims = tuple(d for d in short_dims if d in spec.get("mrl", []))     # bge-m3 MRL değil
    done_path, meta_path, stats_path = paths(collection)
    meta = {"corpus": str(corpus), "embed": key, "model": spec["model"], "dim": spec["dim"], "batch": size,
            "short_dims": list(short_dims), "full_on_disk": full_on_disk, "full_hnsw": full_hnsw}
    if meta_path.exists():
        old = json.loads(meta_path.read_text(encoding="utf-8"))
        diff = {k: (old.get(k), v) for k, v in meta.items() if old.get(k) != v}
        if diff:
            raise SystemExit(f"{collection}: önceki koşudan farklı ayar {diff}; aynı ayarla sürdürün ya da "
                             f"koleksiyonu ve {done_path.name} dosyasını silin")
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    done = {int(x) for x in done_path.read_text().split()} if done_path.exists() else set()
    all_ids = {k for k, _ in batches(corpus, size, max_kademe)}
    todo = all_ids - done
    log.info("%s: %d toplu iş (%d parça/iş), %d bitmiş, %d kalan", collection, len(all_ids), size, len(done), len(todo))
    if not todo:
        qc = server_client()
        finalize(qc, collection)
        return {"collection": collection, "status": "tamam"}
    usd, tokens = estimate_usd(spec, corpus, todo, size, max_kademe)
    log.info("tahmin: ~%.1f M token, ~%.2f USD (%s)", tokens / 1e6, usd, spec["model"])
    if usd > COST_LIMIT_USD and not yes:
        raise SystemExit(f"tahmin {usd:.2f} USD > {COST_LIMIT_USD} USD: onay için --yes")

    qc = server_client()
    ensure_collection(qc, collection, meta)
    embed = Embedder(spec, device)
    bm25_lock, done_lock = threading.Lock(), threading.Lock()
    local = threading.local()
    stop = threading.Event()

    def client():
        if not hasattr(local, "qc"):
            local.qc = server_client()
        return local.qc

    def work(k: int, rows: list[dict[str, Any]]) -> int:
        texts = [doc_text(spec, r) for r in rows]
        for attempt in range(BATCH_RETRIES + 1):
            try:
                vecs = embed(texts)
                if len(vecs) != len(rows) or any(v is None or len(v) != spec["dim"] for v in vecs):
                    raise RuntimeError(f"toplu iş {k}: eksik ya da yanlış boyutlu vektör")
                break
            except RuntimeError:
                if attempt == BATCH_RETRIES or stop.is_set():
                    raise
                with embed.lock:
                    embed.stats["batch_retries"] += 1
                time.sleep(2 ** attempt)
        with bm25_lock:
            sparse = bm25_docs([r["embed_text"] for r in rows])
        first = k * size
        client().upsert(collection, wait=True, points=[models.PointStruct(
            id=first + i, vector=point_vectors({"dense": vecs[i], "sparse": sparse[i]}, sparse="bm25",
                                               short_dims=short_dims),
            payload=payload(rows[i])) for i in range(len(rows))])
        with done_lock, done_path.open("a") as f:
            f.write(f"{k}\n")
        return len(rows)

    prev = signal.getsignal(signal.SIGINT)

    def on_sigint(*_):
        log.info("durduruluyor: süren toplu işler bitiyor, kalanlar sonraki koşuda")
        stop.set()
    signal.signal(signal.SIGINT, on_sigint)

    t0, n_done, n_batches, errors = time.time(), 0, 0, []
    pending: set[Future] = set()
    total_todo = len(todo)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        it = ((k, b) for k, b in batches(corpus, size, max_kademe) if k in todo)
        exhausted = False
        while True:
            while not exhausted and not stop.is_set() and len(pending) < workers * 2:
                if stop_after is not None and n_batches + len(pending) >= stop_after:
                    exhausted = True
                    break
                nxt = next(it, None)
                if nxt is None:
                    exhausted = True
                    break
                pending.add(ex.submit(work, *nxt))
            if not pending:
                break
            fin, pending = wait(pending, return_when=FIRST_COMPLETED)
            for fu in fin:
                try:
                    n_done += fu.result()
                    n_batches += 1
                except Exception as e:          # noqa: BLE001 - toplu iş kalır, sonraki koşuda yeniden denenir
                    errors.append(repr(e)[:300])
                    log.error("toplu iş hatası: %s", errors[-1])
                    if len(errors) >= 5:
                        stop.set()
            if n_batches and (n_batches % LOG_EVERY == 0 or not pending):
                el = time.time() - t0
                rate = n_done / max(el, 1e-9)
                left = (total_todo - n_batches) * size / max(rate, 1e-9)
                log.info("%d/%d toplu iş · %.1f parça/sn · kalan ~%.1f dk · %.4f USD · %d yeniden deneme",
                         n_batches, total_todo, rate, left / 60, embed.stats["cost_usd"], embed.stats["retries"])
    signal.signal(signal.SIGINT, prev)
    el = time.time() - t0
    complete = all_ids <= {int(x) for x in done_path.read_text().split()}
    if complete:
        finalize(qc, collection)
    prev_stats = json.loads(stats_path.read_text(encoding="utf-8")) if stats_path.exists() else {"runs": []}
    run = {"started": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t0)), "seconds": round(el, 1),
           "chunks": n_done, "batches": n_batches, "chunks_per_s": round(n_done / max(el, 1e-9), 2),
           "workers": workers, "embed_stats": embed.stats, "errors": errors, "complete": complete}
    prev_stats["runs"].append(run)
    prev_stats["meta"] = meta
    stats_path.write_text(json.dumps(prev_stats, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    log.info("bitti: %d parça, %.1f sn, %.2f parça/sn, %.4f USD, tamam=%s", n_done, el, run["chunks_per_s"],
             embed.stats["cost_usd"], complete)
    return run


# ---------- kademe kopyası ve durum ----------

def copy(source: str, target: str, max_kademe: int, batch: int = 256) -> int:
    """Büyük koleksiyondan küçük kademe: vektörler kopyalanır, yeniden embed yok."""
    from qdrant_client import models

    from bench.server import server_client
    _, meta_path, _ = paths(source)
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    qc = server_client()
    if qc.collection_exists(target):
        qc.delete_collection(target)
    ensure_collection(qc, target, meta)
    flt = models.Filter(must=[models.FieldCondition(key="kademe", range=models.Range(lte=max_kademe))])
    offset, n = None, 0
    while True:
        pts, offset = qc.scroll(source, scroll_filter=flt, limit=batch, offset=offset, with_payload=True,
                                with_vectors=True)
        if pts:
            qc.upsert(target, wait=True, points=[models.PointStruct(id=p.id, vector=p.vector, payload=p.payload)
                                                 for p in pts])
            n += len(pts)
        if offset is None:
            break
    paths(target)[1].write_text(json.dumps({**meta, "copied_from": source, "max_kademe": max_kademe},
                                           ensure_ascii=False, indent=1), encoding="utf-8")
    finalize(qc, target)
    log.info("%s → %s: %d nokta (kademe ≤ %d)", source, target, n, max_kademe)
    return n


def status(collection: str) -> dict[str, Any]:
    from bench.server import server_client
    qc = server_client()
    i = qc.get_collection(collection)
    out = {"collection": collection, "status": str(i.status), "points": i.points_count,
           "indexed_vectors": i.indexed_vectors_count, "segments": i.segments_count}
    done_path = paths(collection)[0]
    if done_path.exists():
        out["done_batches"] = len(done_path.read_text().split())
    print(json.dumps(out, ensure_ascii=False))
    return out


def search_env(collection: str) -> dict[str, str]:
    """Koleksiyonu pipeline aramasıyla (pilot.retrieve) sorgulamak için ortam değişkenleri (bench.measure de bunlarla)."""
    meta = json.loads(paths(collection)[1].read_text(encoding="utf-8"))
    spec = spec_for(meta["embed"])
    env = {"PILOT_COLLECTION": collection, "PILOT_SPARSE": "bm25"}
    if spec["provider"] == "openrouter":
        env |= {"PILOT_EMBED_PROVIDER": "openrouter", "PILOT_EMBED_MODEL": spec["model"],
                "PILOT_EMBED_QUERY_PREFIX": spec.get("query_prefix", "")}
    if meta["short_dims"]:
        env |= {"PILOT_DENSE_MODE": "short_rescore", "PILOT_DENSE_SHORT_DIM": str(meta["short_dims"][0])}
    return env


def probe(collection: str, query: str) -> None:
    """Hızlı kontrol: bir sorgu, ilk 5 sonuç (pipeline'ın arama yolu, sunucu modu)."""
    import os
    os.environ.setdefault("PILOT_QDRANT_URL", "http://127.0.0.1:6333")
    for k, v in search_env(collection).items():
        os.environ.setdefault(k, v)
    from pilot.retrieve import search
    t = time.perf_counter()
    hits = search(query, top_k=5)
    log.info("probe %s (%.2f sn): %s", collection, time.perf_counter() - t, query)
    for h in hits:
        log.info("  %-28s kademe=%-7s %s", h.chunk["chunk_id"], h.chunk.get("kademe"), h.chunk["text"][:70].replace("\n", " "))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    x = sub.add_parser("index")
    x.add_argument("--corpus", default=str(SCALE_DIR / "corpus"))
    x.add_argument("--collection", required=True)
    x.add_argument("--embed", default="qwen3-8b", help="bench/models.json anahtarı")
    x.add_argument("--workers", type=int, default=16)
    x.add_argument("--batch", type=int, default=64)
    x.add_argument("--short-dims", default="256")
    x.add_argument("--max-kademe", type=int)
    x.add_argument("--device", default="cpu", help="local embedding: cpu | cuda")
    x.add_argument("--full-in-ram", action="store_true", help="tam vektör RAM'de (varsayılan: diskte)")
    x.add_argument("--full-hnsw", action="store_true", help="tam vektöre de HNSW (PILOT_DENSE_MODE=full ölçmek için)")
    x.add_argument("--stop-after", type=int, help="bu kadar toplu işten sonra dur (kaldığı yerden devam denemesi)")
    x.add_argument("--yes", action="store_true")
    c = sub.add_parser("copy")
    c.add_argument("--source", required=True)
    c.add_argument("--target", required=True)
    c.add_argument("--max-kademe", type=int, required=True)
    s = sub.add_parser("status")
    s.add_argument("--collection", required=True)
    pr = sub.add_parser("probe")
    pr.add_argument("--collection", required=True)
    pr.add_argument("--query", required=True)
    a = ap.parse_args()
    if a.cmd == "index":
        index(Path(a.corpus), a.collection, a.embed, a.workers, a.batch,
              tuple(int(d) for d in a.short_dims.split(",") if d), a.max_kademe, a.yes, a.device,
              not a.full_in_ram, a.full_hnsw, a.stop_after)
    elif a.cmd == "copy":
        copy(a.source, a.target, a.max_kademe)
    elif a.cmd == "probe":
        probe(a.collection, a.query)
    else:
        status(a.collection)


if __name__ == "__main__":
    main()
