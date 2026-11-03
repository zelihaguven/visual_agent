"""Aşama 4: local ve bulut embedding karşılaştırması. Adaylar bench/models.json'da (model adı koda gömülmez).

Kullanım (Pilot klasöründe; Qdrant sunucusu açık; bulut için OPENROUTER_API_KEY):
    python -m bench.providers estimate                        # maliyet tablosu (istek göndermez; fiyatlar /models'ten)
    python -m bench.providers build --key qwen3-8b [--yes]    # koleksiyon emb_<key>: dense + MRL kısa + BM25
    python -m bench.providers collect --key qwen3-8b --dense full|short|short_rescore [--short-dim 256]
    python -m bench.rerank_bench compare --candidates data/bench_cache/candidates_qwen3-8b_full.json --configs ...

- Doküman vektörleri önbellekte (data/bench_cache/embed_cache.sqlite): aynı metin iki kez gönderilmez. Bulut
  koleksiyonu tam boyutla bir kez gömülür; MRL kısa vektörler ondan türetilir (baş + normalize), ek maliyet yok.
- Sorgu: süre turlarında bulut çağrısı gerçek (önbelleksiz, ağ dahil); doğruluk ilk turdan.
- Koşmadan önce maliyet tahmini yazılır; 5 USD'yi aşarsa --yes olmadan koşmaz (kural 5). ZDR zorunlu (pilot/cloud.py).
"""
import argparse
import json
import logging
import time
import warnings
from pathlib import Path
from typing import Any

from bench.common import (KNOWN_SETS, PILOT_DIR, StageTimer, accuracy, first_rank, fmt_pct, fmt_s, load_questions,
                          meta, prepare, write_result)

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("providers")

MODELS_PATH = Path(__file__).with_name("models.json")
CACHE_DIR = PILOT_DIR / "data" / "bench_cache"
COST_LIMIT_USD = 5.0
CHARS_PER_TOKEN = 3.0          # tutucu tahmin (İngilizce ~4; kod/sayı/Türkçe daha az)
QUERY_TOKENS = 40              # önek dahil ortalama sorgu
RERANK_TOKENS_PER_QUERY = 20 * 220


def specs() -> dict[str, dict[str, Any]]:
    return {m["key"]: m for m in json.loads(MODELS_PATH.read_text(encoding="utf-8"))["embeddings"]}


def collection_name(key: str) -> str:
    return "manuals" if key == "bge-m3-local" else f"emb_{key}"


def doc_text(spec: dict[str, Any], chunk: dict[str, Any]) -> str:
    t = chunk["embed_text"]
    if spec.get("max_chars"):
        t = t[:spec["max_chars"]]
    return spec.get("doc_prefix", "") + t


# ---------- maliyet ----------

def prices() -> dict[str, float]:
    """Model → USD/token (sağlayıcılar arasında en düşük; ZDR uyumlu uç noktalardan)."""
    from pilot.cloud import _fetch_zdr_endpoints
    out: dict[str, float] = {}
    for e in _fetch_zdr_endpoints():
        p = float((e.get("pricing") or {}).get("prompt") or 0)
        mid = e.get("model_id")
        if mid and p and (mid not in out or p < out[mid]):
            out[mid] = p
    return out


def estimate(keys: list[str] | None = None) -> dict[str, Any]:
    from pilot.chunk import read_chunks
    chunks = read_chunks()
    pr = prices()
    measured = json.loads(MODELS_PATH.read_text(encoding="utf-8")).get("rerank_usd_per_mtok_measured", {})
    rerank_price = pr.get("qwen/qwen3-reranker-8b") or measured.get("qwen/qwen3-reranker-8b", 0.0) / 1e6
    rows = {}
    for key, s in specs().items():
        if keys and key not in keys:
            continue
        chars = sum(len(doc_text(s, c)) for c in chunks)
        tokens = chars / CHARS_PER_TOKEN
        price = pr.get(s["model"], 0.0) if s["provider"] == "openrouter" else 0.0
        rows[key] = {"provider": s["provider"], "model": s["model"], "chunks": len(chunks), "tokens_est": int(tokens),
                     "usd_per_mtok": price * 1e6, "index_usd": tokens * price,
                     "index_1m_usd": tokens * price * 1_000_000 / len(chunks),
                     "query_1k_usd": QUERY_TOKENS * 1000 * price}
    total = sum(r["index_usd"] for r in rows.values())
    return {"rows": rows, "total_index_usd": total, "rerank_usd_per_mtok": rerank_price * 1e6,
            "rerank_1k_queries_usd": RERANK_TOKENS_PER_QUERY * 1000 * rerank_price}


