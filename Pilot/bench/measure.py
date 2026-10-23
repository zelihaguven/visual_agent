"""Arama katmanı ölçümü: doğruluk (hit@1, hit@5, MRR), aşama süreleri (embed, Qdrant, rerank), ANN recall, bellek.

Kullanım (Pilot klasöründe, arayüz kapalıyken; gömülü Qdrant klasörü tek süreçte açılır):
    $env:PYTHONUTF8="1"; python -m bench.measure --name baseline
    python -m bench.measure --name x --repeats 5 --sets questions sekil_sorular
    python -m bench.measure --name juki --sets gorulmemis_juki     # yalnız son raporda (ayrı tutulan set)
Çıktı: eval/bench/<name>_<tarih>.json ve .md

Yöntem (BENCHMARK-RAPORU.md §Yöntem): Modeller ısınma sorgularıyla yüklenir (süreye girmez). Her soru --repeats kez
aranır; doğruluk ilk turdan (arama deterministik), süreler bütün turlardan. Arama pipeline'daki gibi hazırlanır
(common.prepare); netleştirme sorulan sorular aranmaz. expect_not_found soruları doğruluğa girmez, skorları kaydedilir.
"""
import argparse
import gc
import logging
import random
import warnings
from typing import Any

from bench.common import (KNOWN_SETS, StageTimer, accuracy, dir_size, first_rank, fmt_pct, fmt_s, load_questions,
                          meta, overlap_at_k, prepare, timing_table, write_result)

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("bench")

STAGES = ("embed", "qdrant_open", "qdrant", "rerank", "total")


def retrieval_params() -> dict[str, Any]:
    from pilot import config, retrieve
    return {"PREFETCH_K": retrieve.PREFETCH_K, "FUSED_K": retrieve.FUSED_K, "TOP_K_SOURCES": config.TOP_K_SOURCES,
            "EMBED_MODEL": config.EMBED_MODEL, "RERANK_MODEL": config.RERANK_MODEL,
            "EMBED_MAX_LENGTH": config.EMBED_MAX_LENGTH, "EMBED_DEVICE": config.EMBED_DEVICE}


def run_questions(items: list[dict[str, Any]], repeats: int, warmup: int, do_rerank: bool = True,
                  unfiltered: bool = False) -> tuple[list[dict[str, Any]], StageTimer]:
    """unfiltered: pipeline'ın doküman filtresi kaldırılır (bütün koleksiyonda arama; kalabalıkta en kötü durum)."""
    from pilot import retrieve

    prepared = [(it, prepare(it["q"])) for it in items]
    if unfiltered:
        prepared = [(it, {**p, "doc_ids": None}) for it, p in prepared]
    runnable = [(it, p) for it, p in prepared if not p["skip"] and not it.get("expect_clarify")]
    timer = StageTimer()
    for it, p in runnable[:warmup]:
        retrieve.search(p["search_q"], doc_ids=p["doc_ids"], top_k=retrieve.FUSED_K, do_rerank=do_rerank)
    retrieve.timing_hook = timer
    rows: dict[str, dict[str, Any]] = {}
    try:
        for r in range(repeats):
            for it, p in runnable:
                timer.start()
                hits = retrieve.search(p["search_q"], doc_ids=p["doc_ids"], top_k=retrieve.FUSED_K,
                                       do_rerank=do_rerank)
                t = timer.stop()
                if r == 0:
                    chunks = [h.chunk for h in hits]
                    rows[it["qid"]] = {
                        "qid": it["qid"], "set": it["set"], "kind": it.get("kind"),
                        "not_found": bool(it.get("expect_not_found")),
                        "rank": None if it.get("expect_not_found") else first_rank(chunks, it),
                        "top_score": hits[0].rerank_score if hits else None,
                        "scores": [round(h.rerank_score, 3) for h in hits[:5] if h.rerank_score is not None],
                        "top5": [(c["doc_id"], c["pages"]) for c in chunks[:5]],
                        "forbidden_in_top5": bool(set(it.get("forbid_docs", [])) & {c["doc_id"] for c in chunks[:5]}),
                        "seconds": []}
                rows[it["qid"]]["seconds"].append(round(t["total"], 4))
            log.info("tur %d/%d bitti", r + 1, repeats)
    finally:
        retrieve.timing_hook = None
    skipped = [{"qid": it["qid"], "set": it["set"], "skip": p["skip"] or "expect_clarify"}
               for it, p in prepared if p["skip"] or it.get("expect_clarify")]
    return list(rows.values()) + skipped, timer


