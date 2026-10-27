"""Aşama 3 süre ölçümleri: Qdrant konteynerine kaynak sınırı, hazır sorgu vektörleriyle gecikme, ANN recall, bellek.

Kullanım (Pilot klasöründe):
    python -m bench.scale_bench queries --collection scale_qwen3_8b                 # sorgu vektörleri (yerelde de olur)
    python -m bench.scale_bench limits --cpus 8 --memory 16g                        # VM: Qdrant çekirdek 0..7, 16 GB
    python -m bench.scale_bench limits --none                                       # sınırsız (indeksleme)
    python -m bench.scale_bench latency --collection scale_qwen3_8b --label 8cpu-16g [--repeats 5]
    python -m bench.scale_bench stats --collection scale_qwen3_8b
    python -m bench.scale_bench wait                                                # Qdrant hazır olana kadar bekle

- Sınır (limits): docker update --cpuset-cpus 0..n-1 --cpus n --memory M --memory-swap M, sonra konteyner yeniden
  başlatılır ve sayfa önbelleği boşaltılır (soğuk başlangıç; ölçüm ısınma turuyla başlar). cgroup v2'de dosya sayfa
  önbelleği de konteynerin bellek sınırına sayılır: 16 GB'ı aşan vektör dosyaları önbellekte tutulamaz, diskten okunur.
  Yük üreten istemci (bench.load_test) sınırın dışındaki çekirdeklerde çalışır.
- Gecikme (latency): yalnız Qdrant (sorgu vektörü önceden hesaplı; bulut embed ağı girmez). Dört biçim: filtresiz hibrit,
  marka filtreli hibrit, yetki filtreli hibrit (["all", "g1"]), yalnız dense. Arama pipeline'ınki (retrieve.candidates).
- limits yalnız docker içindir (VM). Docker'sız şirket içi sunucuda sınırı systemd verir (bench/onprem/asama3_sunucu.sh:
  systemd-run -p AllowedCPUs -p CPUQuota -p MemoryMax); kaynak ölçümü resource_stats ikisini de okur.
- Docker komutları sudo'suz çağrılır (kök kullanıcı).
"""
import argparse
import json
import os
import random
import statistics
import subprocess
import time
from pathlib import Path
from typing import Any

from bench.common import PILOT_DIR, load_questions, meta, write_result, KNOWN_SETS
from bench.scale_corpus import SCALE_DIR

CONTAINER = os.environ.get("PILOT_QDRANT_CONTAINER", "visual-agent-qdrant")
MODES = ("hibrit", "hibrit_marka", "hibrit_yetki", "dense")
ACCESS_USER = ["all", "g1"]                 # yapay yetki: herkese açık + bir grup


def apply_env(collection: str) -> None:
    """Koleksiyonun arama ayarları (bench.scale_index.search_env) pilot içe aktarılmadan önce ortama yazılır."""
    from bench.scale_index import search_env
    for k, v in search_env(collection).items():
        os.environ[k] = v
    os.environ.setdefault("PILOT_QDRANT_URL", "http://127.0.0.1:6333")


# ---------- konteyner ----------

def sh(*args: str, check: bool = True) -> str:
    return subprocess.run(args, capture_output=True, text=True, check=check).stdout.strip()


def wait_ready(url: str = "http://127.0.0.1:6333", timeout: float = 300) -> None:
    import requests
    t = time.time()
    while time.time() - t < timeout:
        try:
            if requests.get(f"{url}/readyz", timeout=2).ok:
                return
        except requests.RequestException:
            pass
        time.sleep(2)
    raise RuntimeError("Qdrant hazır değil")


def limits(cpus: int | None, memory: str | None) -> dict[str, Any]:
    if cpus:
        sh("docker", "update", f"--cpuset-cpus=0-{cpus - 1}", f"--cpus={cpus}", f"--memory={memory}",
           f"--memory-swap={memory}", CONTAINER)
    else:
        n = os.cpu_count() or 1
        sh("docker", "update", f"--cpuset-cpus=0-{n - 1}", "--cpus=0", "--memory=0", "--memory-swap=-1", CONTAINER)
    sh("docker", "restart", CONTAINER)
    sh("sh", "-c", "sync; echo 3 > /proc/sys/vm/drop_caches", check=False)
    wait_ready()
    got = json.loads(sh("docker", "inspect", CONTAINER))[0]["HostConfig"]
    out = {"cpuset": got.get("CpusetCpus"), "nano_cpus": got.get("NanoCpus"), "memory": got.get("Memory")}
    print(json.dumps(out))
    return out