def print_estimate(est: dict[str, Any]) -> None:
    print(f"{'model':14} {'token':>9} {'$/Mtok':>7} {'bu korpus':>10} {'1M parça':>9} {'1k soru':>8}")
    for k, r in est["rows"].items():
        print(f"{k:14} {r['tokens_est']:9d} {r['usd_per_mtok']:7.3f} {r['index_usd']:10.4f} {r['index_1m_usd']:9.2f} "
              f"{r['query_1k_usd']:8.4f}")
    print(f"toplam indeksleme (bu korpus): {est['total_index_usd']:.4f} USD · bulut rerank: "
          f"{est['rerank_usd_per_mtok']:.3f} $/Mtok, 1.000 soru ≈ {est['rerank_1k_queries_usd']:.2f} USD")


# ---------- koleksiyon ----------

def doc_vectors(spec: dict[str, Any], chunks: list[dict[str, Any]]) -> tuple[list[list[float]], dict[str, Any]]:
    texts = [doc_text(spec, c) for c in chunks]
    if spec["provider"] == "openrouter":
        from pilot.cloud import CloudEmbedder, EmbedCache
        e = CloudEmbedder(spec["model"], cache=EmbedCache(), batch=spec.get("batch", 64))
        t = time.time()
        vecs = e.embed(texts)
        return vecs, {**e.stats, "seconds": round(time.time() - t, 1), "chunks_per_s": len(texts) / max(time.time() - t, 1e-9)}
    if spec["key"] == "bge-m3-local":
        raise ValueError("bge-m3-local: mevcut 'manuals' koleksiyonu kullanılır (bench.server copy)")
    if spec.get("reuse_vectors_from"):
        return reuse_vectors(spec["reuse_vectors_from"], chunks), {"reused_from": spec["reuse_vectors_from"]}
    t = time.time()
    vecs = local_model(spec).encode(texts, batch_size=8, normalize_embeddings=True, show_progress_bar=True).tolist()
    return vecs, {"seconds": round(time.time() - t, 1), "chunks_per_s": len(texts) / (time.time() - t)}


def reuse_vectors(collection: str, chunks: list[dict[str, Any]]) -> list[list[float]]:
    """Sunucudaki bir koleksiyonun dense vektörleri, chunk_id ile eşlenerek (yeniden embed yok)."""
    from bench.server import server_client
    qc = server_client()
    got, offset = {}, None
    while True:
        pts, offset = qc.scroll(collection, limit=1000, offset=offset, with_vectors=["dense"],
                                with_payload=["chunk_id"])
        got.update({p.payload["chunk_id"]: p.vector["dense"] for p in pts})
        if offset is None:
            break
    qc.close()
    return [got[c["chunk_id"]] for c in chunks]


_LOCAL: dict[str, Any] = {}


def _compat_extended_attention_mask(model: Any) -> None:
    """Nomic v2'nin uzak kodu transformers 5'te kaldırılan get_extended_attention_mask'i çağırıyor; aynısı eklenir
    (dolgu konumlarına dtype'ın en küçük değeri)."""
    import torch
    for m in model.modules():
        cls = type(m)
        if cls.__name__.startswith("Nomic") and not hasattr(cls, "get_extended_attention_mask"):
            def get_extended_attention_mask(self, attention_mask, input_shape, dtype=None):
                dtype = dtype or next(self.parameters()).dtype
                ext = attention_mask[:, None, None, :].to(dtype)
                return (1.0 - ext) * torch.finfo(dtype).min
            cls.get_extended_attention_mask = get_extended_attention_mask


def local_model(spec: dict[str, Any]):
    if spec["model"] not in _LOCAL:
        from sentence_transformers import SentenceTransformer
        m = SentenceTransformer(spec["model"], trust_remote_code=True, device="cpu")
        _compat_extended_attention_mask(m)
        _LOCAL[spec["model"]] = m
    return _LOCAL[spec["model"]]