def ann_recall(n_queries: int = 500, ks: tuple[int, ...] = (5, 20), noise: float = 0.05, seed: int = 0,
               search_params: Any = None) -> dict[str, Any]:
    """Saklı dense vektörlerden türetilen rastgele sorgularla (vektör + Gauss gürültüsü, normalize) yaklaşık arama ile
    tam aramanın (exact=True) örtüşmesi. Gömülü modda arama zaten tamdır; değer 1,0 çıkmalı (düzeneğin kontrolü)."""
    import numpy as np
    from qdrant_client import models

    from pilot.config import COLLECTION
    from pilot.index import client

    rng = random.Random(seed)
    qc = client()
    try:
        all_ids, offset = [], None      # kısmi yeniden indeksten sonra kimlikler ardışık değil
        while True:
            batch, offset = qc.scroll(COLLECTION, limit=5000, offset=offset, with_payload=False)
            all_ids += [p.id for p in batch]
            if offset is None:
                break
        ids = rng.sample(all_ids, min(n_queries, len(all_ids)))
        pts = qc.retrieve(COLLECTION, ids=ids, with_vectors=["dense"], with_payload=False)
        gen = np.random.default_rng(seed)
        kmax, res = max(ks), {k: [] for k in ks}
        for p in pts:
            v = np.asarray(p.vector["dense"]) + gen.normal(0, noise, 1024)
            q = (v / np.linalg.norm(v)).tolist()
            approx = qc.query_points(COLLECTION, query=q, using="dense", limit=kmax, search_params=search_params)
            exact = qc.query_points(COLLECTION, query=q, using="dense", limit=kmax,
                                    search_params=models.SearchParams(exact=True))
            for k in ks:
                res[k].append(overlap_at_k([x.id for x in approx.points], [x.id for x in exact.points], k))
    finally:
        qc.close()
    return {"n_queries": len(pts), "noise": noise, **{f"recall@{k}": sum(v) / len(v) for k, v in res.items()}}


def qdrant_memory() -> dict[str, Any]:
    """Gömülü mod: istemci açılınca süreç belleğindeki artış (bütün koleksiyon RAM'e yüklenir) ve disk."""
    import psutil

    from pilot.config import COLLECTION, QDRANT_DIR
    from pilot.index import client

    gc.collect()
    proc = psutil.Process()
    before = proc.memory_info().rss
    qc = client()
    n = qc.count(COLLECTION).count
    after = proc.memory_info().rss
    qc.close()
    return {"mode": "embedded", "points": n, "rss_delta_mb": round((after - before) / 2**20, 1),
            "disk_mb": round(dir_size(QDRANT_DIR) / 2**20, 1)}


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    scored = [r for r in rows if "rank" in r and not r["not_found"]]
    out = {"all": accuracy([r["rank"] for r in scored])}
    for s in sorted({r["set"] for r in scored}):
        out[s] = accuracy([r["rank"] for r in scored if r["set"] == s])
    return out


def acc_table(acc: dict[str, Any]) -> list[str]:
    rows = ["| Set | n | hit@1 | hit@5 | hit@20 | MRR |", "|-----|---|-------|-------|--------|-----|"]
    for k, a in acc.items():
        rows.append(f"| {k} | {a['n']} | {fmt_pct(a['hit@1'])} | {fmt_pct(a['hit@5'])} | "
                    f"{fmt_pct(a.get('hit@20', float('nan')))} | {fmt_pct(a['mrr'])} |")
    return rows


