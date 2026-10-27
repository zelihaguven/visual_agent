"""Aşama 3c: kalabalık (eşzamanlı kullanıcı) testi. Kapalı döngü: her sanal kullanıcı sorar, cevabı bekler, düşünür, sorar.

Kullanım (Pilot klasöründe, VM'de; önce bench.scale_bench queries ve limits):
    python -m bench.load_test --collection scale_qwen3_8b --mode qdrant --users 1,5,10,25,50,100 --think 0 \
        --duration 60 --client-cpus 8-15 --label 8cpu-16g
    python -m bench.load_test ... --mode embed --users 1,5,10,25 --think 0        # yalnız bulut embed (hız sınırı, 429)
    python -m bench.load_test ... --mode e2e --think 5                            # embed + Qdrant (pipeline araması)

- İstemci, Qdrant konteynerinin çekirdeklerinin dışına sabitlenir (--client-cpus; os.sched_setaffinity). Kullanıcılar
  --procs sürece dağıtılır (GIL istemciyi darboğaz yapmasın).
- Sorgular: onaylı setler + aday taslak (scale_bench queries; ~190 farklı soru), kullanıcı başına tohumlu rastgele sıra.
  Karışım: %50 marka filtreli, %25 yetki filtreli (["all", "g1"]), %25 filtresiz. Rerank yok (varsayılan yol).
- Ölçülen: kademe başına istek sayısı, saniyede sorgu, p50/p95/p99, hata türleri (429, zaman aşımı, diğer).
  Doyma noktası: p95 < 1 sn ve hata < %1 olan en yüksek kullanıcı sayısı.
- Bulut çağrısı (embed, e2e): istek tavanı --max-requests; tahmini maliyet koşmadan yazılır (sorgu ~40 token).
"""
import argparse
import multiprocessing as mp
import os
import random
import statistics
import time
from typing import Any

from bench.common import meta, write_result
from bench.scale_bench import ACCESS_USER, apply_env, container_stats, load_query_vectors, pct

QUERY_TOKENS = 40


def parse_cpus(spec: str | None) -> set[int] | None:
    if not spec:
        return None
    out: set[int] = set()
    for part in spec.split(","):
        a, _, b = part.partition("-")
        out |= set(range(int(a), int(b or a) + 1))
    return out


def pick_filter(rng: random.Random, q: dict[str, Any]) -> tuple[list[str] | None, list[str] | None]:
    r = rng.random()
    if r < 0.5 and q.get("brand"):
        return [q["brand"]], None
    if r < 0.75:
        return None, ACCESS_USER
    return None, None