def build(key: str, yes: bool) -> dict[str, Any]:
    from qdrant_client import models

    from bench.server import server_client
    from pilot.chunk import read_chunks
    from pilot.index import PAYLOAD_INDEXES, collection_schema, point_vectors, with_access
    from pilot.sparse import bm25_docs

    spec = specs()[key]
    est = estimate([key])
    print_estimate(est)
    if est["total_index_usd"] > COST_LIMIT_USD and not yes:
        raise SystemExit(f"tahmin {est['total_index_usd']:.2f} USD > {COST_LIMIT_USD} USD: onay için --yes")
    chunks = read_chunks()
    vecs, stats = doc_vectors(spec, chunks)
    log.info("%s: %d vektör (%s)", key, len(vecs), {k: (round(v, 4) if isinstance(v, float) else v) for k, v in stats.items()})
    t = time.time()
    sparse = bm25_docs([c["embed_text"] for c in chunks])
    bm25_s = time.time() - t
    short = tuple(spec.get("mrl", []))
    qc = server_client()
    name = collection_name(key)
    if qc.collection_exists(name):
        qc.delete_collection(name)
    qc.create_collection(name, **collection_schema(len(vecs[0]), sparse="bm25", short_dims=short))
    for f in PAYLOAD_INDEXES + ("nav",):
        qc.create_payload_index(name, f, field_schema=models.PayloadSchemaType.KEYWORD)
    for i in range(0, len(chunks), 128):
        qc.upsert(name, points=[models.PointStruct(
            id=j, vector=point_vectors({"dense": vecs[j], "sparse": sparse[j]}, sparse="bm25", short_dims=short),
            payload=with_access(chunks[j])) for j in range(i, min(i + 128, len(chunks)))])
    qc.close()
    out_path = CACHE_DIR / f"build_{key}.json"
    if stats.get("requests") == 0 and stats.get("cached") and out_path.exists():
        # Önbellekten yeniden kurulum: ölçülen maliyet ve hız ilk kurulumdan korunur
        stats = {**json.loads(out_path.read_text(encoding="utf-8"))["embed_stats"], "rebuilt_from_cache": True}
    res = {"key": key, "collection": name, "dim": len(vecs[0]), "short_dims": short, "embed_stats": stats,
           "bm25_seconds": round(bm25_s, 1), "estimate": est["rows"][key]}
    out_path.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=float),
                                                 encoding="utf-8")
    log.info("kuruldu: %s", name)
    return res


# ---------- aday toplama ----------

class QueryEncoder:
    """Sorgu vektörleri modele göre. last: son çağrının ağ süresi (bulut)."""

    def __init__(self, spec: dict[str, Any], short_dim: int) -> None:
        self.spec, self.short_dim = spec, short_dim
        self.cloud = None
        if spec["provider"] == "openrouter":
            from pilot.cloud import CloudEmbedder, EmbedCache
            self.cloud = CloudEmbedder(spec["model"], cache=EmbedCache())

    def __call__(self, text: str, use_cache: bool) -> dict[str, Any]:
        from pilot.embed import embed, short_vector
        from pilot.sparse import bm25_query
        q = self.spec.get("query_prefix", "") + text
        if self.spec["provider"] == "local" and self.spec["model"] == "BAAI/bge-m3":
            v = embed([text])[0]
            out = {"dense": v["dense"], "sparse": v["sparse"] if self.spec["sparse"] == "bge-m3" else bm25_query(text)}
        elif self.cloud:
            out = {"dense": self.cloud.embed([q], use_cache=use_cache)[0], "sparse": bm25_query(text)}
        else:
            out = {"dense": local_model(self.spec).encode([q], normalize_embeddings=True)[0].tolist(),
                   "sparse": bm25_query(text)}
        out["short"] = short_vector(out["dense"], self.short_dim)
        return out


