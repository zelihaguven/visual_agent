"""Reranker karşılaştırması: aynı aday listesini farklı reranker yapılandırmaları sıralar; doğruluk ve süre birlikte.

Kullanım (Pilot klasöründe, $env:PYTHONUTF8="1"):
    python -m bench.rerank_bench collect                       # adaylar: filtreli + filtresiz (bench_cache/, ~5 dk)
    python -m bench.rerank_bench diag                          # tek çağrı teşhisi: flag/torch, batch, iş parçacığı
    python -m bench.rerank_bench compare --name rerank_modeller \\
        --configs local:BAAI/bge-reranker-v2-m3:flag:512 local:BAAI/bge-reranker-v2-m3:torch:512 ...
    python -m bench.rerank_bench grid --name rerank_izgara      # FUSED_K {10,15,20} × max_length {256,384,512}

Yapılandırma: sağlayıcı:model:backend:max_length[:batch]  (ör. local:BAAI/bge-reranker-v2-m3:onnx-int8:512:8,
openrouter:cohere/rerank-v3.5). Yöntem:
- Adaylar pipeline'daki gibi hazırlanan sorguyla, rerank'sız aramadan gelir (RRF sırası, içindekiler satırı elenmiş).
- Yapılandırmalar her soruda dönüşümlü çalışır (ısınma ve CPU kısması hepsini eşit etkiler); her çağrının CPU frekansı
  kaydedilir. Her yapılandırma önce ısınma çağrılarıyla yüklenir.
- FUSED_K=10/15 doğruluğu, 20 adayın skorlarının ilk 10/15 adaya kısıtlanmasıyla hesaplanır (cross-encoder skoru her
  aday için bağımsızdır). Süreleri grid komutu ayrıca ölçer.
"""
import argparse
import json
import logging
import time
import warnings
from typing import Any

from bench.common import (KNOWN_SETS, accuracy, first_rank, fmt_pct, fmt_s, load_questions, meta, prepare, stats,
                          write_result)
from bench.cpu import CpuMonitor

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("rerank_bench")


def cand_path(holdout: bool = False):
    from pilot.config import DATA_DIR
    return DATA_DIR / "bench_cache" / ("candidates_holdout.json" if holdout else "candidates.json")


# ---------- adaylar ----------

def collect(sets: list[str], repeats: int = 3, holdout: bool = False) -> None:
    """Her soru için filtreli ve filtresiz 20 aday + embed/Qdrant süreleri (rerank'sız arama)."""
    from bench.common import StageTimer
    from pilot import index, retrieve

    index.REUSE = True                    # istemci açılışı (~2 sn) aday süresine girmesin; ayrıca ölçüldü (baseline)
    items = [(it, prepare(it["q"])) for it in load_questions(sets)]
    items = [(it, p) for it, p in items if not p["skip"] and not it.get("expect_clarify")]
    out: dict[str, Any] = {"questions": {}, "timing": {}}
    for it, p in items[:3]:
        retrieve.search(p["search_q"], doc_ids=p["doc_ids"], top_k=retrieve.FUSED_K, do_rerank=False)
    for mode in ("filtered", "unfiltered"):
        timer = StageTimer()
        retrieve.timing_hook = timer
        for r in range(repeats):
            for it, p in items:
                scope = p["doc_ids"] if mode == "filtered" else None
                timer.start()
                hits = retrieve.search(p["search_q"], doc_ids=scope, top_k=retrieve.FUSED_K, do_rerank=False)
                timer.stop()
                if r == 0:
                    q = out["questions"].setdefault(it["qid"], {
                        "qid": it["qid"], "set": it["set"], "q": it["q"], "search_q": p["search_q"],
                        "not_found": bool(it.get("expect_not_found")),
                        "expect_docs": it.get("expect_docs", []), "expect_pages": it.get("expect_pages", [])})
                    q[mode] = [{"chunk_id": h.chunk["chunk_id"], "doc_id": h.chunk["doc_id"],
                                "pages": h.chunk["pages"], "chunk_type": h.chunk.get("chunk_type"),
                                "text": h.chunk["text"]} for h in hits]
        retrieve.timing_hook = None
        out["timing"][mode] = timer.summary()
        log.info("%s: %d soru, %d tur", mode, len(items), repeats)
    index.close_shared()
    out["params"] = {"FUSED_K": retrieve.FUSED_K, "PREFETCH_K": retrieve.PREFETCH_K, "sets": sets}
    path = cand_path(holdout)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    log.info("yazıldı: %s", path)