def report_md(name: str, data: dict[str, Any]) -> str:
    m, acc = data["meta"], data["accuracy"]
    hw = m["hardware"]
    lines = [f"# Arama ölçümü: {name}", "",
             f"{m['date']} · commit `{m['git_commit']}` · {hw.get('cpu')} ({hw.get('logical_cpus')} iş parçacığı), "
             f"{hw.get('ram_gb')} GB RAM · {hw.get('platform')}", "",
             "Parametreler: " + ", ".join(f"`{k}={v}`" for k, v in m["params"].items()), "",
             "## Doğruluk (netleştirme ve bulunamadı soruları hariç)", ""]
    lines += acc_table(acc)
    lines += ["", f"## Süre (soru başına; setler: {', '.join(m['params']['timing_sets'])}; "
              f"{m['params']['repeats']} tur, ısınma hariç)", ""]
    lines += timing_table(data["timing"], STAGES)
    if data.get("ann_recall"):
        r = data["ann_recall"]
        lines += ["", "## ANN recall (dense, rastgele sorgu)", "",
                  f"{r['n_queries']} sorgu · " + " · ".join(f"{k}: {fmt_pct(v)}" for k, v in r.items()
                                                           if k.startswith("recall"))]
    if data.get("memory"):
        mem = data["memory"]
        lines += ["", "## Bellek", "", f"Mod: {mem['mode']} · parça: {mem['points']} · RAM artışı: "
                  f"{mem['rss_delta_mb']} MB · disk: {mem['disk_mb']} MB"]
    if data.get("unfiltered"):
        u = data["unfiltered"]
        lines += ["", "## Filtresiz (doküman filtresi kaldırılmış, bütün koleksiyon, "
                  + ("rerank'lı" if u["rerank"] else "rerank'sız: RRF sırası") + ")", ""]
        lines += acc_table(u["accuracy"])
        lines += [""] + timing_table(u["timing"], STAGES)
    misses = [r for r in data["questions"] if r.get("rank") is None and "rank" in r and not r["not_found"]]
    later = [r for r in data["questions"] if r.get("rank") and r["rank"] > 1]
    nf = [r for r in data["questions"] if r.get("not_found")]
    skipped = [r for r in data["questions"] if r.get("skip")]
    lines += ["", "## Soru ayrıntısı", "",
              "Bulunamayan (ilk 20'de yok): " + (", ".join(r["qid"] for r in misses) or "–"),
              "", "İlk sırada değil: " + (", ".join(f"{r['qid']} ({r['rank']}.)" for r in later) or "–"),
              "", "Bulunamadı beklenen, en iyi rerank skoru: "
              + (", ".join(f"{r['qid']} {r['top_score']:.2f}" for r in nf if r["top_score"] is not None) or "–"),
              "", "Aranmayan (pipeline'da netleştirme): " + (", ".join(f"{r['qid']} ({r['skip']})" for r in skipped)
                                                             or "–"), ""]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="baseline")
    ap.add_argument("--sets", nargs="+", default=list(KNOWN_SETS))
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--warmup", type=int, default=3)
    ap.add_argument("--recall-queries", type=int, default=500)
    ap.add_argument("--no-rerank", action="store_true")
    ap.add_argument("--unfiltered", action="store_true", help="doküman filtresi olmadan da ölç (1 tur)")
    ap.add_argument("--unfiltered-no-rerank", action="store_true", help="filtresiz geçiş rerank'sız (aday listesi)")
    ap.add_argument("--timing-sets", nargs="+", default=None,
                    help="süre yalnız bu setlerde --repeats tur ölçülür; diğerleri 1 tur (yalnız doğruluk)")
    a = ap.parse_args()

    items = load_questions(a.sets)
    timed = [it for it in items if not a.timing_sets or it["set"] in a.timing_sets]
    rest = [it for it in items if it not in timed]
    params = {**retrieval_params(), "sets": a.sets, "timing_sets": a.timing_sets or a.sets, "repeats": a.repeats,
              "warmup": a.warmup, "rerank": not a.no_rerank, "qdrant_mode": "embedded",
              "qdrant_reuse": __import__("pilot.index", fromlist=["REUSE"]).REUSE}
    log.info("%d soru: %d soru %d tur (süre + doğruluk), %d soru 1 tur (doğruluk)", len(items), len(timed),
             a.repeats, len(rest))
    memory = qdrant_memory()
    rows, timer = run_questions(timed, a.repeats, a.warmup, do_rerank=not a.no_rerank)
    if rest:
        rows += run_questions(rest, 1, 0, do_rerank=not a.no_rerank)[0]
    unf = None
    if a.unfiltered:
        log.info("filtresiz geçiş (%s)", "rerank'sız" if a.unfiltered_no_rerank else "rerank'lı")
        urows, utimer = run_questions(items, 1, 0, do_rerank=not (a.no_rerank or a.unfiltered_no_rerank),
                                      unfiltered=True)
        unf = {"rerank": not (a.no_rerank or a.unfiltered_no_rerank), "accuracy": summarize(urows),
               "timing": utimer.summary(), "questions": urows}
    from pilot import index
    index.close_shared()        # gömülü klasörü tek istemci açabilir; recall kendi istemcisini açar
    log.info("ANN recall: %d sorgu", a.recall_queries)
    recall = ann_recall(a.recall_queries) if a.recall_queries else None
    data = {"meta": meta(params), "accuracy": summarize(rows), "timing": timer.summary(),
            "ann_recall": recall, "memory": memory, "questions": rows, "unfiltered": unf}
    path = write_result(a.name, data, report_md(a.name, data))
    log.info("yazıldı: %s", path)
    acc = data["accuracy"]["all"]
    log.info("hit@1 %.2f hit@5 %.2f MRR %.2f · toplam p50 %s p95 %s", acc["hit@1"], acc["hit@5"], acc["mrr"],
             fmt_s(data["timing"]["total"]["p50"]), fmt_s(data["timing"]["total"]["p95"]))


if __name__ == "__main__":
    main()
