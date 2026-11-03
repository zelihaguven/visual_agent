"""Üçlü füzyon, rerank'sız: Qwen3-8B dense + bge-m3 dense + BM25, RRF ile (her kol PREFETCH_K aday).

İki dense kol ayrı koleksiyonlardan gelir (aynı korpus, farklı nokta kimlikleri); parçalar chunk_id ile eşlenir.
RRF pipeline'daki gibi: skor = Σ 1/(sıra + RRF_K); eşitlikte ilk dense kolun skoru, sonra chunk_id. İçindekiler satırı
elenir. Sorgu vektörleri bulut çağrısı olmadan: Qwen önbellekten (önbellekte olmayan soru atlanır), bge-m3 yerelde.
Çıktı bench.providers collect biçiminde (data/bench_cache/candidates_<tag>.json): candidate_report doğrudan okur.

Kullanım (Pilot klasöründe, Qdrant sunucusu açık):
    python -m bench.triple_fusion --tag rr10k_uclu --qwen-collection scale_qwen3_8b_10000 \\
        --bge-collection scale_bge_m3_10000 --sets questions questions_ek sekil_sorular aday_sorular --include-unapproved
"""
import argparse
import json
import logging
from typing import Any

from bench.common import KNOWN_SETS, load_questions, prepare

log = logging.getLogger("bench")
K_OUT = 20


def fuse(arms: list[list[Any]], limit: int, rrf_k: int) -> list[Any]:
    """arms: kol başına sıralı noktalar (payload'da chunk_id). İlk kol eşitlik bozmada kullanılır."""
    fused: dict[str, float] = {}
    point: dict[str, Any] = {}
    for arm in arms:
        for rank, p in enumerate(arm):
            cid = p.payload["chunk_id"]
            fused[cid] = fused.get(cid, 0.0) + 1.0 / (rank + rrf_k)
            point.setdefault(cid, p)
    first = {p.payload["chunk_id"]: p.score for p in arms[0]}
    order = sorted(fused, key=lambda c: (-fused[c], -first.get(c, float("-inf")), c))
    return [point[c] for c in order[:limit]]


def main() -> None:
    from bench.providers import CACHE_DIR, QueryEncoder, specs
    from bench.server import server_client
    from pilot import retrieve

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--qwen-collection", required=True)
    ap.add_argument("--bge-collection", required=True)
    ap.add_argument("--qwen-dense", default="short_rescore", choices=["full", "short_rescore"])
    ap.add_argument("--sets", nargs="+", default=list(KNOWN_SETS))
    ap.add_argument("--include-unapproved", action="store_true")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")

    qwen, bge = QueryEncoder(specs()["qwen3-8b"], 256), QueryEncoder(specs()["bge-m3-local-bm25"], 256)
    items = [(it, prepare(it["q"])) for it in load_questions(a.sets, include_unapproved=a.include_unapproved)]
    items = [(it, p) for it, p in items if not p["skip"] and not it.get("expect_clarify")]
    skipped = [it["qid"] for it, p in items if not qwen.cached(p["search_q"])]
    items = [(it, p) for it, p in items if it["qid"] not in skipped]
    qc = server_client()
    out: dict[str, Any] = {"questions": {}, "timing": {}, "skipped_offline": skipped}
    for n, (it, p) in enumerate(items, 1):
        qv, bv = qwen(p["search_q"], True), bge(p["search_q"], True)
        qd = out["questions"].setdefault(it["qid"], {
            "qid": it["qid"], "set": it["set"], "q": it["q"], "search_q": p["search_q"],
            "not_found": bool(it.get("expect_not_found")),
            "expect_docs": it.get("expect_docs", []), "expect_pages": it.get("expect_pages", [])})
        for mode in ("filtered", "unfiltered"):
            flt = retrieve._filter(None, p["doc_ids"] if mode == "filtered" else None)
            k = retrieve.PREFETCH_K
            arms = [retrieve.candidates(qc, qv, flt, "dense", collection=a.qwen_collection, dense_mode=a.qwen_dense,
                                        short_dim=256, fused_k=k),
                    retrieve.candidates(qc, bv, flt, "dense", collection=a.bge_collection, dense_mode="full", fused_k=k),
                    retrieve.candidates(qc, qv, flt, "sparse", collection=a.qwen_collection, sparse_name="bm25",
                                        fused_k=k)]
            qd[mode] = [{"chunk_id": x.payload["chunk_id"], "doc_id": x.payload["doc_id"], "pages": x.payload["pages"],
                         "chunk_type": x.payload.get("chunk_type"), "text": x.payload["text"],
                         "embed_text": x.payload.get("embed_text")}
                        for x in fuse(arms, K_OUT, retrieve.RRF_K)]
        if n % 25 == 0:
            log.info("%d/%d", n, len(items))
    qc.close()
    if qwen.cloud.stats["requests"]:
        raise RuntimeError(f"bulut çağrısı yapıldı: {qwen.cloud.stats}")
    out["params"] = {"key": "uclu", "tag": a.tag, "arms": [f"qwen3-8b:{a.qwen_dense}@{a.qwen_collection}",
                                                           f"bge-m3:full@{a.bge_collection}", "bm25"],
                     "PREFETCH_K": retrieve.PREFETCH_K, "RRF_K": retrieve.RRF_K, "FUSED_K": K_OUT,
                     "sets": list(a.sets), "include_unapproved": a.include_unapproved, "offline": True,
                     "cloud_stats": qwen.cloud.stats}
    path = CACHE_DIR / f"candidates_{a.tag}.json"
    path.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    log.info("yazıldı: %s (%d soru, atlanan %d)", path, len(out["questions"]), len(skipped))


if __name__ == "__main__":
    main()