def load_candidates(holdout: bool = False, path: str | None = None) -> dict[str, Any]:
    """path: başka bir aday dosyası (ör. bench.providers collect çıktısı, başka embedding modeli)."""
    from pathlib import Path
    return json.loads((Path(path) if path else cand_path(holdout)).read_text(encoding="utf-8"))


# ---------- doğruluk ----------

def ranked_rank(cands: list[dict[str, Any]], scores: list[float] | None, item: dict[str, Any], k: int) -> int | None:
    """İlk k adayı (RRF sırası) skorla sıralayıp beklenen parçanın sırası. scores None: rerank'sız (RRF sırası)."""
    top = list(range(min(k, len(cands))))
    if scores is not None:
        top.sort(key=lambda i: -scores[i])
    return first_rank([cands[i] for i in top], item)


def parse_config(spec: str) -> dict[str, Any]:
    parts = spec.split(":")
    if parts[0] == "openrouter":
        return {"spec": spec, "provider": "openrouter", "model": ":".join(parts[1:]), "backend": "api",
                "max_length": None, "batch": None}
    if parts[0] != "local" or len(parts) < 4:
        raise ValueError(f"yapılandırma: local:model:backend:max_length[:batch] ya da openrouter:model — {spec}")
    return {"spec": spec, "provider": "local", "model": parts[1], "backend": parts[2], "max_length": int(parts[3]),
            "batch": int(parts[4]) if len(parts) > 4 else 8}


def build(cfg: dict[str, Any]):
    from pilot.rerankers import make_reranker
    return make_reranker(cfg["provider"], cfg["model"], cfg["backend"], cfg["max_length"] or 512, cfg["batch"] or 8)


def summarize_config(rows: list[dict[str, Any]], ks: tuple[int, ...] = (10, 15, 20)) -> dict[str, Any]:
    scored = [r for r in rows if not r["not_found"]]
    acc = {f"K{k}": accuracy([r["rank"][str(k)] for r in scored]) for k in ks}
    by_set = {s: accuracy([r["rank"]["20"] for r in scored if r["set"] == s]) for s in sorted({r["set"] for r in scored})}
    secs = [r["seconds"] for r in rows]
    mhz = [r["cpu"]["mhz"] for r in rows if r["cpu"]["mhz"]]
    out = {"accuracy": acc, "by_set": by_set, "time": stats(secs),
           "cpu_mhz": stats(mhz) if mhz else None,
           "not_found_top": {r["qid"]: r["top"] for r in rows if r["not_found"]}}
    costs = [r["cost_usd"] for r in rows if r.get("cost_usd") is not None]
    if costs:
        out["cost_usd_total"] = sum(costs)
    if any(r.get("network_s") is not None for r in rows):
        out["network"] = stats([r["network_s"] for r in rows if r.get("network_s") is not None])
    return out


def compare(name: str, specs: list[str], modes: list[str], warmup: int, limit: int | None,
            candidates: str | None = None) -> None:
    cands = load_candidates(path=candidates)
    items = {it["qid"]: it for it in load_questions(KNOWN_SETS)}
    cfgs = [parse_config(s) for s in specs]
    models = {}
    for c in cfgs:
        t = time.perf_counter()
        models[c["spec"]] = build(c)
        c["load_s"] = round(time.perf_counter() - t, 1)
        log.info("yüklendi %s (%.0f sn)", c["spec"], c["load_s"])
    qs = list(cands["questions"].values())[:limit]
    for c in cfgs:
        for q in qs[:warmup]:
            models[c["spec"]](q["search_q"], [x["text"] for x in q["filtered"]])
    rows: dict[str, dict[str, list[dict[str, Any]]]] = {c["spec"]: {m: [] for m in modes} for c in cfgs}
    with CpuMonitor() as mon:
        for i, q in enumerate(qs):
            for mode in modes:
                passages = [x["text"] for x in q[mode]]
                order = cfgs if i % 2 == 0 else cfgs[::-1]          # dönüşümlü: sıra etkisini dengeler
                for c in order:
                    m = models[c["spec"]]
                    t0 = time.perf_counter()
                    scores = m(q["search_q"], passages)
                    t1 = time.perf_counter()
                    rows[c["spec"]][mode].append({
                        "qid": q["qid"], "set": q["set"], "not_found": q["not_found"], "seconds": t1 - t0,
                        "network_s": getattr(m, "last_network_s", None), "cpu": mon.window(t0, t1),
                        "cost_usd": (getattr(m, "last_usage", None) or {}).get("cost"),
                        "n_passages": len(passages), "top": max(scores) if scores else None,
                        "rank": {str(k): None if q["not_found"] else ranked_rank(q[mode], scores, items[q["qid"]], k)
                                 for k in (10, 15, 20)},
                        "scores": [round(s, 4) for s in scores]})
            log.info("%d/%d %s", i + 1, len(qs), q["qid"])
    # rerank'sız (RRF sırası) referans
    norr = {}
    for mode in modes:
        rr = [ranked_rank(q[mode], None, items[q["qid"]], 20) for q in qs if not q["not_found"]]
        norr[mode] = accuracy(rr)
    data = {"meta": meta({"configs": cfgs, "modes": modes, "warmup": warmup, "candidates": cands["params"]}),
            "no_rerank": norr, "candidate_timing": cands["timing"],
            "configs": {s: {m: {"summary": summarize_config(r), "rows": r} for m, r in v.items()}
                        for s, v in rows.items()}}
    path = write_result(name, data, compare_md(name, data))
    log.info("yazıldı: %s", path)