def container_stats(collection: str | None = None) -> dict[str, Any]:
    """Konteynerin RAM'i (sayfa önbelleği dahil, cgroup) ve koleksiyon diski. Docker yoksa boş."""
    try:
        st = json.loads(sh("docker", "stats", "--no-stream", "--format", "{{json .}}", CONTAINER))
        mount = sh("docker", "inspect", "-f",
                   '{{range .Mounts}}{{if eq .Destination "/qdrant/storage"}}{{.Source}}{{end}}{{end}}', CONTAINER)
        host = json.loads(sh("docker", "inspect", CONTAINER))[0]["HostConfig"]
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
        return {}
    out = {"mode": "docker", "mem_usage": st.get("MemUsage"), "cpu": st.get("CPUPerc"),
           "limit_cpuset": host.get("CpusetCpus"), "limit_memory_gb": round((host.get("Memory") or 0) / 2**30, 1)}
    if collection and mount:
        path = Path(mount) / "collections" / collection
        out["collection_disk_gb"] = round(int(sh("du", "-sb", str(path)).split()[0]) / 2**30, 2) if path.exists() else None
    if collection:
        from bench.server import server_client
        i = server_client().get_collection(collection)
        out.update(points=i.points_count, segments=i.segments_count, status=str(i.status))
    return out


def systemd_stats(collection: str | None = None) -> dict[str, Any]:
    """systemd birimi altında çalışan Qdrant (şirket içi sunucu, bench/onprem): cgroup belleği (sayfa önbelleği dahil),
    sınırlar ve koleksiyon diski. PILOT_QDRANT_UNIT birimin adı; PILOT_QDRANT_UNIT_USER=1 ise kullanıcı birimi."""
    unit = os.environ["PILOT_QDRANT_UNIT"]
    cmd = ["systemctl"] + (["--user"] if os.environ.get("PILOT_QDRANT_UNIT_USER") == "1" else []) + [
        "show", unit, "-p", "MemoryCurrent", "-p", "MemoryMax", "-p", "AllowedCPUs", "-p", "CPUQuotaPerSecUSec"]
    try:
        kv = dict(line.split("=", 1) for line in sh(*cmd).splitlines() if "=" in line)
    except (OSError, subprocess.CalledProcessError):
        return {}
    gb = (lambda v: round(int(v) / 2**30, 2) if v and v.isdigit() else v)
    out = {"mode": "systemd", "unit": unit, "mem_current_gb": gb(kv.get("MemoryCurrent")),
           "limit_memory_gb": gb(kv.get("MemoryMax")), "limit_cpus": kv.get("AllowedCPUs"),
           "cpu_quota": kv.get("CPUQuotaPerSecUSec")}
    storage = os.environ.get("PILOT_QDRANT_STORAGE")
    if collection and storage:
        path = Path(storage) / "collections" / collection
        out["collection_disk_gb"] = round(int(sh("du", "-sb", str(path)).split()[0]) / 2**30, 2) if path.exists() else None
    if collection:
        from bench.server import server_client
        i = server_client().get_collection(collection)
        out.update(points=i.points_count, segments=i.segments_count, status=str(i.status))
    return out


def resource_stats(collection: str | None = None) -> dict[str, Any]:
    """Qdrant'ın kaynak kullanımı ve sınırı: docker (VM) ya da systemd (şirket içi sunucu); ikisi de yoksa boş."""
    if os.environ.get("PILOT_QDRANT_UNIT"):
        return systemd_stats(collection)
    if os.environ.get("PILOT_QDRANT_DOCKER"):
        return container_stats(collection)
    return {}


# ---------- sorgular ----------

def queries_path(collection: str) -> Path:
    from bench.scale_index import paths
    meta_ = json.loads(paths(collection)[1].read_text(encoding="utf-8"))
    return SCALE_DIR / f"queries_{meta_['embed']}.json"


def build_queries(collection: str) -> Path:
    """Onaylı setler + aday taslak: soru metni, beklenen dokümanın markası, sorgu vektörleri (pipeline'ın encode_query'si).
    Yük testi ve gecikme ölçümü bunları kullanır; bulut embed bir kez ödenir."""
    apply_env(collection)
    from pilot.embed import encode_query
    from pilot.registry import BY_ID
    items = load_questions(KNOWN_SETS)
    aday = json.loads((PILOT_DIR / "eval" / "aday_sorular.json").read_text(encoding="utf-8"))
    items += [{**it, "qid": f"aday:{it['id']}"} for it in aday]
    seen, out = set(), []
    for it in items:
        if it["q"] in seen:
            continue
        seen.add(it["q"])
        docs = it.get("expect_docs") or [k["doc"] for k in it.get("kabul") or []]
        brand = BY_ID[docs[0]].brand if docs and docs[0] in BY_ID else None
        out.append({"qid": it["qid"], "q": it["q"], "brand": brand, **encode_query(it["q"])})
    path = queries_path(collection)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    print(f"{len(out)} sorgu → {path}")
    return path


