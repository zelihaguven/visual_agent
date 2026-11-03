"""Gömülü ve sunucu modunun aynı vektörlerle aynı sonucu verip vermediği: dense, sparse ve hibrit (RRF) kolları ayrı.

Kullanım (Pilot klasöründe, sunucu açık, koleksiyon kopyalanmış): python -m bench.mode_diff
Çıktı: eval/bench/genel/mod_farki_<tarih>.json ve .md. Fark varsa hangi kolda başladığı ve RRF skorları.
"""
import warnings

from qdrant_client import QdrantClient, models

from bench.common import KNOWN_SETS, load_questions, meta, prepare, write_result

warnings.filterwarnings("ignore")
K = 20


def run(qc: QdrantClient, dense, sparse, flt) -> dict[str, list]:
    out = {}
    for name, q, using in (("dense", dense, "dense"), ("sparse", sparse, "sparse")):
        r = qc.query_points("manuals", query=q, using=using, query_filter=flt, limit=30, with_payload=False)
        out[name] = [(p.id, round(p.score, 5)) for p in r.points]
    r = qc.query_points("manuals", prefetch=[models.Prefetch(query=dense, using="dense", filter=flt, limit=30),
                                             models.Prefetch(query=sparse, using="sparse", filter=flt, limit=30)],
                        query=models.FusionQuery(fusion=models.Fusion.RRF), limit=K, with_payload=False)
    out["rrf"] = [(p.id, round(p.score, 5)) for p in r.points]
    return out


def main() -> None:
    from pilot import retrieve
    from pilot.config import QDRANT_DIR
    from pilot.embed import embed
    from pilot.retrieve import _filter

    emb = QdrantClient(path=str(QDRANT_DIR))
    srv = QdrantClient(url="http://127.0.0.1:6333")
    rows = []
    for it in load_questions(KNOWN_SETS):
        p = prepare(it["q"])
        if p["skip"] or it.get("expect_clarify"):
            continue
        v = embed([p["search_q"]])[0]
        sp = models.SparseVector(indices=list(v["sparse"]), values=list(v["sparse"].values()))
        flt = _filter(None, p["doc_ids"])
        a, b = run(emb, v["dense"], sp, flt), run(srv, v["dense"], sp, flt)
        row = {"qid": it["qid"]}
        # pipeline'ın kendi araması (belirli sıralı RRF, rrf_fuse): iki modda da aynı istemci yolu
        got = {}
        for name, qc in (("embedded", emb), ("server", srv)):
            retrieve.search_client, retrieve.release = (lambda q=qc: q), (lambda _: None)
            got[name] = [h.chunk["chunk_id"] for h in retrieve.search(p["search_q"], doc_ids=p["doc_ids"],
                                                                      top_k=K, do_rerank=False)]
        row["search"] = {"same_order": got["embedded"] == got["server"],
                         "same_set": set(got["embedded"]) == set(got["server"]),
                         "first_diff": next((i for i, (x, y) in enumerate(zip(got["embedded"], got["server"]))
                                             if x != y), None)}
        for arm in ("dense", "sparse", "rrf"):
            ia, ib = [x[0] for x in a[arm]], [x[0] for x in b[arm]]
            row[arm] = {"same_order": ia == ib, "same_set": set(ia) == set(ib),
                        "first_diff": next((i for i, (x, y) in enumerate(zip(ia, ib)) if x != y), None),
                        "embedded_top5": a[arm][:5], "server_top5": b[arm][:5]}
        rows.append(row)
    emb.close()
    srv.close()
    n = len(rows)
    lines = ["# Gömülü ve sunucu modu: aynı vektörler, aynı sonuç mu?", "",
             f"{n} soru (pipeline gibi hazırlanmış sorgu, filtreli). Kollar: dense ve sparse ilk 30, RRF ilk {K}.", "",
             "rrf: Qdrant'ın kendi RRF'i (FusionQuery). search: pipeline araması (retrieve.search, belirli sıralı RRF).", "",
             "| Kol | sıra aynı | küme aynı |", "|---|---|---|"]
    for arm in ("dense", "sparse", "rrf", "search"):
        lines.append(f"| {arm} | {sum(r[arm]['same_order'] for r in rows)}/{n} | {sum(r[arm]['same_set'] for r in rows)}/{n} |")
    diff = [r for r in rows if not r["rrf"]["same_order"]]
    lines += ["", "RRF sırası farklı olan ilk 3 soru (ilk 5: kimlik, skor):", ""]
    for r in diff[:3]:
        lines += [f"- {r['qid']} (ilk fark: {r['rrf']['first_diff'] + 1}. sıra)",
                  f"  - gömülü: {r['rrf']['embedded_top5']}", f"  - sunucu: {r['rrf']['server_top5']}"]
    m = meta({"K": K})
    print(write_result("mod_farki", {"meta": m, "rows": rows}, "\n".join(lines) + "\n"))
    print("\n".join(line for line in lines if line.startswith("| ")))


if __name__ == "__main__":
    main()