def compare_md(name: str, data: dict[str, Any]) -> str:
    m = data["meta"]
    hw = m["hardware"]
    lines = [f"# Reranker karşılaştırması: {name}", "",
             f"{m['date']} · commit `{m['git_commit']}` · {hw.get('cpu')} · {hw.get('ram_gb')} GB RAM", "",
             "Aynı aday listesi (rerank'sız aramanın ilk 20'si). Süre: yalnız rerank çağrısı, 1 çağrı/soru. "
             "MHz: o çağrı sırasında CPU'nun gerçek ortalama frekansı.", ""]
    for mode in m["params"]["modes"]:
        nr = data["no_rerank"][mode]
        lines += [f"## {'Filtreli' if mode == 'filtered' else 'Filtresiz'}", "",
                  "| Yapılandırma | hit@1 | hit@5 | MRR | süre ort. | p50 | p95 | MHz ort. | yükleme |",
                  "|---|---|---|---|---|---|---|---|---|",
                  f"| rerank yok (RRF) | {fmt_pct(nr['hit@1'])} | {fmt_pct(nr['hit@5'])} | {fmt_pct(nr['mrr'])} "
                  f"| – | – | – | – | – |"]
        for c in m["params"]["configs"]:
            s = data["configs"][c["spec"]][mode]["summary"]
            a, t = s["accuracy"]["K20"], s["time"]
            mhz = f"{s['cpu_mhz']['mean']:.0f}" if s.get("cpu_mhz") else "–"
            net = f" (ağ {fmt_s(s['network']['p50'])})" if s.get("network") else ""
            lines.append(f"| `{c['spec']}` | {fmt_pct(a['hit@1'])} | {fmt_pct(a['hit@5'])} | {fmt_pct(a['mrr'])} | "
                         f"{fmt_s(t['mean'])}{net} | {fmt_s(t['p50'])} | {fmt_s(t['p95'])} | {mhz} | "
                         f"{c.get('load_s', '–')} sn |")
        lines += ["", "FUSED_K etkisi (doğruluk; aynı skorlar ilk K adaya kısıtlanarak):", "",
                  "| Yapılandırma | K=10 hit@1/hit@5/MRR | K=15 | K=20 |", "|---|---|---|---|"]
        for c in m["params"]["configs"]:
            acc = data["configs"][c["spec"]][mode]["summary"]["accuracy"]
            cells = [f"{fmt_pct(acc[k]['hit@1'])} / {fmt_pct(acc[k]['hit@5'])} / {fmt_pct(acc[k]['mrr'])}"
                     for k in ("K10", "K15", "K20")]
            lines.append(f"| `{c['spec']}` | " + " | ".join(cells) + " |")
        lines.append("")
    return "\n".join(lines)


# ---------- tek çağrı teşhisi ----------