def load_query_vectors(collection: str) -> list[dict[str, Any]]:
    qs = json.loads(queries_path(collection).read_text(encoding="utf-8"))
    for q in qs:
        q["sparse"] = {int(k): v for k, v in q["sparse"].items()}
    return qs


# ---------- gecikme ----------

def pct(xs: list[float], p: float) -> float:
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(p / 100 * (len(xs) - 1))))]


def search_once(qc, q: dict[str, Any], mode: str, collection: str) -> float:
    from pilot.retrieve import _filter, candidates, dense_params
    flt = _filter([q["brand"]] if mode == "hibrit_marka" and q.get("brand") else None, None,
                  ACCESS_USER if mode == "hibrit_yetki" else None)
    t = time.perf_counter()
    candidates(qc, q, flt, "dense" if mode == "dense" else "hybrid", collection=collection, dparams=dense_params())
    return time.perf_counter() - t


def latency(collection: str, label: str, repeats: int, warmup: int, recall_queries: int, seed: int = 0) -> Path:
    apply_env(collection)
    from bench.server import server_client
    qs = load_query_vectors(collection)
    qc = server_client()
    rng = random.Random(seed)
    for q in qs[:warmup]:
        for m in MODES:
            search_once(qc, q, m, collection)
    res: dict[str, list[float]] = {m: [] for m in MODES}
    for r in range(repeats):
        order = qs[:]
        rng.shuffle(order)                          # aynı sorgu art arda gelmesin (önbellek etkisi)
        for q in order:
            for m in MODES:
                res[m].append(search_once(qc, q, m, collection))
    timing = {m: {"n": len(v), "p50": statistics.median(v), "p95": pct(v, 95), "p99": pct(v, 99), "mean": statistics.mean(v)}
              for m, v in res.items()}
    from bench.measure import ann_recall
    recall = ann_recall(recall_queries) if recall_queries else None
    data = {"meta": meta({"collection": collection, "label": label, "repeats": repeats, "queries": len(qs),
                          "access_user": ACCESS_USER}),
            "timing": timing, "ann_recall": recall, "resources": resource_stats(collection)}
    lines = [f"# Aşama 3 süre: {collection} · {label}", "",
             f"{len(qs)} sorgu × {repeats} tur, yalnız Qdrant (sorgu vektörü hazır). Kaynak: {data['resources']}", "",
             "| Biçim | n | p50 | p95 | p99 |", "|---|---|---|---|---|"]
    lines += [f"| {m} | {t['n']} | {t['p50'] * 1000:.1f} ms | {t['p95'] * 1000:.1f} ms | {t['p99'] * 1000:.1f} ms |"
              for m, t in timing.items()]
    if recall:
        lines += ["", f"ANN recall ({recall['vector']}, {recall['n_queries']} gürültülü sorgu): "
                  + ", ".join(f"{k} {v:.3f}" for k, v in recall.items() if k.startswith("recall"))]
    path = write_result(f"asama3_sure_{collection}_{label}", data, "\n".join(lines) + "\n")
    print(path)
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("queries")
    q.add_argument("--collection", required=True)
    li = sub.add_parser("limits")
    li.add_argument("--cpus", type=int)
    li.add_argument("--memory", default="16g")
    li.add_argument("--none", action="store_true")
    la = sub.add_parser("latency")
    la.add_argument("--collection", required=True)
    la.add_argument("--label", required=True)
    la.add_argument("--repeats", type=int, default=5)
    la.add_argument("--warmup", type=int, default=20)
    la.add_argument("--recall-queries", type=int, default=300)
    st = sub.add_parser("stats")
    st.add_argument("--collection")
    w = sub.add_parser("wait")
    w.add_argument("--url", default="http://127.0.0.1:6333")
    w.add_argument("--timeout", type=float, default=600)
    a = ap.parse_args()
    if a.cmd == "queries":
        build_queries(a.collection)
    elif a.cmd == "limits":
        limits(None if a.none else a.cpus, a.memory)
    elif a.cmd == "latency":
        latency(a.collection, a.label, a.repeats, a.warmup, a.recall_queries)
    elif a.cmd == "wait":
        wait_ready(a.url, a.timeout)
    else:
        print(json.dumps(resource_stats(a.collection), ensure_ascii=False))


if __name__ == "__main__":
    main()