def collect(key: str, dense_mode: str, short_dim: int, repeats: int, timing_sets: list[str]) -> Path:
    from bench.server import server_client
    from pilot import retrieve

    spec = specs()[key]
    enc = QueryEncoder(spec, short_dim)
    sparse_name = "sparse" if spec["sparse"] == "bge-m3" else "bm25"
    qc = server_client()
    items = [(it, prepare(it["q"])) for it in load_questions(KNOWN_SETS)]
    items = [(it, p) for it, p in items if not p["skip"] and not it.get("expect_clarify")]
    out: dict[str, Any] = {"questions": {}, "timing": {}}

    def run(it, p, scope, use_cache):
        t0 = time.perf_counter()
        q = enc(p["search_q"], use_cache)
        t1 = time.perf_counter()
        pts = retrieve.candidates(qc, q, retrieve._filter(None, scope), "hybrid", collection=collection_name(key),
                                  sparse_name=sparse_name, dense_mode=dense_mode, short_dim=short_dim)
        t2 = time.perf_counter()
        return pts, {"embed": t1 - t0, "qdrant": t2 - t1, "total": t2 - t0,
                     "network": enc.cloud.last_network_s if enc.cloud else 0.0}

    for it, p in items[:3]:                      # ısınma (bağlantı, model yükleme)
        run(it, p, p["doc_ids"], False)
    for mode in ("filtered", "unfiltered"):
        timer = StageTimer()
        for r in range(repeats if mode == "filtered" else 1):
            for it, p in items:
                timed = mode == "filtered" and it["set"] in timing_sets
                if r > 0 and not timed:
                    continue
                scope = p["doc_ids"] if mode == "filtered" else None
                pts, t = run(it, p, scope, use_cache=not timed)
                if timed:
                    timer.record(t)
                if r == 0:
                    qd = out["questions"].setdefault(it["qid"], {
                        "qid": it["qid"], "set": it["set"], "q": it["q"], "search_q": p["search_q"],
                        "not_found": bool(it.get("expect_not_found")),
                        "expect_docs": it.get("expect_docs", []), "expect_pages": it.get("expect_pages", [])})
                    qd[mode] = [{"chunk_id": x.payload["chunk_id"], "doc_id": x.payload["doc_id"],
                                 "pages": x.payload["pages"], "chunk_type": x.payload.get("chunk_type"),
                                 "text": x.payload["text"]} for x in pts]
            log.info("%s tur %d bitti", mode, r + 1)
        out["timing"][mode] = timer.summary()
    qc.close()
    out["params"] = {"key": key, "model": spec["model"], "provider": spec["provider"], "dense_mode": dense_mode,
                     "short_dim": short_dim if dense_mode != "full" else None, "collection": collection_name(key),
                     "FUSED_K": retrieve.FUSED_K, "PREFETCH_K": retrieve.PREFETCH_K, "repeats": repeats,
                     "timing_sets": timing_sets, "cloud_stats": enc.cloud.stats if enc.cloud else None}
    tag = f"{key}_{dense_mode}" + (f"{short_dim}" if dense_mode != "full" else "")
    path = CACHE_DIR / f"candidates_{tag}.json"
    path.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    log.info("yazıldı: %s", path)
    return path


def candidates_accuracy(path: Path) -> dict[str, Any]:
    """Rerank'sız doğruluk (RRF sırası, ilk 20) ve aday aşaması süresi."""
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    items = {it["qid"]: it for it in load_questions(KNOWN_SETS)}
    res = {"params": d["params"], "timing": d["timing"]}
    for mode in ("filtered", "unfiltered"):
        ranks = [first_rank(q[mode], items[q["qid"]]) for q in d["questions"].values() if not q["not_found"]]
        res[mode] = accuracy(ranks)
    return res