def diag(name: str, qids: list[str], calls: int) -> None:
    """Aynı aday listesinde: flag vs torch (batch 4/8/20), torch iş parçacığı 2–12. Her çağrının süresi ve CPU MHz."""
    import torch

    from pilot.config import RERANK_MODEL
    from pilot.rerankers import FlagRerank, TorchRerank

    cands = load_candidates()["questions"]
    qs = [cands[q] for q in qids]
    default_threads = torch.get_num_threads()
    flag = FlagRerank(RERANK_MODEL, 512)
    flag_obj = flag._m
    tr = TorchRerank(RERANK_MODEL, 512, 8)
    results: list[dict[str, Any]] = []

    def run(label: str, fn, threads: int | None = None):
        torch.set_num_threads(threads or default_threads)
        for q in qs:
            fn(q["search_q"], [x["text"] for x in q["filtered"]])           # ısınma
        for _ in range(calls):
            for q in qs:
                passages = [x["text"] for x in q["filtered"]]
                t0 = time.perf_counter()
                scores = fn(q["search_q"], passages)
                t1 = time.perf_counter()
                results.append({"label": label, "threads": threads or default_threads, "qid": q["qid"],
                                "seconds": t1 - t0, "cpu": mon.window(t0, t1), "scores": scores})
        log.info("%s: %s", label, fmt_s(stats([r["seconds"] for r in results if r["label"] == label])["p50"]))

    with CpuMonitor() as mon:
        run("flag (varsayılan)", flag)
        same_obj = flag._m is flag_obj
        for bs in (20, 8, 4):
            tr.batch_size = bs
            run(f"torch batch {bs}", tr)
        tr.batch_size = 8
        for th in (2, 4, 6, 8, 12):
            run(f"torch batch 8, {th} iş parçacığı", tr, th)
    torch.set_num_threads(default_threads)
    # Skor eşitliği: torch ile flag aynı modeli aynı girdiyle çalıştırıyor mu?
    ref = {r["qid"]: r["scores"] for r in results if r["label"] == "flag (varsayılan)"}
    max_diff = max(abs(a - b) for r in results if r["label"].startswith("torch") for a, b in zip(r["scores"], ref[r["qid"]]))
    data = {"meta": meta({"qids": qids, "calls": calls, "default_threads": default_threads,
                          "flag_model_instance_cached": same_obj, "flag_batch_size": flag_obj.batch_size}),
            "max_score_diff_vs_flag": max_diff,
            "rows": [{k: v for k, v in r.items() if k != "scores"} for r in results]}
    labels = list(dict.fromkeys(r["label"] for r in results))
    lines = [f"# Reranker tek çağrı teşhisi: {name}", "", f"{data['meta']['date']} · commit "
             f"`{data['meta']['git_commit']}` · sorular: {', '.join(qids)} · {calls} çağrı/soru (ısınma hariç)", "",
             f"Torch varsayılan iş parçacığı: {default_threads} · FlagReranker örneği önbellekte: {same_obj} · "
             f"Flag batch_size: {flag_obj.batch_size} · torch skorlarının flag'den en büyük farkı: {max_diff:.2e}", "",
             "| Çalıştırma | n | p50 | ort. | p95 | MHz ort. |", "|---|---|---|---|---|---|"]
    for lb in labels:
        rs = [r for r in results if r["label"] == lb]
        s = stats([r["seconds"] for r in rs])
        mh = [r["cpu"]["mhz"] for r in rs if r["cpu"]["mhz"]]
        lines.append(f"| {lb} | {s['n']} | {fmt_s(s['p50'])} | {fmt_s(s['mean'])} | {fmt_s(s['p95'])} | "
                     f"{sum(mh) / len(mh):.0f} |" if mh else f"| {lb} | {s['n']} | {fmt_s(s['p50'])} | – | – | – |")
    path = write_result(name, data, "\n".join(lines) + "\n")
    log.info("yazıldı: %s", path)


# ---------- FUSED_K × max_length süre ızgarası ----------