def worker(args: tuple[str, str, int, int, float, float, int]) -> list[tuple[float, float, str]]:
    """Bir süreç: users kadar iş parçacığı. Döner: (başlangıç, süre, hata türü ya da "")."""
    import threading
    collection, mode, first_user, users, think, deadline, seed = args
    qs = load_query_vectors(collection)
    from bench.server import server_client
    from pilot.retrieve import _filter, candidates, dense_params, search
    out: list[tuple[float, float, str]] = []
    lock = threading.Lock()
    if mode == "embed":
        from pilot.cloud import CloudEmbedder
        from pilot.config import EMBED_CLOUD_MODEL, EMBED_QUERY_PREFIX

    def user(uid: int) -> None:
        rng = random.Random(f"{seed}:{uid}")
        qc = server_client() if mode == "qdrant" else None
        emb = CloudEmbedder(EMBED_CLOUD_MODEL) if mode == "embed" else None
        local: list[tuple[float, float, str]] = []
        time.sleep(rng.random() * min(think, 1.0))          # başlangıçlar yayılsın
        while time.time() < deadline:
            q = rng.choice(qs)
            brands, access = pick_filter(rng, q)
            t0 = time.time()
            err = ""
            try:
                if mode == "qdrant":
                    candidates(qc, q, _filter(brands, None, access), "hybrid", collection=collection,
                               dparams=dense_params())
                elif mode == "embed":
                    emb.embed([EMBED_QUERY_PREFIX + q["q"]], use_cache=False)
                else:
                    search(q["q"], brands=brands, access=access, top_k=5, do_rerank=False)
            except Exception as e:                       # noqa: BLE001 - hata türü kaydedilir, yük sürer
                s = repr(e)
                err = "429" if "429" in s else ("zaman_asimi" if "imeout" in s else "diger")
            local.append((t0, time.time() - t0, err))
            if think:
                time.sleep(think * rng.uniform(0.5, 1.5))
        with lock:
            out.extend(local)

    ts = [threading.Thread(target=user, args=(first_user + i,)) for i in range(users)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    return out


def level(collection: str, mode: str, users: int, think: float, duration: float, procs: int, seed: int) -> dict[str, Any]:
    procs = max(1, min(procs, users))
    split = [users // procs + (1 if i < users % procs else 0) for i in range(procs)]
    deadline = time.time() + duration
    firsts = [sum(split[:i]) for i in range(procs)]
    with mp.get_context("fork" if hasattr(os, "fork") else "spawn").Pool(procs) as pool:
        parts = pool.map(worker, [(collection, mode, f, u, think, deadline, seed) for f, u in zip(firsts, split)])
    rows = [r for p in parts for r in p]
    ok = [d for _, d, e in rows if not e]
    errs: dict[str, int] = {}
    for _, _, e in rows:
        if e:
            errs[e] = errs.get(e, 0) + 1
    span = (max(t + d for t, d, _ in rows) - min(t for t, _, _ in rows)) if rows else duration
    res = {"users": users, "think_s": think, "requests": len(rows), "qps": len(ok) / max(span, 1e-9),
           "errors": errs, "error_rate": (len(rows) - len(ok)) / max(len(rows), 1),
           "p50": statistics.median(ok) if ok else None, "p95": pct(ok, 95) if ok else None,
           "p99": pct(ok, 99) if ok else None}
    print(f"{users:4d} kullanıcı · {res['qps']:.1f} sorgu/sn · p50 {res['p50'] or 0:.3f} p95 {res['p95'] or 0:.3f} "
          f"p99 {res['p99'] or 0:.3f} sn · hata {res['error_rate']:.1%} {errs}", flush=True)
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--collection", required=True)
    ap.add_argument("--mode", choices=["qdrant", "embed", "e2e"], default="qdrant")
    ap.add_argument("--users", default="1,5,10,25,50,100")
    ap.add_argument("--think", type=float, default=0.0)
    ap.add_argument("--duration", type=float, default=60)
    ap.add_argument("--procs", type=int, default=8)
    ap.add_argument("--client-cpus", help="ör. 8-15 (Qdrant'ın cpuset'i dışında)")
    ap.add_argument("--label", required=True)
    ap.add_argument("--max-requests", type=int, default=60_000)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    apply_env(a.collection)
    cpus = parse_cpus(a.client_cpus)
    if cpus and hasattr(os, "sched_setaffinity"):
        os.sched_setaffinity(0, cpus)
    levels = [int(x) for x in a.users.split(",")]
    if a.mode != "qdrant":
        per_user = a.duration / max(a.think + 0.3, 0.3)          # en hızlı ihtimal: 0,3 sn cevap
        est = int(sum(levels) * per_user)
        print(f"bulut isteği tavanı ~{est} (sınır {a.max_requests}), ~{est * QUERY_TOKENS / 1e6:.2f} M token")
        if est > a.max_requests:
            raise SystemExit("istek tahmini sınırı aşıyor: --users, --duration ya da --max-requests")
    res = [level(a.collection, a.mode, u, a.think, a.duration, a.procs, a.seed) for u in levels]
    good = [r["users"] for r in res if r["p95"] is not None and r["p95"] < 1.0 and r["error_rate"] < 0.01]
    data = {"meta": meta({"collection": a.collection, "mode": a.mode, "think_s": a.think, "duration_s": a.duration,
                          "procs": a.procs, "client_cpus": a.client_cpus, "label": a.label,
                          "filter_mix": "50% marka, 25% yetki, 25% filtresiz"}),
            "levels": res, "saturation_users": max(good) if good else None, "resources": container_stats(a.collection)}
    lines = [f"# Aşama 3c yük: {a.collection} · {a.mode} · {a.label}", "",
             f"Kapalı döngü, düşünme süresi {a.think} sn (±%50), kademe {a.duration:.0f} sn, istemci çekirdekleri "
             f"{a.client_cpus or 'hepsi'}, {a.procs} süreç. Karışım: %50 marka, %25 yetki, %25 filtresiz. "
             f"Kaynak: {data['resources']}", "",
             "| Kullanıcı | istek | sorgu/sn | p50 | p95 | p99 | hata |", "|---|---|---|---|---|---|---|"]
    for r in res:
        f = (lambda v: "–" if v is None else f"{v * 1000:.0f} ms")
        lines.append(f"| {r['users']} | {r['requests']} | {r['qps']:.1f} | {f(r['p50'])} | {f(r['p95'])} | {f(r['p99'])} | "
                     f"{r['error_rate']:.1%} {r['errors'] or ''} |")
    lines += ["", f"Doyma noktası (p95 < 1 sn, hata < %1): **{data['saturation_users'] or '–'} kullanıcı**"]
    print(write_result(f"asama3_yuk_{a.collection}_{a.mode}_{a.label}", data, "\n".join(lines) + "\n"))


if __name__ == "__main__":
    main()