def summary(paths: list[str], name: str) -> None:
    rows = [candidates_accuracy(Path(p)) for p in paths]
    lines = ["# Embedding karşılaştırması (rerank'sız, RRF sırası)", "",
             "Süre: sorgu embed (bulutta ağ dahil) + Qdrant (sunucu modu), `questions` seti, ısınma hariç. "
             "Doğruluk: bilinen 36 soru.", "",
             "| Model | dense | filtreli hit@1 | hit@5 | hit@20 | MRR | filtresiz hit@5 | MRR | embed p50 | p95 | "
             "Qdrant p50 | toplam p50 | p95 |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        p, f, u, t = r["params"], r["filtered"], r["unfiltered"], r["timing"]["filtered"]
        dm = p["dense_mode"] + (f" {p['short_dim']}" if p.get("short_dim") else "")
        lines.append(f"| {p['key']} | {dm} | {fmt_pct(f['hit@1'])} | {fmt_pct(f['hit@5'])} | {fmt_pct(f['hit@20'])} | "
                     f"{fmt_pct(f['mrr'])} | {fmt_pct(u['hit@5'])} | {fmt_pct(u['mrr'])} | {fmt_s(t['embed']['p50'])} | "
                     f"{fmt_s(t['embed']['p95'])} | {fmt_s(t['qdrant']['p50'])} | {fmt_s(t['total']['p50'])} | "
                     f"{fmt_s(t['total']['p95'])} |")
    data = {"meta": meta({"paths": paths}), "rows": rows}
    print(write_result(name, data, "\n".join(lines) + "\n"))
    print("\n".join(lines[4:]))


def costs(name: str) -> None:
    """Ölçülen kurulum kayıtlarından (build_<key>.json) maliyet ve hız tablosu; 1M parça ve 1.000 soru projeksiyonu."""
    measured = json.loads(MODELS_PATH.read_text(encoding="utf-8")).get("rerank_usd_per_mtok_measured", {})
    rerank_mtok = measured.get("qwen/qwen3-reranker-8b", 0.0)
    rows = []
    for f in sorted(CACHE_DIR.glob("build_*.json")):
        b = json.loads(f.read_text(encoding="utf-8"))
        st, est = b["embed_stats"], b["estimate"]
        n = est["chunks"]
        tok = st.get("prompt_tokens") or 0
        cost = st.get("cost_usd") or (tok * est["usd_per_mtok"] / 1e6)
        cps = st.get("chunks_per_s")
        rows.append({"key": b["key"], "dim": b["dim"], "tokens": tok, "tokens_per_chunk": tok / n if tok else None,
                     "cost_usd": cost, "chunks_per_s": cps, "index_1m_usd": cost * 1e6 / n,
                     "index_1m_hours": (1e6 / cps / 3600) if cps else None,
                     "query_1k_usd": QUERY_TOKENS * 1000 * est["usd_per_mtok"] / 1e6,
                     "reused": bool(st.get("reused_from")) or not tok and st.get("cached")})
    lines = ["# Aşama 4: embedding maliyeti ve indeksleme hızı (ölçülen)", "",
             "Kurulum kayıtlarından (data/bench_cache/build_*.json). Hız: geliştirme dizüstünden (bulut: ağ dahil, 64'lük "
             "toplu istek, tek iş parçacığı; local: CPU). 1M projeksiyonu doğrusal; paralel istekle bulut hızı artar.",
             f"Bulut rerank (qwen3-reranker-8b): {rerank_mtok} USD/Mtok; 20 aday ≈ {RERANK_TOKENS_PER_QUERY} token → "
             f"1.000 soru ≈ {RERANK_TOKENS_PER_QUERY * 1000 * rerank_mtok / 1e6:.2f} USD.", "",
             "| Model | boyut | token/parça | bu korpus USD | parça/sn | 1M parça USD | 1M parça süre (saat) | 1.000 soru embed USD |",
             "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        tpc = f"{r['tokens_per_chunk']:.0f}" if r["tokens_per_chunk"] else "–"
        cps = f"{r['chunks_per_s']:.1f}" if r["chunks_per_s"] and r["chunks_per_s"] < 1000 else "–"
        hrs = f"{r['index_1m_hours']:.1f}" if r["index_1m_hours"] and r["chunks_per_s"] < 1000 else "–"
        lines.append(f"| {r['key']} | {r['dim']} | {tpc} | {r['cost_usd']:.4f} | {cps} | {r['index_1m_usd']:.2f} | {hrs} | "
                     f"{r['query_1k_usd']:.4f} |")
    lines += ["", "Local bge-m3 (bugünkü indeks): CPU'da ~1,5 parça/sn (Aşama 2.5 yeniden indeksleme) → 1M parça ≈ 185 saat."]
    print(write_result(name, {"meta": meta({}), "rows": rows}, "\n".join(lines) + "\n"))
    print("\n".join(lines))


def matrix(name: str) -> None:
    """Embedding × reranker tablosu (eval/bench/b4/asama4_rerank_*.json): doğruluk, rerank süresi, uçtan uca süre."""
    rows = []
    emb = {r["params"]["key"] + "_" + r["params"]["dense_mode"]: r for r in
           (candidates_accuracy(p) for p in CACHE_DIR.glob("candidates_*_full.json"))}
    for f in sorted(OUT_DIR_GLOB()):
        d = json.loads(f.read_text(encoding="utf-8"))
        key = f.stem.replace("asama4_rerank_", "").rsplit("_", 1)[0]
        e = emb.get(key)
        cand_s = e["timing"]["filtered"]["total"]["p50"] if e else float("nan")
        for mode in ("filtered", "unfiltered"):
            nr = d["no_rerank"][mode]
            rows.append({"emb": key, "mode": mode, "rerank": "yok", **{k: nr[k] for k in ("hit@1", "hit@5", "mrr")},
                         "rerank_p50": 0.0, "total_p50": cand_s})
            for c in d["meta"]["params"]["configs"]:
                sm = d["configs"][c["spec"]][mode]["summary"]
                a = sm["accuracy"]["K20"]
                rows.append({"emb": key, "mode": mode, "rerank": c["spec"].split(":")[1].split("/")[-1] +
                             (" int8" if "int8" in c["spec"] else ""), **{k: a[k] for k in ("hit@1", "hit@5", "mrr")},
                             "rerank_p50": sm["time"]["p50"], "total_p50": cand_s + sm["time"]["p50"],
                             "cost_usd_39": sm.get("cost_usd_total")})
    lines = ["# Aşama 4: embedding × reranker", "",
             "Aynı aday listesi (RRF ilk 20) üzerinde rerank. Süre p50: aday aşaması (sorgu embed + Qdrant, `questions` "
             "seti) + rerank. Geliştirme dizüstü, bulut çağrıları bu makinenin bağlantısından: üretimi temsil etmez. "
             "36 soru: 5–8 puanın altındaki farklar gürültü.", ""]
    for mode, title in (("filtered", "Filtreli (pipeline: doküman filtresi)"), ("unfiltered", "Filtresiz (bütün koleksiyon)")):
        lines += [f"## {title}", "", "| Embedding | Reranker | hit@1 | hit@5 | MRR | rerank p50 | toplam p50 |",
                  "|---|---|---|---|---|---|---|"]
        for r in rows:
            if r["mode"] == mode:
                lines.append(f"| {r['emb']} | {r['rerank']} | {fmt_pct(r['hit@1'])} | {fmt_pct(r['hit@5'])} | "
                             f"{fmt_pct(r['mrr'])} | {fmt_s(r['rerank_p50']) if r['rerank_p50'] else '–'} | "
                             f"{fmt_s(r['total_p50'])} |")
        lines.append("")
    print(write_result(name, {"meta": meta({}), "rows": rows}, "\n".join(lines)))
    print("\n".join(lines))


def OUT_DIR_GLOB():
    from bench.common import stage_dir
    return stage_dir("asama4_rerank").glob("asama4_rerank_*.json")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("estimate")
    e.add_argument("--keys", nargs="*")
    b = sub.add_parser("build")
    b.add_argument("--key", required=True)
    b.add_argument("--yes", action="store_true")
    c = sub.add_parser("collect")
    c.add_argument("--key", required=True)
    c.add_argument("--dense", default="full", choices=["full", "short", "short_rescore"])
    c.add_argument("--short-dim", type=int, default=256)
    c.add_argument("--repeats", type=int, default=3)
    c.add_argument("--timing-sets", nargs="+", default=["questions"])
    sub.add_parser("matrix")
    k = sub.add_parser("costs")
    k.add_argument("--name", default="asama4_maliyet")
    s = sub.add_parser("summary")
    s.add_argument("--name", default="asama4_embedding")
    s.add_argument("paths", nargs="+")
    a = ap.parse_args()
    if a.cmd == "estimate":
        print_estimate(estimate(a.keys))
    elif a.cmd == "build":
        build(a.key, a.yes)
    elif a.cmd == "matrix":
        matrix("asama4_matris")
    elif a.cmd == "costs":
        costs(a.name)
    elif a.cmd == "collect":
        collect(a.key, a.dense, a.short_dim, a.repeats, a.timing_sets)
    else:
        summary(a.paths, a.name)


if __name__ == "__main__":
    main()