def grid(name: str, model: str, backend: str, fks: list[int], mls: list[int], sets: list[str], repeats: int) -> None:
    """Süre: her (FUSED_K, max_length) için ilk K aday reranklanır. Doğruluk: her max_length için bütün sorular."""
    cands = load_candidates()
    items = {it["qid"]: it for it in load_questions(KNOWN_SETS)}
    qs = list(cands["questions"].values())
    timed = [q for q in qs if q["set"] in sets]
    models = {ml: build({"provider": "local", "model": model, "backend": backend, "max_length": ml, "batch": 8})
              for ml in mls}
    combos = [(fk, ml) for ml in mls for fk in fks]
    for ml in mls:
        for q in timed[:2]:
            models[ml](q["search_q"], [x["text"] for x in q["filtered"]])
    times: dict[str, list[dict[str, Any]]] = {f"{fk}x{ml}": [] for fk, ml in combos}
    acc_rows: dict[int, list[dict[str, Any]]] = {ml: [] for ml in mls}
    with CpuMonitor() as mon:
        for r in range(repeats):
            for i, q in enumerate(timed):
                order = combos if (i + r) % 2 == 0 else combos[::-1]
                for fk, ml in order:
                    passages = [x["text"] for x in q["filtered"][:fk]]
                    t0 = time.perf_counter()
                    models[ml](q["search_q"], passages)
                    t1 = time.perf_counter()
                    times[f"{fk}x{ml}"].append({"qid": q["qid"], "seconds": t1 - t0, "cpu": mon.window(t0, t1)})
            log.info("süre turu %d/%d", r + 1, repeats)
        for i, q in enumerate(qs):
            for ml in mls:
                scores = models[ml](q["search_q"], [x["text"] for x in q["filtered"]])
                acc_rows[ml].append({"qid": q["qid"], "set": q["set"], "not_found": q["not_found"],
                                     "top": max(scores) if scores else None,
                                     "rank": {str(k): None if q["not_found"] else
                                              ranked_rank(q["filtered"], scores, items[q["qid"]], k) for k in fks}})
        log.info("doğruluk geçişi bitti")
    table = {}
    for fk, ml in combos:
        rs = times[f"{fk}x{ml}"]
        scored = [x for x in acc_rows[ml] if not x["not_found"]]
        mh = [x["cpu"]["mhz"] for x in rs if x["cpu"]["mhz"]]
        table[f"{fk}x{ml}"] = {"FUSED_K": fk, "max_length": ml, "time": stats([x["seconds"] for x in rs]),
                               "cpu_mhz": sum(mh) / len(mh) if mh else None,
                               "accuracy": accuracy([x["rank"][str(fk)] for x in scored])}
    data = {"meta": meta({"model": model, "backend": backend, "FUSED_K": fks, "max_length": mls,
                          "timing_sets": sets, "repeats": repeats}),
            "table": table, "times": times, "accuracy_rows": {str(k): v for k, v in acc_rows.items()}}
    lines = [f"# FUSED_K × max_length: {name}", "",
             f"{data['meta']['date']} · commit `{data['meta']['git_commit']}` · `{model}` · backend `{backend}` · "
             f"süre: {', '.join(sets)} setleri, {repeats} tur, dönüşümlü sıra · doğruluk: bilinen 36 soru", "",
             "| FUSED_K | max_length | hit@1 | hit@5 | MRR | rerank p50 | p95 | ort. | MHz |",
             "|---|---|---|---|---|---|---|---|---|"]
    for key, t in table.items():
        a, s = t["accuracy"], t["time"]
        lines.append(f"| {t['FUSED_K']} | {t['max_length']} | {fmt_pct(a['hit@1'])} | {fmt_pct(a['hit@5'])} | "
                     f"{fmt_pct(a['mrr'])} | {fmt_s(s['p50'])} | {fmt_s(s['p95'])} | {fmt_s(s['mean'])} | "
                     f"{t['cpu_mhz']:.0f} |")
    path = write_result(name, data, "\n".join(lines) + "\n")
    log.info("yazıldı: %s", path)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect")
    c.add_argument("--sets", nargs="+", default=list(KNOWN_SETS))
    c.add_argument("--repeats", type=int, default=3)
    c.add_argument("--holdout", action="store_true")
    d = sub.add_parser("diag")
    d.add_argument("--name", default="rerank_teshis")
    d.add_argument("--qids", nargs="+", default=["questions:Q01", "questions:Q04", "sekil_sorular:G1"])
    d.add_argument("--calls", type=int, default=2)
    k = sub.add_parser("compare")
    k.add_argument("--name", default="rerank_karsilastirma")
    k.add_argument("--configs", nargs="+", required=True)
    k.add_argument("--modes", nargs="+", default=["filtered"], choices=["filtered", "unfiltered"])
    k.add_argument("--warmup", type=int, default=2)
    k.add_argument("--limit", type=int, default=None)
    k.add_argument("--candidates", default=None, help="aday dosyası (varsayılan: bench_cache/candidates.json)")
    g = sub.add_parser("grid")
    g.add_argument("--name", default="rerank_izgara")
    g.add_argument("--model", default="BAAI/bge-reranker-v2-m3")
    g.add_argument("--backend", default="torch")
    g.add_argument("--fused-k", nargs="+", type=int, default=[10, 15, 20])
    g.add_argument("--max-length", nargs="+", type=int, default=[256, 384, 512])
    g.add_argument("--timing-sets", nargs="+", default=["questions"])
    g.add_argument("--repeats", type=int, default=3)
    a = ap.parse_args()
    if a.cmd == "collect":
        collect(a.sets, a.repeats, a.holdout)
    elif a.cmd == "diag":
        diag(a.name, a.qids, a.calls)
    elif a.cmd == "compare":
        compare(a.name, a.configs, a.modes, a.warmup, a.limit, a.candidates)
    else:
        grid(a.name, a.model, a.backend, a.fused_k, a.max_length, a.timing_sets, a.repeats)


if __name__ == "__main__":
    main()
